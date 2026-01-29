import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: EXPENSE PROFILE SCHEMA ---
EXPENSE_SCHEMA = [
    # Core Profile Info
    {"api": "Name", "type": "text"}, # Profile Name
    {"api": "Record_Status__s", "type": "picklist"},
    
    # Financial Totals
    {"api": "Total_Monthly_Expenses", "type": "currency"},
    {"api": "Total_Fixed_Expenses", "type": "formula (currency)"},
    {"api": "Total_Household_Exp_Fixed", "type": "formula (currency)"},
    {"api": "Total_Individual_Exp_Fixed", "type": "formula (currency)"},
    
    # Detailed Expense Lists (Subforms)
    {"api": "Expense_List_New", "type": "static_subform"}, # Fixed Expenses
    {"api": "Expense_List_Variable", "type": "subform"},   # Variable Expenses
    
    # Relationships
    {"api": "Fact_Find", "type": "lookup (Fact Find)"},
    
    # Advisory Team
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    {"api": "Expense_Profile_Owners", "type": "multiuserlookup"},
    
    # System
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Locked__s", "type": "boolean"}
]

class ExpenseProfileAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in EXPENSE_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Expense Profile JSON into a clean, readable text block.
        """
        if not record:
            return "No Expense Profile Data Available."

        lines = ["=== EXPENSE PROFILE DETAILS ==="]

        # 1. Process Fields
        for field in EXPENSE_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Currency
            if "currency" in field['type']:
                val = f"${val}"
            
            # Formatting Multi-User Lookups
            if key == "Expense_Profile_Owners" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val]
                val = ", ".join(names)

            # Formatting Subforms (Expense Lines)
            if "subform" in field['type'] and isinstance(val, list):
                lines.append(f"\n--- {key.replace('_', ' ')} ---")
                for i, item in enumerate(val, 1):
                    # Try to find standard expense keys (Name, Amount, Frequency)
                    # Adjust 'Expense_Name' or 'Amount' based on your actual subform API names
                    name = item.get("Expense_Name") or item.get("Name") or "Item"
                    amount = item.get("Amount") or item.get("Monthly_Amount") or "0"
                    lines.append(f"  {i}. {name}: ${amount}")
                continue

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, expense_data: dict) -> str:
        """
        Generates a response answering questions about the Expense Profile.
        """
        context_text = self.format_data_for_ai(expense_data)

        prompt = f"""
        You are an expert Budget Analyst & Financial Planner.
        
        Your goal is to analyze this EXPENSE PROFILE based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### EXPENSE CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Total Outflow:** State the 'Total_Monthly_Expenses' clearly.
        - **Structure:** Compare 'Total_Fixed_Expenses' (Needs) vs Variable Expenses (Wants) if data is available.
        - **Household vs Individual:** Note the split between 'Total_Household_Exp_Fixed' and 'Total_Individual_Exp_Fixed'.
        - **Details:** If subform items are listed (e.g., Mortgage, Utilities), mention the largest expenses.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text