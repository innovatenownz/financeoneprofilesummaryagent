import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="CRM Chatbot", page_icon="💬")

st.title("💬 CRM Account Chatbot")

# Backend URL from environment or default
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ✅ REAL Zoho Account ID (demo-ready)
account_id = st.text_input(
    "Enter Account ID",
    value="85473000001367006"
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Ask something about this account...")

if user_input:
    # Show user message
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call backend
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "account_id": account_id,
                "query": user_input
            },
            timeout=30
        )
        response.raise_for_status()
        bot_reply = response.json().get(
            "response",
            "No response from backend"
        )

    except requests.exceptions.Timeout:
        bot_reply = "❌ Request timed out. Backend is slow or unresponsive."
    except requests.exceptions.ConnectionError:
        bot_reply = f"❌ Cannot connect to backend at {BACKEND_URL}. Is the server running?"
    except requests.exceptions.HTTPError as e:
        bot_reply = f"❌ Backend error: {e.response.status_code}"
    except ValueError:
        bot_reply = "❌ Invalid response from backend."
    except Exception as e:
        bot_reply = f"❌ Error: {str(e)}"

    # Show bot response
    st.session_state.messages.append(
        {"role": "assistant", "content": bot_reply}
    )
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
