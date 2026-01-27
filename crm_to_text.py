def crm_record_to_text(record: dict) -> str:
    return f"""
    Account Name: {record.get('Account_Name')}
    Industry: {record.get('Industry')}
    Annual Revenue: {record.get('Annual_Revenue')}
    Phone: {record.get('Phone')}
    Website: {record.get('Website')}
    Description: {record.get('Description')}
    """
