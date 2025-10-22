/**
 * Playwright Test Fixtures for E2E Testing
 *
 * Provides reusable test fixtures with WebAuthn mocking and API client.
 */

import { test as base, expect } from '@playwright/test';
import { WebAuthnMock } from '../mocks/webauthn-mock';
import { BiometricApiClient, waitForApiReady } from '../utils/api-client';

// Extend test fixtures
type TestFixtures = {
  webauthnMock: WebAuthnMock;
  apiClient: BiometricApiClient;
  enrolledFingers: Map<string, any>;
};

export const test = base.extend<TestFixtures>({
  // WebAuthn mock fixture
  webauthnMock: async ({ page }, use) => {
    const mock = new WebAuthnMock();
    await mock.install(page);
    await use(mock);
    await mock.clearEnrollments(page);
  },

  // API client fixture
  apiClient: async ({ }, use) => {
    const apiUrl = process.env.API_URL || 'http://localhost:8000';

    // Wait for API to be ready
    const isReady = await waitForApiReady(apiUrl, 30, 1000);
    if (!isReady) {
      throw new Error('API is not ready after 30 seconds');
    }

    const client = new BiometricApiClient({ baseUrl: apiUrl });

    // Verify API health
    await client.checkHealth();

    await use(client);
  },

  // Enrolled fingers storage fixture
  enrolledFingers: async ({ }, use) => {
    const storage = new Map<string, any>();
    await use(storage);
    storage.clear();
  },
});

export { expect };

/**
 * Custom assertions for biometric testing
 */
export const biometricAssertions = {
  /**
   * Assert DID format is valid
   */
  assertValidDid(did: string) {
    expect(did).toMatch(/^did:cardano:[a-zA-Z0-9_-]+$/);
  },

  /**
   * Assert metadata structure is valid (CIP-30 v1.1 mock)
   */
  assertValidMetadata(metadata: any, expectedStorage: 'inline' | 'external') {
    expect(metadata).toBeDefined();
    expect(metadata).toHaveProperty('version');
    expect(metadata.version).toBe('1.1');
    expect(Array.isArray(metadata.controllers)).toBe(true);
    expect(metadata.controllers.length).toBeGreaterThan(0);
    expect(metadata).toHaveProperty('enrollmentTimestamp');
    expect(metadata).toHaveProperty('walletAddress');
    expect(metadata).toHaveProperty('biometric');

    const biometric = metadata.biometric;
    expect(biometric).toHaveProperty('idHash');
    expect(typeof biometric.idHash).toBe('string');
    expect(biometric).toHaveProperty('helperStorage');
    expect(biometric.helperStorage).toBe(expectedStorage);

    if (expectedStorage === 'inline') {
      expect(biometric.helperData).toBeTruthy();
    } else {
      expect(biometric.helperData).toBeNull();
    }
  },

  /**
   * Assert helper data structure is valid
   */
  assertValidHelperData(helpers: Record<string, any>, expectedFingers: string[]) {
    expect(Object.keys(helpers).sort()).toEqual(expectedFingers.sort());

    for (const [fingerId, helper] of Object.entries(helpers)) {
      expect(helper).toHaveProperty('salt_b64');
      expect(helper).toHaveProperty('auth_b64');
      expect(typeof helper.salt_b64).toBe('string');
      expect(typeof helper.auth_b64).toBe('string');
    }
  },

  /**
   * Assert verification response is valid
   */
  assertValidVerification(
    response: any,
    expectedVerified: boolean,
    expectedMatchedCount: number
  ) {
    expect(response.success).toBe(expectedVerified);
    expect(response.matched_fingers).toHaveLength(expectedMatchedCount);

    if (expectedVerified) {
      expect(response.error ?? null).toBeFalsy();
    }
  },
};
