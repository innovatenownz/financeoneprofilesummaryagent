"""
Zoho OAuth token refresh utility.
Handles OAuth token refreshing for Zoho CRM API calls.
"""
import os
import requests
from typing import Optional


def get_access_token() -> Optional[str]:
    """
    Refreshes and returns a valid Zoho access token.
    
    Returns:
        Access token string if successful, None otherwise.
    """
    refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
    client_id = os.getenv("ZOHO_CLIENT_ID")
    client_secret = os.getenv("ZOHO_CLIENT_SECRET")
    
    if not all([refresh_token, client_id, client_secret]):
        raise ValueError("Missing required Zoho OAuth credentials in environment variables")
    
    url = "https://accounts.zoho.com/oauth/v2/token"
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }
    
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error refreshing Zoho token: {e}")
        return None
