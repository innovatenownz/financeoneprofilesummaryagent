import json
import google.generativeai as genai

# --- 1. CONFIGURATION ---

# Related List Configuration (for fetching details)
SPECIFIC_LIST_CONFIG = {
    "Notes": ["Note_Title", "Note_Content", "Created_Time", "Owner"],
    "Tasks": ["Subject", "Status", "Priority", "Due_Date"],
    "Calls": ["Subject", "Call_Type", "Call_Duration", "Call_Start_Time"],
    "Events": ["Event_Title", "Start_DateTime", "End_DateTime", "Location"],
    "Emails": ["Subject", "Status", "Sent_Time", "To"],
    "Attachments": ["File_Name", "Size", "Created_Time"],
    "CheckLists": ["Name", "Status", "Created_Time"]
}

# --- KNOWLEDGE BASE: PORTFOLIO SCHEMA ---
# [UPDATED] Added 'target' keys so main.py can resolve lookups automatically
PORTFOLIO_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Name", "type": "text"}, # Investment portfolio Name
    {"api": "Record_Status__s", "type": "picklist"},
    {"api": "Owner", "type": "ownerlookup", "target": "Users"},
    {"api": "Email", "type": "email"},
    {"api": "Secondary_Email", "type": "email"},
    {"api": "Created_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Modified_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Modified_Time", "type": "datetime"},
    {"api": "Last_Activity_Time", "type": "datetime"},
    {"api": "Email_Opt_Out", "type": "boolean"},
    {"api": "Tag", "type": "text"},
    {"api": "Unsubscribed_Mode", "type": "picklist"},
    {"api": "Unsubscribed_Time", "type": "datetime"},
    {"api": "Portfolio_ID", "type": "text"},
    {"api": "Portfolio_status", "type": "picklist"},
    {"api": "Locked__s", "type": "boolean"},
    
    # Dates & Compliance
    {"api": "Original_setup_date", "type": "date"},
    {"api": "Review_date", "type": "date"},
    {"api": "Closure_transfer_date", "type": "date"},
    {"api": "Review_frequency", "type": "picklist"},
    {"api": "Last_Review_Date", "type": "date"},
    {"api": "Next_Review_Date", "type": "formula"}, 
    
    # Operations
    {"api": "Minimum_Signatures", "type": "integer"},
    {"api": "Portoflio_Deal_Association", "type": "picklist"},
    
    # Relationships (Lookups with Targets)
    {"api": "Deal", "type": "lookup", "target": "Deals"},
    {"api": "Portfolio_Owners", "type": "subform"}, 
    
    # Advisory Team
    {"api": "Primary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "Secondary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "Investment_Portfolios_Owners", "type": "multiuserlookup", "target": "Users"}
]

class InvestmentPortfoliosAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in PORTFOLIO_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Investment Portfolio JSON into a clean, readable text block.
        """
        if not record: return "No Investment Portfolio Data Available."

        # === 1. LIST MODE (Context Switch / Search Results) ===
        if "items" in record:
            items = record["items"]
            if not items: return "No Investment Portfolios found."
            
            lines = [f"=== FOUND {len(items)} PORTFOLIOS ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Portfolio #{i} ---")
                
                # A. ALWAYS show identifiers
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Name" in item: lines.append(f"Name: {item['Name']}")
                
                # B. FORCE SHOW critical fields even if empty (for Updates)
                critical_fields = ["Portfolio_status", "Review_date", "Next_Review_Date", "Deal"]
                
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
        lines = ["=== INVESTMENT PORTFOLIO DETAILS ==="]

        # Process Standard Fields
        for field in PORTFOLIO_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in v: val = val["name"]
            
            # Formatting Multi-User Lookups
            if key == "Investment_Portfolios_Owners" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val if isinstance(u, dict)]
                val = ", ".join(names)

            # Formatting Subforms (Portfolio Owners)
            if key == "Portfolio_Owners" and isinstance(val, list):
                lines.append("\n--- PORTFOLIO OWNERS / SIGNATORIES ---")
                for i, owner in enumerate(val, 1):
                    owner_name = owner.get("Name") or owner.get("Owner_Name") or "Unknown"
                    lines.append(f"  {i}. {owner_name}")
                continue

            clean_key = key.replace("_", " ")
            lines.append(f"{clean_key}: {val}")

        # Process Related Lists
        lines.append("\n--- RELATED ACTIVITY DATA ---")
        list_keys = [k for k, v in record.items() if isinstance(v, list) and k not in ["Tag", "Portfolio_Owners"]]
        
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
                    priority_keywords = ["subject", "name", "title", "status", "date"]
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

        if not found_details: lines.append("(No recent activities or notes found)")

        return "\n".join(lines)

    def generate_response(self, user_query: str, portfolio_data: dict, history: list = []) -> str:
        """
        Generates a response answering questions about the Investment Portfolio.
        """
        context_text = self.format_data_for_ai(portfolio_data)

        # Format History
        history_block = ""
        if history:
            history_block = "### CONVERSATION HISTORY\n"
            for msg in history[-3:]:
                role = "User" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_block += f"{role}: {content}\n"

        prompt = f"""
        You are an expert Investment Portfolio Manager & Compliance Officer.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### PORTFOLIO CONTEXT
        {context_text}
        
        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** Include `record_id` for updates.
        - **Lookups:** If the user provides a Deal Name, pass it as text. My system will convert it.
        - **Compliance:** Check 'Next Review Date' vs Today.

        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Investment_portfolios", 
            "record_id": "12345",
            "data": {{ 
                "Name": "REQUIRED_PORTFOLIO_NAME",
                "Portfolio_status": "Active",
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text