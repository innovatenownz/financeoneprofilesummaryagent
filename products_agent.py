import json
import google.generativeai as genai

# --- KNOWLEDGE BASE: PRODUCTS SCHEMA ---
PRODUCTS_SCHEMA = [
    # Core Product Info
    {"api": "Product_Name", "type": "text"},
    {"api": "Product_Code", "type": "text"},
    {"api": "Product_Category", "type": "picklist"},
    {"api": "Product_Active", "type": "boolean"},
    {"api": "Manufacturer", "type": "picklist"},
    {"api": "Vendor_Name", "type": "lookup (Vendor)"},
    
    # Pricing & Tax
    {"api": "Unit_Price", "type": "currency"},
    {"api": "Tax", "type": "multiselectpicklist"},
    {"api": "Taxable", "type": "boolean"},
    {"api": "Commission_Rate", "type": "currency"},
    
    # Inventory Management
    {"api": "Usage_Unit", "type": "picklist"},
    {"api": "Qty_in_Stock", "type": "double"},
    {"api": "Qty_Ordered", "type": "double"},
    {"api": "Qty_in_Demand", "type": "double"},
    {"api": "Reorder_Level", "type": "double"},
    {"api": "Handler", "type": "ownerlookup"},
    
    # Dates
    {"api": "Sales_Start_Date", "type": "date"},
    {"api": "Sales_End_Date", "type": "date"},
    {"api": "Support_Start_Date", "type": "date"},
    {"api": "Support_Expiry_Date", "type": "date"},
    
    # Custom Commission Fields (Financials)
    {"api": "Commission_Type", "type": "picklist"},
    {"api": "Upfront_Rate", "type": "percent"},
    {"api": "Trail_Rate", "type": "percent"},
    {"api": "Fees", "type": "percent"},
    {"api": "Clawback_Type", "type": "picklist"},
    {"api": "Clawback_Duration_Months", "type": "integer"},
    
    # System
    {"api": "Description", "type": "textarea"},
    {"api": "Record_Status__s", "type": "picklist"}
]

class ProductsAgent:
    def __init__(self, model):
        self.model = model
        self.schema_string = "\n".join([f"- {f['api']} ({f['type']})" for f in PRODUCTS_SCHEMA])

    def format_data_for_ai(self, record: dict) -> str:
        """
        Parses Product JSON into a clean, readable text block.
        """
        if not record:
            return "No Product Data Available."

        lines = ["=== PRODUCT DETAILS ==="]

        # 1. Process Fields
        for field in PRODUCTS_SCHEMA:
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

            # Formatting Percentages (add % sign if missing)
            if field['type'] == 'percent' and isinstance(val, (int, float)):
                val = f"{val}%"

            lines.append(f"{key}: {val}")

        return "\n".join(lines)

    def generate_response(self, user_query: str, product_data: dict) -> str:
        """
        Generates a response answering questions about the Product.
        """
        context_text = self.format_data_for_ai(product_data)

        prompt = f"""
        You are an expert Inventory & Product Manager.
        
        Your goal is to analyze this PRODUCT based on the data below.
        
        ### DATA SCHEMA
        {self.schema_string}

        ### PRODUCT CONTEXT
        {context_text}

        ### USER QUESTION
        "{user_query}"

        ### INSTRUCTIONS
        - **Inventory Status:** Check 'Qty_in_Stock' vs 'Reorder_Level'. Warn if stock is low.
        - **Pricing:** Clearly state the Unit Price and if it is Taxable.
        - **Commission Logic:** Explain the commission structure (Upfront vs Trail rates) if asked about earnings.
        - **Availability:** Check 'Sales_End_Date' and 'Product_Active' to see if it's still sellable.
        
        Answer:
        """
        
        response = self.model.generate_content(prompt)
        return response.text