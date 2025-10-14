import {
  PeerConnectionMetadataRecord,
  PeerConnectionMetadataRecordProps,
} from "./peerConnectionMetadataRecord";
import type { StoredBiometricMetadata } from "../../cardano/walletConnect/peerConnection.types";

const mockData: PeerConnectionMetadataRecordProps = {
  id: "id",
  name: "name",
  url: "url",
  iconB64: "icon",
  selectedAid: "aid",
  biometricMetadata: {
    did: "did:cardano:testnet:zQmXyZ1a2B3c4D5e6F7g8H9i0J",
    label: 1990,
    walletAddress: "addr_test1qpl4w3u",
    idHash: "zQmXyZ1a2B3c4D5e6F7g8H9i0J",
    helperStorage: "inline",
    metadata: [[1990, { dummy: true }]] as StoredBiometricMetadata["metadata"],
    createdAt: new Date().toISOString(),
  },
};

describe("Peer Connection Record", () => {
  test("should fill the record based on supplied props", () => {
    const createdAt = new Date();
    const settingsRecord = new PeerConnectionMetadataRecord({
      ...mockData,
      createdAt: createdAt,
    });
    settingsRecord.getTags();
    expect(settingsRecord.type).toBe(PeerConnectionMetadataRecord.type);
    expect(settingsRecord.id).toBe(mockData.id);
    expect(settingsRecord.name).toBe(mockData.name);
    expect(settingsRecord.url).toBe(mockData.url);
    expect(settingsRecord.selectedAid).toBe(mockData.selectedAid);
    expect(settingsRecord.iconB64).toBe(mockData.iconB64);
    expect(settingsRecord.createdAt).toBe(createdAt);
    expect(settingsRecord.biometricMetadata).toEqual(mockData.biometricMetadata);
  });
});
