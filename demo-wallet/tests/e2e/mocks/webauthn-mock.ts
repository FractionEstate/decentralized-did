/**
 * WebAuthn Mock for E2E Testing
 *
 * Simulates biometric authentication for testing without real hardware.
 * Supports fingerprint enrollment and verification flows.
 */

import { Page } from '@playwright/test';

export interface MockBiometricData {
  fingerId: string;
  minutiae: number[]; // Simulated minutiae points
  quality: number; // 0-100
}

export interface MockCredential {
  id: string;
  rawId: ArrayBuffer;
  type: 'public-key';
  response: {
    clientDataJSON: ArrayBuffer;
    attestationObject: ArrayBuffer;
  };
}

/**
 * Mock WebAuthn API for testing
 */
export class WebAuthnMock {
  private enrolledBiometrics: Map<string, MockBiometricData> = new Map();
  private credentialCounter = 0;

  /**
   * Install WebAuthn mock into the page
   */
  async install(page: Page): Promise<void> {
    await page.addInitScript(() => {
      // Mock PublicKeyCredential
      (window as any).PublicKeyCredential = class MockPublicKeyCredential {
        static isUserVerifyingPlatformAuthenticatorAvailable() {
          return Promise.resolve(true);
        }

        static isConditionalMediationAvailable() {
          return Promise.resolve(true);
        }
      };

      // Store mock data in window for access
      (window as any).__webauthnMock = {
        enrolledBiometrics: new Map(),
        lastEnrollment: null,
        lastVerification: null,
      };

      // Mock navigator.credentials
      if (!navigator.credentials) {
        (navigator as any).credentials = {};
      }

      // Mock credentials.create (enrollment)
      (navigator.credentials as any).create = async (options: any) => {
        const mockData = (window as any).__webauthnMock;

        // Simulate biometric capture
        const fingerId = `finger_${Date.now()}`;
        const minutiae = Array.from({ length: 32 }, () => Math.floor(Math.random() * 256));
        const quality = 75 + Math.floor(Math.random() * 25); // 75-100

        const biometricData = {
          fingerId,
          minutiae,
          quality,
        };

        mockData.enrolledBiometrics.set(fingerId, biometricData);
        mockData.lastEnrollment = biometricData;

        // Create mock credential
        const credentialId = new Uint8Array(32);
        crypto.getRandomValues(credentialId);

        const clientDataJSON = new TextEncoder().encode(JSON.stringify({
          type: 'webauthn.create',
          challenge: Array.from(new Uint8Array(options.publicKey.challenge)),
          origin: window.location.origin,
        }));

        const attestationObject = new Uint8Array([
          ...Array.from(credentialId),
          ...minutiae,
        ]);

        return {
          id: Array.from(credentialId).map(b => b.toString(16).padStart(2, '0')).join(''),
          rawId: credentialId.buffer,
          type: 'public-key',
          response: {
            clientDataJSON: clientDataJSON.buffer,
            attestationObject: attestationObject.buffer,
            getPublicKey: () => new Uint8Array(65).buffer,
            getPublicKeyAlgorithm: () => -7,
            getTransports: () => ['internal'],
          },
        };
      };

      // Mock credentials.get (verification)
      (navigator.credentials as any).get = async (options: any) => {
        const mockData = (window as any).__webauthnMock;

        // Simulate biometric verification with slight noise
        const enrolledKeys = Array.from(mockData.enrolledBiometrics.keys());
        if (enrolledKeys.length === 0) {
          throw new Error('No enrolled biometrics');
        }

        const fingerId = enrolledKeys[0];
        const enrolled = mockData.enrolledBiometrics.get(fingerId);

        // Add noise to minutiae to simulate real-world variation
        const noisyMinutiae = enrolled.minutiae.map((val: number) => {
          const noise = Math.floor((Math.random() - 0.5) * 10);
          return Math.max(0, Math.min(255, val + noise));
        });

        const biometricData = {
          fingerId,
          minutiae: noisyMinutiae,
          quality: enrolled.quality - 5 + Math.floor(Math.random() * 10),
        };

        mockData.lastVerification = biometricData;

        const credentialId = new Uint8Array(32);
        crypto.getRandomValues(credentialId);

        const clientDataJSON = new TextEncoder().encode(JSON.stringify({
          type: 'webauthn.get',
          challenge: Array.from(new Uint8Array(options.publicKey.challenge)),
          origin: window.location.origin,
        }));

        const authenticatorData = new Uint8Array([
          ...Array.from(credentialId),
          ...noisyMinutiae,
        ]);

        const signature = new Uint8Array(64);
        crypto.getRandomValues(signature);

        return {
          id: Array.from(credentialId).map(b => b.toString(16).padStart(2, '0')).join(''),
          rawId: credentialId.buffer,
          type: 'public-key',
          response: {
            clientDataJSON: clientDataJSON.buffer,
            authenticatorData: authenticatorData.buffer,
            signature: signature.buffer,
            userHandle: new Uint8Array([1, 2, 3, 4]).buffer,
          },
        };
      };
    });
  }

  /**
   * Enroll a biometric with specific characteristics
   */
  async enrollBiometric(
    page: Page,
    fingerId: string,
    quality: number = 85
  ): Promise<MockBiometricData> {
    const minutiae = Array.from({ length: 32 }, () => Math.floor(Math.random() * 256));

    const biometricData: MockBiometricData = {
      fingerId,
      minutiae,
      quality,
    };

    await page.evaluate((data) => {
      (window as any).__webauthnMock.enrolledBiometrics.set(data.fingerId, data);
    }, biometricData);

    this.enrolledBiometrics.set(fingerId, biometricData);
    return biometricData;
  }

  /**
   * Get last enrollment data from the page
   */
  async getLastEnrollment(page: Page): Promise<MockBiometricData | null> {
    return await page.evaluate(() => {
      return (window as any).__webauthnMock.lastEnrollment;
    });
  }

  /**
   * Get last verification data from the page
   */
  async getLastVerification(page: Page): Promise<MockBiometricData | null> {
    return await page.evaluate(() => {
      return (window as any).__webauthnMock.lastVerification;
    });
  }

  /**
   * Clear all enrolled biometrics
   */
  async clearEnrollments(page: Page): Promise<void> {
    await page.evaluate(() => {
      (window as any).__webauthnMock.enrolledBiometrics.clear();
      (window as any).__webauthnMock.lastEnrollment = null;
      (window as any).__webauthnMock.lastVerification = null;
    });
    this.enrolledBiometrics.clear();
  }

  /**
   * Check if platform authenticator is available (should always be true in mock)
   */
  async isPlatformAuthenticatorAvailable(page: Page): Promise<boolean> {
    return await page.evaluate(async () => {
      return await (window as any).PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
    });
  }
}

/**
 * Create a mock biometric response for API testing
 */
export function createMockBiometricResponse(fingerId: string, quality: number = 85): MockBiometricData {
  return {
    fingerId,
    minutiae: Array.from({ length: 32 }, () => Math.floor(Math.random() * 256)),
    quality,
  };
}

/**
 * Convert mock biometric data to API format
 */
export function convertToApiFormat(biometric: MockBiometricData) {
  return {
    finger_id: biometric.fingerId,
    minutiae: biometric.minutiae.map(val => ({
      x: val % 256,
      y: Math.floor(val / 256),
      angle: (val * 137.5) % 360,
      quality: biometric.quality,
    })),
  };
}
