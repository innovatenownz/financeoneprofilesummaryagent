import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: HOUSEHOLDS SCHEMA ---
HOUSEHOLDS_SCHEMA = [
    # Core Identity
    {"api": "Name", "type": "text"}, # Households1 Name
    {"api": "Household_ID", "type": "autonumber"},
    {"api": "Household_Type", "type": "picklist"}, # e.g., Family, Business, Trust
    {"api": "Status", "type": "picklist"}, # Active, Inactive
    
    # Financials
    {"api": "Total_Assets", "type": "currency"},
    {"api": "Total_Liabilities", "type": "currency"},
    {"api": "Household_Net_Worth", "type": "formula (double)"},
    
    # Relationships
    {"api": "Primary_Contact", "type": "lookup (Contact)"},
    {"api": "Owner", "type": "ownerlookup"},
    
    # System
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Modified_Time", "type": "datetime"},
    {"api": "Tag", "type": "jsonarray"}
]

class HouseholdsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in HOUSEHOLDS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Household JSON into a clean, readable text block.
        """
        if not record:
            return "No Household Data Available."

        lines = ["=== HOUSEHOLD PROFILE ==="]

        # 1. Process Fields
        for field in HOUSEHOLDS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Financials
            if field['type'] == 'currency':
                val = f"${val}"
            
            # Formatting Net Worth (Formula)
            if key == "Household_Net_Worth":
                val = f"${val} (Calculated)"

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, household_data: dict) -> str:
        """
        Generates a response answering questions about the Household.
        """
        context_text = self.format_data_for_ai(household_data)

        prompt = f"""
        You are an expert Wealth Management & CRM Assistant.
        
        Your goal is to analyze this HOUSEHOLD based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### HOUSEHOLD CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Financial Health:** Compare Assets vs. Liabilities. Comment on the Net Worth.
        - **Key Contact:** Identify the 'Primary_Contact' as the main point of communication.
        - **Status:** Check if the household is 'Active'.
        - **Identification:** Use 'Household_ID' or 'Name' to refer to the record.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text