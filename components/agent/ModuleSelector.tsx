'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { cn } from '@/lib/utils/cn';

export interface ModuleOption {
  value: string;
  label: string;
  description?: string;
}

export interface ModuleSelectorProps {
  options: ModuleOption[];
  selected: string[];
  lockedValues?: string[];
  onChange: (nextSelected: string[]) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Multi-select dropdown for CRM modules.
 *
 * - Supports multiple selections
 * - Locks required modules (e.g., current record module)
 * - Minimal, mobile-friendly layout
 */
export function ModuleSelector({
  options,
  selected,
  lockedValues = [],
  onChange,
  disabled = false,
  className,
}: ModuleSelectorProps) {
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const lockedSet = useMemo(() => new Set(lockedValues), [lockedValues]);
  const selectedSet = useMemo(() => new Set(selected), [selected]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (
        (buttonRef.current && buttonRef.current.contains(target)) ||
        (panelRef.current && panelRef.current.contains(target))
      ) {
        return;
      }
      setOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleValue = (value: string) => {
    if (disabled || lockedSet.has(value)) return;
    const next = new Set(selectedSet);
    if (next.has(value)) {
      next.delete(value);
    } else {
      next.add(value);
    }
    lockedValues.forEach((locked) => next.add(locked));
    onChange(Array.from(next));
  };

  const handleSelectAll = () => {
    if (disabled) return;
    const all = new Set<string>(lockedValues);
    options.forEach((option) => all.add(option.value));
    onChange(Array.from(all));
  };

  const handleClear = () => {
    if (disabled) return;
    onChange(Array.from(new Set(lockedValues)));
  };

  const selectedLabel = selected.length
    ? `${selected.length} selected`
    : 'Select modules';

  return (
    <div className={cn('relative', className)}>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        disabled={disabled}
        className={cn(
          'w-full md:w-auto min-w-[180px] flex items-center justify-between gap-3',
          'rounded-lg border border-primary/20 bg-white px-3 py-2',
          'text-sm text-primary shadow-sm',
          'hover:border-primary/40 focus:outline-none focus:ring-2 focus:ring-primary/20',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        <span className="truncate">Modules</span>
        <span className="text-xs text-primary/60">{selectedLabel}</span>
      </button>

      {open && (
        <div
          ref={panelRef}
          className={cn(
            'absolute z-20 mt-2 w-full md:w-80',
            'rounded-lg border border-primary/10 bg-white shadow-lg'
          )}
        >
          <div className="flex items-center justify-between px-3 py-2 border-b border-primary/10">
            <span className="text-xs text-primary/60">Choose modules</span>
            <div className="flex items-center gap-2 text-xs">
              <button
                type="button"
                onClick={handleSelectAll}
                className="text-primary/70 hover:text-primary"
              >
                All
              </button>
              <span className="text-primary/20">|</span>
              <button
                type="button"
                onClick={handleClear}
                className="text-primary/70 hover:text-primary"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="max-h-64 overflow-y-auto p-2 space-y-1">
            {options.map((option) => {
              const isLocked = lockedSet.has(option.value);
              const isSelected = selectedSet.has(option.value);
              return (
                <label
                  key={option.value}
                  className={cn(
                    'flex items-start gap-2 rounded-md px-2 py-1.5 text-sm',
                    'hover:bg-primary/5',
                    isLocked ? 'cursor-not-allowed opacity-70' : 'cursor-pointer'
                  )}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleValue(option.value)}
                    disabled={disabled || isLocked}
                    className="mt-0.5"
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-primary">{option.label}</span>
                      {isLocked && (
                        <span className="text-[10px] uppercase tracking-wide text-primary/50">
                          Required
                        </span>
                      )}
                    </div>
                    {option.description && (
                      <p className="text-xs text-primary/50">{option.description}</p>
                    )}
                  </div>
                </label>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
