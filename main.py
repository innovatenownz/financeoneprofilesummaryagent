from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Custom Modules
from zoho_auth import get_access_token
from zoho_crm_api_call import get_record

# --- IMPORT ALL AGENTS ---
from account_agent import AccountAgent
from leads_agent import LeadsAgent
from contacts_agent import ContactsAgent
from deals_agent import DealsAgent
from tasks_agent import TasksAgent
from events_agent import EventsAgent
from calls_agent import CallsAgent
from products_agent import ProductsAgent
from quotes_agent import QuotesAgent
from sales_orders_agent import SalesOrdersAgent
from invoices_agent import InvoicesAgent
from campaigns_agent import CampaignsAgent
from vendors_agent import VendorsAgent
from price_books_agent import PriceBooksAgent
from cases_agent import CasesAgent
from forecasts_agent import ForecastsAgent
from users_agent import UsersAgent
from households_agent import HouseholdsAgent
from client_relationships_agent import ClientRelationshipsAgent
from client_household_roles_agent import ClientHouseholdRolesAgent
from professional_contacts_agent import ProfessionalContactsAgent
from household_relationships_agent import HouseholdRelationshipsAgent
from life_events_agent import LifeEventsAgent
from financial_goals_agent import FinancialGoalsAgent
from income_profile_agent import IncomeProfileAgent
from expense_profile_agent import ExpenseProfileAgent
from asset_ownership_agent import AssetOwnershipAgent
from loans_agent import LoansAgent
from loan_structures_agent import LoanStructuresAgent
from investment_portfolios_agent import InvestmentPortfoliosAgent
from associated_portfolios_agent import AssociatedPortfoliosAgent
from reviews_agent import ReviewsAgent

load_dotenv()

# --- CONFIGURATION ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

app = FastAPI()

# --- AGENT REGISTRY ---
# Maps the frontend "slug" to the (API Name, Agent Instance)
AGENTS = {
    "accounts": ("Accounts", AccountAgent(model)),
    "leads": ("Leads", LeadsAgent(model)),
    "contacts": ("Contacts", ContactsAgent(model)),
    "deals": ("Deals", DealsAgent(model)),
    "tasks": ("Tasks", TasksAgent(model)),
    "events": ("Events", EventsAgent(model)),
    "calls": ("Calls", CallsAgent(model)),
    "products": ("Products", ProductsAgent(model)),
    "quotes": ("Quotes", QuotesAgent(model)),
    "sales_orders": ("Sales_Orders", SalesOrdersAgent(model)),
    "invoices": ("Invoices", InvoicesAgent(model)),
    "campaigns": ("Campaigns", CampaignsAgent(model)),
    "vendors": ("Vendors", VendorsAgent(model)),
    "price_books": ("Price_Books", PriceBooksAgent(model)),
    "cases": ("Cases", CasesAgent(model)),
    "forecasts": ("Forecasts", ForecastsAgent(model)),
    "users": ("users", UsersAgent(model)), # Note lowercase 'users' for API
    "households": ("Households", HouseholdsAgent(model)),
    "client_to_client_reln_new": ("Client_to_Client_Reln_New", ClientRelationshipsAgent(model)),
    "client_household_roles_n": ("Client_Household_Roles_N", ClientHouseholdRolesAgent(model)),
    "professional_contacts_new": ("Professional_Contacts_New", ProfessionalContactsAgent(model)),
    "household_to_household_n": ("Household_to_Household_N", HouseholdRelationshipsAgent(model)),
    "life_events_new": ("Life_Events_New", LifeEventsAgent(model)),
    "financial_goals_new": ("Financial_Goals_New", FinancialGoalsAgent(model)),
    "income_profile_new": ("Income_Profile_New", IncomeProfileAgent(model)),
    "expense_profile_new": ("Expense_Profile_New", ExpenseProfileAgent(model)),
    "asset_ownership_new": ("Asset_Ownership_New", AssetOwnershipAgent(model)),
    "loans_new": ("Loans_New", LoansAgent(model)),
    "loan_structures_new": ("Loan_Structures_New", LoanStructuresAgent(model)),
    "investment_portfolios": ("Investment_portfolios", InvestmentPortfoliosAgent(model)),
    "associated_portfolios": ("Associated_portfolios", AssociatedPortfoliosAgent(model)),
    "reviews": ("Reviews", ReviewsAgent(model))
}

class ChatRequest(BaseModel):
    id: str           
    module: str       
    query: str

@app.post("/chat")
def chat(req: ChatRequest):
    token = get_access_token()
    if not token: raise HTTPException(status_code=500, detail="Auth Failed")

    # Normalize module name from frontend
    slug = req.module.lower() 
    
    # 1. Validate Module
    if slug not in AGENTS:
        raise HTTPException(status_code=400, detail=f"Agent for {slug} not configured.")

    api_name, agent_instance = AGENTS[slug]
    
    print(f"🤖 Agent: {slug} | API: {api_name} | ID: {req.id}")

    # 2. Fetch Data
    # Special handling for Accounts related lists
    related_lists = None
    if slug == "accounts":
        related_lists = ["Notes", "Deals"] 

    record = get_record(api_name, req.id, token, dynamic_related_list=related_lists)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found in Zoho.")

    # 3. Generate Response
    if hasattr(agent_instance, "generate_response_stream"):
        return StreamingResponse(
            agent_instance.generate_response_stream(req.query, record),
            media_type="text/plain"
        )

    response_text = agent_instance.generate_response(req.query, record)
    return {"response": response_text}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)