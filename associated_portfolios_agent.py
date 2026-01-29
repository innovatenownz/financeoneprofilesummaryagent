import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: ASSOCIATED PORTFOLIOS SCHEMA ---
ASSOC_PORTFOLIO_SCHEMA = [
    # Core Identity
    {"api": "Name", "type": "text"}, # Association Name
    {"api": "Role", "type": "picklist"}, # e.g. Trustee, Beneficiary
    {"api": "Portfolio_Association_Type", "type": "picklist"}, # Joint, Individual
    {"api": "Portfolio_Ownership_Status", "type": "picklist"},
    {"api": "Share_Percentage", "type": "percent"},
    
    # Links
    {"api": "Client", "type": "lookup (Contact)"},
    {"api": "Household", "type": "lookup (Account)"},
    {"api": "Investment_portfolio", "type": "lookup (Portfolio)"},
    
    # Governance & Reporting
    {"api": "Receives_IMS_Report", "type": "boolean"},
    {"api": "Portfolio_Next_Review_Date", "type": "date"},
    
    # Advisory Team
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    {"api": "Portfolio_Associations_Owners", "type": "multiuserlookup"},
    
    # System
    {"api": "Record_Status__s", "type": "picklist"},
    {"api": "Created_Time", "type": "datetime"}
]

class AssociatedPortfoliosAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in ASSOC_PORTFOLIO_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Associated Portfolio JSON into a clean, readable text block.
        """
        if not record:
            return "No Associated Portfolio Data Available."

        lines = ["=== PORTFOLIO ASSOCIATION DETAILS ==="]

        # 1. Process Fields
        for field in ASSOC_PORTFOLIO_SCHEMA:
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
                
            # Formatting Booleans
            if field['type'] == 'boolean':
                val = "Yes" if val else "No"
            
            # Formatting Multi-User Lookups
            if key == "Portfolio_Associations_Owners" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val]
                val = ", ".join(names)

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, assoc_data: dict) -> str:
        """
        Generates a response answering questions about the Portfolio Association.
        """
        context_text = self.format_data_for_ai(assoc_data)

        prompt = f"""
        You are an expert Governance & Compliance Officer.
        
        Your goal is to analyze this PORTFOLIO ASSOCIATION based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### ASSOCIATION CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **The Connection:** Explain the relationship: "[Client] acts as [Role] for [Investment_portfolio]".
        - **Rights:** Check 'Receives_IMS_Report'. Does this person get the financial statements?
        - **Ownership:** If 'Share_Percentage' is > 0, mention their equity stake.
        - **Review:** Note the 'Portfolio_Next_Review_Date'.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text