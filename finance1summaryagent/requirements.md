
---
# Agentic CRM Widget (Integrated Edition)

## 1. Project Overview

A responsive Zoho CRM widget that serves as the frontend for existing **LangChain agents** stored in GitHub. The widget facilitates real-time, record-aware interactions and executes CRM actions derived from LangChain's reasoning.

## 2. Technical Stack & Integration

* **Agent Logic:** LangChain (Python or TypeScript).
* **Version Control:** GitHub (Existing repository).
* **Deployment:** Vercel (Hosting the Widget UI and API routes).
* **IDE:** Cursor (For UI development and API glue-code).
* **CRM Integration:** Zoho Widget SDK (ZSDK).

---

## 3. Development Phase: API Name Mapping

*This is a developer-only step to ensure your LangChain agents can "talk" to Zoho correctly.*

* **Mapping Utility:** In the development environment, Cursor should generate a utility script to fetch **Zoho API Names** (e.g., `Deal_Name`, `Account_ID`).
* **LangChain Alignment:** These API names must be fed into your LangChain tools or prompt templates so the agent knows exactly which fields to read from or update.

---

## 4. Functional Requirements

### 4.1 LangChain Connectivity

* **API Proxy:** Create a Vercel API route (`/api/agent`) that receives the `recordData` from Zoho.
* **Context Passing:** The widget must pass the entire JSON of the Zoho record to the LangChain agent.
* **Streaming Support:** (Optional) If your LangChain agent supports streaming, the UI should use **Server-Sent Events (SSE)** or Vercel's AI SDK to show the agent thinking in real-time.

### 4.2 The "Proactive" UI Layer

Your LangChain agents likely output structured data (using `JsonOutputParser`).

* **Actionable Recommendations:** If the agent identifies an "Alert" or "Next Step," it should return a specific JSON schema.
* **Widget Rendering:** The frontend must detect this schema and render a "Accept/Decline" UI card rather than just a text bubble.

### 4.3 Document Upload & RAG

* **File Handling:** When a user uploads a document via the widget, the file is sent to the LangChain backend.
* **Vectorization:** Depending on your GitHub code, the file is either processed on-the-fly or stored in a vector DB (like Pinecone or Weaviate) for the agent to query.

---

## 5. System Architecture Flow

1. **Trigger:** User opens a record in Zoho CRM.
2. **Context Fetch:** `ZSDK` grabs record data + `Entity_API_Name`.
3. **Agent Call:** Widget sends this data to the **Vercel API Route**.
4. **LangChain Execution:** The API route pulls the latest agent logic from your repository, processes the CRM data, and returns a response.
5. **UI Render:** The widget displays the text response and any "Action Buttons" (e.g., *Update Status to 'Negotiation'*).

---

## 6. Cursor Implementation Strategy

When you open your repository in **Cursor**, you should follow this sequence:

1. **Step 1: The Bridge.** Ask Cursor to create a Next.js API route that imports your existing LangChain logic and wraps it in a handler.
2. **Step 2: The UI.** Use Cursor to build a React component that uses the `ZSDK` to listen for record changes and send them to that API route.
3. **Step 3: Action Execution.** Ensure that when the LangChain agent calls a "Tool" to update Zoho, Cursor generates the code to send that command back to the widget's `ZSDK.execute()` method.

---

## 7. Performance & Security

* **Caching:** Use Vercel's edge caching for common LangChain responses to reduce latency.
* **Environment Variables:** Store Zoho Client Secrets and OpenAI/LLM keys in Vercel's environment settings, synced with your GitHub repo.

---