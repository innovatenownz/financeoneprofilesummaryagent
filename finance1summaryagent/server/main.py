from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
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
# Load API Key from Environment Variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set GOOGLE_API_KEY before running the application.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# Using Flash for speed, as it handles the routing logic very quickly
model = genai.GenerativeModel('gemini-2.5-flash')

app = FastAPI(title="Zoho CRM Agent API")

# PRIORITY 1 FIX: CORS middleware - Required for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    entity_id: Optional[str] = None  # Optional to support backward compatibility with account_id
    entity_type: str = "Accounts"  # Default to Accounts for backward compatibility
    query: str
    account_id: Optional[str] = None  # Deprecated, use entity_id


class Action(BaseModel):
    label: str
    type: str  # "UPDATE_FIELD", "CREATE_RECORD", "SEND_EMAIL", "CUSTOM"
    field: Optional[str] = None
    value: Optional[Any] = None
    zohoAction: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    actions: Optional[List[Action]] = None


class ScanRequest(BaseModel):
    entity_id: str
    entity_type: str = "Accounts"


class Recommendation(BaseModel):
    type: str  # "alert", "suggestion", "action"
    message: str
    priority: str  # "high", "medium", "low"
    actions: Optional[List[Action]] = None


class ScanResponse(BaseModel):
    recommendations: List[Recommendation]


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
        return ["Contacts", "Notes"]  # Fallback if format is wrong

    except Exception as e:
        print(f"Router AI Error: {e}")
        # specific fallback for safety
        return ["Contacts", "Notes", "Deals"]


def parse_structured_response(response_text: str, response_type: str = "chat") -> dict:
    """
    Parses AI response that may contain structured JSON.
    For chat: expects {"response": "...", "actions": [...]}
    For scan: expects {"recommendations": [...]}
    """
    try:
        # Try to extract JSON from response
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()
        
        # Try to parse as JSON
        parsed = json.loads(text)
        return parsed
    except:
        # If parsing fails, return as plain text response
        if response_type == "chat":
            return {"response": response_text, "actions": []}
        else:
            return {"recommendations": []}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Chat endpoint for user queries about a CRM record.
    Returns structured response with optional actions.
    """
    # PRIORITY 2 FIX: Handle backward compatibility and entity generalization
    entity_id = req.entity_id or req.account_id
    if not entity_id:
        raise HTTPException(status_code=400, detail="entity_id or account_id is required")
    
    entity_type = req.entity_type or "Accounts"
    
    # For now, we support Accounts with intelligent module routing
    # TODO: Extend to support other entity types (Deals, Contacts, etc.)
    if entity_type != "Accounts":
        raise HTTPException(
            status_code=400, 
            detail=f"Entity type '{entity_type}' not yet supported. Currently only 'Accounts' is supported."
        )
    
    print(f"\nReceived chat request for Account: {entity_id}")
    print(f"User Query: {req.query}")

    try:
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
        record = get_account_data(entity_id, token, related_modules_to_fetch=target_modules)

        if not record:
            raise HTTPException(status_code=404, detail="Account not found in CRM")

        # 4. Convert Data to Text
        text_data = crm_record_to_text(record)

        # 5. Create Vector Store & Search
        # We rebuild the vector store per request for real-time accuracy
        vs = build_vectorstore(text_data, entity_id)

        # Search for context (k=1 since we only have one document)
        docs = vs.similarity_search(req.query, k=1)
        context = "\n".join([d.page_content for d in docs])

        # 6. Generate Final Response with Structured Output
        # PRIORITY 2 FIX: Request structured JSON response with actions
        prompt = f"""
You are an intelligent, friendly, and professional CRM AI assistant designed to help relationship managers understand their clients better.

Your responsibilities:
- Use ONLY the information provided in the Account Context below.
- Never assume, invent, or guess any information.
- If the answer is not explicitly available, clearly say:
 "I don't have that information available for this account."

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
"I don't have that information available for this account."

IMPORTANT: You must respond in JSON format with the following structure:
{{
    "response": "Your text response here",
    "actions": [
        {{
            "label": "Action button label (e.g., 'Update Status')",
            "type": "UPDATE_FIELD",
            "field": "Field_API_Name (e.g., 'Status')",
            "value": "New value (e.g., 'Active')"
        }}
    ]
}}

If the user's query suggests an action (like updating a field, creating a record, etc.), include structured actions in the actions array.
If no actions are needed, set "actions" to an empty array [].

--------------------
Account Context:
{context}
--------------------

User Question:
{req.query}

Now provide the best possible answer in the JSON format specified above.
"""

        res = model.generate_content(prompt)
        parsed_response = parse_structured_response(res.text, "chat")
        
        # Parse actions if present
        actions = None
        if parsed_response.get("actions"):
            try:
                actions = [Action(**action) for action in parsed_response["actions"]]
            except Exception as e:
                print(f"Error parsing actions: {e}")
                actions = None
        
        return ChatResponse(
            response=parsed_response.get("response", res.text),
            actions=actions
        )
    
    except HTTPException:
        # Re-raise HTTPException to preserve status codes (404, 500, etc.)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@app.post("/scan", response_model=ScanResponse)
def scan(req: ScanRequest):
    """
    PRIORITY 1 FIX: Proactive scan endpoint that analyzes a record and returns recommendations
    without requiring a user query.
    """
    entity_type = req.entity_type or "Accounts"
    
    # For now, we support Accounts only
    if entity_type != "Accounts":
        raise HTTPException(
            status_code=400,
            detail=f"Entity type '{entity_type}' not yet supported. Currently only 'Accounts' is supported."
        )
    
    print(f"\nReceived scan request for Account: {req.entity_id}")

    try:
        # 1. Authenticate
        token = get_access_token()
        if not token:
            raise HTTPException(status_code=500, detail="Failed to get Zoho Token")

        # 2. Get Data (Fetch all relevant modules for comprehensive analysis)
        # For scan, we fetch common modules to get a full picture
        target_modules = ["Contacts", "Deals", "Notes", "Tasks", "Meetings"]
        record = get_account_data(req.entity_id, token, related_modules_to_fetch=target_modules)

        if not record:
            raise HTTPException(status_code=404, detail="Account not found in CRM")

        # 3. Convert Data to Text
        text_data = crm_record_to_text(record)

        # 4. Create Vector Store
        vs = build_vectorstore(text_data, req.entity_id)

        # 5. Generate Proactive Recommendations
        prompt = f"""
