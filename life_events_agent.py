import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: LIFE EVENTS SCHEMA ---
LIFE_EVENTS_SCHEMA = [
    # Core Event Info
    {"api": "Name", "type": "text"}, # Event Name (e.g. "John's 50th Birthday")
    {"api": "Event_Type", "type": "picklist"}, # e.g. Birthday, Anniversary, Graduation
    {"api": "Event_Date", "type": "date"},
    {"api": "Status", "type": "picklist"}, # e.g. Upcoming, Completed
    
    # Actionable Info
    {"api": "Next_Action_Date", "type": "date"},
    {"api": "Description", "type": "textarea"},
    
    # People
    {"api": "Client", "type": "lookup (Contact)"},
    {"api": "Life_Event_Managers", "type": "multiuserlookup"}, # Team members responsible
    {"api": "Owner", "type": "ownerlookup"},
    
    # System
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Record_Status__s", "type": "picklist"}
]

class LifeEventsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in LIFE_EVENTS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Life Event JSON into a clean, readable text block.
        """
        if not record:
            return "No Life Event Data Available."

        lines = ["=== LIFE EVENT DETAILS ==="]

        # 1. Process Fields
        for field in LIFE_EVENTS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Multi-User Lookups
            if key == "Life_Event_Managers" and isinstance(val, list):
                names = [u.get("name", "Unknown") for u in val]
                val = ", ".join(names)

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, event_data: dict) -> str:
        """
        Generates a response answering questions about the Life Event.
        """
        context_text = self.format_data_for_ai(event_data)

        prompt = f"""
        You are an expert Client Relationship Manager.
        
        Your goal is to analyze this CLIENT LIFE EVENT based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### EVENT CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Timing:** Highlight the 'Event_Date'. Is it coming up or in the past?
        - **Next Steps:** Check 'Next_Action_Date'. If defined, tell the user what needs to be done by then.
        - **Context:** Mention the Client this event belongs to.
        - **Team:** Identify the 'Life_Event_Managers' responsible for handling this (e.g., sending a gift).
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text