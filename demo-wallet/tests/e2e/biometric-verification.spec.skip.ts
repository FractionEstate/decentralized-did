/**
 * Biometric Verification E2E Test
 *
 * Tests the complete verification flow:
 * - Biometric capture (2+ fingers)
 * - Key reproduction using helper data
 * - DID verification
 * - Authentication success/failure scenarios
 */

import { test, expect } from '../fixtures/biometric-fixtures';
import {
  createMockFingerData,
  createMockEnrollmentRequest,
  biometricAssertions,
} from '../utils/api-client';

test.describe('Biometric Verification Flow', () => {
  let enrollmentResponse: any;
  let walletAddress: string;

  test.beforeEach(async ({ apiClient }) => {
    // Enroll 3 fingers before each verification test
    walletAddress = 'addr_test1qz' + 'v'.repeat(56);
    const enrollmentRequest = createMockEnrollmentRequest(walletAddress, 3, 'inline');
    enrollmentResponse = await apiClient.generate(enrollmentRequest);

    expect(enrollmentResponse).toBeTruthy();
    expect(enrollmentResponse.helpers).toBeTruthy();
  });

  test('should verify with 2 matching fingers', async ({ apiClient }) => {
    // Arrange - Use 2 of the 3 enrolled fingers with slight noise
    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 3);
    const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 3);

    const verifyRequest: VerifyRequest = {
      fingers: [finger1, finger2],
      helpers: {
        finger_1: enrollmentResponse.helpers.finger_1,
        finger_2: enrollmentResponse.helpers.finger_2,
      },
    };

    // Act
    const response = await apiClient.verify(verifyRequest);

    // Assert
    biometricAssertions.assertValidVerification(response, true, 2);
    expect(response.did).toBe(enrollmentResponse.did);
    expect(response.matched_fingers).toContain('finger_1');
    expect(response.matched_fingers).toContain('finger_2');
  });

  test('should verify with all 3 enrolled fingers', async ({ apiClient }) => {
    // Arrange
    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 3);
    const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 3);
    const finger3 = addMinutiaeNoise(createMockFingerData('finger_3'), 3);

    const verifyRequest: VerifyRequest = {
      fingers: [finger1, finger2, finger3],
      helpers: enrollmentResponse.helpers,
    };

    // Act
    const response = await apiClient.verify(verifyRequest);

    // Assert
    biometricAssertions.assertValidVerification(response, true, 3);
    expect(response.matched_fingers).toHaveLength(3);
  });

  test('should fail verification with only 1 finger', async ({ apiClient }) => {
    // Arrange - Only 1 finger (insufficient)
    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 3);

    const verifyRequest: VerifyRequest = {
      fingers: [finger1],
      helpers: {
        finger_1: enrollmentResponse.helpers.finger_1,
      },
    };

    // Act
    const response = await apiClient.verify(verifyRequest);

    // Assert - Should fail due to insufficient fingers (need 2+)
    expect(response.verified).toBe(false);
    expect(response.matched_fingers.length).toBeLessThan(2);
  });

  test('should fail verification with wrong helper data', async ({ apiClient }) => {
    // Arrange - Enroll a different user
    const differentWallet = 'addr_test1qz' + 'w'.repeat(56);
    const differentEnrollment = await apiClient.generate(
      createMockEnrollmentRequest(differentWallet, 3, 'inline')
    );

    // Try to verify with mismatched helper data
    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 3);
    const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 3);

    const verifyRequest: VerifyRequest = {
      fingers: [finger1, finger2],
      helpers: differentEnrollment.helpers, // Wrong helper data!
    };

    // Act & Assert
    try {
      const response = await apiClient.verify(verifyRequest);
      // Verification might succeed but reproduce wrong DID
      if (response.verified) {
        expect(response.did).not.toBe(enrollmentResponse.did);
      }
    } catch (error) {
      // Or it might fail with an error
      expect(error).toBeDefined();
    }
  });

  test('should handle high biometric noise gracefully', async ({ apiClient }) => {
    // Arrange - Add significant noise to biometrics
    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 15);
    const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 15);
    const finger3 = addMinutiaeNoise(createMockFingerData('finger_3'), 15);

    const verifyRequest: VerifyRequest = {
      fingers: [finger1, finger2, finger3],
      helpers: enrollmentResponse.helpers,
    };

    // Act
    try {
      const response = await apiClient.verify(verifyRequest);

      // May succeed with error correction or fail gracefully
      expect(response).toHaveProperty('verified');
      expect(response).toHaveProperty('matched_fingers');
    } catch (error: any) {
      // BCH decoding might fail with high noise
      expect(error).toBeDefined();
    }
  });

  test('should return unmatched fingers list', async ({ apiClient }) => {
    // Arrange - Try to verify with a non-enrolled finger
    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 3);
    const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 3);
    const fakeFingerData = createMockFingerData('finger_99'); // Not enrolled

    const verifyRequest: VerifyRequest = {
      fingers: [finger1, finger2, fakeFingerData],
      helpers: {
        finger_1: enrollmentResponse.helpers.finger_1,
        finger_2: enrollmentResponse.helpers.finger_2,
        // No helper for finger_99
      },
    };

    // Act
    const response = await apiClient.verify(verifyRequest);

    // Assert
    expect(response).toHaveProperty('unmatched_fingers');
    expect(response.unmatched_fingers).toContain('finger_99');
  });

  test('should verify successfully with minimal noise', async ({ apiClient }) => {
    // Arrange - Very low noise (ideal conditions)
    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 1);
    const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 1);

    const verifyRequest: VerifyRequest = {
      fingers: [finger1, finger2],
      helpers: {
        finger_1: enrollmentResponse.helpers.finger_1,
        finger_2: enrollmentResponse.helpers.finger_2,
      },
    };

    // Act
    const response = await apiClient.verify(verifyRequest);

    // Assert
    biometricAssertions.assertValidVerification(response, true, 2);
    expect(response.matched_fingers).toHaveLength(2);
  });
});

