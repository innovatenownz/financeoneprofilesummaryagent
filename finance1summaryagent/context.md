
---

# Project Context: Zoho Agentic CRM Widget

## 1. Project Goal

Develop a context-aware, actionable AI agent widget for Zoho CRM. The widget will replace the current Streamlit prototype with a native Zoho Widget (React/Next.js) deployed on Vercel, integrating with an existing FastAPI/LangChain backend.

## 2. Technical Stack

* **Frontend:** React/Next.js (optimized for Vercel).
* **Backend:** FastAPI (Python) using LangChain and Gemini.
* **Integration:** Zoho Embedded App SDK (ZSDK).
* **Authentication:** Zoho OAuth (Refresh Token flow).
* **AI:** Google Gemini-1.5-Flash via `google-generativeai`.
* **Data Store:** FAISS for temporary RAG (Transitioning to persistent storage).

## 3. Existing Backend Logic (Python)

The current backend consists of:

* **`zoho_auth.py`**: Handles OAuth token refreshing.
* **`zoho_crm_api_call.py`**: Fetches specific record data using the API.
* **`crm_to_text.py`**: Formats JSON record data into a string for LLM consumption.
* **`vectorstore_runtime.py`**: Creates a temporary FAISS vector store for the record context.
* **`main.py`**: FastAPI app that orchestrates the RAG flow and generates responses.

## 4. Product Requirements (To be Implemented)

### 4.1. Automatic Context Detection

* **Requirement:** Use `ZSDK.embeddedApp.on("PageLoad", ...)` to capture the `EntityId` and `Entity` (Module Name) automatically.
* **Elimination:** Remove manual ID entry found in the current `frontend.py`.

### 4.2. Proactive Agent Layer

* **Feature:** On record load, the widget should perform a "Silent Scan."
* **Task:** Create an endpoint that triggers the agent to generate 2-3 proactive recommendations (e.g., "Missing Phone Number," "Follow-up overdue") before the user types anything.

### 4.3. Actionable UI

* **Feature:** AI responses must contain actionable buttons.
* **Task:** Modify the LLM prompt in `main.py` to return structured JSON containing both a text message and an "actions" array (e.g., `{"label": "Approve", "type": "ZSDK_UPDATE"}`).

### 4.4. Developer Utility: API Metadata Discovery

* **Instruction:** During development, create a utility script to fetch and log the **API Names** of fields for the current module.
* **Constraint:** This is for development mapping only and should not be a user-facing feature.

## 5. Development Roadmap for Cursor

### Step 1: Initialize Next.js Widget

* Create a Next.js application designed to run in a sidebar.
* Import the Zoho SDK: `https://live.zwidgets.com/js-sdk/1.1/ZohoEmbededAppSDK.min.js`.

### Step 2: Bridge ZSDK and FastAPI

* Set up a listener in React that catches the `EntityId`.
* Call the `/chat` (or new `/scan`) endpoint in `main.py` using this ID.

### Step 3: Structured AI Responses

* Update `main.py` to use a structured output parser so the UI can render "Action Cards" with buttons.

### Step 4: Document Support

* Implement a file upload component in the React UI.
* Extend the backend to ingest uploaded files into the FAISS vector store.

## 6. Important Reference Files

* **Auth Logic:** `zoho_auth.py`
* **CRM Data Fetching:** `zoho_crm_api_call.py`
* **Backend Orchestration:** `main.py`
* **Data Formatting:** `crm_to_text.py`

---

### Instructions for Cursor (Prompt Examples)

* *"Based on `ZOHO_WIDGET_CONTEXT.md`, create a Next.js page that initializes the Zoho SDK and logs the current record's API Name to the console."*
* *"Rewrite the `chat` function in `main.py` to return a JSON object that includes a 'suggested_actions' list for the UI to render as buttons."*
* *"Create a React component for the proactive recommendation cards described in the PRD section of the context file."*