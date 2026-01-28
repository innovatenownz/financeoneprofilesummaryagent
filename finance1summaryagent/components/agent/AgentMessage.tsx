'use client';

import React from 'react';
import { cn } from '@/lib/utils/cn';
import { Card, CardContent } from '@/components/ui/Card';
import type { Action } from '@/types/api';
import { ActionCard } from './ActionCard';

export interface AgentMessageProps {
  role: 'user' | 'assistant';
  content: string;
  actions?: Action[];
  timestamp?: Date;
}

/**
 * Individual message bubble component for chat interface
 * 
 * Displays user and assistant messages with different styling
 * Shows action buttons if provided in assistant messages
 */
export function AgentMessage({ 
  role, 
  content, 
  actions = [],
  timestamp 
}: AgentMessageProps) {
  const isUser = role === 'user';
  
  return (
    <div
      className={cn(
        'flex w-full mb-4',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[80%] flex flex-col',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        {/* Message bubble */}
        <div
          className={cn(
            'rounded-xl px-4 py-3 mb-2',
            isUser
              ? 'bg-primary text-secondary-white'
              : 'bg-secondary border border-primary/10 text-primary'
          )}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
            {content}
          </p>
        </div>
        
        {/* Actions (only for assistant messages) */}
        {!isUser && actions.length > 0 && (
          <div className="w-full space-y-2 mt-2">
            {actions.map((action, index) => (
              <ActionCard
                key={index}
                action={action}
                compact
              />
            ))}
          </div>
        )}
        
        {/* Timestamp (optional) */}
        {timestamp && (
          <span className="text-xs text-primary/60 mt-1">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>
    </div>
  );
}
