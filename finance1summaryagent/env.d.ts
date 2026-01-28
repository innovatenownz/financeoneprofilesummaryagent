/// <reference types="node" />

declare namespace NodeJS {
  interface ProcessEnv {
    NEXT_PUBLIC_FASTAPI_URL?: string;
    FASTAPI_URL?: string;
    NEXT_PUBLIC_ZOHO_CLIENT_ID?: string;
    NEXT_PUBLIC_ENVIRONMENT?: string;
    NEXT_PUBLIC_API_VERSION?: string;
    NEXT_PUBLIC_ENABLE_SCAN?: string;
  }
}