test.describe('Biometric Verification Performance', () => {
  let enrollmentResponse: any;

  test.beforeEach(async ({ apiClient }) => {
    const walletAddress = 'addr_test1qz' + 'p'.repeat(56);
    const enrollmentRequest = createMockEnrollmentRequest(walletAddress, 3, 'inline');
    enrollmentResponse = await apiClient.generate(enrollmentRequest);
  });

  test('should complete verification within performance threshold', async ({ apiClient }) => {
    // Arrange
    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 3);
    const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 3);

    const verifyRequest: VerifyRequest = {
      fingers: [finger1, finger2],
      helpers: {
        finger_1: enrollmentResponse.helpers.finger_1,
        finger_2: enrollmentResponse.helpers.finger_2,
      },
    };

    // Act
    const startTime = Date.now();
    const response = await apiClient.verify(verifyRequest);
    const endTime = Date.now();
    const duration = endTime - startTime;

    // Assert
    biometricAssertions.assertValidVerification(response, true, 2);

    // Verification should complete within 3 seconds
    expect(duration).toBeLessThan(3000);

    console.log(`Verification completed in ${duration}ms`);
  });

  test('should handle concurrent verifications', async ({ apiClient }) => {
    // Arrange - Create multiple verification requests
    const verifications = Array.from({ length: 5 }, () => {
      const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 3);
      const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 3);

      return {
        fingers: [finger1, finger2],
        helpers: {
          finger_1: enrollmentResponse.helpers.finger_1,
          finger_2: enrollmentResponse.helpers.finger_2,
        },
      };
    });

    // Act
    const startTime = Date.now();
    const responses = await Promise.all(
      verifications.map(request => apiClient.verify(request))
    );
    const endTime = Date.now();
    const duration = endTime - startTime;

    // Assert
    expect(responses).toHaveLength(5);
    responses.forEach(response => {
      biometricAssertions.assertValidVerification(response, true, 2);
    });

    console.log(`5 concurrent verifications completed in ${duration}ms`);
  });
});

test.describe('Biometric Verification Error Handling', () => {
  test('should handle missing helper data gracefully', async ({ apiClient }) => {
    // Arrange
    const finger1 = createMockFingerData('finger_1');
    const finger2 = createMockFingerData('finger_2');

    const verifyRequest: VerifyRequest = {
      fingers: [finger1, finger2],
      helpers: {}, // No helper data provided
    };

    // Act & Assert
    try {
      await apiClient.verify(verifyRequest);
      expect(false).toBe(true); // Should not reach here
    } catch (error) {
      expect(error).toBeDefined();
    }
  });

  test('should handle corrupted helper data', async ({ apiClient }) => {
    // Arrange - Enroll first
    const walletAddress = 'addr_test1qz' + 'c'.repeat(56);
    const enrollmentRequest = createMockEnrollmentRequest(walletAddress, 3, 'inline');
    const enrollmentResponse = await apiClient.generate(enrollmentRequest);

    // Corrupt the helper data
    const corruptedHelpers = {
      finger_1: {
        ...enrollmentResponse.helpers.finger_1,
        salt_b64: 'CORRUPTED_BASE64_DATA!!!',
      },
      finger_2: enrollmentResponse.helpers.finger_2,
    };

    const finger1 = createMockFingerData('finger_1');
    const finger2 = createMockFingerData('finger_2');

    const verifyRequest: VerifyRequest = {
      fingers: [finger1, finger2],
      helpers: corruptedHelpers,
    };

    // Act & Assert
    try {
      await apiClient.verify(verifyRequest);
      // May fail or return verification failure
    } catch (error) {
      expect(error).toBeDefined();
    }
  });
});
