import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: ASSOCIATED PORTFOLIOS SCHEMA ---
ASSOC_PORTFOLIO_SCHEMA = [
    # Core Identity
    {"api": "id", "type": "text"},
    {"api": "Name", "type": "text"}, # Association Name
    {"api": "Role", "type": "picklist"}, # e.g. Trustee, Beneficiary
    {"api": "Portfolio_Association_Type", "type": "picklist"}, # Joint, Individual
    {"api": "Portfolio_Ownership_Status", "type": "picklist"},
    {"api": "Share_Percentage", "type": "percent"},
    
    # Links (UPDATED WITH TARGETS)
    {"api": "Client", "type": "lookup", "target": "Contacts"},
    {"api": "Household", "type": "lookup", "target": "Accounts"},
    {"api": "Investment_portfolio", "type": "lookup", "target": "Investment_portfolios"}, # Verify API Name of Portfolios module
    
    # Governance & Reporting
    {"api": "Receives_IMS_Report", "type": "boolean"},
    {"api": "Portfolio_Next_Review_Date", "type": "date"},
    
    # Advisory Team
    {"api": "Primary_Advisor", "type": "userlookup", "target": "Users"},
    {"api": "Secondary_Advisor", "type": "userlookup", "target": "Users"},
]

class AssociatedPortfoliosAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in ASSOC_PORTFOLIO_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Associated Portfolio JSON into a clean, readable text block.
        """
        if not record: return "No Associated Portfolio Data Available."

        # === LIST MODE (Context Switch) ===
        if "items" in record:
            items = record["items"]
            if not items: return "No Associated Portfolios found."
            
            lines = [f"=== FOUND {len(items)} PORTFOLIO ASSOCIATIONS ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Association #{i} ---")
                
                # 1. ALWAYS show identifiers
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Name" in item: lines.append(f"Name: {item['Name']}")
                
                # 2. FORCE SHOW important fields even if empty
                critical_fields = ["Role", "Portfolio_Association_Type", "Share_Percentage", "Client", "Investment_portfolio"]
                
                for k, v in item.items():
                    if k not in ["id", "Name", "Tag"]:
                        val_display = v
                        if isinstance(v, dict) and "name" in v: val_display = v["name"]
                        
                        if v or k in critical_fields:
                            if not v and v is not False: val_display = "[Empty]"
                            lines.append(f"{k}: {val_display}")
                            
            return "\n".join(lines)

        # === SINGLE RECORD MODE ===
        lines = ["=== PORTFOLIO ASSOCIATION DETAILS ==="]
        for field in ASSOC_PORTFOLIO_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]: continue
            
            if isinstance(val, dict) and "name" in val: val = val["name"]
            if field['type'] == 'percent': val = f"{val}%"
            if field['type'] == 'boolean': val = "Yes" if val else "No"
            
            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, assoc_data: dict, history: list = []) -> str:
        context_text = self.format_data_for_ai(assoc_data)

        # Format History
        history_block = ""
        if history:
            history_block = "### CONVERSATION HISTORY\n"
            for msg in history[-3:]:
                role = "User" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_block += f"{role}: {content}\n"

        prompt = f"""
        You are an expert Governance & Compliance Officer.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### ASSOCIATION CONTEXT
        {context_text}
        
        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** Include `record_id` for updates.
        - **Lookups:** If the user provides a Client Name or Portfolio Name, pass it as text. My system will convert it to an ID.

        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Associated_portfolios", 
            "record_id": "12345",
            "data": {{ 
                "Name": "REQUIRED_NAME",
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text