import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: TASKS SCHEMA ---
TASKS_SCHEMA = [
    # Core Task Info
    {"api": "Subject", "type": "picklist"},
    {"api": "Due_Date", "type": "date"},
    {"api": "Status", "type": "picklist"},
    {"api": "Priority", "type": "picklist"},
    {"api": "Description", "type": "textarea"},
    
    # Ownership & People
    {"api": "Owner", "type": "ownerlookup"},
    {"api": "Who_Id", "type": "lookup (Contact)"}, # Contact Name
    {"api": "What_Id", "type": "lookup (Related To)"}, # Account/Deal
    {"api": "Created_By", "type": "ownerlookup"},
    
    # Timings
    {"api": "Closed_Time", "type": "datetime"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Remind_At", "type": "alarm"},
    {"api": "Recurring_Activity", "type": "rrule"},
    
    # Custom Compliance Fields (Booleans)
    {"api": "Annual_Tax_Return", "type": "boolean"},
    {"api": "W8_BEN_Form", "type": "boolean"},
    {"api": "W9_Form", "type": "boolean"},
    {"api": "FATCA_Report", "type": "boolean"},
    {"api": "CRS_Report", "type": "boolean"},
    {"api": "Other_December_Report", "type": "boolean"},
    
    # System
    {"api": "Send_Notification_Email", "type": "boolean"},
    {"api": "Tag", "type": "jsonarray"}
]

class TasksAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in TASKS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Task JSON into a clean, readable text block.
        """
        if not record:
            return "No Task Data Available."

        lines = ["=== TASK / ACTIVITY DETAILS ==="]

        # 1. Process Fields
        for field in TASKS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Booleans (True/False to Yes/No for readability)
            if field['type'] == 'boolean':
                val = "Yes" if val else "No"

            # Formatting Lists (Tags)
            if isinstance(val, list):
                val = ", ".join([str(v) for v in val])

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, task_data: dict) -> str:
        """
        Generates a response answering questions about the Task.
        """
        context_text = self.format_data_for_ai(task_data)

        prompt = f"""
        You are an expert Operations & Compliance Assistant.
        
        Your goal is to manage this TASK/ACTIVITY based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### TASK CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Deadline Focus:** Check 'Due_Date' vs current status. If overdue, flag it.
        - **Compliance Check:** If this task involves 'Annual Tax Return', 'FATCA', or 'W8/W9' forms, emphasize the importance of accuracy.
        - **Relationships:** Identify WHO this is for ('Who_Id') and WHAT it is related to ('What_Id').
        - **Next Action:** If Status is 'Not Started' or 'Deferred', suggest immediate action based on Priority.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text