/**
 * Utility function for merging classNames
 * Combines clsx and tailwind-merge for optimal className handling
 */
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
