import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: LOANS SCHEMA ---
LOANS_SCHEMA = [
    # Core Loan Info
    {"api": "Name", "type": "text"}, # Loan Facility Name
    {"api": "Loan_Type", "type": "picklist"}, # e.g. Mortgage, Business Loan
    {"api": "Record_Status__s", "type": "picklist"},
    
    # Financial Totals (Rollups)
    {"api": "Total_Current_Loan_Balance", "type": "rollup_summary"},
    {"api": "Total_Original_Loan_Balance", "type": "rollup_summary"},
    {"api": "Number_of_loans", "type": "rollup_summary"},
    
    # Critical Dates
    {"api": "Earliest_Fixed_Rate_Expiry", "type": "rollup_summary"}, # Refinance Trigger
    
    # Relationships & Security
    {"api": "Lender", "type": "lookup"},
    {"api": "Security", "type": "lookup"}, # Collateral
    {"api": "Real_Assets_Security", "type": "lookup"}, # Real Estate Collateral
    {"api": "Deal", "type": "lookup (Deal)"},
    
    # Advisory Team
    {"api": "Primary_Advisor", "type": "userlookup"},
    
    # System
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Locked__s", "type": "boolean"}
]

class LoansAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in LOANS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Loan JSON into a clean, readable text block.
        """
        if not record:
            return "No Loan Data Available."

        lines = ["=== LOAN FACILITY DETAILS ==="]

        # 1. Process Fields
        for field in LOANS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Currency (Rollups are usually numbers/currency)
            if "Balance" in key and isinstance(val, (int, float, str)):
                 lines.append(f"{key}: ${val}")
                 continue

            lines.append(f"{key}: {val}")

        # 2. Add Debt Utilization Context
        try:
            current = float(record.get("Total_Current_Loan_Balance", 0))
            original = float(record.get("Total_Original_Loan_Balance", 0))
            if original > 0:
                paid_off = original - current
                percent = round((paid_off / original) * 100, 1)
                lines.append(f"\n[Analysis]: {percent}% of original principal paid off.")
        except:
            pass

        return "\n".join(lines)

    def generate_response(self, user_query: str, loan_data: dict) -> str:
        """
        Generates a response answering questions about the Loan.
        """
        context_text = self.format_data_for_ai(loan_data)

        prompt = f"""
        You are an expert Debt Manager & Credit Analyst.
        
        Your goal is to analyze this LOAN PORTFOLIO based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### LOAN CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Total Debt:** State the 'Total_Current_Loan_Balance'.
        - **Risk Check:** Check 'Earliest_Fixed_Rate_Expiry'. If it's soon, warn about refinancing.
        - **Collateral:** Identify what is securing this loan ('Security' or 'Real_Assets_Security').
        - **Lender:** Identify the financial institution providing the loan.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text