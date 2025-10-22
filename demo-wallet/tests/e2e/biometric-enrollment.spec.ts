import { test, expect } from '../fixtures/biometric-fixtures';
import {
  biometricAssertions,
  createMockEnrollmentRequest,
  GenerateRequest,
} from './utils/api-client';

const buildWallet = (char: string): string => `addr_test1qz${char.repeat(56)}`;

const regenerateRequest = (
  walletAddress: string,
  fingers: number,
  storage: 'inline' | 'external' = 'inline'
): GenerateRequest => createMockEnrollmentRequest(walletAddress, fingers, storage);

test.describe('Biometric Enrollment Flow', () => {
  test('enrolls three fingers with inline helper data', async ({ apiClient }) => {
    const request = regenerateRequest(buildWallet('x'), 3, 'inline');

    const response = await apiClient.generate(request);

    biometricAssertions.assertValidDid(response.did);
    biometricAssertions.assertValidHelpers(response.helpers!, ['finger_1', 'finger_2', 'finger_3']);

    const metadata = response.metadata_cip30_inline;
    biometricAssertions.assertValidMetadata(metadata, 'inline');
    biometricAssertions.assertValidHelperData(metadata.biometric.helperData, 'inline');
  });

  test('supports external helper storage', async ({ apiClient }) => {
    const request = regenerateRequest(buildWallet('b'), 3, 'external');

    const response = await apiClient.generate(request);

    const metadata = response.metadata_cip30_inline;
    biometricAssertions.assertValidMetadata(metadata, 'external');
    biometricAssertions.assertValidHelperData(metadata.biometric.helperData, 'external');

    expect(Object.keys(response.helpers!)).toEqual(['finger_1', 'finger_2', 'finger_3']);
  });

  test('returns deterministic DID for identical payloads', async ({ apiClient }) => {
    const walletAddress = buildWallet('c');

    const first = await apiClient.generate(regenerateRequest(walletAddress, 3, 'inline'));
    const second = await apiClient.generate(regenerateRequest(walletAddress, 3, 'inline'));

    expect(second.did).toBe(first.did);
    expect(second.metadata_cip30_inline.biometric.idHash).toBe(first.metadata_cip30_inline.biometric.idHash);
  });

  test('produces unique DIDs for different wallets', async ({ apiClient }) => {
    const alpha = await apiClient.generate(regenerateRequest(buildWallet('d'), 3, 'inline'));
    const beta = await apiClient.generate(regenerateRequest(buildWallet('e'), 3, 'inline'));

    expect(alpha.did).not.toBe(beta.did);
    expect(alpha.metadata_cip30_inline.biometric.idHash).not.toBe(beta.metadata_cip30_inline.biometric.idHash);
  });

  test('exposes CIP-30 v1.1 metadata fields', async ({ apiClient }) => {
    const walletAddress = buildWallet('f');
    const response = await apiClient.generate(regenerateRequest(walletAddress, 3, 'inline'));

    const metadata = response.metadata_cip30_inline;
    biometricAssertions.assertValidMetadata(metadata, 'inline');

    expect(metadata.controllers).toContain(walletAddress);
    expect(metadata.enrollmentTimestamp).toBeTruthy();
    expect(metadata.revoked).toBe(false);
  });

  test('includes helper data per enrolled finger', async ({ apiClient }) => {
    const response = await apiClient.generate(regenerateRequest(buildWallet('g'), 4, 'inline'));

    biometricAssertions.assertValidHelpers(response.helpers!, ['finger_1', 'finger_2', 'finger_3', 'finger_4']);
    Object.values(response.helpers!).forEach(helper => {
      expect(helper.salt_b64.length).toBeGreaterThan(0);
      expect(helper.auth_b64.length).toBeGreaterThan(0);
    });
  });
});

test.describe('Biometric Enrollment Performance', () => {
  test('completes single enrollment within five seconds', async ({ apiClient }) => {
    const request = regenerateRequest(buildWallet('h'), 3, 'inline');

    const start = Date.now();
    const response = await apiClient.generate(request);
    const duration = Date.now() - start;

    biometricAssertions.assertValidDid(response.did);
    expect(duration).toBeLessThan(5000);
  });

  test('handles concurrent enrollments', async ({ apiClient }) => {
    const requests = Array.from({ length: 5 }, (_, index) =>
      regenerateRequest(buildWallet(String(index)), 3, 'inline')
    );

    const responses = await Promise.all(requests.map(request => apiClient.generate(request)));

    expect(responses).toHaveLength(5);
    const dids = responses.map(result => result.did);
    expect(new Set(dids).size).toBe(responses.length);
  });
});
