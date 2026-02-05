import json
import google.generativeai as genai

# --- 1. CONFIGURATION ---

# Related List Configuration (for fetching details)
SPECIFIC_LIST_CONFIG = {
    "Notes": ["Note_Title", "Note_Content", "Created_Time", "Owner"],
    "Tasks": ["Subject", "Status", "Priority", "Due_Date"],
    "Calls": ["Subject", "Call_Type", "Call_Duration", "Call_Start_Time"],
    "Events": ["Event_Title", "Start_DateTime", "End_DateTime", "Location"],
    "Emails": ["Subject", "Status", "Sent_Time", "To"],
    "Attachments": ["File_Name", "Size", "Created_Time"],
    "Campaigns": ["Campaign_Name", "Type", "Status", "Expected_Revenue"]
}

# --- KNOWLEDGE BASE: LEADS SCHEMA ---
# [UPDATED] Added 'target' keys so main.py can resolve lookups automatically
LEADS_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Full_Name", "type": "text"},
    {"api": "First_Name", "type": "text"},
    {"api": "Last_Name", "type": "text"},
    {"api": "Company", "type": "text"},
    {"api": "Designation", "type": "text"},
    {"api": "Email", "type": "email"},
    {"api": "Phone", "type": "phone"},
    {"api": "Mobile", "type": "phone"},
    {"api": "Website", "type": "website"},
    {"api": "Lead_Status", "type": "picklist"},
    {"api": "Lead_Source", "type": "picklist"},
    {"api": "Rating", "type": "picklist"},
    {"api": "Interest_Level", "type": "picklist"},
    {"api": "Reason_for_Loss", "type": "picklist"},
    {"api": "Industry", "type": "picklist"},
    {"api": "Annual_Revenue", "type": "currency"},
    {"api": "No_of_Employees", "type": "integer"},
    {"api": "Lead_Type1", "type": "picklist"},
    {"api": "Owner", "type": "ownerlookup", "target": "Users"},
    
    # Address Fields
    {"api": "City", "type": "text"},
    {"api": "Country", "type": "picklist"},
    {"api": "State", "type": "picklist"},
    {"api": "Street", "type": "text"},
    {"api": "Zip_Code", "type": "text"},
    
    # Conversion Data (Lookups with Targets)
    {"api": "Converted__s", "type": "boolean"},
    {"api": "Converted_Date_Time", "type": "datetime"},
    {"api": "Converted_Account", "type": "lookup", "target": "Accounts"},
    {"api": "Converted_Contact", "type": "lookup", "target": "Contacts"},
    {"api": "Converted_Deal", "type": "lookup", "target": "Deals"},
    
    # Relationships
    {"api": "Referring_client", "type": "lookup", "target": "Contacts"},
    {"api": "Referring_account", "type": "lookup", "target": "Accounts"},
    {"api": "Primary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "Secondary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "Lead_Owners", "type": "multiuserlookup", "target": "Users"}
]

class LeadsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in LEADS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Lead JSON into a clean, readable text block.
        """
        if not record: return "No Lead Data Available."

        # === 1. LIST MODE (Context Switch / Search Results) ===
        if "items" in record:
            items = record["items"]
            if not items: return "No Leads found."
            
            lines = [f"=== FOUND {len(items)} LEADS ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Lead #{i} ---")
                
                # A. ALWAYS show identifiers
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Full_Name" in item: lines.append(f"Name: {item['Full_Name']}")
                
                # B. FORCE SHOW critical fields even if empty (for Updates)
                critical_fields = ["Lead_Status", "Company", "Email", "Phone", "Lead_Source"]
                
                for k, v in item.items():
                    if k not in ["id", "Full_Name", "Tag"]:
                        val_display = v
                        if isinstance(v, dict) and "name" in v: val_display = v["name"]
                        
                        # Show if value exists OR if it is critical
                        if v or k in critical_fields:
                            if not v and v is not False: val_display = "[Empty]"
                            lines.append(f"{k}: {val_display}")
            return "\n".join(lines)

        # === 2. SINGLE RECORD MODE ===
        lines = ["=== LEAD OVERVIEW ==="]

        # Check Conversion Status
        if record.get("Converted__s") or record.get("Converted_Date_Time"):
            lines.append("!!! THIS LEAD HAS BEEN CONVERTED !!!")
            conv_contact = record.get('Converted_Contact', {}).get('name', 'Unknown')
            conv_account = record.get('Converted_Account', {}).get('name', 'Unknown')
            lines.append(f"Converted To: Contact ({conv_contact}), Account ({conv_account})")

        # Process Standard Fields
        for field in LEADS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val: val = val["name"]
            
            # Formatting Currency
            if field['type'] == 'currency': val = f"${val}"
            
            # Formatting Multi-User Lookups
            if key == "Lead_Owners" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val if isinstance(u, dict)]
                val = ", ".join(names)

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
                    priority_keywords = ["subject", "name", "status", "date", "time"]
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

    def generate_response(self, user_query: str, lead_data: dict, history: list = []) -> str:
        """
        Generates a response answering the user's query about the sales lead.
        """
        context_text = self.format_data_for_ai(lead_data)

        # Format History
        history_block = ""
        if history:
            history_block = "### CONVERSATION HISTORY\n"
            for msg in history[-3:]:
                role = "User" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_block += f"{role}: {content}\n"

        prompt = f"""
        You are an expert Sales Development Representative (SDR) Assistant.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### LEAD CONTEXT
        {context_text}
        
        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** Include `record_id` for updates.
        - **Lookups:** If the user provides a Referring Account or Client, pass it as text. My system will convert it.
        - **Qualification:** Check 'Rating' and 'Interest Level'.
        - **Conversion:** If 'Converted', direct user to the Contact/Account.

        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Leads", 
            "record_id": "12345",
            "data": {{ 
                "Last_Name": "REQUIRED_NAME",
                "Company": "REQUIRED_COMPANY",
                "Lead_Status": "Pre-Qualified",
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text