import { cip30MetadataMap } from "./cip30_payload";

export type Cip30Metadata = Map<bigint, unknown>;

export interface Cip30Transaction {
  metadata?: Cip30Metadata;
  // The sample helper keeps the type open so existing transaction fields remain untouched.
  [key: string]: unknown;
}

export const attachBiometricMetadata = <T extends Cip30Transaction>(tx: T) => {
  const mergedMetadata: Cip30Metadata = new Map(tx.metadata ?? []);

  for (const [label, payload] of cip30MetadataMap.entries()) {
    mergedMetadata.set(label, payload);
  }

  return {
    ...tx,
    metadata: mergedMetadata,
  };
};
