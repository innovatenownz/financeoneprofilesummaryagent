import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: FORECASTS SCHEMA ---
FORECASTS_SCHEMA = [
    # Core Forecast Info
    {"api": "Forecast_Name", "type": "text"},
    {"api": "Year", "type": "integer"},
    {"api": "Quarter", "type": "integer"},
    {"api": "Start_Date", "type": "date"},
    {"api": "End_Date", "type": "date"},
    
    # Ownership & Groups
    {"api": "Owner", "type": "ownerlookup"},
    {"api": "Group_Id", "type": "lookup (Forecast Group)"},
    {"api": "Period_Name", "type": "lookup (Fiscal Period)"},
    
    # Status & Locking
    {"api": "Is_Archived", "type": "boolean"},
    {"api": "Forecast_Locked__s", "type": "boolean"},
    {"api": "Forecast_Locked_By__s", "type": "userlookup"},
    {"api": "Forecast_Locked_Time__s", "type": "datetime"},
    
    # System
    {"api": "Created_By", "type": "ownerlookup"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Last_Computed_Time", "type": "datetime"}
]

class ForecastsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in FORECASTS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Forecast JSON into a clean, readable text block.
        """
        if not record:
            return "No Forecast Data Available."

        lines = ["=== FORECAST CONFIGURATION ==="]

        # 1. Process Fields
        for field in FORECASTS_SCHEMA:
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
            
            # Formatting Quarters
            if key == "Quarter":
                val = f"Q{val}"

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, forecast_data: dict) -> str:
        """
        Generates a response answering questions about the Forecast.
        """
        context_text = self.format_data_for_ai(forecast_data)

        prompt = f"""
        You are an expert Sales Planning Assistant.
        
        Your goal is to analyze this FORECAST CONFIGURATION based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### FORECAST CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Timeline:** Clearly state the 'Year', 'Quarter', and date range ('Start_Date' to 'End_Date').
        - **Status:** Check if the forecast is 'Locked' ('Forecast_Locked__s') or 'Archived'.
        - **Ownership:** Identify the 'Forecast Owner'.
        - **Note:** This data represents the *structure* of the forecast (time period), not necessarily the specific revenue numbers unless provided in custom fields.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text