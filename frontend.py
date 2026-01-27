import streamlit as st
import requests

st.set_page_config(page_title="CRM Chatbot", page_icon="💬")

st.title("💬 CRM Account Chatbot")

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
            "http://127.0.0.1:8000/chat",
            json={
                "account_id": account_id,
                "query": user_input
            },
            timeout=30
        )

        bot_reply = response.json().get(
            "response",
            "No response from backend"
        )

    except Exception:
        bot_reply = "Backend not reachable."

    # Show bot response
    st.session_state.messages.append(
        {"role": "assistant", "content": bot_reply}
    )
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
