from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re, json, os
from dotenv import load_dotenv
import google.generativeai as genai

# --- UTILS & AGENTS ---
from zoho_auth import get_access_token
from zoho_crm_api_call import get_record, create_record, update_record, search_record, search_by_criteria
from router_agent import RouterAgent 

# Import all agents (Ensure these files exist in your directory)
from account_agent import AccountAgent
from contacts_agent import ContactsAgent
from asset_ownership_agent import AssetOwnershipAgent
from loans_agent import LoansAgent
from households_agent import HouseholdRelationshipsAgent
# ... (Import all other 45+ agents here as shown in previous steps)

load_dotenv()
app = FastAPI()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
router = RouterAgent(model)

# --- 1. AGENT REGISTRY ---
AGENTS = {
    "global_search": ("Accounts", AccountAgent(model)),
    "accounts": ("Accounts", AccountAgent(model)),
    "contacts": ("Contacts", ContactsAgent(model)),
    "asset_ownership_new": ("Asset_Ownership_New", AssetOwnershipAgent(model)),
    "loans_new": ("Loans_New", LoansAgent(model)),
    "repayments": ("Repayment_Schedules", AccountAgent(model)), # Placeholder agent
    "household_relationships": ("Household_to_Household_N", HouseholdRelationshipsAgent(model)),
    # ... Add all remaining slugs from your CRM structure here
}

# --- 2. CONTEXT LINKING MAP ---
# This ensures that when on an Account page, searching for assets uses the ID.
DIRECT_SEARCH_CONFIG = {
    "asset_ownership_new": "Households",
    "financial_accounts_new": "Accounts",
    "liabilities_new": "Accounts",
    "loans_new": "Accounts",
    "insurance_policies_new": "Insurance_Profile",
    "kyc_documents_new": "Accounts"
}

class ChatRequest(BaseModel):
    id: str = None
    module: str = None
    query: str
    history: list = []
    confirm_action: bool = False

@app.post("/chat")
def chat(req: ChatRequest):
    token = get_access_token()
    if not token: raise HTTPException(status_code=500, detail="Auth Failed")

    # A. Orchestration
    plan_data = router.route_request(req.query, {"module": req.module, "id": req.id}, req.history)
    steps = plan_data.get("plan", [])
    
    execution_context = {}
    final_response = ""

    for step in steps:
        slug = step.get("agent")
        action = step.get("action")
        api_name, agent = AGENTS.get(slug, AGENTS["global_search"])

        # B. Context-Aware Verification
        if action == "verify":
            return {"response": f"⚠️ I'm ready to perform an action in **{api_name}**. Please confirm by saying 'Yes' or 'Proceed'.", "requires_confirmation": True}

        # C. Contextual Data Retrieval
        if action == "search":
            results = None
            if req.id and slug in DIRECT_SEARCH_CONFIG:
                lookup_field = DIRECT_SEARCH_CONFIG[slug]
                results = search_by_criteria(api_name, lookup_field, req.id, token)
            
            if not results:
                results = search_record(api_name, step.get("query"), token)

            if results:
                execution_context[f"step_{step['step']}_id"] = results[0]['id']
                final_response += agent.generate_response("Summarize this:", {"items": results}) + "\n\n"
            else:
                final_response += f"No records found for '{step.get('query')}' in {api_name}.\n"

        elif action == "query":
            # Use Active ID from context
            target_id = req.id or execution_context.get("step_1_id")
            data = get_record(api_name, target_id, token) if target_id else {}
            final_response += agent.generate_response(req.query, data, req.history)

    return {"response": final_response}