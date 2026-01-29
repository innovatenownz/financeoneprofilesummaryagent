'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useRecordData } from '@/components/zoho/useRecordData';
import { AgentMessage } from './AgentMessage';
import { AgentInput } from './AgentInput';
import { Card } from '@/components/ui/Card';
import { ModuleSelector, type ModuleOption } from './ModuleSelector';
import { QuickPrompts, type QuickPrompt } from './QuickPrompts';
import type { ChatRequest, ChatResponse, Action } from '@/types/api';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  actions?: Action[];
  timestamp: Date;
  isStreaming?: boolean;
  streamingLabel?: string;
}

export interface AgentChatProps {
  className?: string;
}

const BASE_MODULE_OPTIONS: ModuleOption[] = [
  { value: 'Accounts', label: 'Accounts', description: 'Account profile and fields' },
  { value: 'Contacts', label: 'Contacts', description: 'Associated contacts' },
  { value: 'Deals', label: 'Deals', description: 'Open and closed opportunities' },
  { value: 'Tasks', label: 'Tasks', description: 'Open tasks and reminders' },
  { value: 'Notes', label: 'Notes', description: 'Internal notes and updates' },
  { value: 'Emails', label: 'Emails', description: 'Recent email conversations' },
  { value: 'Calls', label: 'Calls', description: 'Call history' },
  { value: 'Events', label: 'Events', description: 'Meetings and events' },
];

