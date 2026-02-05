import json
import google.generativeai as genai

CALLS_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Subject", "type": "text"},
    {"api": "Call_Type", "type": "picklist"}, # Inbound/Outbound
    {"api": "Call_Start_Time", "type": "datetime"},
    {"api": "Call_Duration", "type": "text"},
    {"api": "Who_Id", "type": "lookup", "target": "Contacts"},
    {"api": "What_Id", "type": "lookup", "target": "Accounts"},
    {"api": "Owner", "type": "ownerlookup", "target": "Users"},
    {"api": "Description", "type": "textarea"}, # Call Result
    {"api": "Call_Result", "type": "text"}
]

class CallsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in CALLS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        if not record: return "No Call Data."
        if "items" in record:
            lines = [f"=== FOUND {len(record['items'])} CALLS ==="]
            for i, item in enumerate(record['items'], 1):
                lines.append(f"\n--- Call #{i} ---")
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Subject" in item: lines.append(f"Subject: {item['Subject']}")
                for k, v in item.items():
                    if k not in ["id", "Subject"]:
                        val = v["name"] if isinstance(v, dict) and "name" in v else v
                        if not val: val = "[Empty]"
                        lines.append(f"{k}: {val}")
            return "\n".join(lines)
        
        lines = ["=== CALL DETAILS ==="]
        for k, v in record.items():
            if isinstance(v, dict) and "name" in v: v = v["name"]
            lines.append(f"{k}: {v}")
        return "\n".join(lines)

    def generate_response(self, query, data, history=[]):
        context = self.format_data_for_ai(data)
        hist = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in history[-3:]])
        prompt = f"""
        You are an expert Call Logger.
        ### DATA
        {context}
        ### HISTORY
        {hist}
        ### QUERY
        "{query}"
        ### INSTRUCTIONS
        - Answer based on data.
        - Updates need 'record_id'.
        
        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Calls",
            "record_id": "123",
            "data": {{ "Subject": "REQUIRED", "Call_Type": "Outbound" }}
        }}
        <<<END_ACTION>>>
        """
        return self.model.generate_content(prompt).text