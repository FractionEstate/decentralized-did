import { test, expect } from '../fixtures/biometric-fixtures';
import {
  addMinutiaeNoise,
  biometricAssertions,
  createMockEnrollmentRequest,
  createMockFingerData,
  GenerateRequest,
} from './utils/api-client';

const buildWallet = (char: string): string => `addr_test1qz${char.repeat(56)}`;

const regenerateRequest = (
  walletAddress: string,
  fingers: number,
  storage: 'inline' | 'external' = 'inline'
): GenerateRequest => createMockEnrollmentRequest(walletAddress, fingers, storage);

test.describe('Biometric Verification Flow', () => {
  let enrollmentResponse: any;
  const enrolledFingers = ['finger_1', 'finger_2', 'finger_3'] as const;

  test.beforeEach(async ({ apiClient }) => {
    const walletAddress = buildWallet('v');
    enrollmentResponse = await (apiClient as any).generate(
      regenerateRequest(walletAddress, enrolledFingers.length, 'inline')
    );
  });

  test('verifies when two fingers match', async ({ apiClient }) => {
    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 2);
    const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 2);

    const verificationRequest = {
      fingers: [finger1, finger2],
      helpers: {
        finger_1: enrollmentResponse.helpers.finger_1,
        finger_2: enrollmentResponse.helpers.finger_2,
      },
      expected_id_hash: enrollmentResponse.id_hash,
    };

    const response = await (apiClient as any).verify(verificationRequest);

    biometricAssertions.assertValidVerification(response as any, true, 2);
    expect(response.unmatched_fingers).toEqual([]);
  });

  test('fails when helper hash mismatches', async ({ apiClient }) => {
    const otherWallet = buildWallet('w');
    const foreignEnrollment = await apiClient.generate(
      regenerateRequest(otherWallet, enrolledFingers.length, 'inline')
    );

    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 2);
    const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 2);

    const verificationRequest = {
      fingers: [finger1, finger2],
      helpers: foreignEnrollment.helpers,
      expected_id_hash: enrollmentResponse.id_hash,
    };

    const response = await (apiClient as any).verify(verificationRequest);

    expect(response.success).toBe(false);
    expect(response.error).toBe('Helper data hash mismatch');
  });

  test('reports unmatched fingers', async ({ apiClient }) => {
    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 2);
    const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 2);
    const fakeFinger = createMockFingerData('finger_99');

    const verificationRequest = {
      fingers: [finger1, finger2, fakeFinger],
      helpers: {
        finger_1: enrollmentResponse.helpers.finger_1,
        finger_2: enrollmentResponse.helpers.finger_2,
      },
      expected_id_hash: enrollmentResponse.id_hash,
    };

    const response = await (apiClient as any).verify(verificationRequest);

    expect(response.success).toBe(false);
    expect(response.unmatched_fingers).toContain('finger_99');
  });

  test('requires at least two matching fingers', async ({ apiClient }) => {
    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 2);

    const verificationRequest = {
      fingers: [finger1],
      helpers: {
        finger_1: enrollmentResponse.helpers.finger_1,
      },
      expected_id_hash: enrollmentResponse.id_hash,
    };

    const response = await (apiClient as any).verify(verificationRequest);

    expect(response.success).toBe(false);
    expect(response.error).toBe('Insufficient matching fingerprints');
  });
});

test.describe('Biometric Verification Performance', () => {
  test('completes verification within three seconds', async ({ apiClient }) => {
    const request = regenerateRequest(buildWallet('p'), 3, 'inline');
    const enrollment = await (apiClient as any).generate(request);

    const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 2);
    const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 2);

    const start = Date.now();
    const verificationRequest = {
      fingers: [finger1, finger2],
      helpers: {
        finger_1: enrollment.helpers.finger_1,
        finger_2: enrollment.helpers.finger_2,
      },
      expected_id_hash: enrollment.id_hash,
    };

    const response = await (apiClient as any).verify(verificationRequest);
    const duration = Date.now() - start;

    biometricAssertions.assertValidVerification(response as any, true, 2);
    expect(duration).toBeLessThan(3000);
  });

  test('handles concurrent verifications', async ({ apiClient }) => {
    const enrollment = await (apiClient as any).generate(regenerateRequest(buildWallet('q'), 3, 'inline'));

    const verifications = Array.from({ length: 5 }, () => {
      const finger1 = addMinutiaeNoise(createMockFingerData('finger_1'), 2);
      const finger2 = addMinutiaeNoise(createMockFingerData('finger_2'), 2);

      const verificationRequest = {
        fingers: [finger1, finger2],
        helpers: {
          finger_1: enrollment.helpers.finger_1,
          finger_2: enrollment.helpers.finger_2,
        },
        expected_id_hash: enrollment.id_hash,
      };

      return (apiClient as any).verify(verificationRequest);
    });

    const responses = await Promise.all(verifications);
    responses.forEach(result => biometricAssertions.assertValidVerification(result as any, true, 2));
  });
});
