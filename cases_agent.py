import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: CASES SCHEMA ---
CASES_SCHEMA = [
    # Core Case Info
    {"api": "Case_Number", "type": "autonumber"},
    {"api": "Subject", "type": "text"},
    {"api": "Status", "type": "picklist"},
    {"api": "Priority", "type": "picklist"},
    {"api": "Case_Origin", "type": "picklist"}, # Email, Phone, Web
    {"api": "Case_Reason", "type": "picklist"},
    {"api": "Type", "type": "picklist"}, # Feature Request, Problem
    
    # People & Relations
    {"api": "Account_Name", "type": "lookup (Account)"},
    {"api": "Related_To", "type": "lookup (Contact)"},
    {"api": "Deal_Name", "type": "lookup (Deal)"},
    {"api": "Product_Name", "type": "lookup (Product)"},
    {"api": "Owner", "type": "ownerlookup"},
    
    # Contact Details
    {"api": "Email", "type": "email"},
    {"api": "Phone", "type": "phone"},
    {"api": "Reported_By", "type": "text"},
    
    # Content
    {"api": "Description", "type": "textarea"},
    {"api": "Internal_Comments", "type": "textarea"},
    {"api": "Solution", "type": "textarea"},
    {"api": "Comments", "type": "jsonarray"}, # Read-only list of comments
    {"api": "No_of_comments", "type": "integer"},
    
    # System
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Modified_Time", "type": "datetime"}
]

class CasesAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in CASES_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Case JSON into a clean, readable text block.
        """
        if not record:
            return "No Case Data Available."

        lines = ["=== SUPPORT CASE DETAILS ==="]

        # 1. Process Fields
        for field in CASES_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Comments (if array)
            if key == "Comments" and isinstance(val, list):
                # Sometimes comments are simple strings or dicts
                lines.append(f"Recent Comments: {len(val)} items")
                continue

            lines.append(f"{key}: {val}")

        # 2. Add Related Notes (Standard for Support)
        if "Related_Notes" in record:
            notes = record["Related_Notes"]
            if notes:
                lines.append(f"\n=== TICKET UPDATES/NOTES ({len(notes)}) ===")
                for i, note in enumerate(notes[:3], 1):
                    content = note.get("Note_Content") or ""
                    author = note.get("Created_By", {}).get("name", "Unknown")
                    lines.append(f"  {i}. [{author}]: {content}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, case_data: dict) -> str:
        """
        Generates a response answering questions about the Support Case.
        """
        context_text = self.format_data_for_ai(case_data)

        prompt = f"""
        You are an expert Customer Support Manager.
        
        Your goal is to analyze this SUPPORT TICKET (CASE) based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### CASE CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Status Check:** Immediately state if the case is 'Closed' or 'Open'.
        - **Priority:** If Priority is 'High' or 'Critical', emphasize urgency.
        - **Solution:** If the 'Solution' field is populated, summarize it clearly.
        - **Context:** Identify the Customer ('Related_To' or 'Account_Name') and the Issue ('Subject', 'Description').
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text