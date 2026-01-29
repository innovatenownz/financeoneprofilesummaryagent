import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: CONTACTS SCHEMA ---
CONTACTS_SCHEMA = [
    # Identity & Demographics
    {"api": "Full_Name", "type": "text"},
    {"api": "First_Name", "type": "text"},
    {"api": "Last_Name", "type": "text"},
    {"api": "Date_of_Birth", "type": "date"},
    {"api": "Age1", "type": "formula (double)"},
    {"api": "Life_Stage", "type": "picklist"},
    {"api": "Citizenship_s", "type": "multiselectpicklist"},
    {"api": "Country_of_birth", "type": "picklist"},
    {"api": "Country_of_residence", "type": "picklist"},
    
    # Contact Info
    {"api": "Email", "type": "email"},
    {"api": "Phone", "type": "phone"},
    {"api": "Mobile", "type": "phone"},
    {"api": "Secondary_Email", "type": "email"},
    {"api": "Street", "type": "text"},
    {"api": "City", "type": "text"},
    {"api": "State", "type": "text"},
    {"api": "Zip_Code", "type": "text"},
    {"api": "Country", "type": "text"},
    
    # Professional Profile
    {"api": "Account_Name", "type": "lookup (Account)"},
    {"api": "Job_Title", "type": "text"},
    {"api": "Employer", "type": "text"},
    {"api": "Designation", "type": "picklist"},
    {"api": "Industry", "type": "picklist"},
    {"api": "Education", "type": "text"},
    {"api": "School", "type": "text"},
    {"api": "LinkedIn_Profile", "type": "website"},
    
    # Financial Profile (Individual)
    {"api": "Net_Worth1", "type": "currency"},
    {"api": "Total_Asset_Value1", "type": "rollup (currency)"},
    {"api": "Total_Liabilities_Value1", "type": "rollup (currency)"},
    {"api": "Total_General_Asset_Value1", "type": "rollup (currency)"},
    {"api": "Total_Investment_Holding_Values1", "type": "rollup (currency)"},
    {"api": "Rollup_Summary_10", "type": "rollup (currency)"}, # Total Real Estate Value
    {"api": "Annual_Income", "type": "currency"},
    {"api": "Active_Income", "type": "currency"},
    {"api": "Real_estate_income", "type": "currency"},
    {"api": "Total_Asset_Income", "type": "currency"},
    {"api": "Investment_holding_income", "type": "currency"},
    
    # Relationship Management
    {"api": "Client_Status", "type": "picklist"},
    {"api": "Client_Type", "type": "picklist"},
    {"api": "Client_Segment", "type": "picklist"},
    {"api": "Interest_Level", "type": "picklist"},
    {"api": "Investment_Preferences", "type": "picklist"},
    {"api": "Client_Interests", "type": "multiselectpicklist"},
    {"api": "Personal_Intrests", "type": "multiselectpicklist"},
    {"api": "Active_Power_of_Attorney", "type": "boolean"},
    
    # System / Internal
    {"api": "Owner", "type": "ownerlookup"},
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    {"api": "Client_Relationship_Team", "type": "multiuserlookup"},
    {"api": "Referring_Client", "type": "lookup (Contact)"},
]

class ContactsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in CONTACTS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Contact JSON into a clean, readable text block.
        """
        if not record:
            return "No Contact Data Available."

        lines = ["=== CLIENT PROFILE ==="]

        # 1. Process defined fields
        for field in CONTACTS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups (Standard logic)
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Lists (Multi-select picklists)
            if isinstance(val, list):
                # Filter out raw ID dictionaries if they sneak in
                clean_val = [str(v) if not isinstance(v, dict) else v.get("name", "") for v in val]
                val = ", ".join(clean_val)

            clean_key = key.replace("_", " ").replace("1", "") # Remove appended numbers like Age1
            lines.append(f"{clean_key}: {val}")

        # 2. Add Related Notes (Crucial for Client History)
        if "Related_Notes" in record:
            notes = record["Related_Notes"]
            if notes:
                lines.append(f"\n=== RECENT INTERACTIONS ({len(notes)}) ===")
                for i, note in enumerate(notes[:5], 1): # Top 5 notes
                    title = note.get("Note_Title") or "Update"
                    content = note.get("Note_Content") or ""
                    # Truncate very long notes
                    if len(content) > 200:
                        content = content[:200] + "..."
                    lines.append(f"  {i}. [{title}] {content}")

        return "\n".join(lines)

    def generate_response_stream(self, user_query: str, contact_data: dict):
        """
        Generates a response answering questions about the individual client in a streaming fashion.
        """
        context_text = self.format_data_for_ai(contact_data)

        prompt = f"""
        You are an expert Private Wealth Manager Assistant.
        
        Your goal is to provide deep insights into this INDIVIDUAL CLIENT based on the profile below.
        
        ### DATA SCHEMA (Field Types)
        {self.schema_string}

        ### CLIENT PROFILE CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Person-Centric:** Focus on the individual (Age, Interests, Career, Life Stage).
        - **Financial Health:** If asked about wealth, combine 'Net Worth', 'Total Assets', and 'Income' to give a holistic view.
        - **Relationships:** Mention the 'Primary Advisor' or 'Referring Client' if relevant to connection context.
        - **Tone:** Professional, empathetic, and discreet (Wealth Management standard).
        - If the user asks for contact details, provide Email and Phone clearly.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def generate_response(self, user_query: str, contact_data: dict) -> str:
        """
        Generates a response answering questions about the individual client.
        """
        context_text = self.format_data_for_ai(contact_data)

        prompt = f"""
        You are an expert Private Wealth Manager Assistant.
        
        Your goal is to provide deep insights into this INDIVIDUAL CLIENT based on the profile below.
        
        ### DATA SCHEMA (Field Types)
        {self.schema_string}

        ### CLIENT PROFILE CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Person-Centric:** Focus on the individual (Age, Interests, Career, Life Stage).
        - **Financial Health:** If asked about wealth, combine 'Net Worth', 'Total Assets', and 'Income' to give a holistic view.
        - **Relationships:** Mention the 'Primary Advisor' or 'Referring Client' if relevant to connection context.
        - **Tone:** Professional, empathetic, and discreet (Wealth Management standard).
        - If the user asks for contact details, provide Email and Phone clearly.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text