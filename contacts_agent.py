import json
import google.generativeai as genai

# --- 1. CONFIGURATION ---
SPECIFIC_LIST_CONFIG = {
    "Notes": ["Note_Title", "Note_Content", "Created_Time", "Owner"],
    "Deals": ["Deal_Name", "Stage", "Amount", "Closing_Date"],
    "Tasks": ["Subject", "Status", "Priority", "Due_Date"],
    "Events": ["Event_Title", "Start_DateTime", "End_DateTime"],
    "Calls": ["Subject", "Call_Type", "Call_Duration"],
    "Asset_Ownership_New": ["Name", "Asset_Type", "Value", "Ownership_Status"],
    "Loans": ["Name", "Amount"],
    "Insurance_Policy_New": ["Policy_Name", "Policy_Number", "Sum_Assured", "Premium"],
}

# [UPDATED] Schema with Targets
CONTACTS_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "First_Name", "type": "text"},
    {"api": "Last_Name", "type": "text"},
    {"api": "Full_Name", "type": "text"},
    {"api": "Account_Name", "type": "lookup", "target": "Accounts"},
    {"api": "Email", "type": "email"},
    {"api": "Phone", "type": "phone"},
    {"api": "Mobile", "type": "phone"},
    {"api": "Date_of_Birth", "type": "date"},
    {"api": "Street", "type": "text"},
    {"api": "City", "type": "text"},
    {"api": "State", "type": "text"},
    {"api": "Country", "type": "text"},
    {"api": "Client_Type", "type": "picklist"},
    {"api": "Referring_Client", "type": "lookup", "target": "Contacts"},
    {"api": "Primary_Advisor", "type": "userlookup", "target": "Users"},
]

class ContactsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in CONTACTS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        if not record: return "No Contact Data Available."

        if "items" in record:
            items = record["items"]
            if not items: return "No Contacts found."
            lines = [f"=== FOUND {len(items)} CONTACTS ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Contact #{i} ---")
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Full_Name" in item: lines.append(f"Name: {item['Full_Name']}")
                if "Email" in item: lines.append(f"Email: {item['Email']}")
                
                for k, v in item.items():
                    if k not in ["id", "Full_Name", "Email", "Tag"] and v:
                        val = v
                        if isinstance(v, dict) and "name" in v: val = v["name"]
                        lines.append(f"{k}: {val}")
            return "\n".join(lines)

        lines = ["=== CLIENT PROFILE ==="]
        for field in CONTACTS_SCHEMA:
            key = field['api']
            val = record.get(key)
            if isinstance(val, dict) and "name" in val: val = val["name"]
            if val in [None, ""]: 
                if key in ["Email", "Phone", "Mobile"]: val = "[Empty]"
                else: continue
            lines.append(f"{key}: {val}")

        lines.append("\n--- RELATED DETAILS ---")
        list_keys = [k for k, v in record.items() if isinstance(v, list) and k != "Tag"]
        for list_name in list_keys:
            items = record[list_name]
            if not items: continue
            clean_name = list_name.replace("Related_", "")
            lines.append(f"\n# {clean_name} ({len(items)} items)")
            config_key = next((k for k in SPECIFIC_LIST_CONFIG if k == clean_name), None)
            for i, item in enumerate(items, 1):
                row_parts = []
                if "id" in item: row_parts.append(f"ID: {item['id']}")
                if config_key:
                    for f in SPECIFIC_LIST_CONFIG[config_key]:
                        val = item.get(f)
                        if val: row_parts.append(f"{f}: {val}")
                else:
                    for k, v in item.items():
                        if isinstance(v, (str, int, float)) and "id" not in k.lower():
                            row_parts.append(f"{k}: {v}")
                        if len(row_parts) > 5: break
                lines.append(f"  {i}. " + " | ".join(row_parts))
        return "\n".join(lines)

    def generate_response(self, user_query: str, contact_data: dict, history: list = []) -> str:
        context_text = self.format_data_for_ai(contact_data)
        history_block = ""
        if history:
            history_block = "### HISTORY\n" + "\n".join([f"{m.get('role')}: {m.get('content')}" for m in history[-3:]])

        prompt = f"""
        You are an expert Private Wealth Manager Assistant.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### CLIENT PROFILE
        {context_text}

        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** Include `record_id` for updates.
        
        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Contacts", 
            "record_id": "12345",
            "data": {{ 
                "Last_Name": "REQUIRED_NAME",
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        """
        response = self.model.generate_content(prompt)
        return response.text