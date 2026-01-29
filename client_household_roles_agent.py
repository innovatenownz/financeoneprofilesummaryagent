import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: CLIENT HOUSEHOLD ROLES SCHEMA ---
ROLES_SCHEMA = [
    # Core Role Info
    {"api": "Name", "type": "text"}, # Role Name
    {"api": "Primary_Relationships", "type": "picklist"}, # e.g. Head of Household
    {"api": "Generation", "type": "picklist"}, # e.g. G1, G2
    {"api": "Record_Status__s", "type": "picklist"},
    
    # Relationships
    {"api": "Client", "type": "lookup (Contact)"},
    {"api": "Household", "type": "lookup (Account)"}, # Mapped from API Name 'Household'
    {"api": "Client_Role_Owners", "type": "multiuserlookup"}, # Advisors assigned
    
    # Contact Details (Specific to this role)
    {"api": "Email", "type": "email"},
    {"api": "Secondary_Email", "type": "email"},
    {"api": "Email_Opt_Out", "type": "boolean"},
    
    # System
    {"api": "Created_By", "type": "ownerlookup"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Tag", "type": "jsonarray"}
]

class ClientHouseholdRolesAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in ROLES_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Role JSON into a clean, readable text block.
        """
        if not record:
            return "No Role Data Available."

        lines = ["=== CLIENT HOUSEHOLD ROLE DETAILS ==="]

        # 1. Process Fields
        for field in ROLES_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Multi-User Lookups (Advisors)
            if key == "Client_Role_Owners" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val]
                val = ", ".join(names)
            
            # Formatting Booleans
            if field['type'] == 'boolean':
                val = "Yes" if val else "No"

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, role_data: dict) -> str:
        """
        Generates a response answering questions about the Role.
        """
        context_text = self.format_data_for_ai(role_data)

        prompt = f"""
        You are an expert Family Governance & CRM Analyst.
        
        Your goal is to analyze this CLIENT HOUSEHOLD ROLE based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### ROLE CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **The Link:** Explain who the Client is and which Household they belong to.
        - **Position:** Use 'Primary_Relationships' and 'Generation' to explain their standing (e.g., "G2 Beneficiary").
        - **Advisors:** Identify the 'Client_Role_Owners' who manage this specific relationship.
        - **Contact:** Note if they have opted out of emails or have a secondary email listed.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text