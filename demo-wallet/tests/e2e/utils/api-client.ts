/**
 * API Client Utilities for E2E Testing
 *
 * Helper functions to interact with the backend API during tests.
 */

import { expect } from '@playwright/test';

const DEFAULT_HEALTH_PATH = process.env.API_HEALTH_PATH || '/health';
const DEFAULT_GENERATE_PATH = process.env.API_GENERATE_PATH || '/api/biometric/generate';
const DEFAULT_VERIFY_PATH = process.env.API_VERIFY_PATH || '/api/biometric/verify';

export interface ApiConfig {
  baseUrl: string;
  timeout?: number;
  healthPath?: string;
  generatePath?: string;
  verifyPath?: string;
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
  storage?: 'inline' | 'external';
  format?: 'json';
  // Legacy fields for compatibility with older test helpers
  finger_count: number;
  helper_mode: 'inline' | 'external';
  finger_data: Array<{
    finger_index: number;
    template: string;
    quality_score: number;
  }>;
}

export interface HelperData {
  finger_id: string;
  salt_b64: string;
  auth_b64: string;
  grid_size?: number;
  angle_bins?: number;
}

export interface GenerateResponse {
  did: string;
  id_hash: string;
  wallet_address: string;
  helpers: Record<string, HelperData>;
  metadata_cip30_inline: {
    version: string;
    walletAddress: string;
    controllers: string[];
    enrollmentTimestamp: string;
    revoked: boolean;
    revokedAt?: string | null;
    biometric: {
      idHash: string;
      helperStorage: string;
      helperData: Record<string, HelperData> | null;
    };
  };
}

export interface VerifyRequest {
  fingers: FingerData[];
  helpers: Record<string, HelperData>;
  expected_id_hash: string;
}

export interface VerifyResponse {
  success: boolean;
  did?: string;
  matched_fingers: string[];
  unmatched_fingers: string[];
  error?: string | null;
}

/**
 * API Client for biometric DID operations
 */
export class BiometricApiClient {
  private config: ApiConfig;
  private routes: {
    health: string;
    generate: string;
    verify: string;
  };

  constructor(config: ApiConfig) {
    this.config = {
      timeout: 30000,
      ...config,
    };

    this.routes = {
      health: config.healthPath || DEFAULT_HEALTH_PATH,
      generate: config.generatePath || DEFAULT_GENERATE_PATH,
      verify: config.verifyPath || DEFAULT_VERIFY_PATH,
    };
  }

