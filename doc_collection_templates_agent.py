import json
import google.generativeai as genai

# --- 1. CONFIGURATION ---

# Related List Configuration
SPECIFIC_LIST_CONFIG = {
    "Notes": ["Note_Title", "Note_Content", "Created_Time", "Owner"],
    "Tasks": ["Subject", "Status", "Priority", "Due_Date"],
    "Calls": ["Subject", "Call_Type", "Call_Duration", "Call_Start_Time"],
    "Events": ["Event_Title", "Start_DateTime", "End_DateTime", "Location"],
    "Attachments": ["File_Name", "Size", "Created_Time"],
    "Documents_Required": ["Document_Name", "Description", "Mandatory"] # Assuming subform structure based on name
}

# --- KNOWLEDGE BASE: DOC COLLECTION TEMPLATES SCHEMA ---
DOC_COLLECTION_TEMPLATES_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Name", "type": "text"}, # Template Name
    {"api": "Record_Status__s", "type": "picklist"},
    {"api": "Owner", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Modified_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Modified_Time", "type": "datetime"},
    {"api": "Last_Activity_Time", "type": "datetime"},
    {"api": "Tag", "type": "text"},
    {"api": "Unsubscribed_Mode", "type": "picklist"},
    {"api": "Unsubscribed_Time", "type": "datetime"},
    {"api": "Email", "type": "email"},
    {"api": "Secondary_Email", "type": "email"},
    {"api": "Email_Opt_Out", "type": "boolean"},
    
    # Template Details
    {"api": "Doc_Collection_Type", "type": "picklist"}, # e.g. Onboarding, Loan Application
    {"api": "Applicable_Entities", "type": "picklist"}, # e.g. Individual, Company
    {"api": "Applicable_Incomes", "type": "picklist"}, # e.g. Salary, Self-Employed
    {"api": "Record_Image", "type": "profileimage"},
    {"api": "Locked__s", "type": "boolean"},
    
    # Subform
    {"api": "Documents_Required", "type": "subform"}
]

class DocCollectionTemplatesAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in DOC_COLLECTION_TEMPLATES_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Doc Collection Template JSON into a clean, readable text block.
        """
        if not record: return "No Doc Collection Template Data Available."

        # === 1. LIST MODE (Context Switch / Search Results) ===
        if "items" in record:
            items = record["items"]
            if not items: return "No Doc Collection Templates found."
            
            lines = [f"=== FOUND {len(items)} TEMPLATES ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Template #{i} ---")
                
                # A. ALWAYS show identifiers
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Name" in item: lines.append(f"Name: {item['Name']}")
                
                # B. FORCE SHOW critical fields
                critical_fields = ["Doc_Collection_Type", "Applicable_Entities", "Applicable_Incomes"]
                
                for k, v in item.items():
                    if k not in ["id", "Name", "Tag"]:
                        val_display = v
                        if isinstance(v, dict) and "name" in v: val_display = v["name"]
                        
                        # Show if value exists OR if it is critical
                        if v or k in critical_fields:
                            if not v and v is not False: val_display = "[Empty]"
                            lines.append(f"{k}: {val_display}")
            return "\n".join(lines)

        # === 2. SINGLE RECORD MODE ===
        lines = ["=== DOC COLLECTION TEMPLATE DETAILS ==="]

        # Process Standard Fields
        for field in DOC_COLLECTION_TEMPLATES_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val: val = val["name"]
            
            # Formatting Subforms
            if field['type'] == 'subform' and isinstance(val, list):
                lines.append(f"\n--- {key} (Subform) ---")
                for i, row in enumerate(val, 1):
                    details = []
                    for k, v in row.items():
                        if v and k not in ["id", "s_id"]:
                            if isinstance(v, dict) and "name" in v: v = v["name"]
                            details.append(f"{k}: {v}")
                    lines.append(f"  {i}. " + ", ".join(details))
                continue

            # Formatting Booleans
            if field['type'] == 'boolean': val = "Yes" if val else "No"

            clean_key = key.replace("_", " ")
            lines.append(f"{clean_key}: {val}")

        # Process Related Lists
        lines.append("\n--- RELATED ACTIVITY ---")
        list_keys = [k for k, v in record.items() if isinstance(v, list) and k != "Tag" and "Documents_Required" not in k]
        
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

    def generate_response(self, user_query: str, template_data: dict, history: list = []) -> str:
        """
        Generates a response answering questions about the Doc Collection Template.
        """
        context_text = self.format_data_for_ai(template_data)

        # Format History
        history_block = ""
        if history:
            history_block = "### CONVERSATION HISTORY\n"
            for msg in history[-3:]:
                role = "User" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_block += f"{role}: {content}\n"

        prompt = f"""
        You are an expert Document Controller & Compliance Officer.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### TEMPLATE CONTEXT
        {context_text}
        
        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** Include `record_id` for updates.
        - **Scope:** Identify 'Applicable Entities' and 'Doc Collection Type'.
        - **Content:** List items from the 'Documents Required' subform if asked about contents.

        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Doc_Collection_Templates", bb
            "record_id": "12345",
            "data": {{ 
                "Name": "REQUIRED_TEMPLATE_NAME",
                "Doc_Collection_Type": "Onboarding",
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text