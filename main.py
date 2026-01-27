from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Custom Modules
from zoho_auth import get_access_token
from zoho_crm_api_call import get_account_data
from crm_to_text import crm_record_to_text
from vectorstore_runtime import build_vectorstore

# --- CONFIGURATION ---
genai.configure(api_key="AIzaSyA3hHsrl5o-qr8oH5-XWaXdVPdaidkEyu0")

# Using Flash for speed, as it handles the routing logic very quickly
model = genai.GenerativeModel('gemini-2.5-flash') 

app = FastAPI()

class ChatRequest(BaseModel):
    account_id: str
    query: str

# --- 1. DEFINE AVAILABLE MODULES ---
# This list allows the AI to map user intent (e.g., "money") to API names (e.g., "Income_Profile_New").
AVAILABLE_MODULES = [
    "Contacts", 
    "Deals", 
    "Notes", 
    "Tasks", 
    "Meetings", 
    "Attachments",
    "Household_to_Household_N", 
    "Client_Household_Roles_N", 
    "Client_to_Client_Realtion",
    "Professional_Contacts_New", 
    "Liabilites_New", 
    "Expenses_New", 
    "Income_Profile_New", 
    "Asset_Ownership_New", 
    "Insurance_Policies_New", 
    "Insurance_Policy_Holder_N", 
    "Policy_Renewals_New", 
    "Policy_Benefits", 
    "Associated_portfolios",
    "Tax_profile", 
    "Loan_Applications"
]

def identify_relevant_modules(user_query: str) -> list:
    """
    Uses AI to identify which Zoho CRM modules are relevant to the user's question.
    """
    prompt = f"""
    You are a backend API Router for a CRM system.
    
    The user is asking a question. Your job is to select the specific database tables (Modules) needed to answer it.
    
    USER QUESTION: "{user_query}"
    
    AVAILABLE MODULES (API Names):
    {json.dumps(AVAILABLE_MODULES)}
    
    INSTRUCTIONS:
    1. Analyze the user's intent. Match synonyms (e.g., "Debt" -> "Liabilites_New", "Job" -> "Professional_Contacts_New").
    2. Select ALL modules that could possibly contain the answer.
    3. If the user asks for a general summary or overview, return ["Contacts", "Deals", "Notes"].
    4. Return ONLY a valid JSON list of strings. Do not include markdown formatting or explanations.
    
    Example Output:
    ["Income_Profile_New", "Expenses_New"]
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up potential markdown formatting from AI response
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove the first and last lines if they are code block markers
            filtered_lines = [line for line in lines if "```" not in line]
            text = "\n".join(filtered_lines)
            
        modules = json.loads(text)
        
        if isinstance(modules, list):
            return modules
        return ["Contacts", "Notes"] # Fallback if format is wrong
        
    except Exception as e:
        print(f"Router AI Error: {e}")
        # specific fallback for safety
        return ["Contacts", "Notes", "Deals"]

@app.post("/chat")
def chat(req: ChatRequest):
    print(f"\nReceived chat request for Account: {req.account_id}")
    print(f"User Query: {req.query}")

    # 1. Authenticate
    token = get_access_token()
    if not token:
        print("Authentication failed.")
        raise HTTPException(status_code=500, detail="Failed to get Zoho Token")

    # 2. INTELLIGENT FETCHING (The Router)
    # Ask AI which modules are needed based on the user's query
    target_modules = identify_relevant_modules(req.query)
    print(f"AI Router decided to fetch: {target_modules}")

    # 3. Get Data (Fetching ONLY the identified modules)
    record = get_account_data(req.account_id, token, related_modules_to_fetch=target_modules)
    
    if not record:
        raise HTTPException(status_code=404, detail="Account not found in CRM")

    # 4. Convert Data to Text
    text_data = crm_record_to_text(record)
    
    # 5. Create Vector Store & Search
    # We rebuild the vector store per request for real-time accuracy
    vs = build_vectorstore(text_data, req.account_id)
    
    # Search for context
    docs = vs.similarity_search(req.query, k=4)
    context = "\n".join([d.page_content for d in docs])

    # 6. Generate Final Response
    prompt = f"""
You are an intelligent, friendly, and professional CRM AI assistant designed to help relationship managers understand their clients better.

Your responsibilities:
- Use ONLY the information provided in the Account Context below.
- Never assume, invent, or guess any information.
- If the answer is not explicitly available, clearly say:
  "I don’t have that information available for this account."

Tone & Style:
- Friendly, clear, and confident
- Professional business language
- Easy to understand (non-technical)
- Helpful and consultative

Response Guidelines:
- If the user asks for a summary, provide a **clear, well-structured, and descriptive overview**
- Highlight important details such as:
  • Company background  
  • Financial or deal-related information  
  • Client interests or risks  
  • Recent activities or follow-ups  
- Use short paragraphs or bullet points when helpful
- Do NOT mention internal systems, vector databases, embeddings, or AI processes

STRICT DATA SAFETY RULE:
You must ONLY answer based on the Account Context below.
If the question goes outside this data, respond with:
"I don’t have that information available for this account."

--------------------
Account Context:
{context}
--------------------

User Question:
{req.query}

Now provide the best possible answer following all the rules above.
"""

    res = model.generate_content(prompt)
    return {"response": res.text}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)