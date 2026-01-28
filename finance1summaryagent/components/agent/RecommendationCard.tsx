'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { ActionCard } from './ActionCard';
import { cn } from '@/lib/utils/cn';
import type { Recommendation } from '@/types/api';

export interface RecommendationCardProps {
  recommendation: Recommendation;
  className?: string;
}

/**
 * Individual recommendation card component
 * 
 * Displays proactive recommendations from the scan endpoint
 * Shows different styling based on type (alert, suggestion, action) and priority
 */
export function RecommendationCard({ recommendation, className }: RecommendationCardProps) {
  const { type, message, priority, actions = [] } = recommendation;
  
  // Determine styling based on type and priority
  const getCardStyles = () => {
    if (type === 'alert') {
      return 'border-alert/30 bg-alert/5';
    }
    if (type === 'action') {
      return 'border-accent/30 bg-accent/5';
    }
    return 'border-primary/10 bg-secondary-white';
  };
  
  const getPriorityBadge = () => {
    const badgeColors = {
      high: 'bg-alert text-white',
      medium: 'bg-primary text-secondary-white',
      low: 'bg-primary/20 text-primary',
    };
    
    return (
      <span
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
          badgeColors[priority]
        )}
      >
        {priority.toUpperCase()}
      </span>
    );
  };
  
  const getTypeIcon = () => {
    switch (type) {
      case 'alert':
        return (
          <svg
            className="w-5 h-5 text-alert"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        );
      case 'action':
        return (
          <svg
            className="w-5 h-5 text-accent"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
        );
      default:
        return (
          <svg
            className="w-5 h-5 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
        );
    }
  };
  
  return (
    <Card
      variant="outlined"
      className={cn('border', getCardStyles(), className)}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className="shrink-0 mt-0.5">
            {getTypeIcon()}
          </div>
          
          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-primary/70 uppercase tracking-wide">
                  {type}
                </span>
                {getPriorityBadge()}
              </div>
            </div>
            
            <p className="text-sm text-primary leading-relaxed mb-3">
              {message}
            </p>
            
            {/* Actions */}
            {actions.length > 0 && (
              <div className="space-y-2 mt-3 pt-3 border-t border-primary/10">
                {actions.map((action, index) => (
                  <ActionCard
                    key={index}
                    action={action}
                    compact
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
