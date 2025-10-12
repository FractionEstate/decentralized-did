/**
 * Unit Tests for WebAuthn Credential Storage
 * Tests biometricDidService WebAuthn credential management
 */

import { biometricDidService } from '../biometricDidService';
import { SecureStorage } from '../../storage/secureStorage';

// Mock SecureStorage
jest.mock('../../storage/secureStorage', () => ({
  SecureStorage: {
    set: jest.fn(),
    get: jest.fn(),
    delete: jest.fn(),
  },
}));

describe('BiometricDidService - WebAuthn Credential Storage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('saveWebAuthnCredential', () => {
    it('should save credential to SecureStorage', async () => {
      const mockSet = SecureStorage.set as jest.Mock;
      mockSet.mockResolvedValue(undefined);

      await biometricDidService.saveWebAuthnCredential(
        'credentialId123',
        'publicKey456'
      );

      expect(mockSet).toHaveBeenCalledTimes(1);
      expect(mockSet).toHaveBeenCalledWith(
        'biometric_webauthn_credential',
        expect.any(String)
      );

      // Parse and verify the saved data
      const savedData = JSON.parse(mockSet.mock.calls[0][1]);
      expect(savedData.credentialId).toBe('credentialId123');
      expect(savedData.publicKey).toBe('publicKey456');
      expect(savedData.createdAt).toBeDefined();
    });

    it('should include createdAt timestamp in ISO format', async () => {
      const mockSet = SecureStorage.set as jest.Mock;
      mockSet.mockResolvedValue(undefined);

      const beforeTime = new Date().toISOString();
      await biometricDidService.saveWebAuthnCredential(
        'credentialId123',
        'publicKey456'
      );
      const afterTime = new Date().toISOString();

      const savedData = JSON.parse(mockSet.mock.calls[0][1]);
      expect(savedData.createdAt).toBeDefined();
      expect(typeof savedData.createdAt).toBe('string');

      // Verify timestamp is between before and after
      expect(savedData.createdAt >= beforeTime).toBe(true);
      expect(savedData.createdAt <= afterTime).toBe(true);
    });

    it('should handle SecureStorage errors gracefully', async () => {
      const mockSet = SecureStorage.set as jest.Mock;
      mockSet.mockRejectedValue(new Error('Storage full'));

      await expect(
        biometricDidService.saveWebAuthnCredential('credentialId123', 'publicKey456')
      ).rejects.toThrow('Storage full');
    });

    it('should overwrite existing credential', async () => {
      const mockSet = SecureStorage.set as jest.Mock;
      mockSet.mockResolvedValue(undefined);

      // Save first credential
      await biometricDidService.saveWebAuthnCredential(
        'credentialId1',
        'publicKey1'
      );

      // Save second credential (should overwrite)
      await biometricDidService.saveWebAuthnCredential(
        'credentialId2',
        'publicKey2'
      );

      expect(mockSet).toHaveBeenCalledTimes(2);

      // Verify second call has new data
      const secondSave = JSON.parse(mockSet.mock.calls[1][1]);
      expect(secondSave.credentialId).toBe('credentialId2');
      expect(secondSave.publicKey).toBe('publicKey2');
    });
  });

  describe('loadWebAuthnCredential', () => {
    it('should load credential from SecureStorage', async () => {
      const mockData = {
        credentialId: 'credentialId123',
        publicKey: 'publicKey456',
        createdAt: new Date().toISOString(),
      };

      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockResolvedValue(JSON.stringify(mockData));

      const result = await biometricDidService.loadWebAuthnCredential();

      expect(mockGet).toHaveBeenCalledWith('biometric_webauthn_credential');
      expect(result).toEqual({
        credentialId: 'credentialId123',
        publicKey: 'publicKey456',
      });
    });

    it('should return null when no credential exists', async () => {
      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockResolvedValue(null);

      const result = await biometricDidService.loadWebAuthnCredential();

      expect(result).toBeNull();
    });

    it('should return null when stored data is undefined', async () => {
      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockResolvedValue(undefined);

      const result = await biometricDidService.loadWebAuthnCredential();

      expect(result).toBeNull();
    });

    it('should return null when stored data is invalid JSON', async () => {
      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockResolvedValue('invalid json {{{');

      const result = await biometricDidService.loadWebAuthnCredential();

      expect(result).toBeNull();
    });

    it('should return null when stored data is missing required fields', async () => {
      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockResolvedValue(JSON.stringify({ credentialId: 'test' })); // Missing publicKey

      const result = await biometricDidService.loadWebAuthnCredential();

      expect(result).toBeNull();
    });

    it('should handle SecureStorage errors', async () => {
      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockRejectedValue(new Error('Storage unavailable'));

      const result = await biometricDidService.loadWebAuthnCredential();

      expect(result).toBeNull();
    });

    it('should not return createdAt timestamp', async () => {
      const mockData = {
        credentialId: 'credentialId123',
        publicKey: 'publicKey456',
        createdAt: '2025-10-12T15:30:00Z',
      };

      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockResolvedValue(JSON.stringify(mockData));

      const result = await biometricDidService.loadWebAuthnCredential();

      expect(result).toEqual({
        credentialId: 'credentialId123',
        publicKey: 'publicKey456',
      });
      expect((result as any).createdAt).toBeUndefined();
    });
  });

  describe('hasWebAuthnCredential', () => {
    it('should return true when credential exists', async () => {
      const mockData = {
        credentialId: 'credentialId123',
        publicKey: 'publicKey456',
        createdAt: new Date().toISOString(),
      };

      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockResolvedValue(JSON.stringify(mockData));

      const result = await biometricDidService.hasWebAuthnCredential();

      expect(result).toBe(true);
    });

    it('should return false when credential does not exist', async () => {
      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockResolvedValue(null);

      const result = await biometricDidService.hasWebAuthnCredential();

      expect(result).toBe(false);
    });

    it('should return false when stored data is invalid', async () => {
      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockResolvedValue('invalid json');

      const result = await biometricDidService.hasWebAuthnCredential();

      expect(result).toBe(false);
    });

    it('should return false when stored data is missing required fields', async () => {
      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockResolvedValue(JSON.stringify({ credentialId: 'test' }));

      const result = await biometricDidService.hasWebAuthnCredential();

      expect(result).toBe(false);
    });

    it('should handle SecureStorage errors by returning false', async () => {
      const mockGet = SecureStorage.get as jest.Mock;
      mockGet.mockRejectedValue(new Error('Storage unavailable'));

      const result = await biometricDidService.hasWebAuthnCredential();

      expect(result).toBe(false);
    });
  });

  describe('deleteWebAuthnCredential', () => {
    it('should delete credential from SecureStorage', async () => {
      const mockDelete = SecureStorage.delete as jest.Mock;
      mockDelete.mockResolvedValue(undefined);

      await biometricDidService.deleteWebAuthnCredential();

      expect(mockDelete).toHaveBeenCalledWith('biometric_webauthn_credential');
    });

    it('should not throw error if credential does not exist', async () => {
      const mockDelete = SecureStorage.delete as jest.Mock;
      mockDelete.mockResolvedValue(undefined);

      await expect(
        biometricDidService.deleteWebAuthnCredential()
      ).resolves.not.toThrow();
    });

    it('should handle SecureStorage errors gracefully', async () => {
      const mockDelete = SecureStorage.delete as jest.Mock;
      mockDelete.mockRejectedValue(new Error('Storage unavailable'));

      await expect(
        biometricDidService.deleteWebAuthnCredential()
      ).rejects.toThrow('Storage unavailable');
    });
  });

  describe('WebAuthn credential lifecycle', () => {
    it('should complete full save-load-delete cycle', async () => {
      const mockSet = SecureStorage.set as jest.Mock;
      const mockGet = SecureStorage.get as jest.Mock;
      const mockDelete = SecureStorage.delete as jest.Mock;

      mockSet.mockResolvedValue(undefined);
      mockGet.mockResolvedValue(null);
      mockDelete.mockResolvedValue(undefined);

      // 1. Initially no credential
      mockGet.mockResolvedValueOnce(null);
      let hasCredential = await biometricDidService.hasWebAuthnCredential();
      expect(hasCredential).toBe(false);

      // 2. Save credential
      await biometricDidService.saveWebAuthnCredential(
        'credentialId123',
        'publicKey456'
      );
      expect(mockSet).toHaveBeenCalled();

      // 3. Load credential
      const savedData = {
        credentialId: 'credentialId123',
        publicKey: 'publicKey456',
        createdAt: new Date().toISOString(),
      };
      mockGet.mockResolvedValueOnce(JSON.stringify(savedData));

      const loaded = await biometricDidService.loadWebAuthnCredential();
      expect(loaded).toEqual({
        credentialId: 'credentialId123',
        publicKey: 'publicKey456',
      });

      // 4. Verify credential exists
      mockGet.mockResolvedValueOnce(JSON.stringify(savedData));
      hasCredential = await biometricDidService.hasWebAuthnCredential();
      expect(hasCredential).toBe(true);

      // 5. Delete credential
      await biometricDidService.deleteWebAuthnCredential();
      expect(mockDelete).toHaveBeenCalled();

      // 6. Verify credential is gone
      mockGet.mockResolvedValueOnce(null);
      hasCredential = await biometricDidService.hasWebAuthnCredential();
      expect(hasCredential).toBe(false);
    });

    it('should handle rapid save operations', async () => {
      const mockSet = SecureStorage.set as jest.Mock;
      mockSet.mockResolvedValue(undefined);

      // Save multiple credentials rapidly
      const promises = [
        biometricDidService.saveWebAuthnCredential('id1', 'key1'),
        biometricDidService.saveWebAuthnCredential('id2', 'key2'),
        biometricDidService.saveWebAuthnCredential('id3', 'key3'),
      ];

      await Promise.all(promises);

      // All saves should complete
      expect(mockSet).toHaveBeenCalledTimes(3);
    });
  });

  describe('Error handling and edge cases', () => {
    it('should handle empty credential ID', async () => {
      const mockSet = SecureStorage.set as jest.Mock;
      mockSet.mockResolvedValue(undefined);

      await biometricDidService.saveWebAuthnCredential('', 'publicKey456');

      const savedData = JSON.parse(mockSet.mock.calls[0][1]);
      expect(savedData.credentialId).toBe('');
    });

    it('should handle empty public key', async () => {
      const mockSet = SecureStorage.set as jest.Mock;
      mockSet.mockResolvedValue(undefined);

      await biometricDidService.saveWebAuthnCredential('credentialId123', '');

      const savedData = JSON.parse(mockSet.mock.calls[0][1]);
      expect(savedData.publicKey).toBe('');
    });

    it('should handle very long credential ID', async () => {
      const mockSet = SecureStorage.set as jest.Mock;
      mockSet.mockResolvedValue(undefined);

      const longId = 'x'.repeat(10000);
      await biometricDidService.saveWebAuthnCredential(longId, 'publicKey456');

      const savedData = JSON.parse(mockSet.mock.calls[0][1]);
      expect(savedData.credentialId).toBe(longId);
    });

    it('should handle special characters in credential data', async () => {
      const mockSet = SecureStorage.set as jest.Mock;
      const mockGet = SecureStorage.get as jest.Mock;
      mockSet.mockResolvedValue(undefined);

      const specialId = 'cred!@#$%^&*()_+-={}[]|\\:";\'<>?,./';
      const specialKey = 'key™€£¥©®™';

      await biometricDidService.saveWebAuthnCredential(specialId, specialKey);

      const savedData = JSON.parse(mockSet.mock.calls[0][1]);
      mockGet.mockResolvedValue(mockSet.mock.calls[0][1]);

      const loaded = await biometricDidService.loadWebAuthnCredential();
      expect(loaded?.credentialId).toBe(specialId);
      expect(loaded?.publicKey).toBe(specialKey);
    });
  });
});
