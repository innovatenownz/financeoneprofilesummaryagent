import json
import google.generativeai as genai

# --- 1. CONFIGURATION ---

# Related List Configuration (for fetching details)
SPECIFIC_LIST_CONFIG = {
    "Notes": ["Note_Title", "Note_Content", "Created_Time", "Owner"],
    "Tasks": ["Subject", "Status", "Priority", "Due_Date"],
    "Calls": ["Subject", "Call_Type", "Call_Duration", "Call_Start_Time"],
    "Events": ["Event_Title", "Start_DateTime", "End_DateTime", "Location"],
    "Emails": ["Subject", "Status", "Sent_Time", "To"],
    "Attachments": ["File_Name", "Size", "Created_Time"],
    "Payments_Received": ["Payment_Number", "Amount", "Payment_Date", "Reference_Number"]
}

# --- KNOWLEDGE BASE: INVOICES SCHEMA ---
# [UPDATED] Added 'target' keys so main.py can resolve lookups automatically
INVOICES_SCHEMA = [
    {"api": "id", "type": "text"},
    {"api": "Invoice_Number", "type": "autonumber"},
    {"api": "Subject", "type": "text"},
    {"api": "Record_Status__s", "type": "picklist"},
    {"api": "Owner", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Modified_By", "type": "ownerlookup", "target": "Users"},
    {"api": "Created_Time", "type": "datetime"},
    {"api": "Modified_Time", "type": "datetime"},
    {"api": "Last_Activity_Time", "type": "datetime"},
    {"api": "Tag", "type": "text"},
    
    # Dates & References
    {"api": "Invoice_Date", "type": "date"},
    {"api": "Due_Date", "type": "date"},
    {"api": "Sales_Order", "type": "lookup", "target": "Sales_Orders"},
    {"api": "Purchase_Order", "type": "text"},
    {"api": "Deal_Name__s", "type": "lookup", "target": "Deals"},
    
    # Relationships (Lookups with Targets)
    {"api": "Account_Name", "type": "lookup", "target": "Accounts"},
    {"api": "Contact_Name", "type": "lookup", "target": "Contacts"},
    
    # Financials
    {"api": "Status", "type": "picklist"},
    {"api": "Sub_Total", "type": "formula"},
    {"api": "Grand_Total", "type": "formula"},
    {"api": "Discount", "type": "currency"},
    {"api": "Tax", "type": "currency"},
    {"api": "Adjustment", "type": "currency"},
    {"api": "Excise_Duty", "type": "currency"},
    {"api": "Sales_Commission", "type": "currency"},
    
    # Address
    {"api": "Billing_Street", "type": "text"},
    {"api": "Billing_City", "type": "text"},
    {"api": "Billing_State", "type": "text"},
    {"api": "Billing_Code", "type": "text"},
    {"api": "Billing_Country", "type": "text"},
    {"api": "Shipping_Street", "type": "text"},
    {"api": "Shipping_City", "type": "text"},
    {"api": "Shipping_State", "type": "text"},
    {"api": "Shipping_Code", "type": "text"},
    {"api": "Shipping_Country", "type": "text"},
    
    # System & Content
    {"api": "Terms_and_Conditions", "type": "textarea"},
    {"api": "Description", "type": "textarea"},
    {"api": "Locked__s", "type": "boolean"},
    
    # Line Items
    {"api": "Invoiced_Items", "type": "subform"}
]

class InvoicesAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in INVOICES_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Invoice JSON into a clean, readable text block.
        """
        if not record: return "No Invoice Data Available."

        # === 1. LIST MODE (Context Switch / Search Results) ===
        if "items" in record:
            items = record["items"]
            if not items: return "No Invoices found."
            
            lines = [f"=== FOUND {len(items)} INVOICES ==="]
            for i, item in enumerate(items, 1):
                lines.append(f"\n--- Invoice #{i} ---")
                
                # A. ALWAYS show identifiers
                if "id" in item: lines.append(f"ID: {item['id']}")
                if "Invoice_Number" in item: lines.append(f"Number: {item['Invoice_Number']}")
                if "Subject" in item: lines.append(f"Subject: {item['Subject']}")
                
                # B. FORCE SHOW critical fields even if empty (for Updates)
                critical_fields = ["Status", "Grand_Total", "Due_Date", "Account_Name"]
                
                for k, v in item.items():
                    if k not in ["id", "Invoice_Number", "Subject", "Tag"]:
                        val_display = v
                        if isinstance(v, dict) and "name" in v: val_display = v["name"]
                        
                        # Show if value exists OR if it is critical
                        if v or k in critical_fields:
                            if not v and v is not False: val_display = "[Empty]"
                            lines.append(f"{k}: {val_display}")
            return "\n".join(lines)

        # === 2. SINGLE RECORD MODE ===
        lines = ["=== INVOICE DETAILS ==="]

        # Process Standard Fields
        for field in INVOICES_SCHEMA:
            key = field['api']
            val = record.get(key)

            if val in [None, "", [], {}]:
                continue
            
            # Formatting Lookups
            if isinstance(val, dict) and "name" in val: val = val["name"]
            
            # Formatting Currency
            if "currency" in field['type'] or "formula" in field['type']:
                val = f"${val}"

            # Formatting Subforms (Invoiced Items)
            if key == "Invoiced_Items" and isinstance(val, list):
                lines.append("\n--- BILLED ITEMS ---")
                for i, item in enumerate(val, 1):
                    prod = item.get("Product_Name", {}).get("name", "Unknown Product")
                    qty = item.get("Quantity", 0)
                    total = item.get("Net_Total", 0)
                    lines.append(f"  {i}. {prod} (Qty: {qty}) | Total: ${total}")
                continue

            clean_key = key.replace("_", " ")
            lines.append(f"{clean_key}: {val}")

        # Process Related Lists
        lines.append("\n--- RELATED ACTIVITY ---")
        list_keys = [k for k, v in record.items() if isinstance(v, list) and k not in ["Tag", "Invoiced_Items"]]
        
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
                    priority_keywords = ["subject", "name", "amount", "date", "status"]
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

        if not found_details: lines.append("(No recent notes or payments found)")

        return "\n".join(lines)

    def generate_response(self, user_query: str, invoice_data: dict, history: list = []) -> str:
        """
        Generates a response answering questions about the Invoice.
        """
        context_text = self.format_data_for_ai(invoice_data)

        # Format History
        history_block = ""
        if history:
            history_block = "### CONVERSATION HISTORY\n"
            for msg in history[-3:]:
                role = "User" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_block += f"{role}: {content}\n"

        prompt = f"""
        You are an expert Accounts Receivable Assistant.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### INVOICE CONTEXT
        {context_text}
        
        {history_block}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - Answer based ONLY on the data provided.
        - **Updates:** Include `record_id` for updates.
        - **Lookups:** If the user provides an Account Name or Contact Name, pass it as text. My system will convert it to an ID.
        - **Payment Status:** Check 'Status'. If 'Overdue' or 'Unpaid', flag it.

        ### ACTION PROTOCOL
        <<<ACTION>>>
        {{
            "action": "create" | "update",
            "module": "Invoices", 
            "record_id": "12345",
            "data": {{ 
                "Subject": "REQUIRED_SUBJECT",
                "Status": "Draft",
                "Field_Name": "Value" 
            }}
        }}
        <<<END_ACTION>>>
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text