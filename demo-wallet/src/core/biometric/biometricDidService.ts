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

const HELPER_DATA_KEY_PREFIX = "biometric_helpers_";
const CURRENT_DID_KEY = "biometric_current_did";

export class BiometricDidService {
  private static instance: BiometricDidService;
  private pythonCliPath: string;

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
   * Generate biometric DID and helper data from fingerprint minutiae
   */
  async generate(
    input: BiometricEnrollmentInput,
    walletAddress: string
  ): Promise<BiometricGenerateResult> {
    try {
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
      // Return mock generate result
      return JSON.stringify({
        did: "did:cardano:addr_test1_mock#MockIdHash123",
        id_hash: "MockIdHash123",
        wallet_address: "addr_test1_mock",
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
    // Backend API implementation
    const API_BASE_URL = process.env.BIOMETRIC_API_URL || "http://localhost:8000";

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
        const response = await fetch(`${API_BASE_URL}/api/biometric/generate`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            fingers: input.fingers || [],
            wallet_address: walletAddress,
            storage: storage,
            format: "json",
          }),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || "API request failed");
        }

        return JSON.stringify(await response.json());

      } else if (command.includes("verify")) {
        // Parse input data
        const input = stdinData ? JSON.parse(stdinData) : {};

        // Extract expected hash from command
        const hashMatch = command.match(/--expected-hash\s+(\S+)/);
        const expectedHash = hashMatch ? hashMatch[1] : "";

        // Call API endpoint
        const response = await fetch(`${API_BASE_URL}/api/biometric/verify`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            fingers: input.fingers || [],
            helpers: input.helpers || {},
            expected_id_hash: expectedHash,
          }),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || "API request failed");
        }

        return JSON.stringify(await response.json());
      }

      throw new Error(`Unknown command: ${command}`);

    } catch (error) {
      if (error instanceof Error && error.message.includes("fetch")) {
        throw new Error(
          `Backend API unavailable. Please ensure API server is running at ${API_BASE_URL}.

          To start the API server:
          1. cd /path/to/decentralized-did
          2. python api_server_mock.py

          Or set BIOMETRIC_API_URL environment variable to your API endpoint.

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
    const idHash = cliOutput.id_hash || cliOutput.idHash;
    const did = cliOutput.did || `did:cardano:${walletAddress}#${idHash}`;

    return {
      did,
      id_hash: idHash,
      wallet_address: walletAddress,
      helpers: cliOutput.helpers || {},
      metadata_cip30_inline: {
        version: 1,
        walletAddress: walletAddress,
        biometric: {
          idHash: idHash,
          helperStorage: "inline",
          helperData: cliOutput.helpers || {},
        },
      },
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
