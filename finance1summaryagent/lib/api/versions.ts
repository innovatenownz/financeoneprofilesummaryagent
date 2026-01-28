/**
 * API Version Management
 * 
 * This module handles API versioning strategy and provides utilities
 * for managing different API versions.
 * 
 * Versioning Strategy: URL-based versioning (e.g., /api/v1/...)
 * 
 * This allows:
 * - Clear version separation
 * - Gradual migration
 * - Backward compatibility
 * - Easy deprecation management
 */

/**
 * Current API version
 */
export const CURRENT_API_VERSION = 'v1' as const;

/**
 * Supported API versions
 */
export const SUPPORTED_VERSIONS = ['v1'] as const;

export type ApiVersion = typeof SUPPORTED_VERSIONS[number];

/**
 * API Version Configuration
 */
export interface ApiVersionConfig {
  version: ApiVersion;
  isCurrent: boolean;
  isDeprecated: boolean;
  deprecatedSince?: string;
  endOfLife?: string;
  notes?: string;
}

/**
 * Version registry
 */
export const API_VERSIONS: Record<ApiVersion, ApiVersionConfig> = {
  v1: {
    version: 'v1',
    isCurrent: true,
    isDeprecated: false,
    notes: 'Initial API version with chat, scan, upload, and Zoho integration endpoints',
  },
};

/**
 * Get version configuration
 */
export function getVersionConfig(version: ApiVersion): ApiVersionConfig {
  return API_VERSIONS[version];
}

/**
 * Get current API version
 */
export function getCurrentVersion(): ApiVersion {
  return CURRENT_API_VERSION;
}

/**
 * Check if a version is supported
 */
export function isVersionSupported(version: string): version is ApiVersion {
  return SUPPORTED_VERSIONS.includes(version as ApiVersion);
}

/**
 * Get API base path for a version
 */
export function getApiBasePath(version: ApiVersion = CURRENT_API_VERSION): string {
  return `/api/${version}`;
}

/**
 * Parse version from URL path
 * 
 * @param path - API path (e.g., '/api/v1/agent/chat' or '/api/agent/chat')
 * @returns Parsed version or current version if not specified
 */
export function parseVersionFromPath(path: string): ApiVersion {
  const match = path.match(/^\/api\/(v\d+)\//);
  if (match && isVersionSupported(match[1])) {
    return match[1] as ApiVersion;
  }
  // Default to current version if no version specified
  return CURRENT_API_VERSION;
}

/**
 * Add version to path
 * 
 * @param path - Path without version (e.g., '/api/agent/chat')
 * @param version - Version to add (defaults to current)
 * @returns Versioned path (e.g., '/api/v1/agent/chat')
 */
export function addVersionToPath(
  path: string,
  version: ApiVersion = CURRENT_API_VERSION
): string {
  // Remove existing version if present
  const pathWithoutVersion = path.replace(/^\/api\/v\d+\//, '/api/');
  
  // Add version
  if (pathWithoutVersion.startsWith('/api/')) {
    return pathWithoutVersion.replace('/api/', `/api/${version}/`);
  }
  
  return path;
}

/**
 * Remove version from path
 * 
 * @param path - Versioned path (e.g., '/api/v1/agent/chat')
 * @returns Path without version (e.g., '/api/agent/chat')
 */
export function removeVersionFromPath(path: string): string {
  return path.replace(/^\/api\/v\d+\//, '/api/');
}

/**
 * Environment-based version configuration
 * 
 * Allows different API versions per environment via environment variables
 */
export function getApiVersionFromEnv(): ApiVersion {
  const envVersion = process.env.NEXT_PUBLIC_API_VERSION;
  
  if (envVersion && isVersionSupported(envVersion)) {
    return envVersion;
  }
  
  return CURRENT_API_VERSION;
}

/**
 * Feature flags for API features
 * 
 * Allows gradual rollout of new features
 */
export const API_FEATURE_FLAGS = {
  ENABLE_SCAN: process.env.NEXT_PUBLIC_ENABLE_SCAN !== 'false',
  ENABLE_UPLOAD: process.env.NEXT_PUBLIC_ENABLE_UPLOAD !== 'false',
  ENABLE_ACTIONS: process.env.NEXT_PUBLIC_ENABLE_ACTIONS !== 'false',
} as const;

/**
 * Check if a feature is enabled
 */
export function isFeatureEnabled(feature: keyof typeof API_FEATURE_FLAGS): boolean {
  return API_FEATURE_FLAGS[feature];
}

/**
 * Version migration utilities
 * 
 * These utilities help with migrating between API versions
 */

/**
 * Version compatibility matrix
 * 
 * Defines which versions are compatible with each other
 */
export const VERSION_COMPATIBILITY: Record<ApiVersion, ApiVersion[]> = {
  v1: ['v1'],
};

/**
 * Check if two versions are compatible
 */
export function areVersionsCompatible(
  version1: ApiVersion,
  version2: ApiVersion
): boolean {
  return VERSION_COMPATIBILITY[version1]?.includes(version2) ?? false;
}

/**
 * Get the latest compatible version for a given version
 */
export function getLatestCompatibleVersion(version: ApiVersion): ApiVersion {
  const compatible = VERSION_COMPATIBILITY[version];
  if (!compatible || compatible.length === 0) {
    return CURRENT_API_VERSION;
  }
  
  // Return the highest version in the compatibility list
  return compatible[compatible.length - 1];
}
