/**
 * Service for integrating Python CLI biometric DID commands
 * Provides enrollment and verification functionality
 */

import { Capacitor } from "@capacitor/core";
import { SecureStorage } from "../storage/secureStorage/secureStorage";
import {
  BiometricEnrollmentInput,
  BiometricGenerateResult,
  BiometricVerifyInput,
  BiometricVerifyResult,
  HelperDataEntry,
} from "./biometricDid.types";
import { blake2b } from "blakejs";
import bs58 from "bs58";

const HELPER_DATA_KEY_PREFIX = "biometric_helpers_";
const CURRENT_DID_KEY = "biometric_current_did";
const WEBAUTHN_CREDENTIAL_KEY = "biometric_webauthn_credential";

/**
 * Generate deterministic DID from biometric commitment
 *
 * This function creates a Sybil-resistant DID that:
 * - Is derived solely from biometric data (no wallet address)
 * - Is deterministic (same biometric = same DID)
 * - Preserves privacy (no personal information in identifier)
 *
 * @param commitment - 32-byte biometric commitment (master key)
 * @param network - Target network ("mainnet" or "testnet")
 * @returns Deterministic DID in format: did:cardano:{network}:{base58_hash}
 */
function generateDeterministicDID(commitment: Uint8Array | string, network: string = "mainnet"): string {
  // Convert string to Uint8Array if needed
  let commitmentBytes: Uint8Array;
  if (typeof commitment === "string") {
    // If string, assume it's hex or base64 - convert appropriately
    if (commitment.length === 64) {
      // Hex string (64 chars = 32 bytes)
      commitmentBytes = new Uint8Array(
        commitment.match(/.{2}/g)!.map(byte => parseInt(byte, 16))
      );
    } else {
      // Base64 string
      commitmentBytes = Uint8Array.from(atob(commitment), c => c.charCodeAt(0));
    }
  } else {
    commitmentBytes = commitment;
  }

  // Hash the commitment with Blake2b (32 bytes output)
  const hash = blake2b(commitmentBytes, undefined, 32);

  // Encode with Base58 for compact, URL-safe representation
  const base58Hash = bs58.encode(hash);

  // Build DID with network identifier
  return `did:cardano:${network}:${base58Hash}`;
}

export class BiometricDidService {
  private static instance: BiometricDidService;
  private pythonCliPath: string;
  private authState: { token: string; expiresAt: number } | null = null;
  private pendingAuthRequest: Promise<string | null> | null = null;
  private readonly REQUEST_TIMEOUT_MS = 10000; // 10 seconds

