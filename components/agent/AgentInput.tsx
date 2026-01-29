'use client';

import React, { useState, KeyboardEvent } from 'react';
import { cn } from '@/lib/utils/cn';
import { Button } from '@/components/ui/Button';

export interface AgentInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * Chat input component with send button
 * 
 * Features:
 * - Multi-line text input
 * - Enter to send, Shift+Enter for new line
 * - Loading state support
 * - Auto-resize textarea
 */
export function AgentInput({
  onSend,
  isLoading = false,
  disabled = false,
  placeholder = 'Ask a question about this record...',
}: AgentInputProps) {
  const [message, setMessage] = useState('');
  const [textareaHeight, setTextareaHeight] = useState('auto');
  
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  
  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isLoading && !disabled) {
      onSend(trimmedMessage);
      setMessage('');
      setTextareaHeight('auto');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };
  
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 120; // Max height in pixels (about 5 lines)
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
      setTextareaHeight(`${Math.min(scrollHeight, maxHeight)}px`);
    }
  };
  
  return (
    <div className="flex items-end gap-2 p-4 bg-secondary-white border-t border-primary/10">
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isLoading}
          rows={1}
          className={cn(
            'w-full px-4 py-2 pr-12 rounded-lg border border-primary/20',
            'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
            'resize-none overflow-y-auto',
            'text-sm text-primary placeholder:text-primary/50',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'transition-colors'
          )}
          style={{ height: textareaHeight, minHeight: '40px', maxHeight: '120px' }}
        />
        <div className="absolute bottom-2 right-2 text-xs text-primary/40">
          {message.length > 0 && `${message.length} chars`}
        </div>
      </div>
      
      <Button
        onClick={handleSend}
        disabled={disabled || isLoading || !message.trim()}
        isLoading={isLoading}
        variant="accent"
        size="md"
        className="shrink-0"
      >
        Send
      </Button>
    </div>
  );
}
