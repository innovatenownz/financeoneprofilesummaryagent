import google.generativeai as genai
import json

# --- 1. CONFIGURATION ---
# [UPDATED] Full Schema Mapping based on provided field list
ACCOUNT_SCHEMA = [
    {"api": "Owner", "type": "ownerlookup"},
    {"api": "Account_Name", "type": "text"},
    {"api": "Parent_Account", "type": "lookup"},
    {"api": "Website", "type": "website"},
    {"api": "Ticker_Symbol", "type": "text"},
    {"api": "Account_Type", "type": "picklist"},
    {"api": "Ownership", "type": "picklist"},
    {"api": "Industry", "type": "picklist"},
    {"api": "Employees", "type": "integer"},
    {"api": "Annual_Revenue", "type": "currency"},
    {"api": "Created_By", "type": "ownerlookup"},
    {"api": "Modified_By", "type": "ownerlookup"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Modified_Time", "type": "datetime"},
    {"api": "Last_Activity_Time", "type": "datetime"},
    {"api": "Tag", "type": "text"}, # Simplified from text (jsonarray)
    {"api": "Description", "type": "textarea"},
    {"api": "id", "type": "bigint"},
    {"api": "Change_Log_Time__s", "type": "datetime"},
    {"api": "Locked__s", "type": "boolean"},
    {"api": "Last_Enriched_Time__s", "type": "datetime"},
    {"api": "Enrich_Status__s", "type": "picklist"},
    {"api": "Record_Status__s", "type": "picklist"},
    {"api": "Household_ID", "type": "integer"},
    {"api": "Status", "type": "picklist"},
    {"api": "Primary_Contact1", "type": "lookup"},
    {"api": "Real_estate_income", "type": "currency"},
    {"api": "Total_Asset_Value", "type": "currency"},
    {"api": "Total_Liabilites", "type": "currency"},
    {"api": "Trust_Type", "type": "picklist"},
    {"api": "State", "type": "text"},
    {"api": "Country", "type": "text"},
    {"api": "Zip_Code", "type": "text"},
    {"api": "City", "type": "text"},
    {"api": "Street", "type": "text"},
    {"api": "Trust_Registration_ID_Number", "type": "text"},
    {"api": "Trust_Establishment_Date", "type": "date"},
    {"api": "Net_Worth", "type": "formula"},
    {"api": "Trust_Purpose", "type": "textarea"},
    {"api": "Family_Type", "type": "picklist"},
    {"api": "Total_Members", "type": "rollup_summary"},
    {"api": "Interest_Level", "type": "picklist"},
    {"api": "Household_Segment", "type": "picklist"},
    {"api": "Total_General_Asset_Value", "type": "rollup_summary"},
    {"api": "Total_Real_Estate_Value", "type": "rollup_summary"},
    {"api": "Total_Investment_Holding_Values", "type": "rollup_summary"},
    {"api": "Total_Annual_Income", "type": "currency"},
    {"api": "Trust_Income", "type": "currency"},
    {"api": "Family_Income", "type": "currency"},
    {"api": "Business_Group_Income", "type": "currency"},
    {"api": "Professional_Contact", "type": "rollup_summary"},
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
    {"api": "Account_Relations", "type": "subform"},
    {"api": "Account_Client_Relation", "type": "subform"},
    {"api": "Wizard", "type": "bigint"}
]

# Keys here MUST match the API names used in main.py
SPECIFIC_LIST_CONFIG = {
    "Notes": ["Note_Title", "Note_Content", "Created_Time", "Owner"],
    "Deals": ["Deal_Name", "Stage", "Amount", "Closing_Date"],
    "Activities": ["Subject", "Status", "Priority", "Due_Date"],
    "Asset_Ownerships_New": ["Asset_Type", "Real_Estate_Value", "Asset_Ownership", "Ownership", "Share_Percentage"],
    "Loans": ["Name", "Amount", "Interest_Rate", "Lender"],
    "Insurance_policy_New": ["Policy_Name", "Sum_Assured", "Policy_Status"],
    "Entity_KYC_New": ["Name", "Status", "Verification_Date"],
    "Income_Profile_New": ["Name", "Total_Annual_Income"],
    "Associated_portfolio": ["Portfolio_Name", "Total_Value"],
    "Tax_profile": ["Name"],
    "Account_Risks": ["Name", "Risk_Level", "Description"],
    "Professional_Contacts_New": ["Name", "Role", "Email"],
    "Expenses_New": ["Name", "Amount", "Date"],
    "Household_Relationships_New": ["Name", "Role"]
}

class AccountAgent:
    def __init__(self, model):
        self.model = model

    def format_data_for_ai(self, record: dict) -> str:
        if not record: return "No Account Data Found."
        # DEBUG
        print(f"🧐 AGENT SEES: {list(record.keys())}")

        lines = ["=== CLIENT DASHBOARD ==="]
        lines.append("--- Overview ---")
        for field in ACCOUNT_SCHEMA:
            val = record.get(field['api'])
            if val is not None: # Check for None explicitly so we don't skip 0 or False
                lines.append(f"{field['api']} ({field['type']}): {val}")

        lines.append("\n--- ALL RELATED DATA ---")
        list_keys = [k for k, v in record.items() if isinstance(v, list) and k != "Tag"]
        found_details = False

        for list_name in list_keys:
            items = record[list_name]
            if not items: continue

            clean_name = list_name.replace("Related_", "")
            lines.append(f"\n# {clean_name} ({len(items)} items)")
            found_details = True
            config_key = next((k for k in SPECIFIC_LIST_CONFIG if k == clean_name), None)

            for i, item in enumerate(items, 1):
                row_parts = []
                if "id" in item: row_parts.append(f"ID: {item['id']}") # ALWAYS SHOW ID

                if config_key:
                    for f in SPECIFIC_LIST_CONFIG[config_key]:
                        val = item.get(f)
                        if val: row_parts.append(f"{f}: {val}")
                else:
                    # Auto-Detect
                    priority_keywords = ["name", "subject", "title", "content", "type", "status", "amount", "value", "date"]
                    def key_func(k):
                        low = k.lower()
                        for idx, kw in enumerate(priority_keywords):
                            if kw in low: return idx
                        return len(priority_keywords)
                    sorted_keys = sorted(item.keys(), key=key_func)
                    count = 0
                    for k in sorted_keys:
                        val = item.get(k)
                        # [FIX] ALLOW IDs to be seen
                        if val and isinstance(val, (str, int, float)):
                            if k.lower() == "id": continue 
                            row_parts.append(f"{k}: {val}")
                            count += 1
                        if count >= 6: break
                
                if row_parts: lines.append(f"  {i}. " + " | ".join(row_parts))
                else: lines.append(f"  {i}. [Details present but hidden]")

        if not found_details: lines.append("(No related module data found)")
        return "\n".join(lines)

    # [UPDATED] generate_response now accepts 'history'
    def generate_response(self, query: str, account_data: dict, history: list = []) -> str:
        context_text = self.format_data_for_ai(account_data)

        # [NEW] Format history for the prompt
        history_block = ""
        if history:
            history_block = "### CONVERSATION HISTORY (Use this to resolve 'it', 'that', or context)\n"
            # Look back 5 messages max
            for msg in history[-5:]: 
                role = "User" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_block += f"{role}: {content}\n"

        prompt = f"""
        You are an intelligent Relationship Manager AI Assistant.
        
        ### CLIENT DATA
        {context_text}

        {history_block}

        ### CURRENT QUESTION
        "{query}"

        ### INSTRUCTIONS
        1. Answer based *only* on the data above.
        2. **Use History:** If the user says "Change it" or "Update that", refer to the 'CONVERSATION HISTORY' to understand what they are talking about.
        3. If the user wants to CREATE or UPDATE, use the Action Protocol below.
        4. **IMPORTANT:** When updating a specific item (like a Loan or Asset), you MUST include its "ID" in the `record_id` field.
        
        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "API_NAME_FROM_ABOVE",
            "record_id": "123456789", 
            "data": {{ "Field_Name": "New Value" }}
        }}
        <<<END_ACTION>>>
        
        Answer:
        """
        response = self.model.generate_content(prompt)
        return response.text