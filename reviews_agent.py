import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: REVIEWS SCHEMA ---
REVIEWS_SCHEMA = [
    # Core Review Info
    {"api": "Name", "type": "text"}, # Review Name
    {"api": "Type_of_review", "type": "picklist"}, # Annual, Ad-hoc
    {"api": "Area_Reviewed", "type": "picklist"}, # e.g. Investment, Insurance
    {"api": "Review_Status", "type": "picklist"}, # Scheduled, Completed
    
    # Dates
    {"api": "Date_initiated", "type": "date"},
    {"api": "Date_completed", "type": "date"},
    
    # Outcomes & Actions
    {"api": "Discussion_Summary", "type": "textarea"},
    {"api": "Change_and_update_in_client_situation_and_goals", "type": "textarea"},
    {"api": "Recommended_Actions", "type": "textarea"},
    {"api": "Identify_Next_Steps", "type": "textarea"},
    
    # Linked Entities (What was reviewed?)
    {"api": "Account_Reviewed", "type": "lookup (Account)"},
    {"api": "Review_Contact", "type": "lookup (Contact)"},
    {"api": "Portfolio", "type": "lookup (Investment Portfolio)"},
    {"api": "Lending", "type": "lookup (Loan)"},
    {"api": "Insurances", "type": "lookup (Insurance Policy)"},
    
    # Advisory Team
    {"api": "Review_Owners", "type": "multiuserlookup"},
    {"api": "Owner", "type": "ownerlookup"},
    
    # System
    {"api": "Record_Status__s", "type": "picklist"},
    {"api": "Details_Received", "type": "boolean"}
]

class ReviewsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in REVIEWS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Review JSON into a clean, readable text block.
        """
        if not record:
            return "No Review Data Available."

        lines = ["=== REVIEW DETAILS ==="]

        # 1. Process Fields
        for field in REVIEWS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Multi-User Lookups
            if key == "Review_Owners" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val]
                val = ", ".join(names)
            
            # Formatting Booleans
            if field['type'] == 'boolean':
                val = "Yes" if val else "No"

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, review_data: dict) -> str:
        """
        Generates a response answering questions about the Client Review.
        """
        context_text = self.format_data_for_ai(review_data)

        prompt = f"""
        You are an expert Compliance Officer & Financial Advisor Assistant.
        
        Your goal is to analyze this CLIENT REVIEW RECORD based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### REVIEW CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Summary:** Summarize the 'Discussion_Summary' and 'Recommended_Actions'.
        - **Status:** Is this review 'Completed' or still in progress?
        - **Scope:** Identify what was reviewed (e.g., Portfolio, Insurance, or General Account).
        - **Changes:** Highlight any 'Change_and_update_in_client_situation_and_goals'.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text