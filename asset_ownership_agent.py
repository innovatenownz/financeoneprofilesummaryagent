import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: ASSET OWNERSHIP SCHEMA ---
# [CRITICAL] Added 'target' so main.py knows where to search for IDs
ASSET_OWNERSHIP_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Name", "type": "text"}, 
    {"api": "Ownership", "type": "picklist"}, 
    {"api": "Ownership_Status", "type": "picklist"},
    {"api": "Asset_Type", "type": "picklist"},
    {"api": "Share_Percentage", "type": "percent"},
    {"api": "Share_Value_Total", "type": "currency"}, 
    {"api": "Asset_Value", "type": "currency"},
    {"api": "Real_Estate_Value", "type": "currency"},
    {"api": "Investment_Holding_Value", "type": "currency"},
    
    # [FIX] Define target modules for lookups
    {"api": "Client", "type": "lookup", "target": "Contacts"},
    {"api": "Households", "type": "lookup", "target": "Accounts"},
]

class AssetOwnershipAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in ASSET_OWNERSHIP_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        if not record: return "No Asset Data Available."

        # LIST MODE
        if "items" in record:
            items = record["items"]
            if not items: return "No Assets found linked to this Account."
            
            lines = [f"=== FOUND {len(items)} ASSETS ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Asset #{i} ---")
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Name" in item: lines.append(f"Name: {item['Name']}")
                
                # Show key fields even if empty
                critical_fields = ["Ownership_Status", "Ownership", "Asset_Type", "Asset_Value", "Client"]
                for k, v in item.items():
                    if k not in ["id", "Name", "Tag"]:
                        val_display = v
                        if isinstance(v, dict) and "name" in v: val_display = v["name"]
                        if v or k in critical_fields:
                            if not v: val_display = "[Empty]"
                            lines.append(f"{k}: {val_display}")
            return "\n".join(lines)

        # SINGLE MODE
        lines = ["=== ASSET DETAILS ==="]
        for field in ASSET_OWNERSHIP_SCHEMA:
            key = field['api']
            val = record.get(key)
            if val in [None, "", [], {}]: continue
            if isinstance(val, dict) and "name" in val: val = val["name"]
            lines.append(f"{key}: {val}")
        return "\n".join(lines)

    def generate_response(self, user_query: str, ownership_data: dict, history: list = []) -> str:
        context_text = self.format_data_for_ai(ownership_data)

        history_block = ""
        if history:
            history_block = "### HISTORY\n" + "\n".join([f"{m.get('role')}: {m.get('content')}" for m in history[-3:]])

        prompt = f"""
        You are an expert Asset Manager.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### ASSET DATA
        {context_text}
        
        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** If updating, use the `record_id` visible in the list.
        - **Lookups:** If the user provides a Client Name (e.g. "Kane"), pass it as the text value for "Client". My system will convert it to an ID.

        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Asset_Ownership_New", 
            "record_id": "12345",
            "data": {{ 
                "Name": "REQUIRED_ASSET_NAME",  <-- MUST BE INCLUDED
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        """
        
        response = self.model.generate_content(prompt)
        return response.text