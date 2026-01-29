'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRecordData } from '@/components/zoho/useRecordData';
import { AgentMessage } from './AgentMessage';
import { AgentInput } from './AgentInput';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Card } from '@/components/ui/Card';
import { ModuleSelector } from './ModuleSelector';
import { PreconfiguredPrompts } from './PreconfiguredPrompts';
import type { Action } from '@/types/api';

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

export function AgentChat({ className }: AgentChatProps) {
  const { entityId, entityType } = useRecordData();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedModule, setSelectedModule] = useState<string>('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  
  // Initialize selected module based on current entity type
  useEffect(() => {
    if (entityType) {
        // Map Zoho Module Names to our Agent keys (simple lowercase match often works, but let's be safe)
        // This is a naive mapping, might need refinement
        const normalized = entityType.toLowerCase().replace(/ /g, '_');
        setSelectedModule(normalized);
    }
  }, [entityType]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]); // Scroll on loading state change too
  
  // Reset messages when record changes
  useEffect(() => {
    if (entityId) {
      setMessages([]);
      setError(null);
    }
  }, [entityId]);
  
  const sendMessage = async (content: string) => {
    if (!entityId) {
      setError('No record loaded.');
      return;
    }
    
    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    // Create placeholder for assistant message
    const assistantId = `assistant-${Date.now()}`;
    setMessages((prev) => [...prev, {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date()
    }]);
    
    try {
      const response = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_id: entityId,
          entity_type: selectedModule || entityType, // Use selected module or default
          query: content,
        }),
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let assistantContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        
        // Check if the response was actually JSON (error or non-streaming)
        // This is a bit hacky but if the first chunk starts with {, it might be JSON.
        // However, our backend now forces stream or JSON.
        // If it was JSON, we'd parse it. But here we assume stream.
        // If we get a JSON error in a stream, it might look like text.
        
        assistantContent += chunk;
        
        // Update the specific message in state
        setMessages((prev) => prev.map(msg => 
            msg.id === assistantId 
                ? { ...msg, content: assistantContent }
                : msg
        ));
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      setMessages((prev) => prev.filter(msg => msg.id !== assistantId)); // Remove the empty/partial message or mark as error?
      setMessages((prev) => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${errorMessage}`,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const hasRecord = !!entityId;
  
  return (
    <div className={`flex flex-col h-full ${className || ''}`}>
      {/* Header / Module Selector */}
      <div className="p-4 border-b bg-white">
        <div className="flex items-center justify-between mb-2">
           <span className="text-xs font-semibold text-gray-500 uppercase">Context</span>
           <ModuleSelector 
             value={selectedModule} 
             onChange={setSelectedModule} 
             className="w-48"
           />
        </div>
      </div>

      {/* Messages */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 bg-secondary"
      >
        {!hasRecord ? (
          <div className="flex items-center justify-center h-full text-center text-primary/60">
             <p>Waiting for record...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full space-y-4">
             <p className="text-sm text-gray-500">Ask about this {selectedModule}...</p>
             <PreconfiguredPrompts onSelect={sendMessage} />
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
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      {/* Input */}
      <div className="p-4 bg-white border-t">
        {messages.length > 0 && <PreconfiguredPrompts onSelect={sendMessage} className="mb-3" />}
        <AgentInput
            onSend={sendMessage}
            isLoading={isLoading}
            disabled={!hasRecord}
            placeholder={`Ask about ${selectedModule}...`}
        />
      </div>
    </div>
  );
}
