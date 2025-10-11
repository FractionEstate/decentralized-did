import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useCardano } from "@cardano-foundation/cardano-connect-with-wallet";
import { NetworkType } from "@cardano-foundation/cardano-connect-with-wallet-core";
import {
  attachBiometricMetadata,
  type Cip30Metadata,
} from "../biometric/attachBiometricMetadata";

export interface WalletInfo {
  name: string;
  address: string;
  oobi: string;
}

const defaultWalletInfo: WalletInfo = {
  name: "",
  address: "",
  oobi: "",
};

const wait = (duration: number) =>
  new Promise((resolve) => setTimeout(resolve, duration));

const waitForProvider = async (
  walletName: string,
  timeoutMs = 6000,
  intervalMs = 150,
) => {
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    const provider = window.cardano?.[walletName];
    if (provider) {
      return provider;
    }
    await wait(intervalMs);
  }

  throw new Error(`Timeout while connecting ${walletName} wallet`);
};

export interface PeerConnectionState {
  meerkatAddress: string;
  walletInfo: WalletInfo;
  awaitingApproval: boolean;
  isConnected: boolean;
  connectionError: string | null;
}

export interface PeerConnectionControls {
  approveConnection: () => Promise<void>;
  rejectConnection: () => void;
  disconnectWallet: () => void;
  clearConnectionError: () => void;
  signPayload: (payload: string) => Promise<string>;
  sendMetadata: (metadata: Cip30Metadata) => Promise<void>;
}

export type PeerConnectionHook = PeerConnectionState & PeerConnectionControls;

export const usePeerConnection = (): PeerConnectionHook => {
  const [walletInfo, setWalletInfo] = useState<WalletInfo>(defaultWalletInfo);
  const [awaitingApproval, setAwaitingApproval] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const acceptCallbackRef = useRef<() => void>(() => undefined);
  const rejectCallbackRef = useRef<() => void>(() => undefined);

  const {
    dAppConnect,
    meerkatAddress,
    initDappConnect,
    disconnect,
    connect,
  } = useCardano({
    limitNetwork: NetworkType.TESTNET,
  });

  const clearConnectionError = useCallback(() => {
    setConnectionError(null);
  }, []);

  useEffect(() => {
    if (dAppConnect.current !== null) {
      return;
    }

    const verifyConnection = (
      info: WalletInfo,
      callback: (granted: boolean, autoconnect: boolean) => void,
    ) => {
      setWalletInfo(info);
      setAwaitingApproval(true);
      acceptCallbackRef.current = () => callback(true, true);
      rejectCallbackRef.current = () => callback(false, false);
    };

    const onApiInject = async (name: string) => {
      try {
        const provider = await waitForProvider(name, 1200, 100);
        const enabledApi = await provider.enable();
        const keriIdentifier = await enabledApi.experimental?.getKeriIdentifier?.();

        setWalletInfo((prev) => ({
          ...prev,
          name,
          address: keriIdentifier?.id ?? prev.address,
          oobi: keriIdentifier?.oobi ?? prev.oobi,
        }));

        setAwaitingApproval(false);
        setIsConnected(true);
        setConnectionError(null);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to initialise wallet API";
        setConnectionError(message);
        setIsConnected(false);
        setAwaitingApproval(false);
      }
    };

    const onApiEject = () => {
      setWalletInfo(defaultWalletInfo);
      setAwaitingApproval(false);
      setIsConnected(false);
    };

    const onP2PConnect = () => {
      // The demo currently relies on the wallet to drive session state.
      // This callback is kept for future flows (e.g. auto-approve heuristics).
    };

    initDappConnect(
      "CIP-45 Sample Demo",
      window.location.href,
      verifyConnection,
      onApiInject,
      onApiEject,
      [
        "wss://tracker.webtorrent.dev:443/announce",
        "wss://dev.btt.cf-identity-wallet.metadata.dev.cf-deployments.org",
      ],
      onP2PConnect,
    );
  }, [dAppConnect, initDappConnect]);

  const approveConnection = useCallback(async () => {
    if (!awaitingApproval || !walletInfo.name) {
      throw new Error("No wallet awaiting approval");
    }

    try {
      acceptCallbackRef.current?.();
      await connect(walletInfo.name);
      const provider = await waitForProvider(walletInfo.name);
      const enabledApi = await provider.enable();
      const keriIdentifier = await enabledApi.experimental?.getKeriIdentifier?.();

      setWalletInfo((prev) => ({
        ...prev,
        address: keriIdentifier?.id ?? prev.address,
        oobi: keriIdentifier?.oobi ?? prev.oobi,
      }));

      setAwaitingApproval(false);
      setIsConnected(true);
      setConnectionError(null);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to approve wallet connection";
      setConnectionError(message);
      setIsConnected(false);
      throw new Error(message);
    }
  }, [awaitingApproval, connect, walletInfo.name]);

  const rejectConnection = useCallback(() => {
    rejectCallbackRef.current?.();
    setAwaitingApproval(false);
    setWalletInfo(defaultWalletInfo);
  }, []);

  const disconnectWallet = useCallback(() => {
    disconnect();
    setWalletInfo(defaultWalletInfo);
    setAwaitingApproval(false);
    setIsConnected(false);
  }, [disconnect]);

  const requireConnectedProvider = useCallback(async () => {
    if (!walletInfo.name) {
      throw new Error("No wallet connected");
    }

    const provider = window.cardano?.[walletInfo.name];
    if (!provider) {
      throw new Error("Wallet not available in browser context");
    }

    const enabledApi = await provider.enable();
    if (!enabledApi) {
      throw new Error("Wallet enable() did not return an API");
    }

    return enabledApi;
  }, [walletInfo.name]);

  const signPayload = useCallback(
    async (payload: string) => {
      if (!isConnected) {
        throw new Error("Wallet not connected");
      }

      const enabledApi = await requireConnectedProvider();
      const targetAddress = walletInfo.address;

      if (!targetAddress) {
        throw new Error("Wallet AID unavailable");
      }

      try {
        const signature = await enabledApi.experimental?.signKeri?.(
          targetAddress,
          payload,
        );

        if (!signature) {
          throw new Error("Wallet did not return a signature");
        }

        return signature;
      } catch (err) {
        if (err && typeof err === "object" && "code" in err) {
          const code = (err as { code?: number }).code;
          if (code === 2) {
            throw new Error("User declined to sign the payload");
          }
        }

        const message =
          err instanceof Error ? err.message : "Failed to sign payload";
        throw new Error(message);
      }
    },
    [isConnected, requireConnectedProvider, walletInfo.address],
  );

  const sendMetadata = useCallback(
    async (metadata: Cip30Metadata) => {
      if (!isConnected) {
        throw new Error("Wallet not connected");
      }

      const enabledApi = await requireConnectedProvider();
      const txApi = enabledApi.experimental?.tx;

      if (!txApi || typeof txApi.send !== "function") {
        throw new Error("Wallet missing experimental.tx.send helper");
      }

      const payload = attachBiometricMetadata({}, metadata);
      await txApi.send(payload);
    },
    [isConnected, requireConnectedProvider],
  );

  const state = useMemo<PeerConnectionState>(() => {
    return {
      meerkatAddress,
      walletInfo,
      awaitingApproval,
      isConnected,
      connectionError,
    };
  }, [awaitingApproval, connectionError, isConnected, meerkatAddress, walletInfo]);

  return {
    ...state,
    approveConnection,
    rejectConnection,
    disconnectWallet,
    clearConnectionError,
    signPayload,
    sendMetadata,
  };
};
