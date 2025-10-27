import { SecureStoragePlugin } from "@evva/capacitor-secure-storage-plugin";

enum KeyStoreKeys {
  APP_PASSCODE = "app-login-passcode",
  APP_OP_PASSWORD = "app-operations-password",
  SIGNIFY_BRAN = "signify-bran",
  MEERKAT_SEED = "app-meerkat-seed",
  DB_ENCRYPTION_BRAN = "db-encryption-bran",
}

class SecureStorage {
  static readonly KEY_NOT_FOUND_ERRORS = [
    "Item with given key does not exist", // Android/Web
    "Error key doesn't exist", // iOS
  ];

  static async get(key: string): Promise<string | null> {
    try {
      const result = await SecureStoragePlugin.get({ key });
      return result.value;
    } catch (e) {
      const error = e as { message?: string; name?: string };

      // Log NotFoundError if it occurs
      if (error.name === 'NotFoundError') {
        console.error(`🔍 [SecureStorage] NotFoundError on get("${key}"):`, error);
      }

      if (!SecureStorage.isErrorKeyNotFound(error.message)) {
        throw e;
      }
      return null;
    }
  }

  static async set(key: string, value: string): Promise<void> {
    try {
      await SecureStoragePlugin.set({
        key,
        value,
        accessibility: "whenUnlockedThisDeviceOnly",
      });
    } catch (e) {
      const error = e as { name?: string };

      // Log NotFoundError if it occurs
      if (error.name === 'NotFoundError') {
        console.error(`🔍 [SecureStorage] NotFoundError on set("${key}"):`, e);
      }
      throw e;
    }
  }

  static async delete(key: string) {
    const result = await this.get(key);
    if (result) {
      await SecureStoragePlugin.remove({ key });
    }
  }

  static async keyExists(key: string): Promise<boolean> {
    return (await SecureStoragePlugin.keys()).value.some((k) => k === key);
  }

  static isErrorKeyNotFound(errorMessage?: string): boolean {
    return errorMessage
      ? SecureStorage.KEY_NOT_FOUND_ERRORS.some((err) =>
        errorMessage.includes(err)
      )
      : false;
  }

  static async isKeyStoreSupported(): Promise<boolean> {
    try {
      await this.set("testKey", "testValue");
      await this.delete("testKey");
      return true;
    } catch (e) {
      return false;
    }
  }

  static async wipe(): Promise<void> {
    for (const key of Object.values(KeyStoreKeys)) {
      await SecureStorage.delete(key);
    }
  }
}

export { SecureStorage, KeyStoreKeys };
