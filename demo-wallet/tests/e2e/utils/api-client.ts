/**
 * API Client Utilities for E2E Testing
 *
 * Helper functions to interact with the backend API during tests.
 */

import { expect } from '@playwright/test';

export interface ApiConfig {
  baseUrl: string;
  timeout?: number;
}

export interface FingerData {
  finger_id: string;
  minutiae: Array<{
    x: number;
    y: number;
    angle: number;
    quality: number;
  }>;
}

export interface GenerateRequest {
  wallet_address: string;
  fingers: FingerData[];
  helper_storage?: 'inline' | 'external';
}

export interface HelperData {
  salt_b64: string;
  auth_b64: string;
  person_b64?: string;
  hmac_b64?: string;
}

export interface GenerateResponse {
  did: string;
  wallet_bundle: any;
  helpers: Record<string, HelperData>;
}

export interface VerifyRequest {
  fingers: FingerData[];
  helpers: Record<string, HelperData>;
}

export interface VerifyResponse {
  verified: boolean;
  did?: string;
  matched_fingers: string[];
  unmatched_fingers: string[];
}

/**
 * API Client for biometric DID operations
 */
export class BiometricApiClient {
  private config: ApiConfig;

  constructor(config: ApiConfig) {
    this.config = {
      timeout: 30000,
      ...config,
    };
  }

  /**
   * Check API health
   */
  async checkHealth(): Promise<any> {
    const response = await fetch(`${this.config.baseUrl}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    expect(response.ok).toBeTruthy();
    return await response.json();
  }

  /**
   * Generate DID from biometric enrollment
   */
  async generate(request: GenerateRequest): Promise<GenerateResponse> {
    const response = await fetch(`${this.config.baseUrl}/api/v2/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    expect(response.ok).toBeTruthy();
    const data = await response.json();

    // Validate response structure
    expect(data).toHaveProperty('did');
    expect(data).toHaveProperty('wallet_bundle');
    expect(data).toHaveProperty('helpers');

    return data;
  }

  /**
   * Verify biometric authentication
   */
  async verify(request: VerifyRequest): Promise<VerifyResponse> {
    const response = await fetch(`${this.config.baseUrl}/api/v2/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    expect(response.ok).toBeTruthy();
    const data = await response.json();

    // Validate response structure
    expect(data).toHaveProperty('verified');
    expect(data).toHaveProperty('matched_fingers');
    expect(data).toHaveProperty('unmatched_fingers');

    return data;
  }

  /**
   * Test rate limiting by making multiple requests
   */
  async testRateLimit(endpoint: string, requests: number = 100): Promise<{
    successful: number;
    rateLimited: number;
  }> {
    let successful = 0;
    let rateLimited = 0;

    const promises = Array.from({ length: requests }, async () => {
      try {
        const response = await fetch(`${this.config.baseUrl}${endpoint}`, {
          method: 'GET',
        });

        if (response.status === 429) {
          rateLimited++;
        } else if (response.ok) {
          successful++;
        }
      } catch (error) {
        // Network error
      }
    });

    await Promise.all(promises);

    return { successful, rateLimited };
  }
}

/**
 * Create mock finger data for testing
 */
export function createMockFingerData(fingerId: string, count: number = 32): FingerData {
  return {
    finger_id: fingerId,
    minutiae: Array.from({ length: count }, (_, i) => ({
      x: Math.floor(Math.random() * 512),
      y: Math.floor(Math.random() * 512),
      angle: (i * 11.25) % 360,
      quality: 70 + Math.floor(Math.random() * 30),
    })),
  };
}

/**
 * Create mock enrollment request
 */
export function createMockEnrollmentRequest(
  walletAddress: string,
  fingerCount: number = 3,
  helperStorage: 'inline' | 'external' = 'inline'
): GenerateRequest {
  const fingers: FingerData[] = Array.from({ length: fingerCount }, (_, i) =>
    createMockFingerData(`finger_${i + 1}`)
  );

  return {
    wallet_address: walletAddress,
    fingers,
    helper_storage: helperStorage,
  };
}

/**
 * Add noise to minutiae to simulate biometric variation
 */
export function addMinutiaeNoise(
  finger: FingerData,
  noiseLevel: number = 5
): FingerData {
  return {
    ...finger,
    minutiae: finger.minutiae.map(m => ({
      x: m.x + Math.floor((Math.random() - 0.5) * noiseLevel * 2),
      y: m.y + Math.floor((Math.random() - 0.5) * noiseLevel * 2),
      angle: (m.angle + (Math.random() - 0.5) * noiseLevel) % 360,
      quality: Math.max(0, Math.min(100, m.quality + Math.floor((Math.random() - 0.5) * 10))),
    })),
  };
}

/**
 * Wait for API to be ready
 */
export async function waitForApiReady(
  baseUrl: string,
  maxRetries: number = 30,
  retryDelay: number = 1000
): Promise<boolean> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(`${baseUrl}/health`, {
        method: 'GET',
      });

      if (response.ok) {
        return true;
      }
    } catch (error) {
      // API not ready yet
    }

    await new Promise(resolve => setTimeout(resolve, retryDelay));
  }

  return false;
}
