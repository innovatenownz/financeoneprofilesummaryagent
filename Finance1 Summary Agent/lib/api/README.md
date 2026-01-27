# API Contract Management

This directory contains the API contract management system that serves as the source of truth for all API endpoints, versioning, and validation.

## Files

- **`contract.ts`** - API endpoint definitions and documentation
- **`versions.ts`** - API versioning strategy and utilities
- **`schemas.ts`** - Zod validation schemas for runtime type checking
- **`client.ts`** - API client utilities for FastAPI backend communication
- **`index.ts`** - Central export point for all API utilities

## Usage

### Importing

```typescript
import {
  // Contract definitions
  AGENT_CHAT_ENDPOINT,
  API_ROUTES,
  
  // Versioning
  getCurrentVersion,
  getApiBasePath,
  
  // Validation
  ChatRequestSchema,
  validateRequest,
  validateResponse,
  
  // Client utilities
  fetchFastAPI,
} from '@/lib/api';
```

### Using Validation Schemas

#### In API Routes (Request Validation)

```typescript
import { ChatRequestSchema, validateRequest } from '@/lib/api';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate request
    const validatedData = validateRequest(ChatRequestSchema, body);
    
    // Use validatedData...
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Invalid request', details: error.format() },
        { status: 400 }
      );
    }
    throw error;
  }
}
```

#### In API Routes (Response Validation)

```typescript
import { ChatResponseSchema, validateResponse } from '@/lib/api';

export async function POST(request: NextRequest) {
  const response = await fetchFastAPI('/chat', { ... });
  const data = await parseJsonResponse(response);
  
  // Validate response (logs warning if invalid, doesn't throw)
  const validationResult = validateResponse(
    ChatResponseSchema,
    data,
    'AGENT_CHAT'
  );
  
  if (validationResult.isValid) {
    // TypeScript knows validationResult.data is ChatResponse here
    return NextResponse.json(validationResult.data);
  } else {
    // Validation failed - return original data with warning
    // Components should handle missing fields gracefully
    console.warn('Response validation failed:', validationResult.error);
    return NextResponse.json(validationResult.data);
  }
}
```

#### Safe Validation (No Exceptions)

```typescript
import { safeValidate, ChatRequestSchema } from '@/lib/api';

const result = safeValidate(ChatRequestSchema, body);

if (result.success) {
  // Use result.data
} else {
  // Handle result.error
  return NextResponse.json(
    { error: 'Validation failed', details: result.error.format() },
    { status: 400 }
  );
}
```

### Using API Contract Definitions

```typescript
import { AGENT_CHAT_ENDPOINT, getEndpointByPath } from '@/lib/api';

// Get endpoint definition
const endpoint = AGENT_CHAT_ENDPOINT;
console.log(endpoint.description); // "Chat with the AI agent..."
console.log(endpoint.path); // "/api/agent/chat"
console.log(endpoint.backendPath); // "/chat"

// Find endpoint by path
const found = getEndpointByPath('/api/agent/chat');
```

### Using Versioning Utilities

```typescript
import {
  getCurrentVersion,
  getApiBasePath,
  parseVersionFromPath,
  isFeatureEnabled,
} from '@/lib/api';

// Get current version
const version = getCurrentVersion(); // "v1"

// Get API base path
const basePath = getApiBasePath(); // "/api/v1"

// Parse version from URL
const version = parseVersionFromPath('/api/v1/agent/chat'); // "v1"

// Check feature flags
if (isFeatureEnabled('ENABLE_SCAN')) {
  // Use scan endpoint
}
```

## When Backend Changes

### Step 1: Update Contract Definition

Edit `contract.ts` to reflect the new endpoint structure:

```typescript
export const AGENT_CHAT_ENDPOINT: EndpointDefinition<ChatRequest, ChatResponse> = {
  // ... update description, notes, etc.
};
```

### Step 2: Update TypeScript Types

Edit `types/api.ts` to match the new structure:

```typescript
export interface ChatResponse {
  response: string;
  actions?: Action[];
  // Add new fields here
  metadata?: Record<string, any>;
}
```

### Step 3: Update Zod Schemas

Edit `schemas.ts` to validate the new structure:

```typescript
export const ChatResponseSchema = z.object({
  response: z.string(),
  actions: z.array(ActionSchema).optional(),
  metadata: z.record(z.any()).optional(), // Add new field
});
```

### Step 4: Update API Routes

Update the corresponding API route to handle the new structure.

### Step 5: Update Changelog

Add an entry to `API_CHANGELOG` in `contract.ts`:

```typescript
{
  date: '2026-01-29',
  version: 'v1.1.0',
  changes: [
    {
      type: 'enhanced',
      endpoint: 'AGENT_CHAT',
      description: 'Added metadata field to chat response',
    },
  ],
}
```

## Versioning Strategy

The project uses **URL-based versioning**:

- Current version: `v1`
- Versioned paths: `/api/v1/agent/chat`
- Unversioned paths (legacy): `/api/agent/chat` (defaults to v1)

### Adding a New Version

1. Add version to `SUPPORTED_VERSIONS` in `versions.ts`
2. Add version config to `API_VERSIONS`
3. Update `CURRENT_API_VERSION` when ready to switch
4. Update route handlers to support versioned paths

## Feature Flags

Feature flags allow gradual rollout of new features:

```typescript
// In versions.ts
export const API_FEATURE_FLAGS = {
  ENABLE_SCAN: process.env.NEXT_PUBLIC_ENABLE_SCAN !== 'false',
  // ...
};

// Usage
if (isFeatureEnabled('ENABLE_SCAN')) {
  // Use scan endpoint
}
```

Set via environment variables:
```bash
NEXT_PUBLIC_ENABLE_SCAN=true
```

## Testing

Validation schemas can be used in tests to ensure API contract compliance:

```typescript
import { ChatResponseSchema } from '@/lib/api';

test('backend response matches contract', async () => {
  const response = await fetch('/api/agent/chat', { ... });
  const data = await response.json();
  
  // This will throw if response doesn't match schema
  ChatResponseSchema.parse(data);
});
```

## Best Practices

1. **Always validate requests** in API routes before processing
2. **Validate responses** from backend (with graceful degradation)
3. **Update contract first** when backend changes
4. **Use feature flags** for new endpoints during development
5. **Document breaking changes** in the changelog
6. **Test schema changes** before deploying
