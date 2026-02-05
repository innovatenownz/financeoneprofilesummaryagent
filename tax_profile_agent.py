import json
import google.generativeai as genai

# --- 1. CONFIGURATION ---

# Related List Configuration
# Standard lists usually available for custom modules
SPECIFIC_LIST_CONFIG = {
    "Notes": ["Note_Title", "Note_Content", "Created_Time", "Owner"],
    "Tasks": ["Subject", "Status", "Priority", "Due_Date"],
    "Calls": ["Subject", "Call_Type", "Call_Duration", "Call_Start_Time"],
    "Events": ["Event_Title", "Start_DateTime", "End_DateTime", "Location"],
    "Emails": ["Subject", "Status", "Sent_Time", "To"],
    "Attachments": ["File_Name", "Size", "Created_Time"]
}

# --- KNOWLEDGE BASE: TAX PROFILE SCHEMA ---
TAX_PROFILE_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Name", "type": "text"}, # Tax Profile Name (Auto Number)
    {"api": "Profile_Name", "type": "text"}, # Descriptive Name
    {"api": "Record_Status__s", "type": "picklist"},
    {"api": "Owner", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Modified_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Modified_Time", "type": "datetime"},
    {"api": "Last_Activity_Time", "type": "datetime"},
    {"api": "Email", "type": "email"},
    {"api": "Secondary_Email", "type": "email"},
    {"api": "Email_Opt_Out", "type": "boolean"},
    {"api": "Tag", "type": "text"},
    {"api": "Unsubscribed_Mode", "type": "picklist"},
    {"api": "Unsubscribed_Time", "type": "datetime"},
    
    # Tax Specifics
    {"api": "Taxpayer_ID", "type": "text"},
    {"api": "Tax_Status", "type": "picklist"},
    {"api": "Status", "type": "picklist"},
    {"api": "Jurisdiction", "type": "picklist"},
    {"api": "Financial_Year_End", "type": "date"},
    {"api": "Reporting_Obligations", "type": "multiselectpicklist"},
    {"api": "Locked__s", "type": "boolean"},
    
    # Relationships (Lookups with Targets)
    {"api": "Client", "type": "lookup", "target": "Contacts"},
    {"api": "Household", "type": "lookup", "target": "Accounts"},
    
    # Advisory Team
    {"api": "Primary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "Secondary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "Tax_Profile_Owners", "type": "multiuserlookup", "target": "Users"}
]

class TaxProfileAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in TAX_PROFILE_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Tax Profile JSON into a clean, readable text block.
        """
        if not record: return "No Tax Profile Data Available."

        # === 1. LIST MODE (Context Switch / Search Results) ===
        if "items" in record:
            items = record["items"]
            if not items: return "No Tax Profiles found."
            
            lines = [f"=== FOUND {len(items)} TAX PROFILES ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Profile #{i} ---")
                
                # A. ALWAYS show identifiers
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Name" in item: lines.append(f"Ref: {item['Name']}")
                if "Profile_Name" in item: lines.append(f"Name: {item['Profile_Name']}")
                
                # B. FORCE SHOW critical fields even if empty
                critical_fields = ["Tax_Status", "Jurisdiction", "Client", "Household", "Financial_Year_End"]
                
                for k, v in item.items():
                    if k not in ["id", "Name", "Profile_Name", "Tag"]:
                        val_display = v
                        if isinstance(v, dict) and "name" in v: val_display = v["name"]
                        
                        # Show if value exists OR if it is critical
                        if v or k in critical_fields:
                            if not v and v is not False: val_display = "[Empty]"
                            lines.append(f"{k}: {val_display}")
            return "\n".join(lines)

        # === 2. SINGLE RECORD MODE ===
        lines = ["=== TAX PROFILE DETAILS ==="]

        # Process Standard Fields
        for field in TAX_PROFILE_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val: val = val["name"]
            
            # Formatting Multi-User Lookups
            if key == "Tax_Profile_Owners" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val if isinstance(u, dict)]
                val = ", ".join(names)
            
            # Formatting Multi-Select Picklists
            if isinstance(val, list) and isinstance(val[0], str):
                val = ", ".join(val)

            # Formatting Booleans
            if field['type'] == 'boolean': val = "Yes" if val else "No"

            clean_key = key.replace("_", " ")
            lines.append(f"{clean_key}: {val}")

        # Process Related Lists
        lines.append("\n--- RELATED ACTIVITY ---")
        list_keys = [k for k, v in record.items() if isinstance(v, list) and k != "Tag"]
        
        found_details = False
        for list_name in list_keys:
            items = record[list_name]
            if not items: continue

            clean_name = list_name.replace("Related_", "")
            lines.append(f"\n# {clean_name} ({len(items)} items)")
            found_details = True
            
            config_key = next((k for k in SPECIFIC_LIST_CONFIG if k == clean_name), None)

            for i, item in enumerate(items, 1):
                row_parts = []
                if "id" in item: row_parts.append(f"ID: {item['id']}")
                
                if config_key:
                    for f in SPECIFIC_LIST_CONFIG[config_key]:
                        val = item.get(f)
                        if val: row_parts.append(f"{f}: {val}")
                else:
                    # Auto-Detect
                    priority_keywords = ["subject", "name", "status", "date"]
                    def key_func(k):
                        low = k.lower()
                        for idx, kw in enumerate(priority_keywords):
                            if kw in low: return idx
                        return len(priority_keywords)
                    sorted_keys = sorted(item.keys(), key=key_func)
                    
                    count = 0
                    for k in sorted_keys:
                        val = item.get(k)
                        if val and isinstance(val, (str, int, float)) and k.lower() != "id":
                            row_parts.append(f"{k}: {val}")
                            count += 1
                        if count >= 3: break
                
                lines.append(f"  {i}. " + " | ".join(row_parts))

        if not found_details: lines.append("(No recent notes or activities found)")

        return "\n".join(lines)

    def generate_response(self, user_query: str, tax_data: dict, history: list = []) -> str:
        """
        Generates a response answering questions about the Tax Profile.
        """
        context_text = self.format_data_for_ai(tax_data)

        # Format History
        history_block = ""
        if history:
            history_block = "### CONVERSATION HISTORY\n"
            for msg in history[-3:]:
                role = "User" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_block += f"{role}: {content}\n"

        prompt = f"""
        You are an expert Tax Accountant & Compliance Officer.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### TAX PROFILE CONTEXT
        {context_text}
        
        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** Include `record_id` for updates.
        - **Lookups:** If the user provides a Client Name or Household Name, pass it as text. My system will convert it.
        - **Compliance:** Check 'Financial Year End' and 'Reporting Obligations'.
        - **Identity:** Identify the 'Taxpayer ID' and 'Jurisdiction'.

        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Tax_profiles", 
            "record_id": "12345",
            "data": {{ 
                "Profile_Name": "REQUIRED_NAME",
                "Tax_Status": "Active",
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text