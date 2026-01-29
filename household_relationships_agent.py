import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: HOUSEHOLD RELATIONSHIPS SCHEMA ---
HH_RELATIONSHIPS_SCHEMA = [
    # Core Identity
    {"api": "Name", "type": "autonumber"},
    {"api": "Household_Main", "type": "lookup (Account)"}, # Primary Entity
    {"api": "Household_Secondary", "type": "lookup (Account)"}, # Secondary Entity
    {"api": "is", "type": "picklist"}, # Relationship Type (e.g. Parent of, Trust for)
    {"api": "Record_Status__s", "type": "picklist"},
    
    # Advisors & Management
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    {"api": "Account_Relationship_Team", "type": "multiuserlookup"},
    
    # Contact & System
    {"api": "Email", "type": "email"},
    {"api": "Create_Inverse_Record", "type": "boolean"},
    {"api": "Source", "type": "picklist"},
    {"api": "Created_Time", "type": "datetime"}
]

class HouseholdRelationshipsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in HH_RELATIONSHIPS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Household Relationship JSON into a clean, readable text block.
        """
        if not record:
            return "No Household Relationship Data Available."

        lines = ["=== HOUSEHOLD RELATIONSHIP DETAILS ==="]

        # 1. Process Fields
        for field in HH_RELATIONSHIPS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Multi-User Lookups
            if key == "Account_Relationship_Team" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val]
                val = ", ".join(names)
            
            # Formatting Booleans
            if field['type'] == 'boolean':
                val = "Yes" if val else "No"

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, rel_data: dict) -> str:
        """
        Generates a response answering questions about the Household Relationship.
        """
        context_text = self.format_data_for_ai(rel_data)

        prompt = f"""
        You are an expert Family Office Manager & CRM Analyst.
        
        Your goal is to analyze this HOUSEHOLD-TO-HOUSEHOLD RELATIONSHIP based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### RELATIONSHIP CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **The Connection:** Explain the link: "[Household_Main] [is] [Household_Secondary]".
        - **Advisory Team:** Identify the 'Primary_Advisor' and any team members involved.
        - **Structure:** If asked about hierarchy, explain which account is the Primary/Main entity.
        - **Status:** Confirm if the record is active ('Record_Status__s').
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text