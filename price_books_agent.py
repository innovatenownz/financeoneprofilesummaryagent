import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: PRICE BOOKS SCHEMA ---
PRICE_BOOKS_SCHEMA = [
    # Core Info
    {"api": "Price_Book_Name", "type": "text"},
    {"api": "Active", "type": "boolean"},
    {"api": "Pricing_Model", "type": "picklist"}, # Flat or Differential
    {"api": "Description", "type": "textarea"},
    
    # Pricing Rules
    {"api": "Pricing_Details", "type": "jsonarray"}, # Complex pricing tiers
    
    # Ownership
    {"api": "Owner", "type": "ownerlookup"},
    {"api": "Created_By", "type": "ownerlookup"},
    {"api": "Modified_By", "type": "ownerlookup"},
    
    # System
    {"api": "Tag", "type": "jsonarray"},
    {"api": "Record_Status__s", "type": "picklist"}
]

class PriceBooksAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in PRICE_BOOKS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Price Book JSON into a clean, readable text block.
        """
        if not record:
            return "No Price Book Data Available."

        lines = ["=== PRICE BOOK DETAILS ==="]

        # 1. Process Standard Fields
        for field in PRICE_BOOKS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Booleans
            if field['type'] == 'boolean':
                val = "Active" if val else "Inactive"

            # Formatting Pricing Details (Tiers/Ranges)
            if key == "Pricing_Details" and isinstance(val, list):
                lines.append("\n--- PRICING TIERS ---")
                for i, tier in enumerate(val, 1):
                    # Usually contains 'from_range', 'to_range', 'discount'
                    from_r = tier.get("from_range", 0)
                    to_r = tier.get("to_range", "End")
                    disc = tier.get("discount", 0)
                    lines.append(f"  Tier {i}: Buy {from_r}-{to_r} -> {disc}% Off")
                continue

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, pb_data: dict) -> str:
        """
        Generates a response answering questions about the Price Book.
        """
        context_text = self.format_data_for_ai(pb_data)

        prompt = f"""
        You are an expert Pricing Strategist.
        
        Your goal is to analyze this PRICE BOOK based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### PRICE BOOK CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Status Check:** Immediately state if this price book is 'Active' or 'Inactive'.
        - **Model Logic:** Explain the 'Pricing_Model'. 'Flat' means a simple list price. 'Differential' means volume-based discounts.
        - **Tiers:** If 'Pricing_Details' are present, explain the discount structure (e.g., "Buy more, save more").
        - **Usage:** This sets the base prices for Products in Quotes/Sales Orders.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text