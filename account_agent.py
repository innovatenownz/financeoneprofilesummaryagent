import json
import google.generativeai as genai

# --- 1. DEFINING THE KNOWLEDGE BASE (SCHEMA) ---
# The AI uses this to understand what the data MEANS before it even looks at the values.
ACCOUNT_SCHEMA = [
    {"api": "Owner", "type": "lookup (User)"},
    {"api": "Account_Name", "type": "text"},
    {"api": "Parent_Account", "type": "lookup"},
    {"api": "Website", "type": "url"},
    {"api": "Ticker_Symbol", "type": "text"},
    {"api": "Account_Type", "type": "picklist"},
    {"api": "Industry", "type": "picklist"},
    {"api": "Employees", "type": "integer"},
    {"api": "Annual_Revenue", "type": "currency"},
    {"api": "Tag", "type": "jsonarray"},
    {"api": "Description", "type": "textarea"},
    {"api": "Household_ID", "type": "integer"},
    {"api": "Status", "type": "picklist"},
    {"api": "Primary_Contact1", "type": "lookup (Contact)"},
    {"api": "Real_estate_income", "type": "currency"},
    {"api": "Total_Asset_Value", "type": "currency"},
    {"api": "Total_Liabilites", "type": "currency"},
    {"api": "Trust_Type", "type": "picklist"},
    {"api": "State", "type": "text"},
    {"api": "Country", "type": "text"},
    {"api": "City", "type": "text"},
    {"api": "Street", "type": "text"},
    {"api": "Zip_Code", "type": "text"},
    {"api": "Trust_Registration_ID_Number", "type": "text"},
    {"api": "Trust_Establishment_Date", "type": "date"},
    {"api": "Net_Worth", "type": "formula (currency)"},
    {"api": "Trust_Purpose", "type": "textarea"},
    {"api": "Family_Type", "type": "picklist"},
    {"api": "Total_Members", "type": "rollup (count)"},
    {"api": "Interest_Level", "type": "picklist"},
    {"api": "Household_Segment", "type": "picklist"},
    {"api": "Total_General_Asset_Value", "type": "rollup (currency)"},
    {"api": "Total_Real_Estate_Value", "type": "rollup (currency)"},
    {"api": "Total_Investment_Holding_Values", "type": "rollup (currency)"},
    {"api": "Total_Annual_Income", "type": "currency"},
    {"api": "Trust_Income", "type": "currency"},
    {"api": "Family_Income", "type": "currency"},
    {"api": "Business_Group_Income", "type": "currency"},
    {"api": "Professional_Contact", "type": "rollup (count)"},
    {"api": "Lead_Source", "type": "picklist"},
    {"api": "Referring_account", "type": "lookup"},
    {"api": "Inquiry_Type", "type": "picklist"},
    {"api": "Account_Sub_Type", "type": "picklist"},
    {"api": "Account_Team_Members", "type": "multiuserlookup"},
    {"api": "Total_Asset_Income_Annual", "type": "currency"},
    {"api": "Total_Investment_holding_Income_Annual", "type": "currency"},
    {"api": "Total_Active_Income_Annual", "type": "currency"},
    {"api": "Total_Real_estate_Income_Annual", "type": "currency"},
    {"api": "Referred_Client", "type": "lookup"},
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    {"api": "NZBN_Number", "type": "text"},
    {"api": "Entity_Status", "type": "text"},
    # Subforms
    {"api": "Account_Relations", "type": "subform"},
    {"api": "Account_Client_Relation", "type": "subform"},
]

class AccountAgent:
    def __init__(self, model):
        self.model = model
        # Pre-format the schema string for the system prompt
        self.schema_string = "\n".join([f"- {item['api']} ({item['type']})" for item in ACCOUNT_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Converts the raw JSON record into a readable text format, 
        handling Subforms and Related lists specifically for Accounts.
        """
        if not record:
            return "No Account Data Found."

        text_lines = ["=== ACCOUNT RECORD DETAILS ==="]

        # 1. Process Main Fields based on Schema
        # We loop through the SCHEMA first to ensure we look for the right fields
        for field in ACCOUNT_SCHEMA:
            key = field['api']
            val = record.get(key)
            dtype = field['type']

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Value based on Type
            display_val = val
            
            # Handle Lookups (usually dicts with 'name' and 'id')
            if isinstance(val, dict) and "name" in val:
                display_val = val["name"]
            
            # Handle Subforms (Lists of objects)
            if dtype == "subform" and isinstance(val, list):
                text_lines.append(f"\n--- Subform: {key} ---")
                for idx, row in enumerate(val, 1):
                    row_txt = []
                    for k, v in row.items():
                        if k not in ["id", "s_id"] and v:
                            # Resolve lookup in subform
                            if isinstance(v, dict) and "name" in v: 
                                v = v["name"]
                            row_txt.append(f"{k}: {v}")
                    text_lines.append(f"  {idx}. " + ", ".join(row_txt))
                continue

            text_lines.append(f"{key}: {display_val}")

        # 2. Handle Related Lists (Data fetched via separate API calls, stored in "Related_X")
        # The Main Manager attaches these to the record dict
        related_keys = [k for k in record.keys() if k.startswith("Related_")]
        if related_keys:
            text_lines.append("\n=== RELATED MODULE DATA ===")
            for r_key in related_keys:
                module_name = r_key.replace("Related_", "")
                items = record[r_key]
                if items:
                    text_lines.append(f"\n[Related Module: {module_name}] ({len(items)} items)")
                    for i, item in enumerate(items[:5], 1): # Limit to top 5 for brevity
                        # Try to find a readable name
                        name = item.get("Name") or item.get("Subject") or item.get("Account_Name") or "Record"
                        
                        # Formatting: Flatten the related item loosely
                        details = [f"{k}: {v}" for k, v in item.items() 
                                   if v and k not in ["id", "Owner", "Created_Time", "Modified_Time"]]
                        # Take only first 3 distinct fields for summary
                        summary = ", ".join(details[:3])
                        text_lines.append(f"  {i}. {name} ({summary}...)")

        return "\n".join(text_lines)

    def generate_response(self, query: str, account_data: dict) -> str:
        """
        Generates the final response using the specific Account Persona.
        """
        # 1. Convert Data to Text
        context_text = self.format_data_for_ai(account_data)

        # 2. Build the Specialist Prompt
        prompt = f"""
        You are an expert Relationship Manager Assistant specializing in CLIENT ACCOUNTS.
        
        Your goal is to answer the user's question using ONLY the provided account data.
        
        ### SYSTEM KNOWLEDGE (The Schema of this Database)
        The following fields exist in the database. Use this to understand the data types (e.g., Currency vs Text):
        {self.schema_string}

        ### CURRENT ACCOUNT CONTEXT
        {context_text}

        ### USER QUESTION
        "{query}"

        ### INSTRUCTIONS
        1. Answer directly and professionally.
        2. If the user asks about financial data (Currency fields), format it nicely (e.g., $1,000,000).
        3. If the user asks about a field that is NOT in the 'CURRENT ACCOUNT CONTEXT' but IS in the 'SYSTEM KNOWLEDGE', explain that the field exists but is currently empty/blank for this client.
        4. If the user asks about related items (like Deals or Contacts) check the 'RELATED MODULE DATA' section.
        
        Answer:
        """

        response = self.model.generate_content(prompt)
        return response.text