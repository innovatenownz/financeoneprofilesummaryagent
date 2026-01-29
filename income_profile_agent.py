import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: INCOME PROFILE SCHEMA ---
INCOME_SCHEMA = [
    # Core Profile Info
    {"api": "Name", "type": "text"}, # Profile Name
    {"api": "Income_Profile_Type", "type": "picklist"}, # e.g. Employment, Business, Retirement
    {"api": "Record_Status__s", "type": "picklist"},
    
    # Financial Totals (The Rollups are key here)
    {"api": "Total_Annual_Income", "type": "currency"},
    {"api": "Total_Active_Income_Annual1", "type": "rollup_summary"}, # Salary/Business
    {"api": "Total_Asset_Income_Annual1", "type": "rollup_summary"}, # Investments
    {"api": "Total_Real_estate_Income_Annual", "type": "rollup_summary"},
    {"api": "Total_Investment_holding_Income_Annual", "type": "rollup_summary"},
    
    # Relationships
    {"api": "Client", "type": "lookup (Contact)"},
    {"api": "Household", "type": "lookup (Account)"},
    {"api": "Fact_Find", "type": "lookup (Custom)"}, # Link to data gathering
    
    # Advisory Team
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    {"api": "Income_Profile_Owners", "type": "multiuserlookup"},
    
    # System
    {"api": "Created_Time", "type": "datetime"}
]

class IncomeProfileAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in INCOME_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Income Profile JSON into a clean, readable text block.
        """
        if not record:
            return "No Income Profile Data Available."

        lines = ["=== INCOME PROFILE DETAILS ==="]

        # 1. Process Fields
        for field in INCOME_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Currency
            if field['type'] in ['currency', 'rollup_summary']:
                val = f"${val}"
            
            # Formatting Multi-User Lookups
            if key == "Income_Profile_Owners" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val]
                val = ", ".join(names)

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, income_data: dict) -> str:
        """
        Generates a response answering questions about the Income Profile.
        """
        context_text = self.format_data_for_ai(income_data)

        prompt = f"""
        You are an expert Financial Analyst & Wealth Manager.
        
        Your goal is to analyze this INCOME PROFILE based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### INCOME CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Total Picture:** State the 'Total_Annual_Income'.
        - **Breakdown:** Compare 'Active Income' (Salary) vs 'Asset Income' (Investments). This shows financial independence.
        - **Ownership:** Identify who (Client/Household) this income belongs to.
        - **Advisory:** Note the 'Primary_Advisor' managing this profile.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text