  /**
   * Generate unique request ID for audit trails
   */
  private generateRequestId(): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 10);
    return `${timestamp}-${random}`;
  }

  private constructor() {
    // In production, this would be the path to the bundled Python CLI
    // For now, assume it's available in the system PATH or via API
    this.pythonCliPath = "python3 -m decentralized_did.cli";
  }

  public static getInstance(): BiometricDidService {
    if (!BiometricDidService.instance) {
      BiometricDidService.instance = new BiometricDidService();
    }
    return BiometricDidService.instance;
  }

  /**
   * Save WebAuthn credential for biometric verification
   */
  async saveWebAuthnCredential(credentialId: string, publicKey: string): Promise<void> {
    try {
      const credentialData = JSON.stringify({
        credentialId,
        publicKey,
        createdAt: new Date().toISOString(),
      });

      await SecureStorage.set(WEBAUTHN_CREDENTIAL_KEY, credentialData);
      console.log('✅ WebAuthn credential saved');
    } catch (error) {
      console.error('Failed to save WebAuthn credential:', error);
      throw (error instanceof Error ? error : new Error(String(error)));
    }
  }

  /**
   * Load WebAuthn credential
   */
  async loadWebAuthnCredential(): Promise<{ credentialId: string; publicKey: string } | null> {
    try {
      const credentialData = await SecureStorage.get(WEBAUTHN_CREDENTIAL_KEY);

      if (!credentialData) {
        return null;
      }

      const parsed = JSON.parse(credentialData);
      if (
        !parsed ||
        typeof parsed.credentialId !== "string" ||
        typeof parsed.publicKey !== "string"
      ) {
        return null;
      }

      return {
        credentialId: parsed.credentialId,
        publicKey: parsed.publicKey,
      };
    } catch (error) {
      console.error('Failed to load WebAuthn credential:', error);
      return null;
    }
  }

  /**
   * Check if WebAuthn credential exists
   */
  async hasWebAuthnCredential(): Promise<boolean> {
    const credential = await this.loadWebAuthnCredential();
    return credential !== null;
  }

  /**
   * Delete WebAuthn credential
   */
  async deleteWebAuthnCredential(): Promise<void> {
    try {
      await SecureStorage.delete(WEBAUTHN_CREDENTIAL_KEY);
      console.log('✅ WebAuthn credential deleted');
    } catch (error) {
      console.error('Failed to delete WebAuthn credential:', error);
      throw new Error(`Failed to delete WebAuthn credential: ${(error as Error).message}`);
    }
  }

  /**
   * Generate biometric DID and helper data from fingerprint minutiae
   */
  async generate(
    input: BiometricEnrollmentInput,
    walletAddress: string
  ): Promise<BiometricGenerateResult> {
    try {
      if (!input.fingers || input.fingers.length === 0) {
        throw new Error("Biometric enrollment requires at least one finger template");
      }
      // Convert input to JSON for CLI
      const inputJson = JSON.stringify(input);

      // Build CLI command
      const command = [
        this.pythonCliPath,
        "generate",
        `--wallet ${walletAddress}`,
        `--storage inline`,
        `--format json`,
      ].join(" ");

      // Execute command with input data
      const output = await this.executeCommand(command, inputJson);
      const result = JSON.parse(output);

      return this.transformGenerateResult(result, walletAddress);
    } catch (error) {
      throw new Error(`Biometric DID generation failed: ${error}`);
    }
  }

  /**
   * Verify fingerprints against stored helper data
   */
  async verify(input: BiometricVerifyInput): Promise<BiometricVerifyResult> {
    try {
      if (!input.fingers || input.fingers.length === 0) {
        throw new Error("Biometric verification requires at least one finger template");
      }
      if (!input.helpers || Object.keys(input.helpers).length === 0) {
        throw new Error("Biometric verification requires helper data from enrollment");
      }
      // Convert inputs to JSON
      const fingersJson = JSON.stringify({ fingers: input.fingers });
      const helpersJson = JSON.stringify(input.helpers);

      // Build CLI command
      const command = [
        this.pythonCliPath,
        "verify",
        `--expected-hash ${input.expected_id_hash}`,
        `--format json`,
      ].join(" ");

      // For verification, we need to pass both fingerprint and helper data
      // This would require a combined input format or separate file handling
      const combinedInput = JSON.stringify({
        fingers: input.fingers,
        helpers: input.helpers,
      });

      const output = await this.executeCommand(command, combinedInput);
      const result = JSON.parse(output);

      return result;
    } catch (error) {
      throw new Error(`Biometric verification failed: ${error}`);
    }
  }

  /**
   * Execute shell command (platform-specific)
   * @param command - The CLI command to execute
   * @param stdinData - Optional data to pipe to stdin
   */
  private async executeCommand(
    command: string,
    stdinData?: string
  ): Promise<string> {
    // For development: Use mock data
    // In production: Integrate with actual CLI via:
    // 1. Capacitor plugin for native shell execution
    // 2. WebAssembly build of Python CLI
    // 3. Backend API endpoint
    // 4. Electron with Node.js child_process

    if (process.env.NODE_ENV === "development") {
      return this.executeMockCommand(command, stdinData);
    }

    if (Capacitor.isNativePlatform()) {
      return this.executeNativeCommand(command, stdinData);
    } else {
      return this.executeWebCommand(command, stdinData);
    }
  }

  private resolveApiBaseUrl(): string {
    const url = (
      process.env.BIOMETRIC_API_URL ||
      process.env.SECURE_API_URL ||
      process.env.MOCK_API_URL ||
      "http://localhost:8000"
    );

    // Enforce HTTPS in production (allow http://localhost for development)
    if (process.env.NODE_ENV === "production" && url.startsWith("http://") && !url.includes("localhost")) {
      console.warn(`⚠️ Enforcing HTTPS: ${url} → ${url.replace("http://", "https://")}`);
      return url.replace("http://", "https://");
    }

    return url;
  }

  private resolveAuthBaseUrl(): string {
    const url = (
      process.env.BIOMETRIC_AUTH_URL ||
      process.env.SECURE_API_URL ||
      this.resolveApiBaseUrl()
    );

    // Enforce HTTPS in production
    if (process.env.NODE_ENV === "production" && url.startsWith("http://") && !url.includes("localhost")) {
      console.warn(`⚠️ Enforcing HTTPS: ${url} → ${url.replace("http://", "https://")}`);
      return url.replace("http://", "https://");
    }

    return url;
  }

  private resolveApiKey(): string | undefined {
    const baseUrl = this.resolveApiBaseUrl().replace(/\/$/, "");
    const mockUrl = (process.env.MOCK_API_URL || "").replace(/\/$/, "");

    if (mockUrl && mockUrl.length > 0 && baseUrl === mockUrl) {
      return undefined;
    }

    const key =
      process.env.BIOMETRIC_API_KEY ||
      process.env.API_KEY ||
      process.env.API_SECRET_KEY;
    return key ? key.trim() || undefined : undefined;
  }

  private invalidateAuthToken(): void {
    this.authState = null;
  }

  private async getApiToken(forceRefresh = false): Promise<string | null> {
    const apiKey = this.resolveApiKey();
    if (!apiKey) {
      return null; // Mock server or unauthenticated setup
    }

    if (!forceRefresh && this.authState && Date.now() < this.authState.expiresAt) {
      return this.authState.token;
    }

    if (!forceRefresh && this.pendingAuthRequest) {
      return this.pendingAuthRequest;
    }

    const authPromise = this.requestAuthToken(apiKey)
      .catch(error => {
        this.invalidateAuthToken();
        throw error;
      })
      .finally(() => {
        this.pendingAuthRequest = null;
      });

    this.pendingAuthRequest = authPromise;
    return authPromise;
  }

  private async requestAuthToken(apiKey: string): Promise<string | null> {
    const authBase = this.resolveAuthBaseUrl();
    const authEndpoint = `${authBase.replace(/\/$/, "")}/auth/token`;
    const requestId = this.generateRequestId();

    try {
      // Create AbortController for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.REQUEST_TIMEOUT_MS);

      const response = await fetch(authEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Request-ID": requestId,
        },
        body: JSON.stringify({ api_key: apiKey }),
        signal: controller.signal,
      }).finally(() => clearTimeout(timeoutId));

      if (!response.ok) {
        const message = await this.extractErrorMessage(response);
        throw new Error(`Authentication failed: ${message}`);
      }

      const data = (await response.json()) as {
        access_token?: string;
        expires_in?: number;
      };

      if (!data.access_token) {
        throw new Error("Authentication response missing access_token");
      }

      const expiresInSeconds = Math.max(0, (data.expires_in ?? 3600) - 5);
      this.authState = {
        token: data.access_token,
        expiresAt: Date.now() + expiresInSeconds * 1000,
      };

      console.log(`✅ Authentication successful [Request ID: ${requestId}]`);
      return data.access_token;
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error(
          `Authentication request timed out after ${this.REQUEST_TIMEOUT_MS}ms [Request ID: ${requestId}]`
        );
      }
      if (this.isNetworkError(error)) {
        throw new Error(
          `Authentication server unavailable at ${authBase}. Ensure the secure API server is running and BIOMETRIC_AUTH_URL is correct. [Request ID: ${requestId}]`
        );
      }
      throw error;
    }
  }

  private isNetworkError(error: unknown): boolean {
    return (
      error instanceof TypeError &&
      (error.message.includes("fetch failed") ||
        error.message.includes("network") ||
        error.message.includes("request") ||
        error.message.includes("connect"))
    );
  }

  private async extractErrorMessage(response: Response): Promise<string> {
    const statusInfo = `${response.status} ${response.statusText}`.trim();

    try {
      const text = await response.text();
      if (!text) {
        return statusInfo;
      }

      try {
        const json = JSON.parse(text);
        if (typeof json === "string") {
          return `${statusInfo}: ${json}`;
        }

        if (json && typeof json === "object") {
          const detail = json.detail || json.error || json.message;
          if (detail) {
            return `${statusInfo}: ${detail}`;
          }
          return `${statusInfo}: ${JSON.stringify(json)}`;
        }
      } catch {
        // Fall through if body is not JSON
      }

      return `${statusInfo}: ${text}`;
    } catch {
      return statusInfo;
    }
  }

  private async performApiRequest<T>(
    path: string,
    init: RequestInit,
    allowRetry: boolean = true
  ): Promise<T> {
    const baseUrl = this.resolveApiBaseUrl().replace(/\/$/, "");
    const url = `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
    const requestId = this.generateRequestId();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "X-Request-ID": requestId,
    };

    if (init.headers) {
      Object.assign(headers, init.headers as Record<string, string>);
    }

    let token: string | null = null;
    try {
      token = await this.getApiToken();
    } catch (authError) {
      if (this.resolveApiKey()) {
        throw authError;
      }
    }

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.REQUEST_TIMEOUT_MS);

    const requestInit: RequestInit = {
      ...init,
      headers,
      signal: controller.signal,
    };

    try {
      const response = await fetch(url, requestInit).finally(() => clearTimeout(timeoutId));

      if (response.status === 401 && allowRetry && token) {
        this.invalidateAuthToken();
        return this.performApiRequest<T>(path, init, false);
      }

      if (!response.ok) {
        const message = await this.extractErrorMessage(response);
        throw new Error(`${message} [Request ID: ${requestId}]`);
      }

      console.log(`✅ API request successful: ${path} [Request ID: ${requestId}]`);
      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error(
          `API request timed out after ${this.REQUEST_TIMEOUT_MS}ms: ${path} [Request ID: ${requestId}]`
        );
      }
      if (this.isNetworkError(error)) {
        throw new Error(
          `Backend API unavailable at ${baseUrl}. Ensure the server is running and BIOMETRIC_API_URL is correct. [Request ID: ${requestId}]`
        );
      }
      throw error;
    }
  }

  /**
   * Execute command with mock data (development only)
   */
  private async executeMockCommand(
    command: string,
    stdinData?: string
  ): Promise<string> {
    console.log("[BiometricDidService] Mock command:", command);
    console.log("[BiometricDidService] Mock stdin:", stdinData?.substring(0, 100));

    // Simulate CLI delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    if (command.includes("generate")) {
      // Generate mock commitment (32 bytes)
      const mockCommitment = new Uint8Array(32);
      for (let i = 0; i < 32; i++) {
        mockCommitment[i] = Math.floor(Math.random() * 256);
      }

      // Generate deterministic DID from mock commitment
      const mockDid = generateDeterministicDID(mockCommitment, "mainnet");

      // Return mock generate result with deterministic DID
      return JSON.stringify({
        did: mockDid,
        commitment: bs58.encode(mockCommitment),
        helpers: {
          left_thumb: {
            finger_id: "left_thumb",
            salt_b64: "MockSaltBase64==",
            auth_b64: "MockAuthBase64==",
            grid_size: 0.05,
            angle_bins: 32,
          },
        },
      });
    } else if (command.includes("verify")) {
      // Return mock verify result
      return JSON.stringify({
        success: true,
        matched_fingers: ["left_thumb"],
        unmatched_fingers: [],
      });
    }

    throw new Error(`Unknown mock command: ${command}`);
  }

  /**
   * Execute command on native platform
   */
  private async executeNativeCommand(
    command: string,
    stdinData?: string
  ): Promise<string> {
    // This requires a custom Capacitor plugin
    // Example plugin interface:
    //
    // interface ShellExecutorPlugin {
    //   execute(options: {
    //     command: string;
    //     stdin?: string;
    //   }): Promise<{ stdout: string; stderr: string; exitCode: number }>;
    // }
    //
    // Implementation would use:
    // - iOS: Process() or NSTask
    // - Android: Runtime.getRuntime().exec()

    throw new Error(
      `Native CLI execution requires custom Capacitor plugin.

      To implement:
      1. Create Capacitor plugin: @decentralized-did/shell-executor
      2. Implement native shell execution (iOS/Android)
      3. Install plugin: npm install @decentralized-did/shell-executor
      4. Use in this method

      Command: ${command}`
    );
  }

  /**
   * Execute command on web platform
   */
  private async executeWebCommand(
    command: string,
    stdinData?: string
  ): Promise<string> {
    try {
      if (command.includes("generate")) {
        // Parse input data
        const input = stdinData ? JSON.parse(stdinData) : {};

        // Extract wallet address from command
        const walletMatch = command.match(/--wallet\s+(\S+)/);
        const walletAddress = walletMatch ? walletMatch[1] : "addr_test1_demo";

        // Extract storage type from command
        const storageMatch = command.match(/--storage\s+(\S+)/);
        const storage = storageMatch ? storageMatch[1] : "inline";

        // Call API endpoint
        const payload = {
          fingers: input.fingers || [],
          wallet_address: walletAddress,
          storage: storage,
          format: "json",
        };

        const apiResponse = await this.performApiRequest<any>(
          "/api/biometric/generate",
          {
            method: "POST",
            body: JSON.stringify(payload),
          }
        );

        return JSON.stringify(apiResponse);

      } else if (command.includes("verify")) {
        // Parse input data
        const input = stdinData ? JSON.parse(stdinData) : {};

        // Extract expected hash from command
        const hashMatch = command.match(/--expected-hash\s+(\S+)/);
        const expectedHash = hashMatch ? hashMatch[1] : "";

        // Call API endpoint
        const payload = {
          fingers: input.fingers || [],
          helpers: input.helpers || {},
          expected_id_hash: expectedHash,
        };

        const apiResponse = await this.performApiRequest<any>(
          "/api/biometric/verify",
          {
            method: "POST",
            body: JSON.stringify(payload),
          }
        );

        return JSON.stringify(apiResponse);
      }

      throw new Error(`Unknown command: ${command}`);

    } catch (error) {
      if (error instanceof Error &&
        (error.message.includes("API unavailable") || error.message.includes("Ensure the server is running"))) {
        throw new Error(
          `${error.message}

          Command: ${command}`
        );
      }
      throw error;
    }
  }

  /**
   * Transform CLI output to expected format
   */
  private transformGenerateResult(
    cliOutput: any,
    walletAddress: string
  ): BiometricGenerateResult {
    // API returns deterministic DID in Phase 4.5+ format
    let did = cliOutput.did;

    // Fallback for development/mock mode: generate deterministic DID locally
    if (!did && process.env.NODE_ENV === "development") {
      // Extract commitment from CLI output (should be master_key or similar)
      const commitment = cliOutput.commitment || cliOutput.master_key;
      if (commitment) {
        did = generateDeterministicDID(commitment, "mainnet");
      } else {
        // Use id_hash as fallback for mock mode
        const idHash = cliOutput.id_hash || cliOutput.idHash;
        console.warn("⚠️  No commitment found, using id_hash for mock DID");
        did = `did:cardano:mainnet:${idHash}`;
      }
    }

    if (!did) {
      throw new Error("Failed to generate DID: No DID returned from API and no commitment available");
    }

    // Extract id_hash for metadata (not used in DID identifier)
    const idHash = cliOutput.id_hash || cliOutput.idHash;
    const helpers = cliOutput.helpers || {};

    // Prefer server-provided metadata, fallback to synthesized structure
    const rawMetadata = cliOutput.metadata_cip30_inline || cliOutput.metadata;
    const metadata = rawMetadata ? { ...rawMetadata } : {};

    if (!metadata.version) {
      metadata.version = "1.1";
    }

    if (!metadata.walletAddress) {
      metadata.walletAddress = walletAddress;
    }

    if (!Array.isArray(metadata.controllers) || metadata.controllers.length === 0) {
      metadata.controllers = [walletAddress];
    }

    if (!metadata.enrollmentTimestamp) {
      metadata.enrollmentTimestamp = new Date().toISOString();
    }

    if (typeof metadata.revoked !== "boolean") {
      metadata.revoked = false;
    }

    if (!metadata.biometric) {
      metadata.biometric = {
        idHash: idHash,
        helperStorage: "inline",
        helperData: helpers,
      };
    } else {
      if (idHash && !metadata.biometric.idHash) {
        metadata.biometric.idHash = idHash;
      }

      if (!metadata.biometric.helperStorage) {
        metadata.biometric.helperStorage = "inline";
      }

      if (metadata.biometric.helperStorage === "inline" && !metadata.biometric.helperData) {
        metadata.biometric.helperData = helpers;
      }
    }

    return {
      did,
      id_hash: idHash,
      wallet_address: walletAddress, // Kept in metadata, not in DID identifier
      tx_hash: cliOutput.tx_hash,  // Optional: Cardano transaction hash for on-chain enrollment
      helpers,
      metadata_cip30_inline: metadata,
    };
  }

  /**
   * Load helper data from secure storage
   */
  async loadHelperData(
    did: string
  ): Promise<Record<string, HelperDataEntry> | null> {
    try {
      const key = `${HELPER_DATA_KEY_PREFIX}${did}`;
      const data = await SecureStorage.get(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error("Failed to load helper data:", error);
      return null;
    }
  }

  /**
   * Save helper data to secure storage
   */
  async saveHelperData(
    did: string,
    helpers: Record<string, HelperDataEntry>
  ): Promise<void> {
    try {
      const key = `${HELPER_DATA_KEY_PREFIX}${did}`;
      const data = JSON.stringify(helpers);
      await SecureStorage.set(key, data);
    } catch (error) {
      throw new Error(`Failed to save helper data: ${error}`);
    }
  }

  /**
   * Delete helper data from storage
   */
  async deleteHelperData(did: string): Promise<void> {
    try {
      const key = `${HELPER_DATA_KEY_PREFIX}${did}`;
      await SecureStorage.delete(key);
    } catch (error) {
      console.warn("Failed to delete helper data:", error);
    }
  }

  /**
   * Check if helper data exists for a DID
   */
  async hasHelperData(did: string): Promise<boolean> {
    try {
      const key = `${HELPER_DATA_KEY_PREFIX}${did}`;
      return await SecureStorage.keyExists(key);
    } catch (error) {
      return false;
    }
  }

  /**
   * Store the current user's biometric DID
   */
  async saveCurrentDid(did: string): Promise<void> {
    try {
      await SecureStorage.set(CURRENT_DID_KEY, did);
    } catch (error) {
      throw new Error(`Failed to save current DID: ${error}`);
    }
  }

  /**
   * Retrieve the current user's biometric DID
   */
  async getCurrentDid(): Promise<string | null> {
    try {
      return await SecureStorage.get(CURRENT_DID_KEY);
    } catch (error) {
      console.error("Failed to get current DID:", error);
      return null;
    }
  }

  /**
   * Delete the current user's biometric DID
   */
  async deleteCurrentDid(): Promise<void> {
    try {
      await SecureStorage.delete(CURRENT_DID_KEY);
    } catch (error) {
      console.warn("Failed to delete current DID:", error);
    }
  }
}

export const biometricDidService = BiometricDidService.getInstance();
