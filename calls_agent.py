import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: CALLS SCHEMA ---
CALLS_SCHEMA = [
    # Core Call Info
    {"api": "Subject", "type": "text"},
    {"api": "Call_Type", "type": "picklist"}, # Inbound, Outbound, Missed
    {"api": "Call_Purpose", "type": "picklist"}, # Demo, Negotiation, Support
    {"api": "Call_Status", "type": "picklist"}, # Scheduled, Completed
    {"api": "Call_Result", "type": "picklist"}, # Interested, Not Interested, Busy
    
    # Timing & Duration
    {"api": "Call_Start_Time", "type": "datetime"},
    {"api": "Call_Duration", "type": "text"}, # e.g. "05:00"
    {"api": "Call_Duration_in_seconds", "type": "integer"},
    
    # Participants
    {"api": "Owner", "type": "ownerlookup"}, # Call Owner
    {"api": "Who_Id", "type": "lookup (Contact)"},
    {"api": "What_Id", "type": "lookup (Related To)"}, # Account/Deal
    {"api": "Caller_ID", "type": "text"},
    {"api": "Dialled_Number", "type": "text"},
    
    # Content & Outcomes
    {"api": "Description", "type": "textarea"},
    {"api": "Call_Agenda", "type": "text"},
    {"api": "Voice_Recording__s", "type": "website"}, # URL
    
    # System
    {"api": "CTI_Entry", "type": "boolean"}, # Was this auto-logged?
    {"api": "Outgoing_Call_Status", "type": "picklist"},
    {"api": "Scheduled_In_CRM", "type": "picklist"}
]

class CallsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in CALLS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Call JSON into a clean, readable text block.
        """
        if not record:
            return "No Call Data Available."

        lines = ["=== CALL LOG DETAILS ==="]

        # 1. Process Fields
        for field in CALLS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Durations
            if key == "Call_Duration_in_seconds":
                mins = int(val) // 60
                secs = int(val) % 60
                val = f"{mins}m {secs}s"

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, call_data: dict) -> str:
        """
        Generates a response answering questions about the Call.
        """
        context_text = self.format_data_for_ai(call_data)

        prompt = f"""
        You are an expert Sales Operations Analyst.
        
        Your goal is to analyze this PHONE CALL LOG based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### CALL CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Outcome Analysis:** Check 'Call_Result' and 'Description'. Was it successful?
        - **Duration Check:** If the call was very short (< 30s), it might be a 'No Answer' or 'Left Voicemail'.
        - **Next Steps:** If the result was 'Interested', suggest following up.
        - **Recording:** If a 'Voice_Recording__s' link exists, point the user to it.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text