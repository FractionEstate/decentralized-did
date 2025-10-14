/**
 * Types for biometric DID integration with Python CLI
 */

export interface FingerData {
  finger_id: string;
  minutiae: Array<[number, number, number]>;
}

export interface BiometricEnrollmentInput {
  fingers: FingerData[];
}

export interface HelperDataEntry {
  finger_id: string;
  salt_b64: string;
  auth_b64: string;
  grid_size: number;
  angle_bins: number;
}

export interface BiometricGenerateResult {
  did: string; // Deterministic format: did:cardano:{network}:{base58_hash}
  id_hash?: string; // Optional: for backward compatibility (not used in deterministic format)
  wallet_address: string; // Kept in metadata only, not in DID identifier
  helpers: Record<string, HelperDataEntry>;
  metadata_cip30_inline: {
    version: number; // 1.1 for deterministic DIDs with multi-controller support
    walletAddress?: string; // Deprecated: use controllers array instead
    controllers?: string[]; // Multi-controller support (metadata v1.1)
    biometric: {
      idHash?: string; // Optional: for backward compatibility
      commitment?: string; // Base58 encoded biometric commitment (deterministic format)
      helperStorage: string;
      helperData: Record<string, HelperDataEntry>;
    };
    enrollmentTimestamp?: string; // ISO 8601 timestamp (metadata v1.1)
    revoked?: boolean; // Revocation flag (metadata v1.1)
  };
}

export interface BiometricVerifyInput {
  fingers: FingerData[];
  helpers: Record<string, HelperDataEntry>;
  expected_id_hash: string;
}

export interface BiometricVerifyResult {
  success: boolean;
  matched_fingers: string[];
  unmatched_fingers: string[];
  error?: string;
}

export enum BiometricEnrollmentStatus {
  NotStarted = "not-started",
  InProgress = "in-progress",
  Complete = "complete",
  Failed = "failed",
}

export interface BiometricEnrollmentState {
  status: BiometricEnrollmentStatus;
  completedFingers: string[];
  totalFingers: number;
  did?: string;
  idHash?: string;
  helperData?: Record<string, HelperDataEntry>;
  error?: string;
}

export const FINGER_IDS = [
  "left_thumb",
  "left_index",
  "left_middle",
  "left_ring",
  "left_little",
  "right_thumb",
  "right_index",
  "right_middle",
  "right_ring",
  "right_little",
] as const;

export type FingerId = (typeof FINGER_IDS)[number];

export interface FingerprintCaptureResult {
  finger_id: FingerId;
  minutiae: Array<[number, number, number]>;
  quality: number;
}
