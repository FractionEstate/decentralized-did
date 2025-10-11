export interface MetadataSummary {
  helperKeys: string[];
  helperStorage?: string;
  helperUri?: string;
  walletAddress?: string;
  labels: bigint[];
}

export interface MetadataParseResult {
  map: Map<bigint, unknown>;
  summary: MetadataSummary;
}

export class MetadataParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "MetadataParseError";
  }
}

const isPlainObject = (value: unknown): value is Record<string, unknown> => {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
};

export const parseMetadataEnvelope = (input: string): MetadataParseResult => {
  let parsed: unknown;

  try {
    parsed = JSON.parse(input);
  } catch (err) {
    throw new MetadataParseError("Metadata is not valid JSON");
  }

  if (!isPlainObject(parsed)) {
    throw new MetadataParseError("Metadata envelope must be an object");
  }

  const metadataField = parsed.metadata;

  if (!Array.isArray(metadataField)) {
    throw new MetadataParseError("Metadata envelope requires a metadata array");
  }

  const summary: MetadataSummary = {
    helperKeys: [],
    labels: [],
  };

  const metadataMap = new Map<bigint, unknown>();

  for (const entry of metadataField) {
    if (!Array.isArray(entry) || entry.length < 2) {
      throw new MetadataParseError("Metadata entries must be [label, payload] tuples");
    }

    const [labelRaw, payload] = entry;

    let label: bigint;

    try {
      label = typeof labelRaw === "bigint" ? labelRaw : BigInt(labelRaw);
    } catch (err) {
      throw new MetadataParseError("Metadata label must be an integer");
    }

    metadataMap.set(label, payload);
    summary.labels.push(label);

    if (!isPlainObject(payload)) {
      continue;
    }

    if (typeof payload.walletAddress === "string") {
      summary.walletAddress = payload.walletAddress;
    }

    if (!isPlainObject(payload.biometric)) {
      continue;
    }

    const biometric = payload.biometric as Record<string, unknown>;

    if (typeof biometric.helperStorage === "string") {
      summary.helperStorage = biometric.helperStorage;
    }

    if (typeof biometric.helperUri === "string") {
      summary.helperUri = biometric.helperUri;
    }

    if (isPlainObject(biometric.helperData)) {
      summary.helperKeys = Object.keys(
        biometric.helperData as Record<string, unknown>,
      );
    }
  }

  return {
    map: metadataMap,
    summary,
  };
};

export const isMetadataParseError = (err: unknown): err is MetadataParseError => {
  return err instanceof MetadataParseError;
};
