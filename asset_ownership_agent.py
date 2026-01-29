import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: ASSET OWNERSHIP SCHEMA ---
ASSET_OWNERSHIP_SCHEMA = [
    # Core Identity
    {"api": "Name", "type": "text"}, # Ownership Record Name
    {"api": "Ownership", "type": "picklist"}, # Joint, Sole, etc.
    {"api": "Ownership_Status", "type": "picklist"},
    {"api": "Asset_Type", "type": "picklist"},
    
    # Valuation & Share
    {"api": "Share_Percentage", "type": "percent"},
    {"api": "Share_Value_Total", "type": "formula (currency)"}, # The value of THIS share
    {"api": "Asset_Value", "type": "currency"},
    {"api": "Real_Estate_Value", "type": "currency"},
    {"api": "Investment_Holding_Value", "type": "currency"},
    
    # Owners
    {"api": "Client", "type": "lookup (Contact)"},
    {"api": "Households", "type": "lookup (Account)"},
    
    # Underlying Assets (Lookups)
    {"api": "Asset", "type": "lookup (General Asset)"},
    {"api": "Real_Estate", "type": "lookup (Real Estate)"},
    {"api": "Investment_Holding", "type": "lookup (Investment)"},
    {"api": "Associated_portfolio", "type": "lookup (Portfolio)"},
    
    # Advisory Team
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    {"api": "Asset_Management_Team", "type": "multiuserlookup"},
    
    # System
    {"api": "Record_Status__s", "type": "picklist"}
]

class AssetOwnershipAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in ASSET_OWNERSHIP_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Asset Ownership JSON into a clean, readable text block.
        """
        if not record:
            return "No Asset Ownership Data Available."

        lines = ["=== ASSET OWNERSHIP DETAILS ==="]

        # 1. Process Fields
        for field in ASSET_OWNERSHIP_SCHEMA:
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
            
            # Formatting Percent
            if field['type'] == 'percent':
                val = f"{val}%"
                
            # Formatting Multi-User Lookups
            if key == "Asset_Management_Team" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val]
                val = ", ".join(names)

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, ownership_data: dict) -> str:
        """
        Generates a response answering questions about the Asset Ownership.
        """
        context_text = self.format_data_for_ai(ownership_data)

        prompt = f"""
        You are an expert Asset Manager & Wealth Analyst.
        
        Your goal is to analyze this ASSET OWNERSHIP RECORD based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### OWNERSHIP CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **The Stake:** Identify the Client/Household and their 'Share_Percentage'.
        - **The Value:** State the 'Share_Value_Total' (Client's portion) vs the total asset value.
        - **The Asset:** Identify WHAT is owned (Real Estate, Investment, or General Asset).
        - **Advisory:** Mention the 'Primary_Advisor' managing this asset.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text