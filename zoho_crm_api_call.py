# FILE: zoho_crm_api_call.py
import requests

BASE_URL = "https://www.zohoapis.com.au/crm/v2.1"

# We renamed this function to match main.py
# We also added 'token' as an argument so main.py can pass it in
def get_account_data(account_id: str, token: str):
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }
    
    # Fetch specific account by ID
    url = f"{BASE_URL}/Accounts/{account_id}"
    
    try:
        print(f"Fetching CRM data for ID: {account_id}...")
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        
        data = res.json().get("data", [])
        if data:
            return data[0] # Return the first matching account
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching CRM data: {e}")
        return None