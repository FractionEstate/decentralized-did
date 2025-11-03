/**
 * Mock for env.ts in Jest environment
 */

export const getApiBaseUrl = (): string => {
  return process.env.VITE_API_BASE_URL || "http://localhost:8002";
};

export const API_BASE_URL = getApiBaseUrl();
