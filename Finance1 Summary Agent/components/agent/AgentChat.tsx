'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRecordData } from '@/components/zoho/useRecordData';
import { AgentMessage } from './AgentMessage';
import { AgentInput } from './AgentInput';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Card } from '@/components/ui/Card';
import type { ChatRequest, ChatResponse, Action } from '@/types/api';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  actions?: Action[];
  timestamp: Date;
}

export interface AgentChatProps {
  className?: string;
}

/**
 * Main chat interface component
 * 
 * Features:
 * - Message history display
 * - Send messages to agent API
 * - Display agent responses with actions
 * - Auto-scroll to latest message
 * - Loading states
 */
export function AgentChat({ className }: AgentChatProps) {
  const { entityId, entityType } = useRecordData();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Reset messages when record changes
  useEffect(() => {
    if (entityId) {
      setMessages([]);
      setError(null);
    }
  }, [entityId]);
  
  const sendMessage = async (content: string) => {
    if (!entityId || !entityType) {
      setError('No record loaded. Please wait for a record to be selected.');
      return;
    }
    
    // Add user message immediately
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    
    try {
      // Prepare request
      const request: ChatRequest = {
        entity_id: entityId,
        entity_type: entityType,
        query: content,
      };
      
      // Call API
      const response = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || errorData.message || `HTTP ${response.status}`);
      }
      
      const data: ChatResponse = await response.json();
      
      // Add assistant message
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response || 'No response received.',
        actions: data.actions,
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      
      // Add error message to chat
      const errorMessageObj: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}`,
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, errorMessageObj]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const hasRecord = entityId && entityType;
  
  return (
    <div className={`flex flex-col h-full ${className || ''}`}>
      {/* Messages container */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-2 bg-secondary"
      >
        {!hasRecord ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-primary/60">
              <p className="text-sm">Waiting for a record to be loaded...</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-primary/60 max-w-md">
              <p className="text-sm mb-2">Ask me anything about this {entityType} record.</p>
              <p className="text-xs">I can help you understand the data, suggest actions, and answer questions.</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <AgentMessage
                key={message.id}
                role={message.role}
                content={message.content}
                actions={message.actions}
                timestamp={message.timestamp}
              />
            ))}
            
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-secondary border border-primary/10 rounded-xl px-4 py-3">
                  <LoadingSpinner size="sm" />
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
        
        {error && !isLoading && (
          <Card variant="outlined" className="bg-alert/5 border-alert/20">
            <p className="text-sm text-alert">{error}</p>
          </Card>
        )}
      </div>
      
      {/* Input */}
      <AgentInput
        onSend={sendMessage}
        isLoading={isLoading}
        disabled={!hasRecord}
        placeholder={
          hasRecord
            ? `Ask a question about this ${entityType} record...`
            : 'Waiting for record...'
        }
      />
    </div>
  );
}