  /**
   * Check API health
   */
  async checkHealth(): Promise<any> {
    const response = await fetch(`${this.config.baseUrl}${this.routes.health}`, {
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
    const response = await fetch(`${this.config.baseUrl}${this.routes.generate}`, {
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
    expect(data).toHaveProperty('metadata_cip30_inline');
    expect(data).toHaveProperty('helpers');

    return data;
  }

  /**
   * Verify biometric authentication
   */
  async verify(request: VerifyRequest): Promise<VerifyResponse> {
    const response = await fetch(`${this.config.baseUrl}${this.routes.verify}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    expect(response.ok).toBeTruthy();
    const data = await response.json();

    // Validate response structure
    expect(data).toHaveProperty('success');
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
  const baseSeed = fingerId
    .split('')
    .reduce((acc, char, idx) => acc + char.charCodeAt(0) * (idx + 1), 0);

  return {
    finger_id: fingerId,
    minutiae: Array.from({ length: count }, (_, index) => {
      const x = (baseSeed * 31 + index * 17) % 512;
      const y = (baseSeed * 17 + index * 31) % 512;
      const angle = (baseSeed + index * 37) % 360;
      const quality = 70 + ((baseSeed + index * 13) % 30);

      return {
        x,
        y,
        angle,
        quality,
      };
    }),
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

  const legacyFingerData = fingers.map((finger, index) => ({
    finger_index: index,
    template: Buffer.from(JSON.stringify(finger.minutiae)).toString('base64'),
    quality_score: 90,
  }));

  return {
    wallet_address: walletAddress,
    fingers,
    storage: helperStorage,
    format: 'json',
    finger_count: fingerCount,
    helper_mode: helperStorage,
    finger_data: legacyFingerData,
  };
}

/**
 * Add noise to minutiae to simulate biometric variation
 */
export function addMinutiaeNoise(
  finger: FingerData,
  noiseLevel: number = 5
): FingerData {
  const baseSeed = finger.finger_id
    .split('')
    .reduce((acc, char, idx) => acc + char.charCodeAt(0) * (idx + 1), 0);

  const spread = Math.max(1, noiseLevel);

  return {
    ...finger,
    minutiae: finger.minutiae.map((m, index) => {
      const offset = (baseSeed + index * 97) % (spread * 2 + 1);
      const delta = offset - spread;
      const angleDelta = ((baseSeed + index * 53) % (spread * 2 + 1)) - spread;
      const qualityDelta = ((baseSeed + index * 19) % 11) - 5;

      const x = Math.max(0, Math.min(511, m.x + delta));
      const y = Math.max(0, Math.min(511, m.y - delta));
      const angle = (m.angle + angleDelta + 360) % 360;
      const quality = Math.max(0, Math.min(100, m.quality + qualityDelta));

      return {
        x,
        y,
        angle,
        quality,
      };
    }),
  };
}

/**
 * Wait for API to be ready
 */
export async function waitForApiReady(
  baseUrl: string,
  maxRetries: number = 30,
  retryDelay: number = 1000,
  healthPath: string = DEFAULT_HEALTH_PATH
): Promise<boolean> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(`${baseUrl}${healthPath}`, {
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

export const biometricAssertions = {
  assertValidDid(did: string): void {
    if (!did || !did.startsWith('did:cardano:')) {
      throw new Error(`Invalid DID format: ${did}. Expected did:cardano:*`);
    }

    const deterministicPattern = /^did:cardano:(mainnet|testnet|preprod):[a-zA-Z0-9]+$/;
    if (!deterministicPattern.test(did)) {
      throw new Error(
        `Invalid DID structure: ${did}. Expected format: did:cardano:{network}:{hash}`
      );
    }
  },

  assertValidHelperData(
    helperData: Record<string, HelperData> | null,
    mode: 'inline' | 'external'
  ): void {
    if (mode === 'inline') {
      if (!helperData || Object.keys(helperData).length === 0) {
        throw new Error('Helper data should be present in inline mode');
      }
    } else if (helperData) {
      throw new Error('Helper data should be null in external mode');
    }
  },

  assertValidMetadata(metadata: any, expectedStorage: 'inline' | 'external'): void {
    if (!metadata) {
      throw new Error('Metadata should be present');
    }

    if (metadata.version !== '1.1') {
      throw new Error(`Unexpected metadata version: ${metadata.version}`);
    }

    if (!Array.isArray(metadata.controllers) || metadata.controllers.length === 0) {
      throw new Error('Metadata controllers must be a non-empty array');
    }

    if (typeof metadata.enrollmentTimestamp !== 'string') {
      throw new Error('Enrollment timestamp should be a string');
    }

    if (typeof metadata.revoked !== 'boolean') {
      throw new Error('Metadata must include revoked boolean');
    }

    if (!metadata.biometric) {
      throw new Error('Metadata missing biometric block');
    }

    const biometric = metadata.biometric;
    if (typeof biometric.idHash !== 'string') {
      throw new Error('Biometric metadata requires idHash');
    }

    if (biometric.helperStorage !== expectedStorage) {
      throw new Error(
        `Expected helper storage ${expectedStorage} but received ${biometric.helperStorage}`
      );
    }

    if (expectedStorage === 'inline') {
      if (!biometric.helperData || Object.keys(biometric.helperData).length === 0) {
        throw new Error('Inline storage should include helper data');
      }
    } else if (biometric.helperData !== null) {
      throw new Error('External storage should not return helper data inline');
    }
  },

  assertValidHelpers(helpers: Record<string, HelperData>, expectedFingers: string[]): void {
    if (!helpers || typeof helpers !== 'object') {
      throw new Error('Helpers should be an object');
    }

    const helperKeys = Object.keys(helpers).sort();
    const expectedKeys = [...expectedFingers].sort();

    if (helperKeys.length !== expectedKeys.length) {
      throw new Error('Helper count does not match expected fingers');
    }

    helperKeys.forEach((key, index) => {
      if (key !== expectedKeys[index]) {
        throw new Error(`Unexpected helper finger: ${key}`);
      }

      const helper = helpers[key];
      if (!helper) {
        throw new Error(`Missing helper data for ${key}`);
      }

      ['salt_b64', 'auth_b64', 'finger_id'].forEach(field => {
        if (!(field in helper)) {
          throw new Error(`Helper data for ${key} missing field ${field}`);
        }
      });

      if ('grid_size' in helper) {
        if (typeof helper.grid_size !== 'number') {
          throw new Error(`Helper grid_size for ${key} should be a number`);
        }
      }

      if ('angle_bins' in helper) {
        if (typeof helper.angle_bins !== 'number') {
          throw new Error(`Helper angle_bins for ${key} should be a number`);
        }
      }
    });
  },

  assertValidVerification(
    response: VerifyResponse,
    expectedSuccess: boolean,
    expectedMatchedCount: number
  ): void {
    if (!response) {
      throw new Error('Verification response missing');
    }

    if (response.success !== expectedSuccess) {
      throw new Error(
        `Expected success=${expectedSuccess} but received ${response.success} (error=${response.error})`
      );
    }

    if (response.matched_fingers.length !== expectedMatchedCount) {
      throw new Error(
        `Expected ${expectedMatchedCount} matched fingers but received ${response.matched_fingers.length}`
      );
    }

    if (expectedSuccess && response.error) {
      throw new Error(`Expected successful verification but received error: ${response.error}`);
    }
  },
};
