/**
 * Environment configuration
 * Handles environment variable access for both Vite and Jest environments
 */

// Declare import.meta for TypeScript
declare const importMeta: any;

// Get API base URL from environment
export const getApiBaseUrl = (): string => {
  // Try to access import.meta.env if available (Vite environment)
  try {
    // Use eval to prevent Jest from parsing import.meta at compile time
    const meta = eval('import.meta');
    if (meta && meta.env) {
      return meta.env.VITE_API_BASE_URL || "http://localhost:8002";
    }
  } catch (e) {
    // Fall through to process.env
  }

  // Fallback to process.env (Node/Jest environment)
  return (process.env as any).VITE_API_BASE_URL || "http://localhost:8002";
};

export const API_BASE_URL = getApiBaseUrl();
