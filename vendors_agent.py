import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: VENDORS SCHEMA ---
VENDORS_SCHEMA = [
    # Core Vendor Info
    {"api": "Vendor_Name", "type": "text"},
    {"api": "Vendor_Unique_Id", "type": "text"},
    {"api": "Phone", "type": "phone"},
    {"api": "Email", "type": "email"},
    {"api": "Website", "type": "website"},
    {"api": "Category", "type": "text"},
    
    # Financials & Status
    {"api": "GL_Account", "type": "picklist"},
    {"api": "Vendor_Type", "type": "picklist"}, # Custom status
    {"api": "Vendor_Type1", "type": "picklist"}, # Secondary type
    
    # Contact People
    {"api": "Contact_Person", "type": "text"},
    {"api": "Alternate_Contact", "type": "phone"},
    
    # Address
    {"api": "Street", "type": "text"},
    {"api": "City", "type": "text"},
    {"api": "State", "type": "text"},
    {"api": "Zip_Code", "type": "text"},
    {"api": "Country", "type": "text"},
    
    # System & Meta
    {"api": "Owner", "type": "ownerlookup"},
    {"api": "Description", "type": "textarea"},
    {"api": "Tag", "type": "jsonarray"}
]

class VendorsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in VENDORS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Vendor JSON into a clean, readable text block.
        """
        if not record:
            return "No Vendor Data Available."

        lines = ["=== VENDOR DETAILS ==="]

        # 1. Process Fields
        for field in VENDORS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Lists (Tags)
            if isinstance(val, list):
                val = ", ".join([str(v) for v in val])

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, vendor_data: dict) -> str:
        """
        Generates a response answering questions about the Vendor.
        """
        context_text = self.format_data_for_ai(vendor_data)

        prompt = f"""
        You are an expert Procurement & Supply Chain Manager.
        
        Your goal is to analyze this VENDOR/SUPPLIER based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### VENDOR CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Identification:** Confirm the Vendor Name and 'GL_Account' if relevant for accounting.
        - **Contact:** If asked how to reach them, prefer 'Contact_Person' or 'Phone'.
        - **Categorization:** Use 'Category' and 'Vendor_Type' to explain what they supply.
        - **Location:** Check Address fields if logistics/shipping is mentioned.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text