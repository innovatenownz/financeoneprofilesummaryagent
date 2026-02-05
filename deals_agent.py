import json
import google.generativeai as genai

# --- 1. CONFIGURATION ---

# Related List Configuration (for fetching details)
SPECIFIC_LIST_CONFIG = {
    "Stage_History": ["Stage", "Amount", "Probability", "Modified_Time", "Modified_By"],
    "Competitors": ["Competitor_Name", "Website", "Strengths", "Weaknesses"],
    "Contact_Roles": ["Contact_Name", "Role", "Phone", "Email"],
    "Products": ["Product_Name", "Unit_Price", "Quantity", "Total"],
    "Quotes": ["Subject", "Grand_Total", "Valid_Till", "Quote_Stage"],
    "SalesOrders": ["Subject", "Grand_Total", "Status"],
    "Deal_Team__s": ["Name", "Role", "User"], 
    "Action_Plans_New": ["Name", "Status", "Due_Date"],
    "Insurance_Sold_New": ["Policy_Name", "Premium", "Sum_Assured", "Policy_Number"],
    "Investment_Sold_New": ["Investment_Name", "Amount_Invested", "Date"],
    "Loan_Arranged_New": ["Loan_Type", "Amount", "Lender", "Status"],
    "Investment_Portfolio": ["Portfolio_Name", "Total_Value", "Allocation"],
    "Loan_Applications": ["Application_ID", "Loan_Amount", "Status", "Lender"],
    "Doc_Collect_Request": ["Document_Name", "Status", "Requested_Date"]
}

# --- KNOWLEDGE BASE: DEALS SCHEMA ---
# [UPDATED] Added 'target' keys so main.py can resolve lookups automatically
DEALS_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Deal_Name", "type": "text"},
    {"api": "Owner", "type": "ownerlookup", "target": "Users"},
    {"api": "Amount", "type": "currency"},
    {"api": "Closing_Date", "type": "date"},
    {"api": "Account_Name", "type": "lookup", "target": "Accounts"},
    {"api": "Contact_Name", "type": "lookup", "target": "Contacts"},
    {"api": "Pipeline", "type": "picklist"},
    {"api": "Stage", "type": "picklist"},
    {"api": "Type", "type": "picklist"},
    {"api": "Probability", "type": "integer"},
    {"api": "Expected_Revenue", "type": "currency"},
    {"api": "Lead_Source", "type": "picklist"},
    {"api": "Campaign_Source", "type": "lookup", "target": "Campaigns"},
    {"api": "Created_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Modified_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Modified_Time", "type": "datetime"},
    {"api": "Last_Activity_Time", "type": "datetime"},
    {"api": "Tag", "type": "text"},
    {"api": "Description", "type": "textarea"},
    {"api": "Reason_For_Loss__s", "type": "picklist"},
    {"api": "Interest_Level", "type": "picklist"},
    {"api": "Inquiry_Type", "type": "picklist"},
    
    # Subforms and Multi-selects
    {"api": "Deal_Team_Members", "type": "multiuserlookup", "target": "Users"},
    {"api": "On_boarding", "type": "subform"},
    {"api": "Assigned_Roles", "type": "subform"},
    
    {"api": "Is_Upsell_Deal", "type": "boolean"},
    {"api": "Secondary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "Primary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "FUM", "type": "currency"},
    {"api": "Deal_Confirmation_Status", "type": "picklist"},
    {"api": "Portfolio_Type", "type": "picklist"}
]

class DealsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in DEALS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Deal JSON into a clean, readable text block.
        """
        if not record: return "No Deal Data Available."

        # === 1. LIST MODE (Context Switch / Search Results) ===
        if "items" in record:
            items = record["items"]
            if not items: return "No Deals found."
            
            lines = [f"=== FOUND {len(items)} DEALS ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Deal #{i} ---")
                
                # A. ALWAYS show identifiers
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Deal_Name" in item: lines.append(f"Name: {item['Deal_Name']}")
                
                # B. FORCE SHOW critical fields even if empty (for Updates)
                # These are the fields we likely want to update or create with
                critical_fields = ["Stage", "Amount", "Closing_Date", "Account_Name", "Contact_Name"]
                
                for k, v in item.items():
                    if k not in ["id", "Deal_Name", "Tag"]:
                        val_display = v
                        if isinstance(v, dict) and "name" in v: val_display = v["name"]
                        
                        # Show if value exists OR if it is critical
                        if v or k in critical_fields:
                            if not v and v is not False: val_display = "[Empty]"
                            lines.append(f"{k}: {val_display}")
            return "\n".join(lines)

        # === 2. SINGLE RECORD MODE ===
        lines = ["=== DEAL DETAILS ==="]

        # Process Standard Fields
        for field in DEALS_SCHEMA:
            key = field['api']
            val = record.get(key)
            if val in [None, "", [], {}]: continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val: val = val["name"]
            
            # Formatting Multi-User Lookups
            if isinstance(val, list) and key == "Deal_Team_Members":
                names = [u.get("name", str(u)) for u in val if isinstance(u, dict)]
                val = ", ".join(names)

            # Formatting Subforms
            if key in ["On_boarding", "Assigned_Roles"] and isinstance(val, list):
                lines.append(f"\n--- {key.replace('_', ' ')} (Subform) ---")
                for i, row in enumerate(val, 1):
                    details = []
                    for k, v in row.items():
                        if v and k not in ["id", "s_id"]:
                            if isinstance(v, dict) and "name" in v: v = v["name"]
                            details.append(f"{k}: {v}")
                    lines.append(f"  {i}. " + ", ".join(details))
                continue

            clean_key = key.replace("_", " ")
            lines.append(f"{clean_key}: {val}")

        # Process Related Lists
        lines.append("\n--- RELATED LISTS ---")
        list_keys = [k for k, v in record.items() if isinstance(v, list) and k not in ["Tag", "On_boarding", "Assigned_Roles", "Deal_Team_Members"]]
        
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
                if "id" in item: row_parts.append(f"ID: {item['id']}")

                if config_key:
                    for f in SPECIFIC_LIST_CONFIG[config_key]:
                        val = item.get(f)
                        if val: row_parts.append(f"{f}: {val}")
                else:
                    # Auto-Detect
                    priority_keywords = ["name", "subject", "stage", "amount", "total", "status", "date", "role"]
                    def key_func(k):
                        low = k.lower()
                        for idx, kw in enumerate(priority_keywords):
                            if kw in low: return idx
                        return len(priority_keywords)
                    sorted_keys = sorted(item.keys(), key=key_func)
                    
                    count = 0
                    for k in sorted_keys:
                        val = item.get(k)
                        if val and isinstance(val, (str, int, float)) and k.lower() != "id":
                            row_parts.append(f"{k}: {val}")
                            count += 1
                        if count >= 5: break
                
                lines.append(f"  {i}. " + " | ".join(row_parts))

        if not found_details: lines.append("(No related interaction or sales data found)")

        return "\n".join(lines)

    def generate_response(self, user_query: str, deal_data: dict, history: list = []) -> str:
        """
        Generates a response answering questions about the Deal.
        """
        context_text = self.format_data_for_ai(deal_data)

        # Format History
        history_block = ""
        if history:
            history_block = "### CONVERSATION HISTORY\n"
            for msg in history[-3:]:
                role = "User" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_block += f"{role}: {content}\n"

        prompt = f"""
        You are an expert Sales Manager Assistant.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### DEAL CONTEXT
        {context_text}
        
        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** Include `record_id` for updates.
        - **Lookups:** If the user provides an Account Name or Contact Name, pass it as text. My system will convert it to an ID.
        - **Revenue Focus:** Use 'Amount' and 'Stage' to explain the deal's health.

        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Deals", 
            "record_id": "12345",
            "data": {{ 
                "Deal_Name": "REQUIRED_NAME",
                "Stage": "Qualification",
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text