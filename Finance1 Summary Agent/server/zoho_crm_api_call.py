"""
Zoho CRM API call utilities.
Fetches record data from Zoho CRM for any module type.
"""
import os
import requests
from typing import Dict, Any, Optional
from zoho_auth import get_access_token


def get_record_data(entity_type: str, entity_id: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches record data from Zoho CRM for the specified entity.
    
    Args:
        entity_type: Module name (e.g., "Accounts", "Deals", "Contacts")
        entity_id: Record ID
        token: Optional access token. If not provided, will be fetched automatically.
    
    Returns:
        Record data dictionary if successful, None otherwise.
    """
    if token is None:
        token = get_access_token()
    
    if not token:
        raise ValueError("Failed to obtain Zoho access token")
    
    # Zoho CRM API endpoint
    api_domain = os.getenv("ZOHO_API_DOMAIN", "www.zohoapis.com")
    url = f"https://{api_domain}/crm/v3/{entity_type}/{entity_id}"
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Zoho API returns data in 'data' array with one record
        if "data" in data and len(data["data"]) > 0:
            return data["data"][0]
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching record data: {e}")
        return None


# Backward compatibility function for Accounts module
def get_account_data(account_id: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches account data from Zoho CRM (backward compatibility).
    
    Args:
        account_id: Account ID
        token: Optional access token
    
    Returns:
        Account data dictionary if successful, None otherwise.
    """
    return get_record_data("Accounts", account_id, token)
