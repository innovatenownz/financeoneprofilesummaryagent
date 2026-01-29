import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: INVESTMENT PORTFOLIOS SCHEMA ---
PORTFOLIO_SCHEMA = [
    # Core Identity
    {"api": "Name", "type": "text"}, # Portfolio Name
    {"api": "Portfolio_ID", "type": "text"},
    {"api": "Portfolio_status", "type": "picklist"}, # Active, Closed
    {"api": "Deal", "type": "lookup (Deal)"},
    
    # Dates & Compliance
    {"api": "Original_setup_date", "type": "date"},
    {"api": "Last_Review_Date", "type": "date"},
    {"api": "Next_Review_Date", "type": "formula (date)"}, # Critical for alerts
    {"api": "Review_frequency", "type": "picklist"},
    {"api": "Minimum_Signatures", "type": "integer"}, # Operational requirement
    
    # Ownership Structure (Subform)
    {"api": "Portfolio_Owners", "type": "subform"}, # List of trustees/owners
    
    # Advisory Team
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    {"api": "Investment_Portfolios_Owners", "type": "multiuserlookup"},
    
    # System
    {"api": "Record_Status__s", "type": "picklist"},
    {"api": "Created_Time", "type": "datetime"}
]

class InvestmentPortfoliosAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in PORTFOLIO_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Investment Portfolio JSON into a clean, readable text block.
        """
        if not record:
            return "No Investment Portfolio Data Available."

        lines = ["=== INVESTMENT PORTFOLIO DETAILS ==="]

        # 1. Process Fields
        for field in PORTFOLIO_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Subforms (Portfolio Owners)
            if key == "Portfolio_Owners" and isinstance(val, list):
                lines.append("\n--- PORTFOLIO OWNERS / SIGNATORIES ---")
                for i, owner in enumerate(val, 1):
                    # Adjust 'Name' or 'Owner_Name' based on actual subform API
                    owner_name = owner.get("Name") or owner.get("Owner_Name") or "Unknown"
                    lines.append(f"  {i}. {owner_name}")
                continue

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, portfolio_data: dict) -> str:
        """
        Generates a response answering questions about the Investment Portfolio.
        """
        context_text = self.format_data_for_ai(portfolio_data)

        prompt = f"""
        You are an expert Investment Portfolio Manager & Compliance Officer.
        
        Your goal is to analyze this INVESTMENT PORTFOLIO based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### PORTFOLIO CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Compliance Check:** Look at 'Next_Review_Date'. Is it overdue or approaching? Mention the 'Review_frequency'.
        - **Operations:** Note the 'Minimum_Signatures' required for changes.
        - **Structure:** List the people in 'PORTFOLIO OWNERS'.
        - **Status:** Confirm if the portfolio is 'Active' ('Portfolio_status').
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text