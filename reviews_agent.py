import json
import google.generativeai as genai

# --- 1. CONFIGURATION ---
SPECIFIC_LIST_CONFIG = {
    "Notes": ["Note_Title", "Note_Content", "Created_Time", "Owner"],
    "Tasks": ["Subject", "Status", "Priority", "Due_Date"],
    "Calls": ["Subject", "Call_Type", "Call_Duration", "Call_Start_Time"],
    "Events": ["Event_Title", "Start_DateTime", "End_DateTime", "Location"],
    "Emails": ["Subject", "Status", "Sent_Time", "To"],
    "Attachments": ["File_Name", "Size", "Created_Time"]
}

# --- KNOWLEDGE BASE: REVIEWS SCHEMA ---
# [UPDATED] Added 'target' keys
REVIEWS_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Name", "type": "text"}, # Review Name
    {"api": "Record_Status__s", "type": "picklist"},
    {"api": "Owner", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Modified_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Modified_Time", "type": "datetime"},
    {"api": "Last_Activity_Time", "type": "datetime"},
    {"api": "Email_Opt_Out", "type": "boolean"},
    {"api": "Tag", "type": "text"},
    {"api": "Unsubscribed_Mode", "type": "picklist"},
    {"api": "Unsubscribed_Time", "type": "datetime"},
    
    # Review Details
    {"api": "Type_of_review", "type": "picklist"}, 
    {"api": "Area_Reviewed", "type": "picklist"},
    {"api": "Review_Status", "type": "picklist"},
    {"api": "Date_initiated", "type": "date"},
    {"api": "Date_completed", "type": "date"},
    
    # Outcomes & Actions
    {"api": "Discussion_Summary", "type": "textarea"},
    {"api": "Change_and_update_in_client_situation_and_goals", "type": "textarea"},
    {"api": "Recommended_Actions", "type": "textarea"},
    {"api": "Identify_Next_Steps", "type": "textarea"},
    {"api": "Details_Received", "type": "boolean"},
    
    # Financial & Compliance
    {"api": "Amount", "type": "currency"},
    {"api": "Contribution_Date", "type": "date"},
    {"api": "FUM", "type": "picklist"},
    {"api": "Min_Client_Signatures_Required", "type": "picklist"},
    {"api": "IMS_Report", "type": "picklist"},
    
    # Linked Entities (Lookups with Targets)
    {"api": "Account_Reviewed", "type": "lookup", "target": "Accounts"},
    {"api": "Review_Contact", "type": "lookup", "target": "Contacts"},
    {"api": "Portfolio", "type": "lookup", "target": "Investment_portfolios"},
    {"api": "Lending", "type": "lookup", "target": "Loans"},
    {"api": "Insurances", "type": "lookup", "target": "Insurance_Policy_New"},
    
    # Advisory Team
    {"api": "Review_Owners", "type": "multiuserlookup", "target": "Users"}
]

class ReviewsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in REVIEWS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        if not record: return "No Review Data Available."

        # === LIST MODE ===
        if "items" in record:
            items = record["items"]
            if not items: return "No Reviews found."
            
            lines = [f"=== FOUND {len(items)} REVIEWS ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Review #{i} ---")
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Name" in item: lines.append(f"Name: {item['Name']}")
                
                critical_fields = ["Review_Status", "Type_of_review", "Date_initiated", "Account_Reviewed"]
                for k, v in item.items():
                    if k not in ["id", "Name", "Tag"]:
                        val_display = v
                        if isinstance(v, dict) and "name" in v: val_display = v["name"]
                        if v or k in critical_fields:
                            if not v: val_display = "[Empty]"
                            lines.append(f"{k}: {val_display}")
            return "\n".join(lines)

        # === SINGLE RECORD MODE ===
        lines = ["=== REVIEW DETAILS ==="]
        for field in REVIEWS_SCHEMA:
            key = field['api']
            val = record.get(key)
            if val in [None, "", [], {}]: continue
            
            if isinstance(val, dict) and "name" in val: val = val["name"]
            if field['type'] == 'currency': val = f"${val}"
            if key == "Review_Owners" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val if isinstance(u, dict)]
                val = ", ".join(names)
            if field['type'] == 'boolean': val = "Yes" if val else "No"

            lines.append(f"{key}: {val}")

        # Related Lists
        lines.append("\n--- RELATED ACTIVITY ---")
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
                        if len(row_parts) > 3: break
                lines.append(f"  {i}. " + " | ".join(row_parts))
        return "\n".join(lines)

    def generate_response(self, user_query: str, review_data: dict, history: list = []) -> str:
        context_text = self.format_data_for_ai(review_data)
        history_block = ""
        if history:
            history_block = "### HISTORY\n" + "\n".join([f"{m.get('role')}: {m.get('content')}" for m in history[-3:]])

        prompt = f"""
        You are an expert Compliance Officer & Financial Advisor Assistant.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### REVIEW CONTEXT
        {context_text}
        
        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** Include `record_id` for updates.
        - **Lookups:** If the user provides an Account Name, pass it as text. My system will convert it.
        - **Summary:** Summarize 'Discussion Summary' and 'Recommended Actions'.

        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Reviews", 
            "record_id": "12345",
            "data": {{ 
                "Name": "REQUIRED_NAME",
                "Review_Status": "In Progress",
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        """
        response = self.model.generate_content(prompt)
        return response.text