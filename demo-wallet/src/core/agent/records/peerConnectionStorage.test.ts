import { describe, expect, test, beforeEach, jest } from "@jest/globals";

import { PeerConnectionMetadataRecord } from "./peerConnectionMetadataRecord";
import { PeerConnectionStorage } from "./peerConnectionStorage";
import type { StorageService } from "../../storage/storage.types";
import type { StoredBiometricMetadata } from "../../cardano/walletConnect/peerConnection.types";

const storageServiceMock = {
  save: jest.fn<
    (record: PeerConnectionMetadataRecord) => Promise<PeerConnectionMetadataRecord>
  >(),
  delete: jest.fn<
    (record: PeerConnectionMetadataRecord) => Promise<void>
  >(),
  deleteById: jest.fn<
    (id: string) => Promise<void>
  >(),
  update: jest.fn<
    (record: PeerConnectionMetadataRecord) => Promise<void>
  >(),
  findById: jest.fn<
    (id: string, recordClass: any) => Promise<PeerConnectionMetadataRecord | null>
  >(),
  findAllByQuery: jest.fn<
    (query: any, recordClass: any) => Promise<PeerConnectionMetadataRecord[]>
  >(),
  getAll: jest.fn<
    (recordClass: any) => Promise<PeerConnectionMetadataRecord[]>
  >(),
};

const peerConnectionStorage = new PeerConnectionStorage(
  storageServiceMock as unknown as StorageService<PeerConnectionMetadataRecord>,
);

const biometricMetadata: StoredBiometricMetadata = {
  did: "did:cardano:testnet:zQmXyZ1a2B3c4D5e6F7g8H9i0J",
  label: 1990,
  walletAddress: "addr_test1qpl4w3u",
  idHash: "zQmXyZ1a2B3c4D5e6F7g8H9i0J",
  helperStorage: "inline",
  helperData: { sample: true },
  metadata: [[1990, { dummy: true }]],
  createdAt: new Date().toISOString(),
};

const peerConnectionMetadataRecordProps = {
  id: "id",
  name: "name",
  url: "url",
  iconB64: "icon",
  selectedAid: "aid",
  createdAt: new Date(),
  biometricMetadata,
};

const peerConnectionMetadataRecord = new PeerConnectionMetadataRecord({
  ...peerConnectionMetadataRecordProps,
});

const peerConnectionMetadataRecord2 = new PeerConnectionMetadataRecord({
  ...peerConnectionMetadataRecordProps,
  id: "id2",
});

describe("Connection service of agent", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  test("Should get all peer connection", async () => {
    storageServiceMock.getAll.mockResolvedValue([
      peerConnectionMetadataRecord,
      peerConnectionMetadataRecord2,
    ]);
    expect(await peerConnectionStorage.getAllPeerConnectionMetadata()).toEqual(
      [peerConnectionMetadataRecord, peerConnectionMetadataRecord2].map(
        (record) => ({
          id: record.id,
          iconB64: record.iconB64,
          name: record.name,
          selectedAid: record.selectedAid,
          url: record.url,
          createdAt: record.createdAt.toISOString(),
          biometricMetadata: record.biometricMetadata,
        })
      )
    );
  });

  test("Should get peer connection meta data record", async () => {
    storageServiceMock.findById.mockResolvedValue(peerConnectionMetadataRecord);
    expect(
      await peerConnectionStorage.getPeerConnectionMetadata(
        peerConnectionMetadataRecord.id
      )
    ).toEqual(peerConnectionMetadataRecord);
  });

  test("Should get peer connection", async () => {
    storageServiceMock.findById.mockResolvedValue(peerConnectionMetadataRecord);
    expect(
      await peerConnectionStorage.getPeerConnection(
        peerConnectionMetadataRecord.id
      )
    ).toEqual({
      id: peerConnectionMetadataRecord.id,
      iconB64: peerConnectionMetadataRecord.iconB64,
      name: peerConnectionMetadataRecord.name,
      selectedAid: peerConnectionMetadataRecord.selectedAid,
      url: peerConnectionMetadataRecord.url,
      createdAt: peerConnectionMetadataRecord.createdAt.toISOString(),
      biometricMetadata: peerConnectionMetadataRecord.biometricMetadata,
    });
  });

  test("Should throw if peerConnection metadata record is missing", async () => {
    storageServiceMock.findById.mockResolvedValue(null);
    await expect(
      peerConnectionStorage.getPeerConnectionMetadata(
        peerConnectionMetadataRecord.id
      )
    ).rejects.toThrowError(
      PeerConnectionStorage.PEER_CONNECTION_METADATA_RECORD_MISSING
    );
  });

  test("Should save peerConnection metadata record", async () => {
    await peerConnectionStorage.createPeerConnectionMetadataRecord(
      peerConnectionMetadataRecordProps
    );
    expect(storageServiceMock.save).toBeCalledWith(peerConnectionMetadataRecord);
  });

  test("Should update peer connection metadata record", async () => {
    storageServiceMock.findById.mockResolvedValue(peerConnectionMetadataRecord);
    await peerConnectionStorage.updatePeerConnectionMetadata(
      peerConnectionMetadataRecord.id,
      {
        name: "update name",
      }
    );
    expect(storageServiceMock.update).toBeCalled();
  });
});
