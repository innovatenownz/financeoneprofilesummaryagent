# Zoho CRM Agent Backend

FastAPI backend for the Zoho CRM Agent Widget. Provides AI-powered chat, proactive scanning, and document upload capabilities.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

3. Run the server:
```bash
python main.py
# or
uvicorn main:app --reload
```

## API Endpoints

### POST `/chat`
Chat endpoint for user queries about a CRM record.

**Request:**
```json
{
  "entity_id": "123456789",
  "entity_type": "Accounts",
  "query": "What is the status of this account?"
}
```

**Response:**
```json
{
  "response": "The account status is Active...",
  "actions": [
    {
      "label": "Update Status",
      "type": "UPDATE_FIELD",
      "field": "Status",
      "value": "Negotiation"
    }
  ]
}
```

### POST `/scan`
Proactive scan endpoint that analyzes a record and returns recommendations.

**Request:**
```json
{
  "entity_id": "123456789",
  "entity_type": "Accounts"
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "type": "alert",
      "message": "Missing phone number",
      "priority": "high",
      "actions": [
        {
          "label": "Add Phone Number",
          "type": "UPDATE_FIELD",
          "field": "Phone",
          "value": ""
        }
      ]
    }
  ]
}
```

### POST `/upload`
Upload endpoint for document ingestion.

**Request:** (multipart/form-data)
- `entity_id`: string
- `entity_type`: string (default: "Accounts")
- `file`: file

**Response:**
```json
{
  "success": true,
  "message": "Document uploaded successfully",
  "entity_id": "123456789",
  "entity_type": "Accounts",
  "filename": "document.pdf"
}
```

## Features

- **Generalized Entity Support**: Works with any Zoho CRM module (Accounts, Deals, Contacts, etc.)
- **Structured Responses**: Chat endpoint returns actionable buttons
- **Proactive Recommendations**: Scan endpoint provides automatic insights
- **Document Upload**: Support for file ingestion (ready for vectorstore integration)

## Environment Variables

- `ZOHO_REFRESH_TOKEN`: Zoho OAuth refresh token
- `ZOHO_CLIENT_ID`: Zoho OAuth client ID
- `ZOHO_CLIENT_SECRET`: Zoho OAuth client secret
- `ZOHO_API_DOMAIN`: Zoho API domain (default: www.zohoapis.com)
- `GOOGLE_API_KEY`: Google Gemini API key
