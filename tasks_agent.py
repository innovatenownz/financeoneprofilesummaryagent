import json
import google.generativeai as genai

TASKS_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Subject", "type": "text"},
    {"api": "Due_Date", "type": "date"},
    {"api": "Status", "type": "picklist"},
    {"api": "Priority", "type": "picklist"},
    {"api": "Who_Id", "type": "lookup", "target": "Contacts"}, # Contact
    {"api": "What_Id", "type": "lookup", "target": "Accounts"}, # Related To
    {"api": "Owner", "type": "ownerlookup", "target": "Users"},
    {"api": "Description", "type": "textarea"}
]

class TasksAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in TASKS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        if not record: return "No Task Data."
        if "items" in record:
            lines = [f"=== FOUND {len(record['items'])} TASKS ==="]
            for i, item in enumerate(record['items'], 1):
                lines.append(f"\n--- Task #{i} ---")
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Subject" in item: lines.append(f"Subject: {item['Subject']}")
                for k, v in item.items():
                    if k not in ["id", "Subject"]:
                        val = v["name"] if isinstance(v, dict) and "name" in v else v
                        if not val: val = "[Empty]"
                        lines.append(f"{k}: {val}")
            return "\n".join(lines)
        
        lines = ["=== TASK DETAILS ==="]
        for k, v in record.items():
            if isinstance(v, dict) and "name" in v: v = v["name"]
            lines.append(f"{k}: {v}")
        return "\n".join(lines)

    def generate_response(self, query, data, history=[]):
        context = self.format_data_for_ai(data)
        hist = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in history[-3:]])
        prompt = f"""
        You are an expert Task Manager.
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
            "module": "Tasks",
            "record_id": "123",
            "data": {{ "Subject": "REQUIRED", "Status": "Not Started" }}
        }}
        <<<END_ACTION>>>
        """
        return self.model.generate_content(prompt).text