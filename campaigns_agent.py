import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: CAMPAIGNS SCHEMA ---
CAMPAIGNS_SCHEMA = [
    # Core Campaign Info
    {"api": "Campaign_Name", "type": "text"},
    {"api": "Type", "type": "picklist"}, # e.g. Webinar, Email, Conference
    {"api": "Status", "type": "picklist"}, # Planned, Active, Inactive, Complete
    {"api": "Start_Date", "type": "date"},
    {"api": "End_Date", "type": "date"},
    {"api": "Parent_Campaign", "type": "lookup (Campaign)"},
    
    # Financials (ROI Analysis)
    {"api": "Expected_Revenue", "type": "currency"},
    {"api": "Budgeted_Cost", "type": "currency"},
    {"api": "Actual_Cost", "type": "currency"},
    
    # Performance Metrics
    {"api": "Expected_Response", "type": "bigint"}, # Target leads/responses
    {"api": "Num_sent", "type": "bigint"}, # Reach
    
    # Ownership
    {"api": "Owner", "type": "ownerlookup"},
    {"api": "Created_By", "type": "ownerlookup"},
    
    # System
    {"api": "Description", "type": "textarea"},
    {"api": "Tag", "type": "jsonarray"}
]

class CampaignsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in CAMPAIGNS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Campaign JSON into a clean, readable text block.
        """
        if not record:
            return "No Campaign Data Available."

        lines = ["=== CAMPAIGN DETAILS ==="]

        # 1. Process Fields
        for field in CAMPAIGNS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Currency (Basic logic, can be enhanced)
            if field['type'] == 'currency':
                val = f"${val}"

            lines.append(f"{key}: {val}")

        # 2. Add ROI / Performance Context (Derived)
        budget = record.get("Budgeted_Cost")
        actual = record.get("Actual_Cost")
        if budget and actual:
            try:
                diff = float(budget) - float(actual)
                status = "Under Budget" if diff >= 0 else "OVER Budget"
                lines.append(f"\n[Analysis] Budget Variance: ${diff} ({status})")
            except:
                pass

        return "\n".join(lines)

    def generate_response(self, user_query: str, campaign_data: dict) -> str:
        """
        Generates a response answering questions about the Campaign.
        """
        context_text = self.format_data_for_ai(campaign_data)

        prompt = f"""
        You are an expert Marketing Analyst.
        
        Your goal is to analyze this MARKETING CAMPAIGN based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### CAMPAIGN CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Status Check:** Is the campaign Active, Planned, or Completed?
        - **Financial Analysis:** Compare 'Budgeted_Cost' vs 'Actual_Cost'. If Actual > Budget, warn the user.
        - **ROI Potential:** Look at 'Expected_Revenue' vs 'Actual_Cost'.
        - **Reach:** Reference 'Num_sent' if asked about how many people were contacted.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text