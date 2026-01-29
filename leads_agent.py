import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: LEADS SCHEMA ---
LEADS_SCHEMA = [
    {"api": "Full_Name", "type": "text"},
    {"api": "First_Name", "type": "text"},
    {"api": "Last_Name", "type": "text"},
    {"api": "Company", "type": "text"},
    {"api": "Designation", "type": "text"},
    {"api": "Email", "type": "email"},
    {"api": "Phone", "type": "phone"},
    {"api": "Mobile", "type": "phone"},
    {"api": "LinkedIn_Profile", "type": "website"},
    {"api": "Lead_Status", "type": "picklist"},
    {"api": "Lead_Source", "type": "picklist"},
    {"api": "Rating", "type": "picklist"},
    {"api": "Interest_Level", "type": "picklist"},
    {"api": "Reason_for_Loss", "type": "picklist"},
    {"api": "Industry", "type": "picklist"},
    {"api": "Annual_Revenue", "type": "currency"},
    {"api": "No_of_Employees", "type": "integer"},
    {"api": "Lead_Type1", "type": "picklist"},
    {"api": "Company_Type", "type": "picklist"},
    {"api": "City", "type": "text"},
    {"api": "Country", "type": "picklist"},
    {"api": "New_address_fields_City", "type": "text"},
    {"api": "New_address_fields_Street_Address", "type": "text"},
    {"api": "New_address_fields_State_Province", "type": "picklist"},
    {"api": "Converted_Date_Time", "type": "datetime"},
    {"api": "Converted_Account", "type": "lookup (Account)"},
    {"api": "Converted_Contact", "type": "lookup (Contact)"},
    {"api": "Converted_Deal", "type": "lookup (Deal)"},
    {"api": "Owner", "type": "ownerlookup"},
    {"api": "Primary_Advisor", "type": "userlookup"},
]

class LeadsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in LEADS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Lead JSON into a clean, readable text block.
        """
        if not record:
            return "No Lead Data Available."

        lines = ["=== LEAD OVERVIEW ==="]

        # 1. Process defined fields
        for field in LEADS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Lists (e.g. Multi-select)
            if isinstance(val, list):
                val = ", ".join([str(v) for v in val])

            lines.append(f"{key}: {val}")

        # 2. Check for Conversion Status explicitly
        if record.get("Converted_Date_Time"):
            lines.insert(1, "!!! THIS LEAD HAS BEEN CONVERTED !!!")

        # 3. Handle Notes specifically for Leads (Sales Context)
        if "Related_Notes" in record:
            notes = record["Related_Notes"]
            if notes:
                lines.append(f"\n=== SALES NOTES ({len(notes)}) ===")
                for i, note in enumerate(notes[:3], 1):
                    content = note.get("Note_Content") or "No content"
                    lines.append(f"  {i}. {content}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, lead_data: dict) -> str:
        """
        Generates a response answering the user's query about the sales lead.
        """
        context_text = self.format_data_for_ai(lead_data)

        prompt = f"""
        You are an expert Sales Development Representative (SDR) Assistant.
        
        Your goal is to assist with LEADS and PROSPECTING based on the data below.
        
        ### DATA SCHEMA (Field Types)
        {self.schema_string}

        ### LEAD CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Focus on **Qualification**: Is this lead hot? Are they interested?
        - If the lead is CONVERTED, explicitly tell the user they should look at the Account or Contact instead.
        - If the user asks for contact info, provide the Email/Phone clearly.
        - If address info appears in 'New_address_fields', use that as the primary address.
        
        Response:
        """
        
        response = self.model.generate_content(prompt)
        return response.text