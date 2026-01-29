import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: PROFESSIONAL CONTACTS SCHEMA ---
PROF_CONTACTS_SCHEMA = [
    # Core Identity
    {"api": "Name", "type": "text"}, # Professional's Name
    {"api": "Role_ID", "type": "autonumber"},
    {"api": "Professional_Type", "type": "picklist"}, # e.g. CPA, Attorney
    {"api": "Role", "type": "picklist"}, # e.g. Tax Advisor, Legal Counsel
    {"api": "Status", "type": "picklist"}, # Active, Inactive
    
    # Relationships (Who they serve)
    {"api": "Client", "type": "lookup (Contact)"},
    {"api": "Household", "type": "lookup (Account)"},
    
    # Internal Management (Who manages them)
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    {"api": "Professional_Contact_Owners", "type": "multiuserlookup"}, # Team ownership
    
    # System
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Record_Status__s", "type": "picklist"}
]

class ProfessionalContactsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in PROF_CONTACTS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Professional Contact JSON into a clean, readable text block.
        """
        if not record:
            return "No Professional Contact Data Available."

        lines = ["=== PROFESSIONAL CONTACT DETAILS ==="]

        # 1. Process Fields
        for field in PROF_CONTACTS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Multi-User Lookups
            if key == "Professional_Contact_Owners" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val]
                val = ", ".join(names)

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, prof_data: dict) -> str:
        """
        Generates a response answering questions about the Professional Contact.
        """
        context_text = self.format_data_for_ai(prof_data)

        prompt = f"""
        You are an expert Center of Influence (COI) Manager & CRM Analyst.
        
        Your goal is to analyze this PROFESSIONAL CONTACT based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### PROFESSIONAL CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Identify:** Who is this professional and what is their 'Professional_Type' (e.g., CPA, Lawyer)?
        - **Context:** Which 'Client' or 'Household' do they serve?
        - **Internal Team:** Who is the 'Primary_Advisor' managing this relationship?
        - **Status:** Is this relationship currently 'Active'?
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text