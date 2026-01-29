import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: SALES ORDERS SCHEMA ---
SALES_ORDERS_SCHEMA = [
    # Core Order Info
    {"api": "SO_Number", "type": "autonumber"},
    {"api": "Subject", "type": "text"},
    {"api": "Purchase_Order", "type": "text"},
    {"api": "Status", "type": "picklist"},
    {"api": "Due_Date", "type": "date"},
    {"api": "Carrier", "type": "picklist"},
    {"api": "Pending", "type": "text"},
    
    # Financials
    {"api": "Grand_Total", "type": "formula (currency)"},
    {"api": "Sub_Total", "type": "formula (currency)"},
    {"api": "Discount", "type": "currency"},
    {"api": "Tax", "type": "currency"},
    {"api": "Adjustment", "type": "currency"},
    {"api": "Excise_Duty", "type": "currency"},
    {"api": "Sales_Commission", "type": "currency"},
    
    # Relationships
    {"api": "Account_Name", "type": "lookup (Account)"},
    {"api": "Contact_Name", "type": "lookup (Contact)"},
    {"api": "Deal_Name", "type": "lookup (Deal)"},
    {"api": "Quote_Name", "type": "lookup (Quote)"},
    {"api": "Owner", "type": "ownerlookup"},
    
    # Billing & Shipping
    {"api": "Billing_Street", "type": "text"},
    {"api": "Billing_City", "type": "text"},
    {"api": "Billing_Country", "type": "text"},
    {"api": "Shipping_Street", "type": "text"},
    {"api": "Shipping_City", "type": "text"},
    {"api": "Shipping_Country", "type": "text"},
    
    # Line Items (Critical)
    {"api": "Ordered_Items", "type": "subform"},
    
    # System
    {"api": "Terms_and_Conditions", "type": "textarea"},
    {"api": "Description", "type": "textarea"}
]

class SalesOrdersAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in SALES_ORDERS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Sales Order JSON into a clean, readable text block.
        """
        if not record:
            return "No Sales Order Data Available."

        lines = ["=== SALES ORDER DETAILS ==="]

        # 1. Process Fields
        for field in SALES_ORDERS_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Line Items (Subform)
            if key == "Ordered_Items" and isinstance(val, list):
                lines.append("\n--- ORDERED ITEMS ---")
                for i, item in enumerate(val, 1):
                    # Extract key info from line item
                    prod = item.get("Product_Name", {}).get("name", "Unknown Product")
                    qty = item.get("Quantity", 0)
                    total = item.get("Net_Total", 0)
                    lines.append(f"  {i}. {prod} (Qty: {qty}) | Total: {total}")
                continue

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, order_data: dict) -> str:
        """
        Generates a response answering questions about the Sales Order.
        """
        context_text = self.format_data_for_ai(order_data)

        prompt = f"""
        You are an expert Fulfillment & Sales Operations Manager.
        
        Your goal is to analyze this SALES ORDER based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### ORDER CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Status Check:** Always note the 'Status' and 'Due_Date'. Is it pending or overdue?
        - **Financials:** Reference 'Grand_Total' when discussing value.
        - **Line Items:** If asked what was ordered, list items from 'ORDERED ITEMS'.
        - **Logistics:** If asked about shipping, check 'Carrier' and 'Shipping_City'.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text