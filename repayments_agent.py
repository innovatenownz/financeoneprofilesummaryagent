import json
import google.generativeai as genai

# --- CONFIGURATION ---
SPECIFIC_LIST_CONFIG = {
    "Notes": ["Note_Title", "Note_Content", "Created_Time"]
}

# --- SCHEMA: REPAYMENT SCHEDULES ---
REPAYMENTS_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Name", "type": "text"}, # Auto Number or Reference
    {"api": "Due_Date", "type": "date"},
    {"api": "Payment_Date", "type": "date"},
    {"api": "Amount", "type": "currency"},
    {"api": "Status", "type": "picklist"}, # e.g. Paid, Overdue
    {"api": "Loan", "type": "lookup", "target": "Loans_New"}, # Linked Loan
    {"api": "Interest_Component", "type": "currency"},
    {"api": "Principal_Component", "type": "currency"},
    {"api": "Balance", "type": "currency"}
]

class RepaymentsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in REPAYMENTS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        if not record: return "No Repayment Data."
        
        # LIST MODE
        if "items" in record:
            lines = [f"=== FOUND {len(record['items'])} REPAYMENTS ==="]
            for i, item in enumerate(record['items'], 1):
                lines.append(f"{i}. {item.get('Name')} | Due: {item.get('Due_Date')} | Amt: {item.get('Amount')}")
            return "\n".join(lines)

        # DETAIL MODE
        lines = ["=== REPAYMENT SCHEDULE DETAILS ==="]
        for field in REPAYMENTS_SCHEMA:
            k = field['api']
            v = record.get(k)
            if v:
                if isinstance(v, dict) and "name" in v: v = v["name"]
                lines.append(f"{k}: {v}")
        return "\n".join(lines)

    def generate_response(self, query: str, data: dict, history: list = []) -> str:
        context = self.format_data_for_ai(data)
        prompt = f"""
        Role: Loan Repayment Analyst.
        Schema: {self.schema_string}
        Data: {context}
        User Question: "{query}"
        
        Action Protocol:
        <<<ACTION>>>
        {{ "action": "create"|"update", "module": "Repayment_Schedules", "data": {{ ... }} }}
        <<<END_ACTION>>>
        
        Answer:
        """
        return self.model.generate_content(prompt).text