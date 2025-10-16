import {
  Cip30MetadataEntry,
  Cip30MetadataEnvelope,
  HelperStorageMode,
  StoredBiometricMetadata,
} from "./peerConnection.types";

type ParsedBiometricMetadata = Omit<StoredBiometricMetadata, "createdAt">;

const HELPER_STORAGE_VALUES = new Set<HelperStorageMode>(["inline", "external"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function toMetadataEntry(entry: unknown, index: number): Cip30MetadataEntry {
  if (!Array.isArray(entry) || entry.length !== 2) {
    throw new Error(
      `metadata entry at index ${index} must be a [label, payload] tuple`
    );
  }
  const [label, payload] = entry;
  if (typeof label !== "number" || Number.isNaN(label)) {
    throw new Error(
      `metadata label at index ${index} must be a finite number`
    );
  }
  return [label, payload] as Cip30MetadataEntry;
}

function parseHelperStorage(value: unknown): HelperStorageMode {
  if (typeof value !== "string") {
    throw new Error(
      "biometric.helperStorage must be either 'inline' or 'external'"
    );
  }

  const storage = value as HelperStorageMode;
  if (!HELPER_STORAGE_VALUES.has(storage)) {
    throw new Error(
      "biometric.helperStorage must be either 'inline' or 'external'"
    );
  }

  return storage;
}

function normaliseVersion(rawVersion: unknown, fallback: string | undefined): string {
  if (typeof rawVersion === "string" && rawVersion.trim().length > 0) {
    return rawVersion.trim();
  }

  if (typeof rawVersion === "number" && Number.isFinite(rawVersion)) {
    return rawVersion.toString();
  }

  if (fallback) {
    return fallback;
  }

  throw new Error("metadata payload requires a version identifier");
}

function normaliseControllers(
  rawControllers: unknown,
  walletAddress?: string
): string[] {
  if (Array.isArray(rawControllers)) {
    const controllers = rawControllers.map((value, index) => {
      if (typeof value !== "string" || value.trim().length === 0) {
        throw new Error(
          `metadata.controllers[${index}] must be a non-empty string`
        );
      }
      return value.trim();
    });

    if (controllers.length === 0) {
      throw new Error("metadata.controllers must not be empty");
    }

    return controllers;
  }

  if (typeof walletAddress === "string" && walletAddress.trim().length > 0) {
    return [walletAddress.trim()];
  }

  throw new Error(
    "metadata payload requires at least one controller or walletAddress"
  );
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
    throw new Error(
      "CIP-30 metadata envelope requires at least one metadata entry"
    );
  }

  const normalisedMetadata = metadata.map(toMetadataEntry);
  const [label, payload] = normalisedMetadata[0];

  if (!isRecord(payload)) {
    throw new Error("metadata payload must be an object");
  }

  const {
    walletAddress: rawWalletAddress,
    controllers: rawControllers,
    version: rawVersion,
    biometric,
    enrollmentTimestamp,
    revoked,
    revokedAt,
  } = payload as Record<string, unknown>;

  let walletAddress: string | undefined;
  if (typeof rawWalletAddress === "string" && rawWalletAddress.trim().length > 0) {
    walletAddress = rawWalletAddress.trim();
  }

  const version = normaliseVersion(
    rawVersion,
    walletAddress ? "1.0" : undefined
  );

  const controllers = normaliseControllers(rawControllers, walletAddress);

  if (!isRecord(biometric)) {
    throw new Error("metadata payload requires a biometric object");
  }

  const { idHash, helperStorage, helperUri, helperData, commitment } =
    biometric as Record<string, unknown>;

  let resolvedIdHash: string | undefined;
  if (typeof idHash === "string" && idHash.trim().length > 0) {
    resolvedIdHash = idHash.trim();
  } else if (typeof commitment === "string" && commitment.trim().length > 0) {
    resolvedIdHash = commitment.trim();
  }

  if (!resolvedIdHash) {
    throw new Error("biometric.idHash must be a non-empty string");
  }

  const parsedHelperStorage = parseHelperStorage(helperStorage);

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

  let parsedEnrollmentTimestamp: string | undefined;
  if (enrollmentTimestamp !== undefined) {
    if (typeof enrollmentTimestamp !== "string" || enrollmentTimestamp.trim().length === 0) {
      throw new Error("enrollmentTimestamp must be an ISO 8601 string when provided");
    }
    parsedEnrollmentTimestamp = enrollmentTimestamp;
  }

  let parsedRevoked: boolean | undefined;
  if (revoked !== undefined) {
    if (typeof revoked !== "boolean") {
      throw new Error("revoked must be a boolean when provided");
    }
    parsedRevoked = revoked;
  }

  let parsedRevokedAt: string | undefined;
  if (revokedAt !== undefined) {
    if (typeof revokedAt !== "string" || revokedAt.trim().length === 0) {
      throw new Error("revokedAt must be an ISO 8601 string when provided");
    }
    parsedRevokedAt = revokedAt;
  }

  const resolvedWalletAddress = walletAddress ?? controllers[0];

  return {
    did,
    label,
    version,
    controllers,
    walletAddress: resolvedWalletAddress,
    metadata: normalisedMetadata,
    idHash: resolvedIdHash,
    helperStorage: parsedHelperStorage,
    helperUri: helperUri as string | undefined,
    helperData: parsedHelperData,
    enrollmentTimestamp: parsedEnrollmentTimestamp,
    revoked: parsedRevoked,
    revokedAt: parsedRevokedAt,
  };
}

export type { ParsedBiometricMetadata };
