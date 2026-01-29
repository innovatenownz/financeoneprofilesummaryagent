import requests
import concurrent.futures
import time

BASE_URL = "https://www.zohoapis.com.au/crm/v2"

# --- CONFIGURATION: Define Related Lists per Module ---
# Format: "API_Name": ["Related_Module_1", "Related_Module_2"]
MODULE_CONFIG = {
    "Leads": ["Notes", "Tasks"],
    "Contacts": ["Notes", "Deals", "Tasks"],
    "Deals": ["Notes", "Tasks", "Stage_History"],
    "Quotes": ["Notes", "Emails"],
    "Sales_Orders": ["Notes", "Invoices"],
    "Invoices": ["Notes", "Payments"],
    "Campaigns": ["Leads", "Deals"],
    "Vendors": ["Products", "Purchase_Orders"],
    "Price_Books": ["Products", "Products_Related_List"],
    "Cases": ["Notes", "Attachments"],
    # Simple Modules (No heavy related lists needed)
    "Tasks": [], "Events": [], "Calls": [], "Products": [], "Forecasts": [], "Users": [],
    # Custom Modules
    "Households": ["Notes"],
    "Client_to_Client_Reln_New": ["Notes"],
    "Client_Household_Roles_N": ["Notes"],
    "Professional_Contacts_New": ["Notes"],
    "Household_to_Household_N": ["Notes"],
    "Life_Events_New": ["Notes"],
    "Financial_Goals_New": ["Notes"],
    "Income_Profile_New": ["Notes"],
    "Expense_Profile_New": ["Notes"],
    "Asset_Ownership_New": ["Notes"],
    "Loans_New": ["Notes"],
    "Loan_Structures_New": ["Notes"],
    "Investment_portfolios": ["Notes"],
    "Associated_portfolios": ["Notes"],
    "Reviews": ["Notes"]
}

# --- CORE FUNCTIONS ---

def fetch_single_module(session, record_url, module, headers):
    """Helper: Fetches one related list safely."""
    try:
        res = session.get(f"{record_url}/{module}", headers=headers, params={"per_page": 5}, timeout=3)
        if res.status_code == 200:
            data = res.json().get("data", [])
            return module, data if data else None
    except: pass
    return module, None

def get_record(module_api_name: str, record_id: str, token: str, dynamic_related_list: list = None):
    """
    Universal Fetcher.
    - module_api_name: The exact API name (e.g., 'Leads', 'Client_Household_Roles_N')
    - dynamic_related_list: Optional override (used for Accounts AI routing)
    """
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    
    # 1. Handle "Users" special endpoint structure
    if module_api_name.lower() == "users":
        try:
            res = requests.get(f"{BASE_URL}/users/{record_id}", headers=headers, timeout=5)
            return res.json().get("users", [])[0] if res.status_code == 200 else None
        except: return None

    # 2. Fetch Main Record
    try:
        url = f"{BASE_URL}/{module_api_name}/{record_id}"
        res = requests.get(url, headers=headers, timeout=8)
        
        if res.status_code != 200:
            print(f" Error fetching {module_api_name}: {res.status_code}")
            return None
            
        data = res.json().get("data", [])
        if not data: return None
        record = data[0]

        # 3. Determine Related Lists to Fetch
        # Use dynamic list if provided (for Accounts), otherwise look up config
        modules_to_fetch = dynamic_related_list if dynamic_related_list is not None else MODULE_CONFIG.get(module_api_name, [])

        if not modules_to_fetch:
            return record

        # 4. Parallel Fetch of Related Lists
        print(f" Fetching related: {modules_to_fetch}...")
        with requests.Session() as session:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(fetch_single_module, session, url, mod, headers): mod for mod in modules_to_fetch}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        name, related_data = future.result()
                        if related_data: record[f"Related_{name}"] = related_data
                    except: pass
        
        return record

    except Exception as e:
        print(f" Critical Error: {e}")
        return None