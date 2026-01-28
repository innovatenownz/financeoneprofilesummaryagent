'use client';

import React, { useState } from 'react';
import { useZohoSDK } from '@/components/zoho/useZohoSDK';
import { useRecordData } from '@/components/zoho/useRecordData';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { cn } from '@/lib/utils/cn';
import type { Action } from '@/types/api';

export interface ActionCardProps {
  action: Action;
  compact?: boolean;
  className?: string;
}

/**
 * Action card component for rendering structured actions from agent responses
 * 
 * Displays actionable buttons that execute Zoho SDK operations
 * Supports different action types: UPDATE_FIELD, CREATE_RECORD, SEND_EMAIL, CUSTOM
 */
export function ActionCard({ action, compact = false, className }: ActionCardProps) {
  const { executeZohoAction, isReady } = useZohoSDK();
  const { entityId, entityType } = useRecordData();
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  const handleExecute = async () => {
    if (!isReady || !entityId) {
      setErrorMessage('Zoho SDK is not ready or no record is loaded');
      setExecutionStatus('error');
      return;
    }
    
    setIsExecuting(true);
    setExecutionStatus('idle');
    setErrorMessage(null);
    
    try {
      // Convert Action to ZohoAction format
      const zohoAction = {
        label: action.label,
        type: action.type,
        field: action.field,
        value: action.value,
        zohoAction: action.zohoAction,
        module: action.module,
        recordData: action.recordData,
        to: action.to,
        subject: action.subject,
        body: action.body,
        templateId: action.templateId,
      };
      
      // Execute via API route
      const response = await fetch('/api/zoho/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: zohoAction,
          entity_id: entityId,
          entity_type: entityType,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || errorData.message || `HTTP ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        setExecutionStatus('success');
        // Reset success status after a delay
        setTimeout(() => {
          setExecutionStatus('idle');
        }, 2000);
      } else {
        throw new Error(result.message || 'Action execution failed');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to execute action';
      setErrorMessage(errorMsg);
      setExecutionStatus('error');
    } finally {
      setIsExecuting(false);
    }
  };
  
  // Determine button variant based on action type
  const getButtonVariant = (): 'primary' | 'accent' | 'alert' | 'secondary' => {
    switch (action.type) {
      case 'UPDATE_FIELD':
        return 'accent';
      case 'CREATE_RECORD':
        return 'primary';
      case 'SEND_EMAIL':
        return 'accent';
      case 'CUSTOM':
        return 'secondary';
      default:
        return 'primary';
    }
  };
  
  // Get action description
  const getActionDescription = (): string => {
    switch (action.type) {
      case 'UPDATE_FIELD':
        return action.field
          ? `Update ${action.field} to ${action.value}`
          : action.label;
      case 'CREATE_RECORD':
        return action.module
          ? `Create new ${action.module} record`
          : action.label;
      case 'SEND_EMAIL':
        return action.subject || action.label;
      default:
        return action.label;
    }
  };
  
  if (compact) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <Button
          onClick={handleExecute}
          disabled={!isReady || isExecuting || executionStatus === 'success'}
          isLoading={isExecuting}
          variant={executionStatus === 'success' ? 'accent' : getButtonVariant()}
          size="sm"
          className="flex-1"
        >
          {executionStatus === 'success' ? (
            <>
              <svg
                className="w-4 h-4 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              Done
            </>
          ) : (
            action.label
          )}
        </Button>
        {errorMessage && (
          <span className="text-xs text-alert">{errorMessage}</span>
        )}
      </div>
    );
  }
  
  return (
    <Card variant="outlined" className={cn('border-primary/10', className)}>
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <p className="text-sm font-medium text-primary mb-1">
              {action.label}
            </p>
            <p className="text-xs text-primary/70">
              {getActionDescription()}
            </p>
            {errorMessage && (
              <p className="text-xs text-alert mt-2">{errorMessage}</p>
            )}
          </div>
          
          <Button
            onClick={handleExecute}
            disabled={!isReady || isExecuting || executionStatus === 'success'}
            isLoading={isExecuting}
            variant={executionStatus === 'success' ? 'accent' : getButtonVariant()}
            size="sm"
          >
            {executionStatus === 'success' ? (
              <>
                <svg
                  className="w-4 h-4 mr-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                Done
              </>
            ) : (
              'Execute'
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
