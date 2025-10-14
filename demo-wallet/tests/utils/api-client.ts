/**
 * API Client for E2E Tests
 *
 * Provides utilities for interacting with backend API during E2E tests
 */

export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
}

export interface EnrollmentRequest {
  wallet_address: string;
  finger_count: number;
  helper_mode: 'inline' | 'external';
  finger_data: Array<{
    finger_index: number;
    template: string;
    quality_score: number;
  }>;
}

export interface DidResponse {
  did: string;
  document: any;
  helper_data: string | null;
  helper_cid: string | null;
  audit_log: any[];
  // New fields for deterministic DID support
  helpers?: Record<string, {
    finger_id: string;
    salt_b64: string;
    auth_b64: string;
    grid_size?: number;
    angle_bins?: number;
  }>;
  wallet_bundle?: {
    version: number;
    controllers?: string[];
    enrollmentTimestamp?: string;
    revoked?: boolean;
    payment_addr?: string;
    helper_data?: any;
    [key: string]: any;
  };
  metadata_cip30_inline?: any;
  metadata_cip30_external?: any;
}

export class ApiClient {
  private baseURL: string;
  private timeout: number;

  constructor(config: ApiClientConfig) {
    this.baseURL = config.baseURL;
    this.timeout = config.timeout || 30000;
  }

