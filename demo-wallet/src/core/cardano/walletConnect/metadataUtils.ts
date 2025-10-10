import {
  Cip30MetadataEntry,
  Cip30MetadataEnvelope,
  StoredBiometricMetadata,
} from "./peerConnection.types";

type ParsedBiometricMetadata = Omit<StoredBiometricMetadata, "createdAt">;

const HELPER_STORAGE_VALUES = new Set(["inline", "external"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function toMetadataEntry(
  entry: unknown,
  index: number
): Cip30MetadataEntry {
  if (!Array.isArray(entry) || entry.length !== 2) {
    throw new Error(`metadata entry at index ${index} must be a [label, payload] tuple`);
  }
  const [label, payload] = entry;
  if (typeof label !== "number" || Number.isNaN(label)) {
    throw new Error(`metadata label at index ${index} must be a finite number`);
  }
  return [label, payload] as Cip30MetadataEntry;
}

function validateHelperStorage(value: unknown): asserts value is string {
  if (typeof value !== "string" || !HELPER_STORAGE_VALUES.has(value)) {
    throw new Error(
      "biometric.helperStorage must be either 'inline' or 'external'"
    );
  }
}

export function parseCip30MetadataEnvelope(
  envelope: unknown
): ParsedBiometricMetadata {
  if (!isRecord(envelope)) {
    throw new Error("CIP-30 metadata envelope must be an object");
  }

  const { did, metadata } = envelope as Record<string, unknown>;

  if (typeof did !== "string" || did.trim().length === 0) {
    throw new Error("CIP-30 metadata envelope requires a non-empty did string");
  }

  if (!Array.isArray(metadata) || metadata.length === 0) {
    throw new Error("CIP-30 metadata envelope requires at least one metadata entry");
  }

  const normalisedMetadata = metadata.map(toMetadataEntry);
  const [label, payload] = normalisedMetadata[0];

  if (!isRecord(payload)) {
    throw new Error("metadata payload must be an object");
  }

  const { walletAddress, biometric } = payload as Record<string, unknown>;

  if (typeof walletAddress !== "string" || walletAddress.trim().length === 0) {
    throw new Error("metadata payload requires a non-empty walletAddress string");
  }

  if (!isRecord(biometric)) {
    throw new Error("metadata payload requires a biometric object");
  }

  const { idHash, helperStorage, helperUri, helperData } = biometric as Record<
    string,
    unknown
  >;

  if (typeof idHash !== "string" || idHash.trim().length === 0) {
    throw new Error("biometric.idHash must be a non-empty string");
  }

  validateHelperStorage(helperStorage);

  if (helperUri !== undefined && typeof helperUri !== "string") {
    throw new Error("biometric.helperUri, when provided, must be a string");
  }

  let parsedHelperData: Record<string, unknown> | undefined;
  if (helperData !== undefined) {
    if (!isRecord(helperData)) {
      throw new Error("biometric.helperData must be an object when provided");
    }
    parsedHelperData = helperData;
  }

  return {
    did,
    label,
    metadata: normalisedMetadata,
    walletAddress,
    idHash,
    helperStorage,
    helperUri: helperUri as string | undefined,
    helperData: parsedHelperData,
  };
}

export type { ParsedBiometricMetadata };
