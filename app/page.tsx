'use client';

import { ZohoProvider, useZohoContext } from '@/components/zoho';
import { ProactiveScan, AgentChat } from '@/components/agent';
import { DocumentUpload } from '@/components/upload';

function WidgetContent() {
  const { sdkState, recordContext } = useZohoContext();
  const enableScan = process.env.NEXT_PUBLIC_ENABLE_SCAN === 'true';
  const enableUpload = process.env.NEXT_PUBLIC_ENABLE_UPLOAD === 'true';

  // Show loading state while SDK initializes
  if (sdkState.status === 'loading') {
    return (
      <div className="min-h-screen bg-secondary p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-600">Initializing Zoho SDK...</p>
        </div>
      </div>
    );
  }

  // Show error state if SDK fails to initialize
  if (sdkState.status === 'error') {
    return (
      <div className="min-h-screen bg-secondary p-8 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-500 text-4xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-primary mb-2">SDK Initialization Error</h2>
          <p className="text-gray-600 mb-4">
            {sdkState.error?.message || 'Failed to initialize Zoho SDK'}
          </p>
          <p className="text-sm text-gray-500">
            Make sure you&apos;re accessing this widget from within Zoho CRM.
          </p>
        </div>
      </div>
    );
  }

  // Main widget content
  return (
    <main className="min-h-screen bg-secondary">
      <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-4">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h1 className="text-xl font-semibold text-primary mb-1">
            AI CRM Assistant
          </h1>
          <p className="text-sm text-gray-600">
            {recordContext.entityId && recordContext.entityType
              ? `Focused on ${recordContext.entityType} record`
              : 'Waiting for record to load...'}
          </p>
        </div>

        {/* Agent Chat Interface */}
        {recordContext.entityId ? (
          <div className="bg-white rounded-lg shadow-sm border border-primary/10 overflow-hidden">
            <AgentChat className="min-h-[520px] max-h-[70vh]" />
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <p className="text-gray-500">
              Open a record in Zoho CRM to start using the agent.
            </p>
          </div>
        )}

        {/* Optional Proactive Scan */}
        {enableScan && recordContext.entityId && (
          <ProactiveScan autoScan={true} />
        )}

        {/* Optional Document Upload */}
        {enableUpload && recordContext.entityId && (
          <div className="bg-white rounded-lg shadow-sm p-4">
            <h2 className="text-lg font-semibold text-primary mb-3">Upload Documents</h2>
            <DocumentUpload />
          </div>
        )}
      </div>
    </main>
  );
}

export default function Home() {
  // Get Zoho Client ID from environment
  const clientId = process.env.NEXT_PUBLIC_ZOHO_CLIENT_ID;

  return (
    <ZohoProvider
      config={{
        clientId: clientId || undefined,
        onReady: () => {
          console.log('Zoho SDK initialized successfully');
        },
        onError: (error) => {
          console.error('Zoho SDK error:', error);
        },
      }}
    >
      <WidgetContent />
    </ZohoProvider>
  );
}