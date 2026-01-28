import json

def crm_record_to_text(record: dict) -> str:
    """
    Dynamically converts ALL JSON data (Fields, Subforms, Related Lists) into text.
    """
    if not record:
        return "No Data Found."

    text_output = []
    
    # --- SECTION 1: MAIN FIELDS & CUSTOM FIELDS ---
    text_output.append("=== ACCOUNT DETAILS ===")
    
    # We loop through everything in the record
    for key, value in record.items():
        # Skip system fields that confuse the AI
        if key in ["id", "Created_Time", "Modified_Time", "Created_By", "Modified_By", "Tag", "$state", "$process_flow"]:
            continue
            
        # Skip Related Lists (we handle them later)
        if key.startswith("Related_"):
            continue

        # Handle Subforms (Lists inside the main record)
        # Example: Account_Client_Relation from your screenshot
        if isinstance(value, list) and value: 
            text_output.append(f"\n--- {key} (Subform) ---")
            for item in value:
                # Summarize the subform row
                row_details = []
                for k, v in item.items():
                    if v and k not in ["id", "s_id"]:
                        # Handle Lookups (e.g. {"name": "John", "id": "..."})
                        if isinstance(v, dict) and "name" in v:
                            v = v["name"]
                        row_details.append(f"{k}: {v}")
                text_output.append("  • " + ", ".join(row_details))
            continue

        # Handle Normal Fields (Text, Currency, Picklist)
        if value:
            # If it's a lookup (like Owner), just get the name
            if isinstance(value, dict) and "name" in value:
                value = value["name"]
            
            # Clean up the key name for easier reading (e.g., "Total_Asset_Value" -> "Total Asset Value")
            clean_key = key.replace("_", " ")
            text_output.append(f"{clean_key}: {value}")

    # --- SECTION 2: RELATED LISTS (Contacts, Deals, etc.) ---
    text_output.append("\n=== RELATED RECORDS ===")
    
    # Find all keys we added starting with "Related_"
    related_keys = [k for k in record.keys() if k.startswith("Related_")]
    
    if not related_keys:
        text_output.append("No related records found.")

    for rel_key in related_keys:
        module_name = rel_key.replace("Related_", "")
        items = record[rel_key]
        
        text_output.append(f"\n {module_name} ({len(items)} records):")
        
        for i, item in enumerate(items, 1):
            # Try to find a name for the record
            item_name = (
                item.get("Name") or 
                item.get("Account_Name") or 
                item.get("Last_Name") or 
                item.get("Subject") or 
                item.get("Title") or 
                "Record"
            )
            text_output.append(f"  {i}. {item_name}")
            
            # Add details (Print the first 5 non-empty fields)
            details = []
            for k, v in item.items():
                if k not in ["id", "Owner", "Created_Time", "Modified_Time", "Tag"] and v:
                     if isinstance(v, (str, int, float)):
                         details.append(f"{k}: {v}")
                if len(details) >= 4: break 
            
            if details:
                text_output.append(f"     [{', '.join(details)}]")

    return "\n".join(text_output)
