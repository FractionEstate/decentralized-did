/**
 * Biometric Test Fixtures
 *
 * Provides mock biometric data and Playwright test fixtures for E2E testing
 */

import { test as base, expect } from '@playwright/test';
import { ApiClient, createApiClient } from '../utils/api-client';

export interface BiometricFixture {
  userId: string;
  fingerIndex: number;
  template: string; // Base64 encoded mock template
  quality: number;
}

export interface EnrollmentFixture {
  userId: string;
  templates: BiometricFixture[];
  helperData: string;
  publicKey: string;
}

/**
 * Extend Playwright test with API client fixture
 */
export const test = base.extend<{ apiClient: ApiClient }>({
  apiClient: async ({ }, use) => {
    const client = createApiClient();

    // Verify API is available before running tests
    try {
      await client.healthCheck();
    } catch (error) {
      console.error('API health check failed. Is the backend running?');
      throw error;
    }

    await use(client);
  },
});

export { expect };/**
 * Generate mock biometric template
 */
export function generateMockTemplate(userId: string, fingerIndex: number): BiometricFixture {
  // Generate deterministic but unique template for testing
  const mockData = `${userId}-finger-${fingerIndex}-${Date.now()}`;
  const template = Buffer.from(mockData).toString('base64');

  return {
    userId,
    fingerIndex,
    template,
    quality: 85 + Math.floor(Math.random() * 15), // 85-100 quality
  };
}

/**
 * Generate complete enrollment fixture with 3 fingers
 */
export function generateEnrollmentFixture(userId: string): EnrollmentFixture {
  const templates = [
    generateMockTemplate(userId, 0), // Right index
    generateMockTemplate(userId, 1), // Right middle
    generateMockTemplate(userId, 2), // Right thumb
  ];

  // Generate mock helper data (normally from fuzzy extractor)
  const helperData = Buffer.from(`helper-${userId}-${Date.now()}`).toString('base64');

  // Generate mock public key
  const publicKey = Buffer.from(`pubkey-${userId}`).toString('base64');

  return {
    userId,
    templates,
    helperData,
    publicKey,
  };
}

/**
 * Pre-defined fixtures for common test scenarios
 */
export const FIXTURES = {
  validUser: generateEnrollmentFixture('test-user-valid'),
  invalidUser: generateEnrollmentFixture('test-user-invalid'),
  lowQuality: {
    ...generateEnrollmentFixture('test-user-low-quality'),
    templates: [
      { userId: 'test-user-low-quality', fingerIndex: 0, template: 'low1', quality: 45 },
      { userId: 'test-user-low-quality', fingerIndex: 1, template: 'low2', quality: 50 },
      { userId: 'test-user-low-quality', fingerIndex: 2, template: 'low3', quality: 48 },
    ],
  },
};

/**
 * Wait for biometric capture simulation
 */
export async function simulateBiometricCapture(page: any, fingerIndex: number): Promise<void> {
  // Simulate the capture delay
  await page.waitForTimeout(2000);

  // Click the capture button or trigger capture
  const captureButton = page.locator(`[data-testid="capture-finger-${fingerIndex}"]`);
  if (await captureButton.isVisible()) {
    await captureButton.click();
  }

  // Wait for success indicator
  await page.waitForSelector(`[data-testid="finger-${fingerIndex}-success"]`, {
    timeout: 5000,
  });
}

/**
 * Complete full 3-finger enrollment
 */
export async function completeEnrollment(page: any): Promise<void> {
  for (let i = 0; i < 3; i++) {
    await simulateBiometricCapture(page, i);

    // Small delay between fingers
    await page.waitForTimeout(500);
  }

  // Wait for enrollment completion
  await page.waitForSelector('[data-testid="enrollment-complete"]', {
    timeout: 10000,
  });
}
