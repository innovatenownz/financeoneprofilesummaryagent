import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: DEALS SCHEMA ---
# Mapped directly from your provided field list
DEALS_SCHEMA = [
    # Core Info
    {"api": "Deal_Name", "type": "text"},
    {"api": "Amount", "type": "currency"},
    {"api": "Closing_Date", "type": "date"},
    {"api": "Stage", "type": "picklist"},
    {"api": "Probability", "type": "integer (%)"},
    {"api": "Pipeline", "type": "picklist"},
    {"api": "Type", "type": "picklist"},
    {"api": "Expected_Revenue", "type": "currency"},
    
    # Relationships
    {"api": "Account_Name", "type": "lookup (Account)"},
    {"api": "Contact_Name", "type": "lookup (Contact)"},
    {"api": "Owner", "type": "ownerlookup"},
    {"api": "Primary_Advisor", "type": "userlookup"},
    {"api": "Secondary_Advisor", "type": "userlookup"},
    {"api": "Deal_Team_Members", "type": "multiuserlookup"},
    
    # Custom Business Fields
    {"api": "FUM", "type": "currency"},
    {"api": "Portfolio_Type", "type": "picklist"},
    {"api": "Inquiry_Type", "type": "picklist"}, # Deal Sub-Type
    {"api": "Is_Upsell_Deal", "type": "boolean"},
    {"api": "Portfolio_Opputunity", "type": "boolean"},
    {"api": "Deal_Confirmation_Status", "type": "picklist"},
    {"api": "Interest_Level", "type": "picklist"},
    {"api": "Entities_involved", "type": "picklist"},
    {"api": "Entity_type", "type": "picklist"},
    
    # Status & Analysis
    {"api": "Reason_For_Loss__s", "type": "picklist"},
    {"api": "Lead_Source", "type": "picklist"},
    {"api": "Campaign_Source", "type": "lookup"},
    {"api": "Sales_Cycle_Duration", "type": "integer"},
    {"api": "Overall_Sales_Duration", "type": "integer"},
    
    # Description
    {"api": "Description", "type": "textarea"},
    
    # Subforms (Complex Related Data)
    {"api": "On_boarding", "type": "subform"},
    {"api": "Assigned_Roles", "type": "subform"}
]

class DealsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in DEALS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Deal JSON into a clean, readable text block.
        """
        if not record:
            return "No Deal Data Available."

        lines = ["=== DEAL / OPPORTUNITY DETAILS ==="]

        # 1. Process Standard Fields
        for field in DEALS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Multi-User Lookups (List of dicts)
            if isinstance(val, list) and key == "Deal_Team_Members":
                names = [u.get("name", str(u)) for u in val if isinstance(u, dict)]
                val = ", ".join(names)

            # Formatting Subforms (On_boarding, Assigned_Roles)
            if key in ["On_boarding", "Assigned_Roles"] and isinstance(val, list):
                lines.append(f"\n--- {key.replace('_', ' ')} (Subform) ---")
                for i, row in enumerate(val, 1):
                    details = []
                    for k, v in row.items():
                        if v and k not in ["id", "s_id"]:
                            # Resolve sub-lookups
                            if isinstance(v, dict) and "name" in v: v = v["name"]
                            details.append(f"{k}: {v}")
                    lines.append(f"  {i}. " + ", ".join(details))
                continue

            lines.append(f"{key}: {val}")

        # 2. Add Notes (Crucial for Sales Context)
        if "Related_Notes" in record:
            notes = record["Related_Notes"]
            if notes:
                lines.append(f"\n=== SALES NOTES ({len(notes)}) ===")
                for i, note in enumerate(notes[:3], 1):
                    content = note.get("Note_Content") or ""
                    lines.append(f"  {i}. {content}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, deal_data: dict) -> str:
        """
        Generates a response answering questions about the Deal.
        """
        context_text = self.format_data_for_ai(deal_data)

        prompt = f"""
        You are an expert Sales Manager Assistant.
        
        Your goal is to provide insights on this DEAL based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### DEAL CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Revenue Focus:** Use 'Amount', 'FUM', and 'Expected Revenue' to assess value.
        - **Pipeline Risk:** Check 'Closing Date' vs 'Stage'. If the date is passed, flag it.
        - **Team:** If asked about the team, check 'Deal Team Members', 'Primary Advisor', or 'Assigned Roles'.
        - **Loss Analysis:** If the deal is Lost, look at 'Reason_For_Loss__s'.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text