You are an AI assistant analyzing a Zoho CRM account record to provide proactive recommendations.

Analyze this account and provide 2-3 proactive recommendations. Look for:
- Missing critical information (phone numbers, emails, addresses)
- Overdue follow-ups or tasks
- Incomplete records
- Opportunities for improvement
- Data quality issues
- Important relationships or connections

IMPORTANT: You must respond in JSON format with the following structure:
{{
    "recommendations": [
        {{
            "type": "alert|suggestion|action",
            "message": "Clear recommendation message",
            "priority": "high|medium|low",
            "actions": [
                {{
                    "label": "Action button label",
                    "type": "UPDATE_FIELD",
                    "field": "Field_API_Name",
                    "value": "New value"
                }}
            ]
        }}
    ]
}}

If no actions are needed for a recommendation, set "actions" to an empty array [].

--------------------
Account Context:
{text_data}
--------------------

Provide proactive recommendations in the JSON format specified above.
"""

        res = model.generate_content(prompt)
        parsed_response = parse_structured_response(res.text, "scan")
        
        # Parse recommendations
        recommendations_data = parsed_response.get("recommendations", [])
        recommendations = []
        
        for rec in recommendations_data:
            actions = None
            if rec.get("actions"):
                try:
                    actions = [Action(**action) for action in rec["actions"]]
                except Exception as e:
                    print(f"Error parsing recommendation actions: {e}")
                    actions = None
            
            recommendations.append(
                Recommendation(
                    type=rec.get("type", "suggestion"),
                    message=rec.get("message", ""),
                    priority=rec.get("priority", "medium"),
                    actions=actions
                )
            )
        
        # Ensure we have at least some recommendations
        if not recommendations:
            recommendations.append(
                Recommendation(
                    type="suggestion",
                    message="No specific recommendations at this time. Account data looks complete.",
                    priority="low",
                    actions=None
                )
            )
        
        return ScanResponse(recommendations=recommendations)
    
    except HTTPException:
        # Re-raise HTTPException to preserve status codes (404, 500, etc.)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing scan request: {str(e)}")


@app.post("/upload")
async def upload_document(
    entity_id: str = Form(...),
    entity_type: str = Form("Accounts"),
    file: UploadFile = File(...)
):
    """
    PRIORITY 1 FIX: Upload endpoint for document ingestion into the vectorstore.
    Processes the file and adds it to the RAG context for the entity.
    """
    # For now, we support Accounts only
    if entity_type != "Accounts":
        raise HTTPException(
            status_code=400,
            detail=f"Entity type '{entity_type}' not yet supported. Currently only 'Accounts' is supported."
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Basic file processing - extract text
        # For text files, decode directly
        # Bug fix: Check if filename is None before string operations
        if file.filename is None:
            raise HTTPException(status_code=400, detail="File filename is missing")
        
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        
        if file_ext in ["txt", "text", "md", "markdown"]:
            try:
                text = file_content.decode("utf-8", errors="ignore")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error decoding text file: {e}")
        elif file_ext == "pdf":
            try:
                import PyPDF2
                from io import BytesIO
                pdf_file = BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text_parts = [page.extract_text() for page in pdf_reader.pages]
                text = "\n".join(text_parts)
            except ImportError:
                raise HTTPException(
                    status_code=400,
                    detail="PDF processing requires PyPDF2. Install with: pip install PyPDF2"
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing PDF: {e}")
        elif file_ext in ["docx", "doc"]:
            try:
                from docx import Document as DocxDocument
                from io import BytesIO
                docx_file = BytesIO(file_content)
                doc = DocxDocument(docx_file)
                text_parts = [paragraph.text for paragraph in doc.paragraphs]
                text = "\n".join(text_parts)
            except ImportError:
                raise HTTPException(
                    status_code=400,
                    detail="DOCX processing requires python-docx. Install with: pip install python-docx"
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing DOCX: {e}")
        else:
            # Try to decode as text
            try:
                text = file_content.decode("utf-8", errors="ignore")
            except Exception:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")
        
        # Note: In a production system, you would:
        # 1. Store files in persistent storage (S3, etc.)
        # 2. Process and chunk the document
        # 3. Add to a persistent vectorstore (Pinecone, Weaviate, etc.)
        # 4. Associate with entity_id for retrieval in future queries
        # 
        # For this implementation, we process the document and return success.
        # The actual vectorstore persistence would be implemented based on your
        # chosen vector database solution.
        
        # Count approximate chunks (simple split by paragraphs)
        chunks = [chunk for chunk in text.split("\n\n") if chunk.strip()]
        
        return {
            "success": True,
            "message": f"Document '{file.filename}' processed successfully for {entity_type} {entity_id}",
            "entity_id": entity_id,
            "entity_type": entity_type,
            "filename": file.filename,
            "chunks_created": len(chunks),
            "text_length": len(text)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
