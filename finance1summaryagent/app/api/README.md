# API Routes

This directory contains Next.js API routes that proxy requests to the FastAPI backend.

## Routes

### Agent Routes

#### `POST /api/agent/chat`
Proxies chat requests to the FastAPI `/chat` endpoint.

**Request:**
```json
{
  "entity_id": "string",
  "entity_type": "string (optional)",
  "query": "string"
}
```

**Response:**
```json
{
  "response": "string",
  "actions": [/* optional Action[] */]
}
```

#### `POST /api/agent/scan`
Proxies scan requests to the FastAPI `/scan` endpoint for proactive recommendations.

**Request:**
```json
{
  "entity_id": "string",
  "entity_type": "string"
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "type": "alert" | "suggestion" | "action",
      "message": "string",
      "priority": "high" | "medium" | "low",
      "actions": [/* optional Action[] */]
    }
  ]
}
```

### Upload Route

#### `POST /api/upload`
Proxies file upload requests to the FastAPI `/upload` endpoint.

**Request:** FormData
- `file`: File (required)
- `entity_id`: string (required)
- `entity_type`: string (required)
- `file_type`: string (optional)

**Response:**
```json
{
  "success": boolean,
  "message": "string"
}
```

### Zoho Utility Routes

#### `GET /api/zoho/metadata`
Development utility for API name discovery. **Note:** This endpoint is a placeholder. Zoho SDK is client-side only, so metadata should be fetched using the `useZohoSDK` hook in client components.

#### `POST /api/zoho/execute`
Validates Zoho action structures. **Note:** Actual Zoho SDK actions must be executed client-side using the `useZohoSDK` hook.

**Request:**
```json
{
  "action": {
    "label": "string",
    "type": "UPDATE_FIELD" | "CREATE_RECORD" | "SEND_EMAIL" | "CUSTOM",
    "field": "string (optional)",
    "value": "any (optional)",
    // ... other action properties
  }
}
```

**Response:**
```json
{
  "success": boolean,
  "message": "string",
  "data": {}
}
```

## Environment Variables

- `NEXT_PUBLIC_FASTAPI_URL` or `FASTAPI_URL`: The base URL of the FastAPI backend (e.g., `http://localhost:8000` for development)

## Error Handling

All routes include comprehensive error handling:
- **400**: Bad request (missing required fields)
- **500**: Internal server error
- **502**: Bad gateway (FastAPI backend error)
- **503**: Service unavailable (endpoint not implemented in backend)

## Backend Compatibility

The routes are designed to work with the existing FastAPI backend while supporting future enhancements:
- Legacy `account_id` support in chat endpoint
- Graceful degradation when new endpoints (`/scan`, `/upload`) are not yet implemented
- Structured error responses for better debugging
