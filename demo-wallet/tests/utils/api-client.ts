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
   */
  assertValidDid(did: string): void {
    if (!did || !did.startsWith('did:key:')) {
      throw new Error(`Invalid DID format: ${did}`);
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
