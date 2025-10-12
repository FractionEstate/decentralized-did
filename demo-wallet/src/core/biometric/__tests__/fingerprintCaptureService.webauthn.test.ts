/**
 * Unit Tests for WebAuthn Integration
 * Tests fingerprintCaptureService WebAuthn methods
 */

import { fingerprintCaptureService } from '../fingerprintCaptureService';

// Mock window.PublicKeyCredential
const mockPublicKeyCredential = jest.fn();
Object.defineProperty(global, 'window', {
  value: {
    PublicKeyCredential: mockPublicKeyCredential,
  },
  writable: true,
});

// Mock navigator.credentials
const mockCreate = jest.fn();
const mockGet = jest.fn();
Object.defineProperty(global, 'navigator', {
  value: {
    credentials: {
      create: mockCreate,
      get: mockGet,
    },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
  },
  writable: true,
  configurable: true,
});

describe('FingerprintCaptureService - WebAuthn Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('isWebAuthnAvailable', () => {
    it('should return true when WebAuthn is supported', () => {
      const result = fingerprintCaptureService.isWebAuthnAvailable();
      expect(result).toBe(true);
    });

    it('should return false when WebAuthn is not supported', () => {
      const originalWindow = global.window;
      // @ts-ignore
      delete global.window.PublicKeyCredential;

      const result = fingerprintCaptureService.isWebAuthnAvailable();
      expect(result).toBe(false);

      // Restore
      global.window = originalWindow;
    });
  });

  describe('getWebAuthnBiometricType', () => {
    it('should return "Touch ID" on macOS', () => {
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        configurable: true,
      });

      const result = fingerprintCaptureService.getWebAuthnBiometricType();
      expect(result).toBe('Touch ID');
    });

    it('should return "Windows Hello" on Windows', () => {
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        configurable: true,
      });

      const result = fingerprintCaptureService.getWebAuthnBiometricType();
      expect(result).toBe('Windows Hello');
    });

    it('should return "Touch ID / Face ID" on iOS', () => {
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
        configurable: true,
      });

      const result = fingerprintCaptureService.getWebAuthnBiometricType();
      expect(result).toBe('Touch ID / Face ID');
    });

    it('should return "Fingerprint" on Android', () => {
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36',
        configurable: true,
      });

      const result = fingerprintCaptureService.getWebAuthnBiometricType();
      expect(result).toBe('Fingerprint');
    });

    it('should return "Biometric" as fallback for unknown platforms', () => {
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (Unknown Platform)',
        configurable: true,
      });

      const result = fingerprintCaptureService.getWebAuthnBiometricType();
      expect(result).toBe('Biometric');
    });
  });

  describe('enrollWithWebAuthn', () => {
    it('should create WebAuthn credential successfully', async () => {
      const mockRawId = new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8]).buffer;
      const mockPublicKey = new Uint8Array([9, 10, 11, 12, 13, 14, 15, 16]).buffer;

      const mockCredential = {
        rawId: mockRawId,
        response: {
          getPublicKey: () => mockPublicKey,
        },
      };

      mockCreate.mockResolvedValue(mockCredential);

      const result = await fingerprintCaptureService.enrollWithWebAuthn(
        'user123',
        'Test User'
      );

      expect(result.success).toBe(true);
      expect(result.credentialId).toBeDefined();
      expect(result.publicKey).toBeDefined();
      expect(typeof result.credentialId).toBe('string');
      expect(typeof result.publicKey).toBe('string');

      // Verify credentials.create was called with correct options
      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          publicKey: expect.objectContaining({
            challenge: expect.any(Uint8Array),
            rp: expect.objectContaining({
              name: 'Biometric DID Wallet',
            }),
            user: expect.objectContaining({
              id: expect.any(Uint8Array),
              name: 'user123',
              displayName: 'Test User',
            }),
            pubKeyCredParams: expect.arrayContaining([
              expect.objectContaining({ type: 'public-key', alg: -7 }),
            ]),
            authenticatorSelection: expect.objectContaining({
              authenticatorAttachment: 'platform',
              userVerification: 'required',
            }),
            timeout: 60000,
            attestation: 'none',
          }),
        })
      );
    });

    it('should throw error when credential creation fails', async () => {
      mockCreate.mockRejectedValue(new Error('User cancelled'));

      await expect(
        fingerprintCaptureService.enrollWithWebAuthn('user123', 'Test User')
      ).rejects.toThrow('WebAuthn enrollment failed: User cancelled');
    });

    it('should throw error when credential response is missing', async () => {
      mockCreate.mockResolvedValue({ rawId: new ArrayBuffer(32) });

      await expect(
        fingerprintCaptureService.enrollWithWebAuthn('user123', 'Test User')
      ).rejects.toThrow('WebAuthn enrollment failed');
    });

    it('should throw error when public key is unavailable', async () => {
      const mockCredential = {
        rawId: new ArrayBuffer(32),
        response: {
          getPublicKey: () => null,
        },
      };

      mockCreate.mockResolvedValue(mockCredential);

      await expect(
        fingerprintCaptureService.enrollWithWebAuthn('user123', 'Test User')
      ).rejects.toThrow('WebAuthn enrollment failed');
    });
  });

  describe('verifyWithWebAuthn', () => {
    it('should verify WebAuthn credential successfully', async () => {
      const mockAssertion = {
        rawId: new ArrayBuffer(32),
      };

      mockGet.mockResolvedValue(mockAssertion);

      const result = await fingerprintCaptureService.verifyWithWebAuthn('credentialId123');

      expect(result).toBe(true);

      // Verify credentials.get was called with correct options
      expect(mockGet).toHaveBeenCalledWith(
        expect.objectContaining({
          publicKey: expect.objectContaining({
            challenge: expect.any(Uint8Array),
            allowCredentials: expect.arrayContaining([
              expect.objectContaining({
                id: expect.any(ArrayBuffer),
                type: 'public-key',
              }),
            ]),
            userVerification: 'required',
            timeout: 60000,
          }),
        })
      );
    });

    it('should use custom challenge if provided', async () => {
      const mockAssertion = { rawId: new ArrayBuffer(32) };
      mockGet.mockResolvedValue(mockAssertion);

      const customChallenge = new Uint8Array([1, 2, 3, 4, 5]);
      await fingerprintCaptureService.verifyWithWebAuthn('credentialId123', customChallenge);

      expect(mockGet).toHaveBeenCalledWith(
        expect.objectContaining({
          publicKey: expect.objectContaining({
            challenge: customChallenge,
          }),
        })
      );
    });

    it('should return false when verification fails', async () => {
      mockGet.mockRejectedValue(new Error('Verification failed'));

      const result = await fingerprintCaptureService.verifyWithWebAuthn('credentialId123');

      expect(result).toBe(false);
    });

    it('should return false when user cancels', async () => {
      mockGet.mockRejectedValue(new Error('User cancelled'));

      const result = await fingerprintCaptureService.verifyWithWebAuthn('credentialId123');

      expect(result).toBe(false);
    });
  });

  describe('arrayBufferToBase64', () => {
    it('should convert ArrayBuffer to base64 string', () => {
      // "Hello" in ASCII
      const buffer = new Uint8Array([72, 101, 108, 108, 111]).buffer;
      // @ts-ignore - accessing private method for testing
      const result = fingerprintCaptureService.arrayBufferToBase64(buffer);
      expect(result).toBe('SGVsbG8=');
    });

    it('should handle empty ArrayBuffer', () => {
      const buffer = new ArrayBuffer(0);
      // @ts-ignore
      const result = fingerprintCaptureService.arrayBufferToBase64(buffer);
      expect(result).toBe('');
    });

    it('should handle binary data correctly', () => {
      const buffer = new Uint8Array([0, 1, 2, 3, 255, 254, 253]).buffer;
      // @ts-ignore
      const result = fingerprintCaptureService.arrayBufferToBase64(buffer);
      expect(typeof result).toBe('string');
      expect(result.length).toBeGreaterThan(0);
    });
  });

  describe('base64ToArrayBuffer', () => {
    it('should convert base64 string to ArrayBuffer', () => {
      const base64 = 'SGVsbG8='; // "Hello"
      // @ts-ignore
      const result = fingerprintCaptureService.base64ToArrayBuffer(base64);
      const bytes = new Uint8Array(result);
      expect(Array.from(bytes)).toEqual([72, 101, 108, 108, 111]);
    });

    it('should handle empty base64 string', () => {
      const base64 = '';
      // @ts-ignore
      const result = fingerprintCaptureService.base64ToArrayBuffer(base64);
      expect(result.byteLength).toBe(0);
    });

    it('should roundtrip with arrayBufferToBase64', () => {
      const original = new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8]).buffer;
      // @ts-ignore
      const base64 = fingerprintCaptureService.arrayBufferToBase64(original);
      // @ts-ignore
      const restored = fingerprintCaptureService.base64ToArrayBuffer(base64);
      const originalBytes = new Uint8Array(original);
      const restoredBytes = new Uint8Array(restored);
      expect(Array.from(restoredBytes)).toEqual(Array.from(originalBytes));
    });
  });

  describe('WebAuthn integration flow', () => {
    it('should complete enrollment and verification flow', async () => {
      // Setup mocks
      const mockRawId = new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8]).buffer;
      const mockPublicKey = new Uint8Array([9, 10, 11, 12, 13, 14, 15, 16]).buffer;

      const mockCredential = {
        rawId: mockRawId,
        response: {
          getPublicKey: () => mockPublicKey,
        },
      };

      const mockAssertion = {
        rawId: new ArrayBuffer(32),
      };

      mockCreate.mockResolvedValue(mockCredential);
      mockGet.mockResolvedValue(mockAssertion);

      // Enroll
      const enrollResult = await fingerprintCaptureService.enrollWithWebAuthn(
        'user123',
        'Test User'
      );

      expect(enrollResult.success).toBe(true);
      expect(enrollResult.credentialId).toBeDefined();

      // Verify
      const verifyResult = await fingerprintCaptureService.verifyWithWebAuthn(
        enrollResult.credentialId
      );

      expect(verifyResult).toBe(true);
    });
  });
});
