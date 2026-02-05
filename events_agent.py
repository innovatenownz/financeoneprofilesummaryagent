import json
import google.generativeai as genai

# --- 1. CONFIGURATION ---

# Related List Configuration (for fetching details)
SPECIFIC_LIST_CONFIG = {
    "Notes": ["Note_Title", "Note_Content", "Created_Time", "Owner"],
    "Attachments": ["File_Name", "Size", "Created_Time"],
    "Invitees": ["Name", "Email", "Status", "Participant_Type"],
    "CheckLists": ["Name", "Status", "Created_Time"]
}

# --- KNOWLEDGE BASE: EVENTS SCHEMA ---
# [UPDATED] Added 'target' keys so main.py can resolve lookups automatically
EVENTS_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Event_Title", "type": "text"}, 
    {"api": "Venue", "type": "text"}, 
    {"api": "All_day", "type": "boolean"},
    {"api": "Start_DateTime", "type": "datetime"}, 
    {"api": "End_DateTime", "type": "datetime"}, 
    {"api": "Owner", "type": "ownerlookup", "target": "Users"}, 
    
    # Lookups with Targets
    {"api": "Who_Id", "type": "lookup", "target": "Contacts"}, # Contact Name
    {"api": "What_Id", "type": "lookup", "target": "Accounts"}, # Related To (Can be Account/Deal/etc, usually Account)
    
    {"api": "Recurring_Activity", "type": "rrule"},
    {"api": "Remind_At", "type": "multireminder"},
    {"api": "Created_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Modified_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Modified_Time", "type": "datetime"},
    {"api": "Participants", "type": "bigint"},
    {"api": "Description", "type": "textarea"},
    
    # Check-In Fields
    {"api": "Check_In_Time", "type": "datetime"},
    {"api": "Check_In_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Check_In_Comment", "type": "textarea"},
    {"api": "Check_In_City", "type": "text"},
    {"api": "Check_In_Status", "type": "text"},
    {"api": "Latitude", "type": "double"},
    {"api": "Longitude", "type": "double"},
    {"api": "Check_In_Address", "type": "textarea"},
    {"api": "ZIP_Code", "type": "text"},
    
    # Meeting Details
    {"api": "Meeting_Venue__s", "type": "picklist"}, # In-office, Online
    {"api": "Meeting_Provider__s", "type": "picklist"},
    {"api": "Record_Status__s", "type": "picklist"},
    {"api": "Remind_Participants", "type": "multireminder"}
]

class EventsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in EVENTS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Event JSON into a clean, readable text block.
        """
        if not record: return "No Event Data Available."

        # === 1. LIST MODE (Context Switch / Search Results) ===
        if "items" in record:
            items = record["items"]
            if not items: return "No Events found."
            
            lines = [f"=== FOUND {len(items)} EVENTS ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Event #{i} ---")
                
                # A. ALWAYS show identifiers
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Event_Title" in item: lines.append(f"Title: {item['Event_Title']}")
                
                # B. FORCE SHOW critical fields even if empty (for Updates)
                critical_fields = ["Start_DateTime", "End_DateTime", "Venue", "Who_Id", "What_Id"]
                
                for k, v in item.items():
                    if k not in ["id", "Event_Title", "Tag"]:
                        val_display = v
                        if isinstance(v, dict) and "name" in v: val_display = v["name"]
                        
                        # Show if value exists OR if it is critical
                        if v or k in critical_fields:
                            if not v and v is not False: val_display = "[Empty]"
                            lines.append(f"{k}: {val_display}")
            return "\n".join(lines)

        # === 2. SINGLE RECORD MODE ===
        lines = ["=== EVENT / MEETING DETAILS ==="]

        # Process Standard Fields
        for field in EVENTS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val: val = val["name"]
            
            # Formatting Booleans
            if field['type'] == 'boolean': val = "Yes" if val else "No"
                
            # Formatting Reminders
            if "reminder" in field['type'] and isinstance(val, list):
                val = f"{len(val)} reminder(s) set"

            clean_key = key.replace("_", " ")
            lines.append(f"{clean_key}: {val}")

        # Process Related Lists
        lines.append("\n--- RELATED EVENT DATA ---")
        list_keys = [k for k, v in record.items() if isinstance(v, list) and k != "Tag"]
        
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
                    priority_keywords = ["name", "email", "status", "title"]
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

        if not found_details: lines.append("(No invitees or notes found)")

        return "\n".join(lines)

    def generate_response(self, user_query: str, event_data: dict, history: list = []) -> str:
        """
        Generates a response answering questions about the Event.
        """
        context_text = self.format_data_for_ai(event_data)

        # Format History
        history_block = ""
        if history:
            history_block = "### CONVERSATION HISTORY\n"
            for msg in history[-3:]:
                role = "User" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_block += f"{role}: {content}\n"

        prompt = f"""
        You are an expert Executive Assistant & Scheduler.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### EVENT CONTEXT
        {context_text}
        
        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** Include `record_id` for updates.
        - **Lookups:** If the user provides a Contact Name for 'Who_Id' or Account Name for 'What_Id', pass it as text. My system will convert it.
        - **Schedule:** State Start/End times clearly.

        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Events", 
            "record_id": "12345",
            "data": {{ 
                "Event_Title": "REQUIRED_TITLE",
                "Start_DateTime": "2023-10-25T10:00:00+05:30",
                "End_DateTime": "2023-10-25T11:00:00+05:30",
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text