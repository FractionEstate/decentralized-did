/**
 * Unit tests for the WebAuthn paths in fingerprintCaptureService.
 */

type FingerprintCaptureServiceModule = typeof import('../fingerprintCaptureService');

interface SetupOptions {
  hasPublicKeyCredential?: boolean;
  userAgent?: string;
}

const DEFAULT_USER_AGENT =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36';

let service: FingerprintCaptureServiceModule['fingerprintCaptureService'];
let mockPublicKeyCredential: jest.Mock;
let mockCreate: jest.Mock;
let mockGet: jest.Mock;

const setupWebAuthnGlobals = (options: SetupOptions = {}) => {
  const { hasPublicKeyCredential = true, userAgent = DEFAULT_USER_AGENT } = options;

  mockPublicKeyCredential = jest.fn();
  mockCreate = jest.fn();
  mockGet = jest.fn();

  Object.defineProperty(global, 'window', {
    value: {
      location: { hostname: 'localhost' },
      ...(hasPublicKeyCredential ? { PublicKeyCredential: mockPublicKeyCredential } : {}),
    },
    configurable: true,
    writable: true,
  });

  Object.defineProperty(global, 'navigator', {
    value: {
      credentials: {
        create: mockCreate,
        get: mockGet,
      },
      userAgent,
    },
    configurable: true,
    writable: true,
  });

  if (!global.crypto || typeof global.crypto.getRandomValues !== 'function') {
    const { webcrypto } = require('crypto');
    Object.defineProperty(global, 'crypto', {
      value: webcrypto,
      configurable: true,
      writable: true,
    });
  }
};

const loadService = async (options: SetupOptions = {}) => {
  jest.resetModules();
  setupWebAuthnGlobals(options);
  const module: FingerprintCaptureServiceModule = await import('../fingerprintCaptureService');
  service = module.fingerprintCaptureService;
  return service;
};

