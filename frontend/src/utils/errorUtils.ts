/**
 * Error handling utilities
 */
import { ApiError } from '../services/apiClient';

/**
 * Extract a user-friendly message from an error
 */
export const getErrorMessage = (error: unknown): string => {
  if (error instanceof ApiError) {
    return `Error (${error.status}): ${error.message}`;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'An unknown error occurred';
};

/**
 * Format the date string for display
 */
export const formatDate = (dateString?: string): string => {
  if (!dateString) return 'N/A';
  
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('default', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  } catch (e) {
    return dateString;
  }
};
