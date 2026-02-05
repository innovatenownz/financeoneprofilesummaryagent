import json
import google.generativeai as genai

# --- 1. CONFIGURATION ---
SPECIFIC_LIST_CONFIG = {
    "Notes": ["Note_Title", "Note_Content", "Created_Time", "Owner"],
    "Expense_List_New": ["Name", "Amount", "Frequency"] # Subform
}

# --- KNOWLEDGE BASE: EXPENSE PROFILE SCHEMA ---
EXPENSE_PROFILE_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Name", "type": "text"},
    {"api": "Total_Monthly_Expenses", "type": "currency"},
    {"api": "Total_Household_Exp_Fixed", "type": "formula"},
    {"api": "Total_Individual_Exp_Fixed", "type": "formula"},
    {"api": "Total_Fixed_Expenses", "type": "formula"},
    {"api": "Locked__s", "type": "boolean"},
    {"api": "Fact_Find", "type": "lookup", "target": "Fact_Find_New"},
    {"api": "Expense_List_New", "type": "static_subform"},
    {"api": "Expense_List_Variable", "type": "subform"},
    {"api": "Primary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "Secondary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "Expense_Profile_Owners", "type": "multiuserlookup", "target": "Users"}
]

class ExpenseProfileAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in EXPENSE_PROFILE_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        if not record: return "No Expense Profile Data Available."
        
        # LIST MODE
        if "items" in record:
            items = record["items"]
            if not items: return "No Expense Profiles found."
            lines = [f"=== FOUND {len(items)} PROFILES ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Profile #{i} ---")
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Name" in item: lines.append(f"Name: {item['Name']}")
                if "Total_Monthly_Expenses" in item: lines.append(f"Total Monthly: {item['Total_Monthly_Expenses']}")
            return "\n".join(lines)

        # DETAIL MODE
        lines = ["=== EXPENSE PROFILE DETAILS ==="]
        for field in EXPENSE_PROFILE_SCHEMA:
            key = field['api']
            val = record.get(key)
            if val:
                if isinstance(val, dict) and "name" in val: val = val["name"]
                lines.append(f"{key}: {val}")
        return "\n".join(lines)

    def generate_response(self, user_query: str, profile_data: dict, history: list = []) -> str:
        context_text = self.format_data_for_ai(profile_data)
        prompt = f"""
        You are an expert Financial Planner.
        ### SCHEMA
        {self.schema_string}
        ### DATA
        {context_text}
        ### QUESTION
        "{user_query}"
        
        If updating or creating, use:
        <<<ACTION>>>
        {{ "action": "create"|"update", "module": "Expense_Profile_New", "data": {{ ... }} }}
        <<<END_ACTION>>>
        
        Answer:
        """
        response = self.model.generate_content(prompt)
        return response.text