  /**
   * Make API request
   */
  private async request<T>(
    method: string,
    path: string,
    body?: any
  ): Promise<T> {
    const url = `${this.baseURL}${path}`;

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error ${response.status}: ${error}`);
    }

    return response.json();
  }

  /**
   * Health check
   */
  async checkHealth(): Promise<{ status: string }> {
    return this.request('GET', '/api/health');
  }

  /**
   * Generate DID from enrollment
   */
  async generate(data: EnrollmentRequest): Promise<DidResponse> {
    return this.request('POST', '/api/v2/did/generate', data);
  }

  /**
   * Verify biometric data against DID
   */
  async verify(data: {
    did: string;
    helper_data: string;
    finger_data: {
      finger_index: number;
      template: string;
    };
  }): Promise<{
    success: boolean;
    match: boolean;
    confidence?: number;
    recovered_key?: string;
  }> {
    return this.request('POST', '/api/v2/did/verify', data);
  }

  /**
   * Create wallet with biometric DID
   */
  async createWallet(data: {
    user_id: string;
    helper_data: string;
    public_key: string;
    seed_phrase: string[];
  }): Promise<{
    success: boolean;
    wallet_address?: string;
    did?: string;
    error?: string;
  }> {
    return this.request('POST', '/api/v2/wallet/create', data);
  }

  /**
   * Get wallet status
   */
  async getWalletStatus(userId: string): Promise<{
    exists: boolean;
    wallet_address?: string;
    did?: string;
  }> {
    return this.request('GET', `/api/v2/wallet/${userId}/status`);
  }

  /**
   * Clean up test data
   */
  async cleanup(userId: string): Promise<void> {
    try {
      await this.request('DELETE', `/api/v2/test/cleanup/${userId}`);
    } catch (error) {
      // Ignore cleanup errors
      console.warn(`Cleanup failed for ${userId}:`, error);
    }
  }

  /**
   * Reset test environment
   */
  async resetTestEnvironment(): Promise<void> {
    try {
      await this.request('POST', '/api/v2/test/reset');
    } catch (error) {
      console.warn('Test environment reset failed:', error);
    }
  }
}

/**
 * Create mock finger data for testing
 */
export function createMockFingerData(fingerIndex: number, quality: number = 90): {
  finger_index: number;
  template: string;
  quality_score: number;
} {
  // Generate deterministic mock template
  const mockData = `mock-finger-${fingerIndex}-${Date.now()}`;
  const template = Buffer.from(mockData).toString('base64');

  return {
    finger_index: fingerIndex,
    template,
    quality_score: quality,
  };
}

/**
 * Create mock enrollment request for testing
 */
export function createMockEnrollmentRequest(
  walletAddress: string,
  fingerCount: number = 3,
  helperMode: 'inline' | 'external' = 'inline'
): EnrollmentRequest {
  const fingerData = [];

  for (let i = 0; i < fingerCount; i++) {
    fingerData.push(createMockFingerData(i));
  }

  return {
    wallet_address: walletAddress,
    finger_count: fingerCount,
    helper_mode: helperMode,
    finger_data: fingerData,
  };
}

/**
 * Create API client from environment
 */
export function createApiClient(): ApiClient {
  const baseURL = process.env.API_URL || 'http://localhost:8000';

  return new ApiClient({
    baseURL,
    timeout: 30000,
  });
}

/**
 * Biometric assertions for tests
 */
export const biometricAssertions = {
  /**
   * Assert DID format is valid
   * Supports both deterministic (did:cardano:{network}:{hash}) and legacy (did:cardano:{addr}#{hash}) formats
   */
  assertValidDid(did: string): void {
    if (!did || !did.startsWith('did:cardano:')) {
      throw new Error(`Invalid DID format: ${did}. Expected did:cardano:*`);
    }

    // Validate deterministic format: did:cardano:mainnet:zQmHash or did:cardano:testnet:zQmHash
    const deterministicPattern = /^did:cardano:(mainnet|testnet|preprod):[a-zA-Z0-9]+$/;
    // Validate legacy format: did:cardano:addr...#hash (deprecated)
    const legacyPattern = /^did:cardano:addr[a-z0-9_]+#[a-f0-9]+$/;

    if (!deterministicPattern.test(did) && !legacyPattern.test(did)) {
      throw new Error(
        `Invalid DID structure: ${did}. ` +
        `Expected deterministic format (did:cardano:{network}:{hash}) ` +
        `or legacy format (did:cardano:{addr}#{hash})`
      );
    }
  },

  /**
   * Assert helper data exists and is valid
   */
  assertValidHelperData(helperData: string | null, mode: 'inline' | 'external'): void {
    if (mode === 'inline') {
      if (!helperData) {
        throw new Error('Helper data should be present in inline mode');
      }
    } else {
      if (helperData) {
        throw new Error('Helper data should be null in external mode');
      }
    }
  },

  /**
   * Assert wallet bundle structure (metadata v1.1)
   */
  assertValidWalletBundle(bundle: any): void {
    if (!bundle) {
      throw new Error('Wallet bundle should be present');
    }

    // Check metadata v1.1 structure
    if (bundle.version !== 1.1 && bundle.version !== 1) {
      throw new Error(`Unexpected metadata version: ${bundle.version}`);
    }

    // For v1.1, check new fields
    if (bundle.version === 1.1) {
      if (!Array.isArray(bundle.controllers)) {
        throw new Error('Metadata v1.1 should have controllers array');
      }
      if (!bundle.enrollmentTimestamp) {
        throw new Error('Metadata v1.1 should have enrollmentTimestamp');
      }
      if (typeof bundle.revoked !== 'boolean') {
        throw new Error('Metadata v1.1 should have revoked boolean field');
      }
    }
  },

  /**
   * Assert helper data per finger
   */
  assertValidHelpers(helpers: Record<string, any>, expectedFingers: string[]): void {
    if (!helpers || typeof helpers !== 'object') {
      throw new Error('Helpers should be an object');
    }

    const actualFingers = Object.keys(helpers);
    if (actualFingers.length !== expectedFingers.length) {
      throw new Error(
        `Expected ${expectedFingers.length} fingers, got ${actualFingers.length}`
      );
    }

    for (const finger of expectedFingers) {
      if (!helpers[finger]) {
        throw new Error(`Missing helper data for finger: ${finger}`);
      }

      const helper = helpers[finger];
      if (!helper.salt_b64 || !helper.auth_b64) {
        throw new Error(`Invalid helper data structure for ${finger}`);
      }
    }
  },

  /**
   * Assert verification response
   */
  assertValidVerification(
    response: any,
    expectedSuccess: boolean,
    minMatchedFingers: number = 2
  ): void {
    if (typeof response.success !== 'boolean') {
      throw new Error('Verification response should have success boolean');
    }

    if (response.success !== expectedSuccess) {
      throw new Error(
        `Expected verification success=${expectedSuccess}, got ${response.success}`
      );
    }

    if (expectedSuccess) {
      if (!Array.isArray(response.matched_fingers)) {
        throw new Error('Successful verification should have matched_fingers array');
      }

      if (response.matched_fingers.length < minMatchedFingers) {
        throw new Error(
          `Expected at least ${minMatchedFingers} matched fingers, ` +
          `got ${response.matched_fingers.length}`
        );
      }
    }
  },

  /**
   * Assert audit log structure
   */
  assertAuditLog(auditLog: any[]): void {
    if (!Array.isArray(auditLog) || auditLog.length === 0) {
      throw new Error('Audit log should be a non-empty array');
    }

    const firstEntry = auditLog[0];
    if (!firstEntry.timestamp || !firstEntry.action) {
      throw new Error('Audit log entries should have timestamp and action');
    }
  },
};