const MODULE_SUGGESTIONS: Record<string, string[]> = {
  Accounts: ['Contacts', 'Deals', 'Tasks', 'Notes'],
  Contacts: ['Accounts', 'Deals', 'Tasks', 'Notes'],
  Deals: ['Accounts', 'Contacts', 'Tasks', 'Notes'],
  Leads: ['Tasks', 'Notes'],
};

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
  const statusIntervalRef = useRef<number | null>(null);
  const streamIntervalRef = useRef<number | null>(null);

  const moduleOptions = useMemo<ModuleOption[]>(() => {
    if (entityType && !BASE_MODULE_OPTIONS.some((option) => option.value === entityType)) {
      return [{ value: entityType, label: entityType }, ...BASE_MODULE_OPTIONS];
    }
    return BASE_MODULE_OPTIONS;
  }, [entityType]);

  const defaultSelectedModules = useMemo(() => {
    if (!entityType) return [];
    const suggestions = MODULE_SUGGESTIONS[entityType] ?? [];
    const next = [entityType, ...suggestions];
    const valid = next.filter((value) => moduleOptions.some((option) => option.value === value));
    return Array.from(new Set(valid));
  }, [entityType, moduleOptions]);

  const [selectedModules, setSelectedModules] = useState<string[]>(defaultSelectedModules);

  const quickPrompts = useMemo<QuickPrompt[]>(() => {
    const targetLabel = entityType ? entityType.toLowerCase() : 'record';
    return [
      {
        id: 'summary',
        label: 'Summary',
        prompt: `Provide a concise summary of this ${targetLabel}.`,
        description: 'Highlight key details, risks, and next steps.',
      },
      {
        id: 'recent-activity',
        label: 'Recent activity',
        prompt: 'Summarize recent activity across the selected modules.',
        description: 'Notes, tasks, emails, calls, and events.',
      },
      {
        id: 'open-items',
        label: 'Open items',
        prompt: 'List open tasks, overdue items, and upcoming follow-ups.',
        description: 'Focus on immediate actions.',
      },
      {
        id: 'data-gaps',
        label: 'Data gaps',
        prompt: 'Identify missing or inconsistent data that should be cleaned up.',
        description: 'Surface data quality issues.',
      },
      {
        id: 'next-steps',
        label: 'Next steps',
        prompt: 'Recommend next best actions for this account based on CRM history.',
        description: 'Provide clear, actionable suggestions.',
      },
    ];
  }, [entityType]);
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Reset messages when record changes
  useEffect(() => {
    if (entityId) {
      setMessages([]);
      setError(null);
      setSelectedModules(defaultSelectedModules);
      if (statusIntervalRef.current) {
        window.clearInterval(statusIntervalRef.current);
        statusIntervalRef.current = null;
      }
      if (streamIntervalRef.current) {
        window.clearInterval(streamIntervalRef.current);
        streamIntervalRef.current = null;
      }
    }
  }, [entityId, defaultSelectedModules]);

  useEffect(() => {
    return () => {
      if (statusIntervalRef.current) {
        window.clearInterval(statusIntervalRef.current);
        statusIntervalRef.current = null;
      }
      if (streamIntervalRef.current) {
        window.clearInterval(streamIntervalRef.current);
        streamIntervalRef.current = null;
      }
    };
  }, []);

  const handleModulesChange = (nextSelected: string[]) => {
    if (entityType && !nextSelected.includes(entityType)) {
      nextSelected = [entityType, ...nextSelected];
    }
    setSelectedModules(Array.from(new Set(nextSelected)));
  };

  const updateMessage = (messageId: string, updates: Partial<Message>) => {
    setMessages((prev) =>
      prev.map((message) => (message.id === messageId ? { ...message, ...updates } : message))
    );
  };

  const streamResponse = (messageId: string, text: string, actions?: Action[]) => {
    if (streamIntervalRef.current) {
      window.clearInterval(streamIntervalRef.current);
      streamIntervalRef.current = null;
    }
    const tokens = text.match(/\S+|\s+/g) ?? [text];
    let index = 0;
    return new Promise<void>((resolve) => {
      streamIntervalRef.current = window.setInterval(() => {
        index += 1;
        updateMessage(messageId, {
          content: tokens.slice(0, index).join(''),
          isStreaming: index < tokens.length,
        });
        if (index >= tokens.length) {
          if (streamIntervalRef.current) {
            window.clearInterval(streamIntervalRef.current);
            streamIntervalRef.current = null;
          }
          updateMessage(messageId, {
            isStreaming: false,
            streamingLabel: undefined,
            actions,
          });
          resolve();
        }
      }, 20);
    });
  };
  
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
    
    const assistantMessageId = `assistant-${Date.now()}`;
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      isStreaming: true,
      streamingLabel: 'Gathering CRM context...',
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);
    setError(null);

    if (statusIntervalRef.current) {
      window.clearInterval(statusIntervalRef.current);
      statusIntervalRef.current = null;
    }

    const statusSteps = [
      'Gathering CRM context...',
      `Reviewing ${selectedModules.length ? selectedModules.join(', ') : entityType}...`,
      'Drafting response...',
    ];
    let statusIndex = 0;
    statusIntervalRef.current = window.setInterval(() => {
      statusIndex = (statusIndex + 1) % statusSteps.length;
      updateMessage(assistantMessageId, { streamingLabel: statusSteps[statusIndex] });
    }, 1200);
    
    try {
      // Prepare request
      const request: ChatRequest = {
        entity_id: entityId,
        entity_type: entityType,
        query: content,
        modules: selectedModules,
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

      if (statusIntervalRef.current) {
        window.clearInterval(statusIntervalRef.current);
        statusIntervalRef.current = null;
      }

      const responseText = data.response || 'No response received.';
      await streamResponse(assistantMessageId, responseText, data.actions);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      
      if (statusIntervalRef.current) {
        window.clearInterval(statusIntervalRef.current);
        statusIntervalRef.current = null;
      }

      updateMessage(assistantMessageId, {
        content: `Sorry, I encountered an error: ${errorMessage}`,
        isStreaming: false,
        streamingLabel: undefined,
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  const hasRecord = entityId && entityType;
  
  return (
    <div className={`flex flex-col h-full ${className || ''}`}>
      <div className="border-b border-primary/10 bg-white px-4 py-3">
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <ModuleSelector
              options={moduleOptions}
              selected={selectedModules}
              lockedValues={entityType ? [entityType] : []}
              onChange={handleModulesChange}
              disabled={!hasRecord || isLoading}
            />
            <div className="text-xs text-primary/60">
              {selectedModules.length
                ? `Using ${selectedModules.length} module${selectedModules.length > 1 ? 's' : ''}`
                : 'No modules selected'}
            </div>
          </div>
          <QuickPrompts
            prompts={quickPrompts}
            onSelect={(prompt) => sendMessage(prompt.prompt)}
            disabled={!hasRecord || isLoading}
          />
        </div>
      </div>

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
                isStreaming={message.isStreaming}
                streamingLabel={message.streamingLabel}
              />
            ))}
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
