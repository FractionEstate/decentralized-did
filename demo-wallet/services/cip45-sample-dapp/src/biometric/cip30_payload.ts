// Auto-generated reference payload for the CIP-30 biometric demo.
// Values come from `python -m decentralized_did.cli demo-kit` using
// `examples/sample_fingerprints.json` and the addr_test1demo123 wallet.

export const biometricDid = "did:cardano:addr_test1demo123#WkR7uRUFPOEQjbHSVibT9WaXKFk1TzKt5mzTHFR8vdw";
export const walletAddress = "addr_test1demo123";

export const cip30MetadataEntries = [
  [
    1990,
    {
      version: 1,
      walletAddress,
      biometric: {
        idHash: "WkR7uRUFPOEQjbHSVibT9WaXKFk1TzKt5mzTHFR8vdw",
        helperStorage: "inline",
        helperData: {
          left_thumb: {
            finger_id: "left_thumb",
            salt_b64: "ULgvOb7Vv0iv3aUT5Upcuw==",
            auth_b64: "f89O2W40apXpXyUY5kbt9Q==",
            grid_size: 0.05,
            angle_bins: 32,
          },
          left_index: {
            finger_id: "left_index",
            salt_b64: "SHm6B6onyepMfecpPa4gfQ==",
            auth_b64: "twqOnQj_nxJuirvIaN5ezw==",
            grid_size: 0.05,
            angle_bins: 32,
          },
          left_middle: {
            finger_id: "left_middle",
            salt_b64: "CvWHUGq1nsR_KNgJjHrN6A==",
            auth_b64: "TMet18ph9LbROm6KqJ4aww==",
            grid_size: 0.05,
            angle_bins: 32,
          },
          left_ring: {
            finger_id: "left_ring",
            salt_b64: "pyP3s17_dtp9EU70uPxtnQ==",
            auth_b64: "qhSo3n9SLJeADBX10xHJwg==",
            grid_size: 0.05,
            angle_bins: 32,
          },
          left_little: {
            finger_id: "left_little",
            salt_b64: "8P3KNrGz_78IuRiUmqYVMA==",
            auth_b64: "fgjai973Qbw2z-0iuNkOJA==",
            grid_size: 0.05,
            angle_bins: 32,
          },
          right_thumb: {
            finger_id: "right_thumb",
            salt_b64: "XSolk0GXf1jjp4IFRm7eVQ==",
            auth_b64: "5Hzek5bAJ65iZOOb-wX1ew==",
            grid_size: 0.05,
            angle_bins: 32,
          },
          right_index: {
            finger_id: "right_index",
            salt_b64: "0y8ICq6GzuwdES_5y0ahgg==",
            auth_b64: "a9Of5fC_iEHhszRyqvHXLQ==",
            grid_size: 0.05,
            angle_bins: 32,
          },
          right_middle: {
            finger_id: "right_middle",
            salt_b64: "WznT4lh7vwD_hgJ9NZaatQ==",
            auth_b64: "tedmtnzHigr84PBWczSCsQ==",
            grid_size: 0.05,
            angle_bins: 32,
          },
          right_ring: {
            finger_id: "right_ring",
            salt_b64: "f4NzvIJiJj8SFNgCN6Gspw==",
            auth_b64: "7KDOzc5GQiToSi37AysSyw==",
            grid_size: 0.05,
            angle_bins: 32,
          },
          right_little: {
            finger_id: "right_little",
            salt_b64: "IFBLKZ3Idj4eJrmaGFy-vw==",
            auth_b64: "BQUkc7BLoMVDx835oM9r9Q==",
            grid_size: 0.05,
            angle_bins: 32,
          },
        },
      },
    },
  ],
] as const;

export const cip30MetadataMap = new Map(
  cip30MetadataEntries.map(([label, payload]) => [BigInt(label), payload])
);

export const helperData = (
  cip30MetadataEntries[0][1] as {
    biometric: { helperData: Record<string, unknown> };
  }
).biometric.helperData;

export const demoMetadataEnvelope = {
  did: biometricDid,
  metadata: cip30MetadataEntries,
} as const;

export const demoMetadataJson = JSON.stringify(demoMetadataEnvelope, null, 2);

export const demoMetadataLabel = cip30MetadataEntries[0][0];

export const demoHelperStorageMode = (
  cip30MetadataEntries[0][1] as { biometric: { helperStorage: string } }
).biometric.helperStorage;
