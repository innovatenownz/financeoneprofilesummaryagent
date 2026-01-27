from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Your Custom Modules
from zoho_auth import get_access_token
from zoho_crm_api_call import get_account_data # Ensure file is renamed to zoho_crm_api_call.py
from crm_to_text import crm_record_to_text
from vectorstore_runtime import build_vectorstore

import google.generativeai as genai

# --- CONFIGURATION ---
# Load API Key from Environment Variable
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

app = FastAPI()

class ChatRequest(BaseModel):
    account_id: str
    query: str

@app.post("/chat")
def chat(req: ChatRequest):
    print(f"Received request for Account: {req.account_id}")

    # 1. Authenticate & Get Data
    token = get_access_token()
    if not token:
        raise HTTPException(status_code=500, detail="Failed to get Zoho Token")

    record = get_account_data(req.account_id, token)
    if not record:
        raise HTTPException(status_code=404, detail="Account not found in CRM")

    # 2. Convert Data to Text
    text_data = crm_record_to_text(record)
    print(f"CRM Context: {text_data}") # Debug print for your demo

    # 3. Create Temporary Vector Store
    # Note: We pass the text_data directly. 
    vs = build_vectorstore(text_data, req.account_id)
    
    # 4. Search Vector Store (Simulating RAG)
    docs = vs.similarity_search(req.query, k=3)
    context = "\n".join([d.page_content for d in docs])

    # 5. Generate AI Response
    prompt = f"""
    You are a helpful CRM assistant. Answer the question using ONLY the context below.
    If the answer is not in the context, say "I don't have that information."

    CONTEXT FROM CRM:
    {context}

    USER QUESTION: 
    {req.query}
    """

    res = model.generate_content(prompt)
    return {"response": res.text}

# This allows you to run the file directly
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)