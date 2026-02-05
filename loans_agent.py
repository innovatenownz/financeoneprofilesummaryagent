import json
import google.generativeai as genai

# --- 1. CONFIGURATION ---

# Related List Configuration (for fetching details)
SPECIFIC_LIST_CONFIG = {
    "Loan_Structures": ["Name", "Current_Balance", "Interest_Rate", "Repayment_Type"],
    "Loan_Structures_New": ["Name", "Current_Balance", "Interest_Rate", "Repayment_Type"],
    "Notes": ["Note_Title", "Note_Content", "Created_Time", "Owner"],
    "Tasks": ["Subject", "Status", "Priority", "Due_Date"],
    "Calls": ["Subject", "Call_Type", "Call_Duration", "Call_Start_Time"],
    "Events": ["Event_Title", "Start_DateTime", "End_DateTime", "Location"]
}

# --- KNOWLEDGE BASE: LOANS SCHEMA ---
# [UPDATED] Added 'target' keys so main.py can resolve lookups automatically
LOANS_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Name", "type": "text"}, # Loans Name
    {"api": "Record_Status__s", "type": "picklist"},
    {"api": "Owner", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Modified_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Modified_Time", "type": "datetime"},
    {"api": "Last_Activity_Time", "type": "datetime"},
    {"api": "Tag", "type": "text"},
    {"api": "Unsubscribed_Mode", "type": "picklist"},
    {"api": "Unsubscribed_Time", "type": "datetime"},
    
    # Financial Totals & Rollups
    {"api": "Total_Current_Loan_Balance", "type": "rollup_summary"},
    {"api": "Total_Original_Loan_Balance", "type": "rollup_summary"},
    {"api": "Number_of_loans", "type": "rollup_summary"},
    {"api": "Earliest_Fixed_Rate_Expiry", "type": "rollup_summary"}, 
    
    # Classification
    {"api": "Loan_Type", "type": "picklist"}, 
    {"api": "Locked__s", "type": "boolean"},
    
    # Relationships & Security (Lookups with Targets)
    {"api": "Lender", "type": "lookup", "target": "Accounts"}, # Often Accounts or Vendors
    {"api": "Deal", "type": "lookup", "target": "Deals"},
    {"api": "Security", "type": "lookup", "target": "Asset_Ownership_New"}, # General Asset
    {"api": "Real_Assets_Security", "type": "lookup", "target": "Asset_Ownership_New"}, # Real Estate Asset
    
    # Advisory Team
    {"api": "Primary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "Primary_Advisors", "type": "userlookup", "target": "Users"}
]

class LoansAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in LOANS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Loan JSON into a clean, readable text block.
        """
        if not record: return "No Loan Data Available."

        # === 1. LIST MODE (Context Switch / Search Results) ===
        if "items" in record:
            items = record["items"]
            if not items: return "No Loans found."
            
            lines = [f"=== FOUND {len(items)} LOANS ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Loan #{i} ---")
                
                # A. ALWAYS show identifiers
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Name" in item: lines.append(f"Name: {item['Name']}")
                
                # B. FORCE SHOW critical fields even if empty (for Updates)
                critical_fields = ["Total_Current_Loan_Balance", "Lender", "Loan_Type", "Earliest_Fixed_Rate_Expiry"]
                
                for k, v in item.items():
                    if k not in ["id", "Name", "Tag"]:
                        val_display = v
                        if isinstance(v, dict) and "name" in v: val_display = v["name"]
                        
                        # Show if value exists OR if it is critical
                        if v or k in critical_fields:
                            if not v and v is not False: val_display = "[Empty]"
                            lines.append(f"{k}: {val_display}")
            return "\n".join(lines)

        # === 2. SINGLE RECORD MODE ===
        lines = ["=== LOAN FACILITY DETAILS ==="]

        # Process Standard Fields
        for field in LOANS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val: val = val["name"]
            
            # Formatting Currency
            if "Balance" in key and isinstance(val, (int, float, str)):
                 val = f"${val}"

            clean_key = key.replace("_", " ")
            lines.append(f"{clean_key}: {val}")

        # Add Debt Utilization Context
        try:
            current = float(record.get("Total_Current_Loan_Balance", 0))
            original = float(record.get("Total_Original_Loan_Balance", 0))
            if original > 0:
                paid_off = original - current
                percent = round((paid_off / original) * 100, 1)
                lines.append(f"\n[AI Analysis]: {percent}% of original principal paid off.")
        except:
            pass

        # Process Related Lists
        lines.append("\n--- RELATED LOAN DATA ---")
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
                if "id" in item: row_parts.append(f"ID: {item['id']}")
                
                if config_key:
                    for f in SPECIFIC_LIST_CONFIG[config_key]:
                        val = item.get(f)
                        if val: row_parts.append(f"{f}: {val}")
                else:
                    # Auto-Detect
                    priority_keywords = ["name", "balance", "rate", "amount", "status"]
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
                        if count >= 3: break
                
                lines.append(f"  {i}. " + " | ".join(row_parts))

        if not found_details: lines.append("(No related loan structures or notes found)")

        return "\n".join(lines)

    def generate_response(self, user_query: str, loan_data: dict, history: list = []) -> str:
        """
        Generates a response answering questions about the Loan.
        """
        context_text = self.format_data_for_ai(loan_data)

        # Format History
        history_block = ""
        if history:
            history_block = "### CONVERSATION HISTORY\n"
            for msg in history[-3:]:
                role = "User" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_block += f"{role}: {content}\n"

        prompt = f"""
        You are an expert Debt Manager & Credit Analyst.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### LOAN CONTEXT
        {context_text}
        
        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** Include `record_id` for updates.
        - **Lookups:** If the user provides a Lender Name or Security Asset, pass it as text. My system will convert it.
        - **Risk:** Check 'Earliest Fixed Rate Expiry'. If imminent, warn the user.

        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Loans", 
            "record_id": "12345",
            "data": {{ 
                "Name": "REQUIRED_LOAN_NAME",
                "Loan_Type": "Mortgage",
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text