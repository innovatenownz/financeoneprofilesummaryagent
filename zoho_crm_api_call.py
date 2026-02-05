import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# API Version Configuration
API_VERSION = "v2.1" 
BASE_URL = f"https://www.zohoapis.com.au/crm/{API_VERSION}"

# --- CONFIGURATION ---
# Default related lists if none are provided dynamically
MODULE_CONFIG = {
    "Leads": ["Notes", "Tasks"],
    "Contacts": ["Notes", "Deals", "Tasks"],
    "Deals": ["Notes", "Tasks", "Stage_History"],
    "Households": ["Notes"],
}

# ==========================================
#  PART 1: READ FUNCTIONS (Standard Parallel API)
# ==========================================

def fetch_single_related_list(session, module_api_name, record_id, related_list_name, headers):
    """
    Fetches a single related list using a standard GET request.
    """
    url = f"{BASE_URL}/{module_api_name}/{record_id}/{related_list_name}"
    try:
        response = session.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            data = response.json().get("data", [])
            # print(f"   ✅ Found {len(data)} items in {related_list_name}")
            return related_list_name, data
        elif response.status_code == 204:
            # 204 means "No Content" (List is empty, which is normal)
            return related_list_name, []
        else:
            # Print error for typos or permission issues
            print(f"   ❌ Failed to fetch '{related_list_name}': {response.status_code} - {response.text}")
            return related_list_name, None
            
    except Exception as e:
        print(f"   ⚠️ Exception fetching '{related_list_name}': {e}")
        return related_list_name, None

def get_record(module_api_name: str, record_id: str, token: str, dynamic_related_list: list = None):
    """
    Fetches Main Record + All Related Lists using Parallel Standard Requests.
    """
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    
    # 1. Fetch Main Record
    try:
        main_url = f"{BASE_URL}/{module_api_name}/{record_id}"
        # print(f"🚀 Fetching Main Record: {module_api_name} ID: {record_id}")
        main_resp = requests.get(main_url, headers=headers, timeout=5)
        
        if main_resp.status_code != 200:
            print(f"❌ Error fetching main record: {main_resp.text}")
            return None
        
        data_list = main_resp.json().get("data", [])
        if not data_list: return None
        record = data_list[0]

    except Exception as e:
        print(f"Critical Error on Main Record: {e}")
        return None

    # 2. Determine Related Lists
    related_modules = dynamic_related_list if dynamic_related_list else MODULE_CONFIG.get(module_api_name, [])
    
    if not related_modules:
        return record

    print(f"📦 Fetching {len(related_modules)} related lists (Standard Parallel)...")

    # 3. Parallel Execution (Standard GETs)
    # We use a Session to re-use the TCP connection for speed
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Launch all requests at once
            future_to_list = {
                executor.submit(fetch_single_related_list, session, module_api_name, record_id, r_name, headers): r_name 
                for r_name in related_modules
            }
            
            for future in as_completed(future_to_list):
                r_name, data = future.result()
                
                if data:
                    # Attach to record using "Related_" prefix so the Agent finds it
                    # e.g., "Notes" -> "Related_Notes"
                    record[f"Related_{r_name}"] = data

    return record

# ==========================================
#  PART 2: WRITE FUNCTIONS (Create / Update / Search)
# ==========================================

def search_record(module_api_name: str, search_text: str, token: str):
    """Searches for a record by Name to get its ID."""
    url = f"{BASE_URL}/{module_api_name}/search"
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    
    criteria = f"(Name:equals:{search_text})"
    if module_api_name == "Accounts": criteria = f"(Account_Name:equals:{search_text})"
    elif module_api_name in ["Leads", "Contacts"]: criteria = f"((Full_Name:equals:{search_text})or(Last_Name:equals:{search_text}))"

    try:
        res = requests.get(url, headers=headers, params={"criteria": criteria}, timeout=5)
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data: return {"id": data[0]["id"], "name": search_text}
    except: pass
    return None

def create_record(module_api_name: str, data: dict, token: str):
    """Creates a new record."""
    url = f"{BASE_URL}/{module_api_name}"
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    try:
        response = requests.post(url, json={"data": [data]}, headers=headers, timeout=10)
        return response.json()
    except Exception as e: return {"error": str(e)}

def update_record(module_api_name: str, record_id: str, data: dict, token: str):
    """Updates an existing record."""
    url = f"{BASE_URL}/{module_api_name}/{record_id}"
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    try:
        response = requests.put(url, json={"data": [data]}, headers=headers, timeout=10)
        return response.json()
    except Exception as e: return {"error": str(e)}
# ... (Keep existing imports and functions) ...

# [NEW FUNCTION] Search by specific criteria (e.g. Find Assets where Household == ID)
def search_by_criteria(module_api_name: str, field_api_name: str, value: str, token: str):
    """
    Searches a module for records where a specific field matches a value.
    Example: Search 'Asset_Ownership_New' where 'Households' equals '8547...'
    """
    url = f"{BASE_URL}/{module_api_name}/search"
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json"
    }
    
    # Construct Criteria: (Field_Name:equals:Value)
    # Note: Value doesn't strictly need quotes for IDs, but safe to strip them just in case
    clean_val = str(value).strip()
    criteria = f"({field_api_name}:equals:{clean_val})"
    
    print(f"🔎 Execute Search: {module_api_name} | Criteria: {criteria}")

    try:
        response = requests.get(url, headers=headers, params={"criteria": criteria}, timeout=10)
        
        if response.status_code == 200:
            data = response.json().get("data", [])
            print(f"   ✅ Search found {len(data)} records.")
            return data
        elif response.status_code == 204:
            print("   ⚠️ Search returned 0 results.")
            return [] 
        else:
            print(f"❌ Search Failed: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"⚠️ Search Exception: {e}")
        return []    