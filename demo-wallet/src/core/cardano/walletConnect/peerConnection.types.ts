interface BaseEventEmitter {
  type: string;
  payload: Record<string, unknown>;
}

type Cip30MetadataEntry = [number, unknown];

interface Cip30MetadataEnvelope {
  did: string;
  metadata: Cip30MetadataEntry[];
}

interface StoredBiometricMetadata {
  did: string;
  label: number;
  walletAddress: string;
  idHash: string;
  helperStorage: string;
  helperUri?: string;
  helperData?: Record<string, unknown>;
  metadata: Cip30MetadataEntry[];
  createdAt: string;
}

interface ExperimentalAPIFunctions {
  getKeriIdentifier: () => Promise<{ id: string; oobi: string }>;
  signKeri: (
    identifier: string,
    payload: string
  ) => Promise<string | { error: PeerConnectionError }>;
  storeBiometricMetadata: (
    metadata: Cip30MetadataEnvelope,
    dAppAddress?: string
  ) => Promise<void>;
}

enum PeerConnectionEventTypes {
  PeerConnectSign = "PeerConnectSign",
  PeerConnected = "PeerConnected",
  PeerDisconnected = "PeerDisconnected",
  PeerConnectionBroken = "PeerConnectionBroken",
  BiometricMetadataUpdated = "BiometricMetadataUpdated",
}

interface PeerConnectSigningEvent extends BaseEventEmitter {
  type: typeof PeerConnectionEventTypes.PeerConnectSign;
  payload: {
    identifier: string;
    payload: string;
    approvalCallback: (approvalStatus: boolean) => void;
  };
}

interface PeerConnectedEvent extends BaseEventEmitter {
  type: typeof PeerConnectionEventTypes.PeerConnected;
  payload: {
    identifier: string;
    dAppAddress: string;
  };
}

interface PeerDisconnectedEvent extends BaseEventEmitter {
  type: typeof PeerConnectionEventTypes.PeerDisconnected;
  payload: {
    dAppAddress: string;
  };
}

interface PeerConnectionBrokenEvent extends BaseEventEmitter {
  type: typeof PeerConnectionEventTypes.PeerConnectionBroken;
}

interface PeerBiometricMetadataEvent extends BaseEventEmitter {
  type: typeof PeerConnectionEventTypes.BiometricMetadataUpdated;
  payload: {
    dAppAddress: string;
    metadata: StoredBiometricMetadata;
  };
}

interface PeerConnectionError {
  code: number;
  info: string;
}

interface PeerConnection {
  id: string;
  name?: string;
  url?: string;
  iconB64?: string;
  selectedAid?: string;
  createdAt?: string;
  biometricMetadata?: StoredBiometricMetadata;
}

export const TxSignError: { [key: string]: PeerConnectionError } = {
  ProofGeneration: {
    code: 1,
    info: "User has accepted the transaction sign, but the wallet was unable to sign the transaction (e.g. not having some of the private keys).",
  },
  UserDeclined: { code: 2, info: "User declined to sign the transaction." },
  TimeOut: { code: 3, info: "Time out" },
};

export { PeerConnectionEventTypes };
export type {
  Cip30MetadataEntry,
  Cip30MetadataEnvelope,
  ExperimentalAPIFunctions,
  PeerBiometricMetadataEvent,
  PeerConnectSigningEvent,
  PeerConnectedEvent,
  PeerDisconnectedEvent,
  PeerConnectionBrokenEvent,
  PeerConnectionError,
  PeerConnection,
  StoredBiometricMetadata,
};
