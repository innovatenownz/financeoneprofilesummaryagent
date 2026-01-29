import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: USERS SCHEMA ---
USERS_SCHEMA = [
    # Core Identity
    {"api": "full_name", "type": "text"},
    {"api": "email", "type": "email"},
    {"api": "alias", "type": "text"},
    {"api": "status", "type": "picklist"}, # Active/Inactive
    {"api": "zuid", "type": "bigint"}, # Zoho User ID
    
    # Roles & Permissions
    {"api": "role", "type": "lookup"},
    {"api": "profile", "type": "lookup"},
    {"api": "confirm", "type": "boolean"}, # Confirmed user?
    
    # Contact Info
    {"api": "phone", "type": "phone"},
    {"api": "mobile", "type": "phone"},
    {"api": "website", "type": "website"},
    {"api": "street", "type": "text"},
    {"api": "city", "type": "text"},
    {"api": "state", "type": "text"},
    {"api": "country", "type": "text"},
    
    # Localization
    {"api": "time_zone", "type": "picklist"},
    {"api": "locale", "type": "picklist"},
    {"api": "country_locale", "type": "picklist"},
    
    # Custom Fields (Professional Info)
    {"api": "License_number", "type": "text"},
    {"api": "Education", "type": "text"},
    {"api": "Product_Segregation", "type": "multiselectpicklist"}, # Product Accreditation
    
    # System
    {"api": "created_time", "type": "datetime"},
    {"api": "Isonline", "type": "boolean"} # Online Status
]

class UsersAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in USERS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses User JSON into a clean, readable text block.
        """
        if not record:
            return "No User Data Available."

        lines = ["=== USER PROFILE DETAILS ==="]

        # 1. Process Fields
        for field in USERS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups (Role/Profile)
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Booleans
            if key == "Isonline":
                val = "🟢 Online" if val else "⚪ Offline"
            elif field['type'] == 'boolean':
                val = "Yes" if val else "No"
                
            # Formatting Lists (Product Accreditation)
            if isinstance(val, list):
                val = ", ".join([str(v) for v in val])

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, user_data: dict) -> str:
        """
        Generates a response answering questions about the User.
        """
        context_text = self.format_data_for_ai(user_data)

        prompt = f"""
        You are an expert HR & System Administrator Assistant.
        
        Your goal is to analyze this CRM USER profile based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### USER CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Status:** Check 'status' and 'confirm'. Warn if the user is 'Inactive'.
        - **Access:** Reference 'role' and 'profile' if asked about permissions.
        - **Availability:** Mention 'Isonline' status and 'time_zone' if relevant to scheduling.
        - **Qualifications:** Check 'Education' and 'Product_Segregation' (Accreditations).
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text