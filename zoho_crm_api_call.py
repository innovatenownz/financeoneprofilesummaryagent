# FILE: zoho_crm_api_call.py
import requests

BASE_URL = "https://www.zohoapis.com.au/crm/v2"

def get_account_data(account_id: str, token: str, related_modules_to_fetch: list = None):
    """
    Fetches Account data from Zoho CRM.
    
    Args:
        account_id (str): The ID of the main account.
        token (str): The OAuth access token.
        related_modules_to_fetch (list, optional): A list of API names for related modules 
                                                   to fetch. If None, only main account 
                                                   data is returned.
    """
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }
    
    try:
        # 1. ALWAYS Fetch the MAIN Account (Core details are always needed)
        print(f"Fetching Main Account ID: {account_id}...")
        url = f"{BASE_URL}/Accounts/{account_id}"
        res = requests.get(url, headers=headers)
        
        if res.status_code != 200:
            print(f"Error fetching Account: {res.text}")
            return None
            
        data = res.json().get("data", [])
        if not data:
            return None
        
        account_data = data[0]
        
        # 2. FETCH SPECIFIC RELATED MODULES (Optimization)
        # If no specific modules are requested, return early to save time.
        if not related_modules_to_fetch:
            print("No specific related modules requested. Returning main account data only.")
            return account_data

        print(f"Fetching requested related modules: {related_modules_to_fetch}")
        
        for module in related_modules_to_fetch:
            # API endpoint: /Accounts/{id}/{Module_API_Name}
            rel_url = f"{BASE_URL}/Accounts/{account_id}/{module}"
            
            try:
                # We limit per_page to 10 to keep payloads manageable
                rel_res = requests.get(rel_url, headers=headers, params={"per_page": 10})
                
                if rel_res.status_code == 200:
                    rel_data = rel_res.json().get("data", [])
                    if rel_data:
                        # Save it into the dictionary with key "Related_ModuleName"
                        account_data[f"Related_{module}"] = rel_data
                        print(f"   Found {len(rel_data)} records in {module}")
                    else:
                        print(f"   {module} is empty.")
                else:
                    # 204 No Content is common for empty lists, anything else is an error
                    if rel_res.status_code != 204:
                        print(f"   Could not fetch {module} (Status: {rel_res.status_code})")
                    
            except Exception as e:
                print(f"   Error fetching {module}: {e}")

        return account_data

    except Exception as e:
        print(f"Critical Error in get_account_data: {e}")
        return None