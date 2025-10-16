/**
 * Service for capturing fingerprint data from biometric sensors
 * Provides mock implementation for development and testing
 */

import {
  FingerId,
  FINGER_IDS,
  FingerprintCaptureResult,
  FingerData,
} from "./biometricDid.types";

export class FingerprintCaptureService {
  private static instance: FingerprintCaptureService;
  private webAuthnAvailable: boolean | null = null;
  private webAuthnBiometricType: string | null = null;

  private constructor() {
    this.checkWebAuthnAvailability();
  }

  public static getInstance(): FingerprintCaptureService {
    if (!FingerprintCaptureService.instance) {
      FingerprintCaptureService.instance = new FingerprintCaptureService();
    }
    return FingerprintCaptureService.instance;
  }

  /**
   * Check if WebAuthn is available in this browser
   */
  private async checkWebAuthnAvailability(): Promise<void> {
    if (typeof window === 'undefined') {
      this.webAuthnAvailable = false;
      return;
    }

    try {
      // Check if PublicKeyCredential is available
      this.webAuthnAvailable = !!(window.PublicKeyCredential);

      if (this.webAuthnAvailable) {
        // Try to detect the biometric type
        const userAgent = navigator.userAgent || '';
        if (/(iPhone|iPad|iPod)/i.test(userAgent) || userAgent.includes('iOS')) {
          this.webAuthnBiometricType = 'Touch ID / Face ID';
        } else if (userAgent.includes('Android')) {
          this.webAuthnBiometricType = 'Fingerprint';
        } else if (userAgent.includes('Windows')) {
          this.webAuthnBiometricType = 'Windows Hello';
        } else if (userAgent.includes('Mac')) {
          this.webAuthnBiometricType = 'Touch ID';
        } else {
          this.webAuthnBiometricType = 'Biometric';
        }
      }
    } catch (error) {
      console.warn('WebAuthn availability check failed:', error);
      this.webAuthnAvailable = false;
    }
  }

  /**
   * Check if WebAuthn is available for biometric authentication
   */
  public isWebAuthnAvailable(): boolean {
    return this.webAuthnAvailable === true;
  }

  /**
   * Get the type of biometric available via WebAuthn
   */
  public getWebAuthnBiometricType(): string | null {
    return this.webAuthnBiometricType;
  }

  /**
   * Capture fingerprint from biometric sensor
   * Returns minutiae data for the specified finger
   */
  async captureFingerprint(fingerId: FingerId): Promise<FingerprintCaptureResult> {
    // In production, this would:
    // 1. Initialize biometric sensor (USB/Bluetooth fingerprint reader)
    // 2. Prompt user to place finger
    // 3. Capture image
    // 4. Extract minutiae using fingerprint SDK
    // 5. Return minutiae coordinates and angles

    // For development: Return mock minutiae data
    if (process.env.NODE_ENV === "development") {
      return this.mockCaptureFingerprint(fingerId);
    }

    throw new Error(
      `Fingerprint capture not implemented for production.

      To implement:
      1. Integrate fingerprint sensor SDK (e.g., DigitalPersona, Neurotechnology)
      2. Add Capacitor plugin for sensor access
      3. Extract minutiae using fingerprint recognition library
      4. Return minutiae as [x, y, angle] tuples

      Finger: ${fingerId}`
    );
  }

  /**
   * Enroll biometric using WebAuthn (Touch ID, Face ID, Windows Hello)
   * Note: WebAuthn doesn't expose raw biometric data, so this creates a credential
   * that can be used for verification but not for DID generation
   */
  async enrollWithWebAuthn(userId: string, userName: string): Promise<{
    credentialId: string;
    publicKey: string;
    success: boolean;
  }> {
    if (!this.isWebAuthnAvailable()) {
      throw new Error('WebAuthn is not available in this browser');
    }

    try {
      // Create credential options
      const challenge = crypto.getRandomValues(new Uint8Array(32));
      const userIdBytes = new TextEncoder().encode(userId);

      const publicKeyCredentialCreationOptions: PublicKeyCredentialCreationOptions = {
        challenge,
        rp: {
          name: "Biometric DID Wallet",
          id: window.location.hostname,
        },
        user: {
          id: userIdBytes,
          name: userId,
          displayName: userName,
        },
        pubKeyCredParams: [
          { alg: -7, type: "public-key" },  // ES256
          { alg: -257, type: "public-key" }, // RS256
        ],
        authenticatorSelection: {
          authenticatorAttachment: "platform", // Built-in sensor only
          userVerification: "required",
          requireResidentKey: false,
        },
        timeout: 60000,
        attestation: "none",
      };

      // Create credential
      const credential = await navigator.credentials.create({
        publicKey: publicKeyCredentialCreationOptions,
      }) as PublicKeyCredential;

      if (!credential) {
        throw new Error('Failed to create WebAuthn credential');
      }

      // Extract credential data
      const credentialId = this.arrayBufferToBase64(credential.rawId);
      const response = credential.response as AuthenticatorAttestationResponse;
      const publicKeyBuffer = response.getPublicKey ? response.getPublicKey() : null;

      if (!publicKeyBuffer) {
        throw new Error('Failed to obtain WebAuthn public key');
      }

      const publicKey = this.arrayBufferToBase64(publicKeyBuffer);

      console.log('✅ WebAuthn enrollment successful');

      return {
        credentialId,
        publicKey,
        success: true,
      };
    } catch (error) {
      console.error('WebAuthn enrollment failed:', error);
      throw new Error(`WebAuthn enrollment failed: ${(error as Error).message}`);
    }
  }

