"""
Converts Zoho CRM record data to formatted text for LLM consumption.
"""
from typing import Dict, Any


def record_to_text(record_data: Dict[str, Any], entity_type: str = "Record") -> str:
    """
    Converts a Zoho CRM record dictionary to a formatted text string.
    
    Args:
        record_data: Record data dictionary from Zoho API
        entity_type: Module name (e.g., "Accounts", "Deals")
    
    Returns:
        Formatted text string representation of the record.
    """
    if not record_data:
        return f"{entity_type} record: No data available"
    
    lines = [f"{entity_type} Record Information:"]
    lines.append("=" * 50)
    
    # Extract ID if present
    record_id = record_data.get("id") or record_data.get("Id")
    if record_id:
        lines.append(f"ID: {record_id}")
    
    # Format all fields
    for key, value in record_data.items():
        # Skip internal fields
        if key.lower() in ["id", "created_time", "modified_time", "created_by", "modified_by"]:
            continue
        
        # Format the field name (replace underscores, capitalize)
        field_name = key.replace("_", " ").title()
        
        # Format the value
        if value is None:
            formatted_value = "Not set"
        elif isinstance(value, dict):
            # Handle nested objects (e.g., Owner, Account_Name)
            if "name" in value:
                formatted_value = value["name"]
            elif "id" in value:
                formatted_value = f"{value.get('name', 'Unknown')} (ID: {value['id']})"
            else:
                formatted_value = str(value)
        elif isinstance(value, list):
            formatted_value = ", ".join(str(v) for v in value)
        else:
            formatted_value = str(value)
        
        lines.append(f"{field_name}: {formatted_value}")
    
    return "\n".join(lines)
