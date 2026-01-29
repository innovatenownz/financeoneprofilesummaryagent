import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: INVOICES SCHEMA ---
INVOICES_SCHEMA = [
    # Core Invoice Info
    {"api": "Invoice_Number", "type": "autonumber"},
    {"api": "Subject", "type": "text"},
    {"api": "Status", "type": "picklist"},
    {"api": "Invoice_Date", "type": "date"},
    {"api": "Due_Date", "type": "date"},
    {"api": "Purchase_Order", "type": "text"},
    
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
    {"api": "Sales_Order", "type": "lookup (Sales Order)"},
    {"api": "Deal_Name__s", "type": "lookup (Deal)"},
    {"api": "Owner", "type": "ownerlookup"},
    
    # Billing & Shipping
    {"api": "Billing_Street", "type": "text"},
    {"api": "Billing_City", "type": "text"},
    {"api": "Billing_Country", "type": "text"},
    {"api": "Shipping_Street", "type": "text"},
    {"api": "Shipping_City", "type": "text"},
    
    # Line Items (Critical)
    {"api": "Invoiced_Items", "type": "subform"},
    
    # System
    {"api": "Terms_and_Conditions", "type": "textarea"},
    {"api": "Description", "type": "textarea"}
]

class InvoicesAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in INVOICES_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Invoice JSON into a clean, readable text block.
        """
        if not record:
            return "No Invoice Data Available."

        lines = ["=== INVOICE DETAILS ==="]

        # 1. Process Fields
        for field in INVOICES_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            
            # Formatting Line Items (Subform)
            if key == "Invoiced_Items" and isinstance(val, list):
                lines.append("\n--- BILLED ITEMS ---")
                for i, item in enumerate(val, 1):
                    # Extract key info
                    prod = item.get("Product_Name", {}).get("name", "Unknown Product")
                    qty = item.get("Quantity", 0)
                    total = item.get("Net_Total", 0)
                    lines.append(f"  {i}. {prod} (Qty: {qty}) | Total: {total}")
                continue

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, invoice_data: dict) -> str:
        """
        Generates a response answering questions about the Invoice.
        """
        context_text = self.format_data_for_ai(invoice_data)

        prompt = f"""
        You are an expert Accounts Receivable Assistant.
        
        Your goal is to analyze this INVOICE based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### INVOICE CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Payment Status:** Check 'Status' immediately. If it is 'Overdue' or 'Unpaid', flag it.
        - **Deadline:** Compare 'Due_Date' with today's date context (if implied).
        - **Details:** If asked what was billed, list items from 'BILLED ITEMS'.
        - **Relationships:** Identify who matches the bill ('Account_Name' or 'Contact_Name').
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text