# Implementation Plan: Zoho CRM AI Agent Widget

## Overview
This plan outlines the steps to integrate an existing LangChain/Python AI agent as a robust Zoho CRM widget. The architecture separates the backend (Python/FastAPI on Railway) from the frontend (Next.js on Vercel), ensuring scalability and security.

## 1. Backend Development (Railway)

### 1.1. Environment Setup
- **Objective**: Prepare the Python application for Railway deployment.
- **Tasks**:
  - Update `requirements.txt` to include `fastapi`, `uvicorn`, `google-generativeai`, `python-dotenv`, `requests`.
  - Create a `Procfile` for Railway: `web: uvicorn main:app --host 0.0.0.0 --port $PORT`.
  - Ensure `python_version` is specified (e.g., `runtime.txt` or `nixpacks.toml` if needed, but usually auto-detected).

### 1.2. Streaming Support
- **Objective**: Enable real-time "typing" effect for AI responses.
- **Tasks**:
  - Update `main.py` to use FastAPI's `StreamingResponse`.
  - Refactor Agent classes (starting with `AccountAgent`) to support `stream=True` in Gemini calls.
  - Create a generator function in the API endpoint to yield chunks of data to the client.

### 1.3. Module & Action Handling
- **Objective**: Support context switching and preconfigured actions.
- **Tasks**:
  - Ensure the API accepts a `module` parameter (already present).
  - (Optional) Create an endpoint `/modules` to list available agents dynamically, or keep it consistent with the frontend hardcoding.

## 2. Frontend Development (Vercel)

### 2.1. API Proxy & Streaming
- **Objective**: Connect the Next.js frontend to the Railway backend securely.
- **Tasks**:
  - Update `app/api/agent/chat/route.ts` to forward requests to the Railway URL.
  - Implement streaming response handling on the client side using `ReadableStream` decoding.

### 2.2. UI Components
- **Objective**: Enhance the user interface for flexibility and usability.
- **Tasks**:
  - **Module Selector**: Create a dropdown component allowing the user to switch the "active knowledge base" (e.g., switch from "Account" context to "Deals" context manually if needed, or query cross-module).
  - **Preconfigured Prompts**: Create a "Quick Actions" component (chips/buttons) with prompts like:
    - "Summarize this account"
    - "What are the open deals?"
    - "Draft a follow-up email"
  - **Agent Chat**: Update to support Markdown rendering and streaming text.

### 2.3. Mobile Responsiveness
- **Objective**: Ensure the widget looks good on mobile apps.
- **Tasks**:
  - Use Tailwind's responsive prefixes (`md:`, `lg:`) to adjust padding and font sizes.
  - Ensure the chat window consumes available height without double scrollbars.

## 3. Zoho Integration (Widget)

### 3.1. Authentication
- **Objective**: Secure the communication.
- **Tasks**:
  - The backend (`zoho_auth.py`) handles Zoho OAuth. Ensure `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, and `ZOHO_REFRESH_TOKEN` are set in Railway variables.
  - The frontend uses the Widget SDK (`ZSDK`) to get the current Record ID.

### 3.2. Domain Handling (.com vs .com.au)
- **Objective**: Ensure the widget works in the NZ environment.
- **Tasks**:
  - The Widget SDK (`ZSDK`) automatically detects the parent window's origin.
  - The backend auth endpoint is hardcoded to `.com.au` in `zoho_auth.py`. This matches the user's requirement.

## 4. Deployment Steps

### 4.1. Railway (Backend)
1. Connect GitHub repo to Railway.
2. Set Environment Variables:
   - `GOOGLE_API_KEY`
   - `ZOHO_CLIENT_ID`
   - `ZOHO_CLIENT_SECRET`
   - `ZOHO_REFRESH_TOKEN`
   - `ZOHO_REFRESH_TOKEN` (Ensure this is generated for the .com.au DC).

### 4.2. Vercel (Frontend)
1. Connect GitHub repo to Vercel.
2. Set Environment Variables:
   - `NEXT_PUBLIC_ZOHO_CLIENT_ID`
   - `RAILWAY_BACKEND_URL` (The URL provided by Railway).

### 4.3. Zoho CRM
1. Go to **Setup > Developer Space > Widgets**.
2. Create "New Widget".
3. Hosting Type: **External**.
4. Base URL: `https://your-vercel-app.vercel.app`.
5. Add the widget to a related list or button in the CRM.

