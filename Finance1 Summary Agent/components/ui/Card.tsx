'use client';

import React from 'react';
import { cn } from '@/lib/utils/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: 'default' | 'outlined' | 'elevated';
}

/**
 * Card component following design system
 * 
 * Variants:
 * - default: White background with soft shadow
 * - outlined: Border with no shadow
 * - elevated: Stronger shadow for emphasis
 */
export function Card({ 
  variant = 'default', 
  className, 
  children, 
  ...props 
}: CardProps) {
  const variants = {
    default: 'bg-secondary-white shadow-soft',
    outlined: 'bg-secondary-white border border-primary/10',
    elevated: 'bg-secondary-white shadow-medium',
  };
  
  return (
    <div
      className={cn(
        'rounded-xl p-4',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function CardHeader({ className, children, ...props }: CardHeaderProps) {
  return (
    <div
      className={cn('mb-4', className)}
      {...props}
    >
      {children}
    </div>
  );
}

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode;
}

export function CardTitle({ className, children, ...props }: CardTitleProps) {
  return (
    <h3
      className={cn('text-lg font-semibold text-primary', className)}
      {...props}
    >
      {children}
    </h3>
  );
}

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function CardContent({ className, children, ...props }: CardContentProps) {
  return (
    <div
      className={cn('text-primary/90', className)}
      {...props}
    >
      {children}
    </div>
  );
}
