/**
 * API Module Index
 * 
 * Central export point for all API-related utilities, contracts, and schemas
 */

// API Client
export {
  fetchFastAPI,
  parseJsonResponse,
  getFastAPIUrl,
  ApiClientError,
  type ApiError,
} from './client';

// API Contract
export {
  API_VERSION,
  API_BASE_PATH,
  BACKEND_ENDPOINTS,
  API_ROUTES,
  ALL_ENDPOINTS,
  AGENT_CHAT_ENDPOINT,
  AGENT_SCAN_ENDPOINT,
  UPLOAD_ENDPOINT,
  ZOHO_METADATA_ENDPOINT,
  ZOHO_EXECUTE_ENDPOINT,
  getEndpointByPath,
  getBackendEndpoints,
  API_CHANGELOG,
  type EndpointDefinition,
} from './contract';

// API Versioning
export {
  CURRENT_API_VERSION,
  SUPPORTED_VERSIONS,
  API_VERSIONS,
  API_FEATURE_FLAGS,
  getVersionConfig,
  getCurrentVersion,
  isVersionSupported,
  getApiBasePath,
  parseVersionFromPath,
  addVersionToPath,
  removeVersionFromPath,
  getApiVersionFromEnv,
  isFeatureEnabled,
  areVersionsCompatible,
  getLatestCompatibleVersion,
  type ApiVersion,
  type ApiVersionConfig,
} from './versions';

// API Validation Schemas
export {
  ActionSchema,
  ChatRequestSchema,
  ChatResponseSchema,
  ScanRequestSchema,
  RecommendationSchema,
  ScanResponseSchema,
  UploadRequestMetadataSchema,
  UploadResponseSchema,
  ZohoExecuteRequestSchema,
  ZohoExecuteResponseSchema,
  ZohoMetadataResponseSchema,
  ErrorResponseSchema,
  validateRequest,
  safeValidate,
  validateResponse,
  type Action,
  type ChatRequest,
  type ChatResponse,
  type ScanRequest,
  type Recommendation,
  type ScanResponse,
  type UploadRequestMetadata,
  type UploadResponse,
  type ZohoExecuteRequest,
  type ZohoExecuteResponse,
  type ZohoFieldMetadata,
  type ZohoMetadataResponse,
  type ErrorResponse,
} from './schemas';
