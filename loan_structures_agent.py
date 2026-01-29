import json
import google.generativeai as genai
from datetime import date

# --- KNOWLEDGE BASE: LOAN STRUCTURES SCHEMA ---
LOAN_STRUCT_SCHEMA = [
    # Core Structure Info
    {"api": "Name", "type": "text"}, # Structure Name (e.g. "Split A - Fixed")
    {"api": "Loan_Structure_Type", "type": "picklist"}, # Fixed, Variable
    {"api": "Product", "type": "lookup (Product)"},
    {"api": "Status", "type": "picklist"},
    
    # Financials
    {"api": "Current_Balance", "type": "currency"},
    {"api": "Original_Balance", "type": "currency"},
    {"api": "Interest_Rate", "type": "percent"},
    {"api": "Monthly_Payment", "type": "currency"},
    {"api": "Frequency", "type": "picklist"}, # Monthly, Fortnightly
    
    # Terms & Expiry
    {"api": "Fixed_Period_End_Date", "type": "date"}, # Critical for refinance
    {"api": "Interest_Only", "type": "picklist"}, # Yes/No
    {"api": "Interest_only_End_Date", "type": "date"},
    {"api": "Next_Repayment_Date", "type": "date"},
    
    # Relationships
    {"api": "Loan", "type": "lookup (Parent Loan)"},
    
    # Advisory
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    
    # System
    {"api": "Record_Status__s", "type": "picklist"}
]

class LoanStructuresAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in LOAN_STRUCT_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Loan Structure JSON into a clean, readable text block.
        """
        if not record:
            return "No Loan Structure Data Available."

        lines = ["=== LOAN STRUCTURE (SPLIT) DETAILS ==="]

        # 1. Process Fields
        for field in LOAN_STRUCT_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Percent
            if field['type'] == 'percent':
                val = f"{val}%"
            
            # Formatting Currency
            if field['type'] == 'currency':
                val = f"${val}"

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, struct_data: dict) -> str:
        """
        Generates a response answering questions about the Loan Structure.
        """
        context_text = self.format_data_for_ai(struct_data)
        today = date.today().isoformat()

        prompt = f"""
        You are an expert Mortgage Broker & Credit Analyst.
        
        Your goal is to analyze this SPECIFIC LOAN SPLIT/STRUCTURE based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### STRUCTURE CONTEXT
        {context_text}
        (Current Date: {today})

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Rate Review:** Look at the 'Interest_Rate'. Is it competitive?
        - **Refinance Risk:** Check 'Fixed_Period_End_Date'. If it is past or within 90 days of today ({today}), flag it URGENTLY as a "Refinance Trigger".
        - **Repayment:** Explain the 'Monthly_Payment' and 'Frequency'.
        - **Context:** Mention which parent 'Loan' facility this belongs to.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text