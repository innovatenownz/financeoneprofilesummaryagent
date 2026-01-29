import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Zoho CRM Assistant", page_icon="⚡")
st.title("⚡ Zoho CRM Assistant")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# --- 32 MODULES ---
MODULES = [
    "Accounts", "Leads", "Contacts", "Deals", "Tasks", "Events", "Calls", 
    "Products", "Quotes", "Sales_Orders", "Invoices", "Campaigns", "Vendors", 
    "Price_Books", "Cases", "Forecasts", "Users", "Households",
    "Client_to_Client_Reln_New", "Client_Household_Roles_N",
    "Professional_Contacts_New", "Household_to_Household_N",
    "Life_Events_New", "Financial_Goals_New", "Income_Profile_New", 
    "Expense_Profile_New", "Asset_Ownership_New", "Loans_New", 
    "Loan_Structures_New", "Investment_portfolios", "Associated_portfolios",
    "Reviews"
]

# --- SIDEBAR ---
with st.sidebar:
    st.header("Target Record")
    module = st.selectbox("Module", MODULES)
    rec_id = st.text_input("Record ID", placeholder="e.g. 4000000012345")
    
    if rec_id:
        st.success(f"Active: {module}")

# --- CHAT UI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input(f"Ask about this {module}..."):
    if not rec_id:
        st.warning("⚠️ Please enter a Record ID in the sidebar.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("Analyzing CRM data..."):
            res = requests.post(f"{BACKEND_URL}/chat", json={
                "id": rec_id,
                "module": module,
                "query": prompt
            }, timeout=30)
            
            if res.status_code == 200:
                reply = res.json().get("response")
                st.session_state.messages.append({"role": "assistant", "content": reply})
                with st.chat_message("assistant"):
                    st.markdown(reply)
            else:
                st.error(f"Error: {res.json().get('detail')}")
    except Exception as e:
        st.error(f"Connection Error: {e}")