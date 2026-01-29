import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: EVENTS SCHEMA ---
EVENTS_SCHEMA = [
    # Core Event Info
    {"api": "Event_Title", "type": "text"},
    {"api": "Venue", "type": "text"},
    {"api": "Start_DateTime", "type": "datetime"},
    {"api": "End_DateTime", "type": "datetime"},
    {"api": "All_day", "type": "boolean"},
    {"api": "Host", "type": "ownerlookup"},
    
    # Participants & Relations
    {"api": "Who_Id", "type": "lookup (Contact)"},
    {"api": "What_Id", "type": "lookup (Related To)"},
    {"api": "Participants", "type": "bigint (count)"},
    
    # Meeting Details
    {"api": "Meeting_Venue__s", "type": "picklist"}, # In-office, Online
    {"api": "Meeting_Provider__s", "type": "picklist"},
    {"api": "Description", "type": "textarea"},
    {"api": "Remind_At", "type": "multireminder"},
    {"api": "Recurring_Activity", "type": "rrule"},
    
    # Check-In Data (Location Tracking)
    {"api": "Check_In_Status", "type": "text"},
    {"api": "Check_In_Time", "type": "datetime"},
    {"api": "Check_In_Address", "type": "textarea"},
    {"api": "Check_In_City", "type": "text"},
    {"api": "Latitude", "type": "double"},
    {"api": "Longitude", "type": "double"},
    {"api": "Check_In_Comment", "type": "textarea"}
]

class EventsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in EVENTS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Event JSON into a clean, readable text block.
        """
        if not record:
            return "No Event Data Available."

        lines = ["=== EVENT / MEETING DETAILS ==="]

        # 1. Process Fields
        for field in EVENTS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Booleans
            if field['type'] == 'boolean':
                val = "Yes" if val else "No"
                
            # Formatting Reminders (List of dicts usually)
            if key == "Remind_At" and isinstance(val, list):
                val = f"{len(val)} reminder(s) set"

            lines.append(f"{key}: {val}")

        # 2. Add Participants List (if available in a separate list)
        if "Related_Participants" in record:
            parts = record["Related_Participants"]
            if parts:
                lines.append(f"\n=== PARTICIPANTS ({len(parts)}) ===")
                for p in parts:
                    name = p.get("name") or p.get("participant_name") or "Unknown"
                    status = p.get("status") or "Invited"
                    lines.append(f"  - {name} ({status})")

        return "\n".join(lines)

    def generate_response(self, user_query: str, event_data: dict) -> str:
        """
        Generates a response answering questions about the Event.
        """
        context_text = self.format_data_for_ai(event_data)

        prompt = f"""
        You are an expert Executive Assistant & Scheduler.
        
        Your goal is to manage this MEETING/EVENT based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### EVENT CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Schedule Check:** Clearly state the Start and End times.
        - **Venue:** Differentiate between Physical locations ('Venue', 'Check_In_City') and Online ('Meeting_Provider__s').
        - **Status:** If the user asks if the meeting happened, check 'Check_In_Status' or if the 'End_DateTime' is in the past.
        - **Attendees:** Identify the Host (Owner) and the Contact ('Who_Id').
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text