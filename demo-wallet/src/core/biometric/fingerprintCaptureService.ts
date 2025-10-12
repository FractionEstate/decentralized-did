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

  private constructor() { }

  public static getInstance(): FingerprintCaptureService {
    if (!FingerprintCaptureService.instance) {
      FingerprintCaptureService.instance = new FingerprintCaptureService();
    }
    return FingerprintCaptureService.instance;
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
