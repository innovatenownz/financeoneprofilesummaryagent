import React from 'react';
import { Button } from '@/components/ui/Button';

const PRECONFIGURED_PROMPTS = [
  "Summarize this record",
  "What are the key details?",
  "Draft a follow-up email",
  "Show related deals",
  "Identify missing information"
];

interface PreconfiguredPromptsProps {
  onSelect: (prompt: string) => void;
  className?: string;
}

export function PreconfiguredPrompts({ onSelect, className }: PreconfiguredPromptsProps) {
  return (
    <div className={`flex flex-wrap gap-2 ${className || ''}`}>
      {PRECONFIGURED_PROMPTS.map((prompt) => (
        <Button
          key={prompt}
          variant="outline"
          size="sm"
          onClick={() => onSelect(prompt)}
          className="text-xs py-1 h-auto whitespace-nowrap"
        >
          {prompt}
        </Button>
      ))}
    </div>
  );
}
