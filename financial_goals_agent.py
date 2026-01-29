import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: FINANCIAL GOALS SCHEMA ---
GOALS_SCHEMA = [
    # Core Goal Info
    {"api": "Name", "type": "text"}, # Goal Name
    {"api": "Goal_Type", "type": "picklist"}, # e.g. Retirement, Education
    {"api": "Priority", "type": "picklist"}, # High, Medium, Low
    {"api": "Status", "type": "picklist"}, # On Track, At Risk
    
    # Financial Metrics
    {"api": "Target_Amount", "type": "currency"},
    {"api": "Current_Savings", "type": "currency"},
    {"api": "Funding_Gap", "type": "formula (currency)"}, # Calculated shortfall
    
    # Timeline
    {"api": "Target_Date", "type": "date"},
    
    # People
    {"api": "Client", "type": "lookup (Contact)"},
    {"api": "Financial_Goal_Owners", "type": "multiuserlookup"}, # Advisors
    {"api": "Owner", "type": "ownerlookup"},
    
    # System & Content
    {"api": "Write_Notes", "type": "textarea"},
    {"api": "Record_Status__s", "type": "picklist"}
]

class FinancialGoalsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in GOALS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Financial Goal JSON into a clean, readable text block.
        """
        if not record:
            return "No Financial Goal Data Available."

        lines = ["=== FINANCIAL GOAL DETAILS ==="]

        # 1. Process Fields
        for field in GOALS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Multi-User Lookups
            if key == "Financial_Goal_Owners" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val]
                val = ", ".join(names)
            
            # Formatting Currency
            if field['type'] == 'currency' or field['type'] == 'formula (currency)':
                val = f"${val}"

            lines.append(f"{key}: {val}")

        # 2. Add Derived Progress (AI Context)
        try:
            target = float(record.get("Target_Amount", 0))
            current = float(record.get("Current_Savings", 0))
            if target > 0:
                percent = round((current / target) * 100, 1)
                lines.append(f"\n[Calculated Progress]: {percent}% Funded")
        except:
            pass

        return "\n".join(lines)

    def generate_response(self, user_query: str, goal_data: dict) -> str:
        """
        Generates a response answering questions about the Financial Goal.
        """
        context_text = self.format_data_for_ai(goal_data)

        prompt = f"""
        You are an expert Financial Planner & Wealth Manager.
        
        Your goal is to analyze this FINANCIAL GOAL based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### GOAL CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Progress Check:** Analyze the 'Funding_Gap' and 'Target_Date'. Is the client on track?
        - **Urgency:** If 'Priority' is High and the Gap is large, emphasize the need for action.
        - **Details:** Mention the 'Goal_Type' (e.g., Retirement) to contextualize the advice.
        - **Ownership:** Identify the 'Financial_Goal_Owners' responsible for this plan.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text