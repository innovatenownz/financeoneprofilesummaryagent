import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: CLIENT RELATIONSHIPS SCHEMA ---
RELATIONSHIPS_SCHEMA = [
    # Core Identity
    {"api": "Name", "type": "text"}, # Relationship Name
    {"api": "Client", "type": "lookup (Contact)"}, # Person A
    {"api": "Related_To", "type": "lookup (Contact)"}, # Person B (labeled "of")
    {"api": "Is", "type": "picklist"}, # Relationship Type (e.g. Spouse, Father)
    {"api": "Relationship_Status", "type": "picklist"},
    
    # Authority & Details
    {"api": "Deciding_Authority", "type": "picklist"},
    {"api": "Power_of_Attorney", "type": "boolean"},
    {"api": "Special_Instructions", "type": "textarea"},
    {"api": "Anniversary", "type": "date"},
    
    # Advisors
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    
    # System
    {"api": "Owner", "type": "ownerlookup"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Record_Status__s", "type": "picklist"}
]

class ClientRelationshipsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in RELATIONSHIPS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Relationship JSON into a clean, readable text block.
        """
        if not record:
            return "No Relationship Data Available."

        lines = ["=== RELATIONSHIP DETAILS ==="]

        # 1. Process Fields
        for field in RELATIONSHIPS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Booleans
            if field['type'] == 'boolean':
                val = "Yes" if val else "No"

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, rel_data: dict) -> str:
        """
        Generates a response answering questions about the Client Relationship.
        """
        context_text = self.format_data_for_ai(rel_data)

        prompt = f"""
        You are an expert Relationship Manager & CRM Assistant.
        
        Your goal is to analyze this CLIENT RELATIONSHIP based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### RELATIONSHIP CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **The Connection:** Explain the link clearly: "[Client] IS the [Is] OF [Related_To]".
        - **Authority:** Check 'Deciding_Authority' and 'Power_of_Attorney'. This is critical for legal/financial questions.
        - **Instructions:** Highlight any 'Special_Instructions' immediately if relevant.
        - **Status:** Ensure the relationship is 'Active' (check 'Relationship_Status').
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text