describe('fingerprintCaptureService - WebAuthn', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('isWebAuthnAvailable', () => {
    it('returns true when WebAuthn support exists', async () => {
      const svc = await loadService();
      expect(svc.isWebAuthnAvailable()).toBe(true);
    });

    it('returns false when PublicKeyCredential is missing', async () => {
      const svc = await loadService({ hasPublicKeyCredential: false });
      expect(svc.isWebAuthnAvailable()).toBe(false);
    });
  });

  describe('getWebAuthnBiometricType', () => {
    const scenarios = [
      {
        ua: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        expected: 'Touch ID',
      },
      {
        ua: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        expected: 'Windows Hello',
      },
      {
        ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
        expected: 'Touch ID / Face ID',
      },
      {
        ua: 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36',
        expected: 'Fingerprint',
      },
      {
        ua: 'ExampleUserAgent',
        expected: 'Biometric',
      },
    ];

    it.each(scenarios)('returns %s when UA is %s', async ({ ua, expected }) => {
      const svc = await loadService({ userAgent: ua });
      expect(svc.getWebAuthnBiometricType()).toBe(expected);
    });
  });

  describe('enrollWithWebAuthn', () => {
    it('returns credential data when enrollment succeeds', async () => {
      const svc = await loadService();
      const mockRawId = new Uint8Array([1, 2, 3, 4]).buffer;
      const mockPublicKey = new Uint8Array([5, 6, 7, 8]).buffer;

      mockCreate.mockResolvedValue({
        rawId: mockRawId,
        response: { getPublicKey: () => mockPublicKey },
      });

      const result = await svc.enrollWithWebAuthn('user123', 'Test User');

      expect(result.success).toBe(true);
      expect(result.credentialId).toBeDefined();
      expect(result.publicKey).toBeDefined();

      expect(mockCreate).toHaveBeenCalledTimes(1);
      const createArgs = mockCreate.mock.calls[0][0] as CredentialCreationOptions;
      expect(createArgs?.publicKey).toBeDefined();

      const publicKeyOptions = createArgs.publicKey as PublicKeyCredentialCreationOptions;
      expect(publicKeyOptions?.rp).toEqual(
        expect.objectContaining({ name: 'Biometric DID Wallet', id: 'localhost' })
      );
      expect(publicKeyOptions?.user).toEqual(
        expect.objectContaining({ name: 'user123', displayName: 'Test User' })
      );
      expect(ArrayBuffer.isView(publicKeyOptions?.user?.id)).toBe(true);
      expect(ArrayBuffer.isView(publicKeyOptions?.challenge)).toBe(true);
    });

    it('throws when credential creation fails', async () => {
      const svc = await loadService();
      mockCreate.mockRejectedValue(new Error('User cancelled'));

      await expect(svc.enrollWithWebAuthn('user123', 'Test User')).rejects.toThrow(
        'WebAuthn enrollment failed: User cancelled'
      );
    });

    it('throws when credential response is missing', async () => {
      const svc = await loadService();
      mockCreate.mockResolvedValue({ rawId: new ArrayBuffer(8) });

      await expect(svc.enrollWithWebAuthn('user123', 'Test User')).rejects.toThrow(
        'WebAuthn enrollment failed'
      );
    });

    it('throws when public key retrieval fails', async () => {
      const svc = await loadService();
      mockCreate.mockResolvedValue({
        rawId: new ArrayBuffer(8),
        response: { getPublicKey: () => null },
      });

      await expect(svc.enrollWithWebAuthn('user123', 'Test User')).rejects.toThrow(
        'WebAuthn enrollment failed: Failed to obtain WebAuthn public key'
      );
    });
  });

  describe('verifyWithWebAuthn', () => {
    it('returns true when verification succeeds', async () => {
      const svc = await loadService();
      mockGet.mockResolvedValue({ rawId: new ArrayBuffer(8) });

      const result = await svc.verifyWithWebAuthn('credentialId123');

      expect(result).toBe(true);
      expect(mockGet).toHaveBeenCalledWith(
        expect.objectContaining({
          publicKey: expect.objectContaining({
            challenge: expect.any(Uint8Array),
            allowCredentials: expect.arrayContaining([
              expect.objectContaining({ id: expect.any(ArrayBuffer), type: 'public-key' }),
            ]),
          }),
        })
      );
    });

    it('uses provided challenge when supplied', async () => {
      const svc = await loadService();
      const customChallenge = new Uint8Array([9, 8, 7]);
      mockGet.mockResolvedValue({ rawId: new ArrayBuffer(8) });

      await svc.verifyWithWebAuthn('credentialId123', customChallenge);

      expect(mockGet).toHaveBeenCalledWith(
        expect.objectContaining({
          publicKey: expect.objectContaining({ challenge: customChallenge }),
        })
      );
    });

    it('returns false when verification throws', async () => {
      const svc = await loadService();
      mockGet.mockRejectedValue(new Error('Verification failed'));

      const result = await svc.verifyWithWebAuthn('credentialId123');
      expect(result).toBe(false);
    });

    it('returns false when assertion is missing', async () => {
      const svc = await loadService();
      mockGet.mockResolvedValue(undefined);

      const result = await svc.verifyWithWebAuthn('credentialId123');
      expect(result).toBe(false);
    });
  });

  describe('array/base64 helpers', () => {
    it('arrayBufferToBase64 converts ASCII text', async () => {
      const svc = await loadService();
      const buffer = new Uint8Array([72, 101, 108, 108, 111]).buffer; // "Hello"
      // @ts-expect-error testing internal helper
      const result = svc.arrayBufferToBase64(buffer);
      expect(result).toBe('SGVsbG8=');
    });

    it('arrayBufferToBase64 handles empty buffer', async () => {
      const svc = await loadService();
      const buffer = new ArrayBuffer(0);
      // @ts-expect-error testing internal helper
      const result = svc.arrayBufferToBase64(buffer);
      expect(result).toBe('');
    });

    it('base64 helpers roundtrip binary data', async () => {
      const svc = await loadService();
      const original = new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8]).buffer;
      // @ts-expect-error testing internal helper
      const base64 = svc.arrayBufferToBase64(original);
      // @ts-expect-error testing internal helper
      const restored = svc.base64ToArrayBuffer(base64);
      const originalBytes = Array.from(new Uint8Array(original));
      const restoredBytes = Array.from(new Uint8Array(restored));
      expect(restoredBytes).toEqual(originalBytes);
    });
  });

  describe('WebAuthn integration flow', () => {
    it('enrolls then verifies successfully', async () => {
      const svc = await loadService();
      const mockRawId = new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8]).buffer;
      const mockPublicKey = new Uint8Array([9, 10, 11, 12, 13, 14, 15, 16]).buffer;

      mockCreate.mockResolvedValue({
        rawId: mockRawId,
        response: { getPublicKey: () => mockPublicKey },
      });
      mockGet.mockResolvedValue({ rawId: mockRawId });

      const enrollResult = await svc.enrollWithWebAuthn('user123', 'Test User');
      expect(enrollResult.success).toBe(true);

      const verifyResult = await svc.verifyWithWebAuthn(enrollResult.credentialId);
      expect(verifyResult).toBe(true);
    });
  });
});
