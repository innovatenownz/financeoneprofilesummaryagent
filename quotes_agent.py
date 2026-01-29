import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: QUOTES SCHEMA ---
QUOTES_SCHEMA = [
    # Core Info
    {"api": "Quote_Number", "type": "autonumber"},
    {"api": "Subject", "type": "text"},
    {"api": "Quote_Stage", "type": "picklist"},
    {"api": "Valid_Till", "type": "date"},
    {"api": "Carrier", "type": "picklist"},
    {"api": "Team", "type": "text"},
    
    # Relationships
    {"api": "Deal_Name", "type": "lookup (Deal)"},
    {"api": "Account_Name", "type": "lookup (Account)"},
    {"api": "Contact_Name", "type": "lookup (Contact)"},
    {"api": "Owner", "type": "ownerlookup"},
    
    # Financials
    {"api": "Grand_Total", "type": "formula (currency)"},
    {"api": "Sub_Total", "type": "formula (currency)"},
    {"api": "Discount", "type": "currency"},
    {"api": "Tax", "type": "currency"},
    {"api": "Adjustment", "type": "currency"},
    
    # Billing Address
    {"api": "Billing_Street", "type": "text"},
    {"api": "Billing_City", "type": "text"},
    {"api": "Billing_State", "type": "text"},
    {"api": "Billing_Country", "type": "text"},
    
    # Details
    {"api": "Description", "type": "textarea"},
    {"api": "Terms_and_Conditions", "type": "textarea"},
    
    # Line Items (Critical)
    {"api": "Quoted_Items", "type": "subform"}
]

class QuotesAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in QUOTES_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Quote JSON into a clean, readable text block.
        """
        if not record:
            return "No Quote Data Available."

        lines = ["=== QUOTE DETAILS ==="]

        # 1. Process Standard Fields
        for field in QUOTES_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Line Items (Subform)
            if key == "Quoted_Items" and isinstance(val, list):
                lines.append("\n--- LINE ITEMS ---")
                for i, item in enumerate(val, 1):
                    # Extract key info from line item (usually Product Name, Qty, Total)
                    prod = item.get("Product_Name", {}).get("name", "Unknown Product")
                    qty = item.get("Quantity", 0)
                    total = item.get("Net_Total", 0)
                    lines.append(f"  {i}. {prod} (Qty: {qty}) | Total: {total}")
                continue

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, quote_data: dict) -> str:
        """
        Generates a response answering questions about the Quote.
        """
        context_text = self.format_data_for_ai(quote_data)

        prompt = f"""
        You are an expert Sales Operations Assistant.
        
        Your goal is to analyze this SALES QUOTE based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### QUOTE CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Value Check:** Always reference the 'Grand_Total' and 'Quote_Stage'.
        - **Urgency:** Check 'Valid_Till'. If the date is passed, warn that the quote is expired.
        - **Details:** If asked what is included, list the items from 'LINE ITEMS'.
        - **Approvals:** If the discount is high, suggest checking 'Terms_and_Conditions' or 'Owner'.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text