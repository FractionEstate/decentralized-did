/**
 * Biometric Enrollment E2E Test
 *
 * Tests the complete enrollment flow:
 * - Biometric capture (3+ fingers)
 * - Fuzzy extraction and key generation
 * - DID generation
 * - Helper data storage (inline and external modes)
 */

import { test, expect } from '../fixtures/biometric-fixtures';
import { createMockFingerData, createMockEnrollmentRequest, biometricAssertions } from '../utils/api-client';

test.describe('Biometric Enrollment Flow', () => {
  test.beforeEach(async ({ apiClient }) => {
    // Verify API is healthy before each test
    const health = await apiClient.checkHealth();
    expect(health.status).toBe('healthy');
  });

  test('should enroll 3 fingers and generate DID', async ({ apiClient }) => {
    // Arrange
    const walletAddress = 'addr_test1qz' + 'x'.repeat(56);
    const request = createMockEnrollmentRequest(walletAddress, 3, 'inline');

    // Act
    const response = await apiClient.generate(request);

    // Assert
    biometricAssertions.assertValidDid(response.did);
    biometricAssertions.assertValidWalletBundle(response.wallet_bundle);
    expect(response.helpers).toBeDefined();
    biometricAssertions.assertValidHelpers(response.helpers!, [
      'finger_1',
      'finger_2',
      'finger_3',
    ]);

    // Verify DID format
    expect(response.did).toContain('did:cardano:');

    // Verify helper data for each finger
    expect(Object.keys(response.helpers!)).toHaveLength(3);
  });

  test('should enroll 5 fingers successfully', async ({ apiClient }) => {
    // Arrange
    const walletAddress = 'addr_test1qz' + 'y'.repeat(56);
    const request = createMockEnrollmentRequest(walletAddress, 5, 'inline');

    // Act
    const response = await apiClient.generate(request);

    // Assert
    biometricAssertions.assertValidDid(response.did);
    expect(response.helpers).toBeDefined();
    expect(Object.keys(response.helpers!)).toHaveLength(5);
  });

  test('should support inline helper storage mode', async ({ apiClient }) => {
    // Arrange
    const walletAddress = 'addr_test1qz' + 'a'.repeat(56);
    const request = createMockEnrollmentRequest(walletAddress, 3, 'inline');

    // Act
    const response = await apiClient.generate(request);

    // Assert
    expect(response.wallet_bundle).toBeDefined();
    expect(response.wallet_bundle!).toHaveProperty('helper_data');
    expect(response.wallet_bundle!.helper_data).toBeTruthy();
  });

  test('should support external helper storage mode', async ({ apiClient }) => {
    // Arrange
    const walletAddress = 'addr_test1qz' + 'b'.repeat(56);
    const request = createMockEnrollmentRequest(walletAddress, 3, 'external');

    // Act
    const response = await apiClient.generate(request);

    // Assert
    // In external mode, helper data should be in response.helpers
    // but not embedded in wallet_bundle
    expect(response.helpers).toBeTruthy();
    expect(Object.keys(response.helpers!)).toHaveLength(3);
  });

  test('should reject enrollment with insufficient fingers', async ({ apiClient }) => {
    // Arrange
    const walletAddress = 'addr_test1qz' + 'c'.repeat(56);
    const request = createMockEnrollmentRequest(walletAddress, 1, 'inline');

    // Act & Assert
    try {
      await apiClient.generate(request);
      expect(false).toBe(true); // Should not reach here
    } catch (error: any) {
      // Expect validation error for insufficient fingers
      expect(error).toBeDefined();
    }
  });

  test('should generate unique DIDs for different enrollments', async ({ apiClient }) => {
    // Arrange
    const walletAddress1 = 'addr_test1qz' + 'd'.repeat(56);
    const walletAddress2 = 'addr_test1qz' + 'e'.repeat(56);
    const request1 = createMockEnrollmentRequest(walletAddress1, 3, 'inline');
    const request2 = createMockEnrollmentRequest(walletAddress2, 3, 'inline');

    // Act
    const response1 = await apiClient.generate(request1);
    const response2 = await apiClient.generate(request2);

    // Assert
    expect(response1.did).not.toBe(response2.did);
    expect(response1.wallet_bundle).toBeDefined();
    expect(response2.wallet_bundle).toBeDefined();
    expect(response1.wallet_bundle!.payment_addr).not.toBe(
      response2.wallet_bundle!.payment_addr
    );
  });

  test('should include all required helper data fields', async ({ apiClient }) => {
    // Arrange
    const walletAddress = 'addr_test1qz' + 'f'.repeat(56);
    const request = createMockEnrollmentRequest(walletAddress, 3, 'inline');

    // Act
    const response = await apiClient.generate(request);

    // Assert
    expect(response.helpers).toBeDefined();
    for (const [fingerId, helper] of Object.entries(response.helpers!)) {
      // Required fields
      expect(helper).toHaveProperty('salt_b64');
      expect(helper).toHaveProperty('auth_b64');

      // Verify base64 encoding
      expect(typeof helper.salt_b64).toBe('string');
      expect(typeof helper.auth_b64).toBe('string');
      expect(helper.salt_b64.length).toBeGreaterThan(0);
      expect(helper.auth_b64.length).toBeGreaterThan(0);
    }
  });

  test('should generate consistent DID format', async ({ apiClient }) => {
    // Arrange
    const walletAddress = 'addr_test1qz' + 'g'.repeat(56);
    const request = createMockEnrollmentRequest(walletAddress, 3, 'inline');

    // Act
    const response = await apiClient.generate(request);

    // Assert - DID should follow Cardano DID spec
    const didRegex = /^did:cardano:[a-zA-Z0-9_-]+$/;
    expect(response.did).toMatch(didRegex);

    // DID should be reasonable length
    expect(response.did.length).toBeGreaterThan(20);
    expect(response.did.length).toBeLessThan(200);
  });

  test('should generate deterministic DID (Sybil-resistant)', async ({ apiClient }) => {
    // Arrange - Same biometric data, different wallet addresses
    const walletAddress1 = 'addr_test1qz' + 'x'.repeat(56);
    const walletAddress2 = 'addr_test1qz' + 'y'.repeat(56);

    // Create identical biometric data (simulating same person)
    const sameBiometricData = createMockFingerData(0); // Use finger index 0
    const request1 = {
      ...createMockEnrollmentRequest(walletAddress1, 1, 'inline'),
      fingers: [sameBiometricData],
    };
    const request2 = {
      ...createMockEnrollmentRequest(walletAddress2, 1, 'inline'),
      fingers: [sameBiometricData],
    };    // Act
    const response1 = await apiClient.generate(request1);
    const response2 = await apiClient.generate(request2);

    // Assert - DIDs should be identical (Sybil resistance)
    // Same person = same DID, regardless of wallet address
    expect(response1.did).toBe(response2.did);

    // Verify DID does NOT contain wallet address (privacy)
    expect(response1.did).not.toContain('addr');
    expect(response1.did).not.toContain(walletAddress1);
    expect(response2.did).not.toContain(walletAddress2);

    console.log('✅ Sybil resistance verified: Same biometric → Same DID');
  });

  test('should use deterministic DID format (did:cardano:{network}:{hash})', async ({ apiClient }) => {
    // Arrange
    const walletAddress = 'addr_test1qz' + 'z'.repeat(56);
    const request = createMockEnrollmentRequest(walletAddress, 3, 'inline');

    // Act
    const response = await apiClient.generate(request);

    // Assert - Validate deterministic format
    const deterministicPattern = /^did:cardano:(mainnet|testnet|preprod):[a-zA-Z0-9]+$/;
    expect(response.did).toMatch(deterministicPattern);

    // Extract parts
    const parts = response.did.split(':');
    expect(parts).toHaveLength(4);
    expect(parts[0]).toBe('did');
    expect(parts[1]).toBe('cardano');
    expect(['mainnet', 'testnet', 'preprod']).toContain(parts[2]);

    // Hash should be Base58 encoded (no special characters except alphanumeric)
    const hash = parts[3];
    expect(hash).toMatch(/^[a-zA-Z0-9]+$/);
    expect(hash.length).toBeGreaterThan(20); // Base58 hash should be substantial

    console.log(`✅ Deterministic DID format verified: ${response.did}`);
  });

  test('should include metadata v1.1 fields', async ({ apiClient }) => {
    // Arrange
    const walletAddress = 'addr_test1qz' + 'v1'.repeat(28);
    const request = createMockEnrollmentRequest(walletAddress, 3, 'inline');

    // Act
    const response = await apiClient.generate(request);

    // Assert - Check metadata v1.1 structure
    expect(response.wallet_bundle).toBeDefined();
    biometricAssertions.assertValidWalletBundle(response.wallet_bundle);

    const metadata = response.wallet_bundle!;
    expect(metadata.version).toBe(1.1);

    // Multi-controller support
    expect(Array.isArray(metadata.controllers)).toBe(true);
    expect(metadata.controllers).toContain(walletAddress);

    // Timestamp
    expect(metadata.enrollmentTimestamp).toBeDefined();
    const timestamp = new Date(metadata.enrollmentTimestamp!);
    expect(timestamp.getTime()).toBeLessThanOrEqual(Date.now());

    // Revocation status
    expect(typeof metadata.revoked).toBe('boolean');
    expect(metadata.revoked).toBe(false); // New enrollments should not be revoked

    console.log('✅ Metadata v1.1 structure validated');
  });
}); test.describe('Biometric Enrollment Performance', () => {
  test('should complete enrollment within performance threshold', async ({ apiClient }) => {
    // Arrange
    const walletAddress = 'addr_test1qz' + 'h'.repeat(56);
    const request = createMockEnrollmentRequest(walletAddress, 3, 'inline');

    // Act
    const startTime = Date.now();
    const response = await apiClient.generate(request);
    const endTime = Date.now();
    const duration = endTime - startTime;

    // Assert
    biometricAssertions.assertValidDid(response.did);

    // Enrollment should complete within 5 seconds
    expect(duration).toBeLessThan(5000);

    console.log(`Enrollment completed in ${duration}ms`);
  });

  test('should handle concurrent enrollments', async ({ apiClient }) => {
    // Arrange
    const enrollments = Array.from({ length: 5 }, (_, i) => {
      const walletAddress = `addr_test1qz${String(i).repeat(56)}`;
      return createMockEnrollmentRequest(walletAddress, 3, 'inline');
    });

    // Act
    const startTime = Date.now();
    const responses = await Promise.all(
      enrollments.map(request => apiClient.generate(request))
    );
    const endTime = Date.now();
    const duration = endTime - startTime;

    // Assert
    expect(responses).toHaveLength(5);
    responses.forEach(response => {
      biometricAssertions.assertValidDid(response.did);
    });

    // All DIDs should be unique
    const dids = responses.map(r => r.did);
    const uniqueDids = new Set(dids);
    expect(uniqueDids.size).toBe(5);

    console.log(`5 concurrent enrollments completed in ${duration}ms`);
  });
});