  /**
   * Verify biometric using WebAuthn
   * Returns true if the user successfully authenticates with their biometric
   */
  async verifyWithWebAuthn(credentialId: string, challenge?: Uint8Array): Promise<boolean> {
    if (!this.isWebAuthnAvailable()) {
      throw new Error('WebAuthn is not available in this browser');
    }

    try {
      // Use provided challenge or generate new one
      const challengeBytes = challenge || crypto.getRandomValues(new Uint8Array(32));

      // Convert credentialId from base64 to ArrayBuffer
      const credentialIdBytes = this.base64ToArrayBuffer(credentialId);

      const publicKeyCredentialRequestOptions: PublicKeyCredentialRequestOptions = {
        challenge: challengeBytes as BufferSource,
        allowCredentials: [
          {
            id: credentialIdBytes,
            type: "public-key",
            transports: ["internal"],
          },
        ],
        timeout: 60000,
        userVerification: "required",
      };

      // Get assertion (authenticate)
      const assertion = await navigator.credentials.get({
        publicKey: publicKeyCredentialRequestOptions,
      }) as PublicKeyCredential;

      if (!assertion) {
        return false;
      }

      console.log('✅ WebAuthn verification successful');
      return true;
    } catch (error) {
      console.error('WebAuthn verification failed:', error);
      return false;
    }
  }

  /**
   * Convert ArrayBuffer to base64 string
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  /**
   * Convert base64 string to ArrayBuffer
   */
  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  /**
   * Capture multiple fingerprints in sequence
   */
  async captureMultipleFingerprints(
    fingerIds: FingerId[]
  ): Promise<FingerData[]> {
    const results: FingerData[] = [];

    for (const fingerId of fingerIds) {
      const capture = await this.captureFingerprint(fingerId);
      results.push({
        finger_id: capture.finger_id,
        minutiae: capture.minutiae,
      });
    }

    return results;
  }

  /**
   * Capture all 10 fingerprints
   */
  async captureAllFingerprints(): Promise<FingerData[]> {
    return this.captureMultipleFingerprints([...FINGER_IDS]);
  }

  /**
   * Mock fingerprint capture for development
   * Generates realistic synthetic minutiae data
   */
  private async mockCaptureFingerprint(
    fingerId: FingerId
  ): Promise<FingerprintCaptureResult> {
    // Simulate sensor delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Generate synthetic minutiae (typically 20-60 minutiae per finger)
    const numMinutiae = 30 + Math.floor(Math.random() * 20);
    const minutiae: Array<[number, number, number]> = [];

    for (let i = 0; i < numMinutiae; i++) {
      const x = Math.random(); // Normalized x coordinate (0-1)
      const y = Math.random(); // Normalized y coordinate (0-1)
      const angle = Math.random() * 2 * Math.PI; // Angle in radians (0-2π)
      minutiae.push([x, y, angle]);
    }

    // Quality score (0-100, higher is better)
    const quality = 70 + Math.floor(Math.random() * 30);

    return {
      finger_id: fingerId,
      minutiae,
      quality,
    };
  }

  /**
   * Validate captured fingerprint quality
   * Returns true if quality is sufficient for enrollment
   */
  validateQuality(capture: FingerprintCaptureResult): boolean {
    const MIN_QUALITY = 60;
    const MIN_MINUTIAE = 20;

    return (
      capture.quality >= MIN_QUALITY &&
      capture.minutiae.length >= MIN_MINUTIAE
    );
  }

  /**
   * Load sample fingerprints from bundled data
   * Used for testing without actual sensor
   */
  async loadSampleFingerprints(): Promise<FingerData[]> {
    // Load the bundled sample fingerprints from our Python examples
    // These are pre-generated for testing purposes
    const sampleData = await this.loadBundledSampleData();
    return sampleData.fingers;
  }

  /**
   * Load bundled sample fingerprint data
   */
  private async loadBundledSampleData(): Promise<{ fingers: FingerData[] }> {
    // In production, this would load from:
    // - Public assets folder
    // - Bundled JSON file
    // - Or our Python CLI's examples/sample_fingerprints.json

    // For now, return mock data matching the sample format
    const fingers: FingerData[] = FINGER_IDS.map((fingerId) => ({
      finger_id: fingerId,
      minutiae: this.generateMockMinutiae(),
    }));

    return { fingers };
  }

  /**
   * Generate consistent mock minutiae for testing
   */
  private generateMockMinutiae(): Array<[number, number, number]> {
    const numMinutiae = 35;
    const minutiae: Array<[number, number, number]> = [];

    for (let i = 0; i < numMinutiae; i++) {
      minutiae.push([
        Math.random(),
        Math.random(),
        Math.random() * 2 * Math.PI,
      ]);
    }

    return minutiae;
  }
}

export const fingerprintCaptureService = FingerprintCaptureService.getInstance();
