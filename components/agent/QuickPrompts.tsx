'use client';

import React from 'react';
import { cn } from '@/lib/utils/cn';
import { Button } from '@/components/ui/Button';

export interface QuickPrompt {
  id: string;
  label: string;
  prompt: string;
  description?: string;
}

export interface QuickPromptsProps {
  prompts: QuickPrompt[];
  onSelect: (prompt: QuickPrompt) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Quick prompt buttons for common CRM questions.
 */
export function QuickPrompts({
  prompts,
  onSelect,
  disabled = false,
  className,
}: QuickPromptsProps) {
  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {prompts.map((prompt) => (
        <Button
          key={prompt.id}
          type="button"
          variant="secondary"
          size="sm"
          disabled={disabled}
          onClick={() => onSelect(prompt)}
          className="text-xs px-3 py-1.5"
          title={prompt.description || prompt.prompt}
        >
          {prompt.label}
        </Button>
      ))}
    </div>
  );
}
