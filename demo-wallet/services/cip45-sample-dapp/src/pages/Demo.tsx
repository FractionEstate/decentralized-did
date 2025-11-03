import React, { useEffect, useMemo, useState } from "react";
import { QRCode } from "react-qrcode-logo";
import { useCardano } from "@cardano-foundation/cardano-connect-with-wallet";
import { NetworkType } from "@cardano-foundation/cardano-connect-with-wallet-core";
import idwLogo from "/idw.png";
import {
  biometricDid,
  demoHelperStorageMode,
  demoMetadataJson,
  demoMetadataLabel,
} from "../biometric/cip30_payload";
import {
  attachBiometricMetadata,
  type Cip30Metadata,
} from "../biometric/attachBiometricMetadata";
import {
  isMetadataParseError,
  parseMetadataEnvelope,
  type MetadataSummary,
} from "../biometric/metadataPreview";

interface IWalletInfoExtended {
  name: string;
  address: string;
  oobi: string;
}

const Demo: React.FC = () => {
  const initialMetadata = useMemo(() => {
    try {
      return parseMetadataEnvelope(demoMetadataJson);
    } catch (err) {
      const fallbackSummary: MetadataSummary = { helperKeys: [], labels: [] };
      if (isMetadataParseError(err) || err instanceof Error) {
        console.warn("Failed to parse default demo metadata", err);
      }
      return { map: new Map<bigint, unknown>(), summary: fallbackSummary };
    }
  }, []);

  const [payload, setPayload] = useState<string>(() => demoMetadataJson);
  const [signature, setSignature] = useState<string>("");
  const [showAcceptButton, setShowAcceptButton] = useState<boolean>(false);
  const [walletIsConnected, setWalletIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [metadataMap, setMetadataMap] = useState<Cip30Metadata>(initialMetadata.map);
  const [metadataSummary, setMetadataSummary] = useState<MetadataSummary>(
    initialMetadata.summary,
  );
  const [metadataError, setMetadataError] = useState<string | null>(null);
  const [txStatus, setTxStatus] = useState<string>("");

  const defaultWallet: IWalletInfoExtended = {
    name: "",
    address: "",
    oobi: "",
  };

  const [peerConnectWalletInfo, setPeerConnectWalletInfo] =
    useState<IWalletInfoExtended>(defaultWallet);

  // @ts-ignore: TS6133
  const [onPeerConnectAccept, setOnPeerConnectAccept] = useState(() => () => {
    /*TODO */
  });
  // @ts-ignore: TS6133
  const [onPeerConnectReject, setOnPeerConnectReject] = useState(() => () => {
    /*TODO */
  });

  const {
    dAppConnect,
    meerkatAddress,
    initDappConnect,
    disconnect,
    connect,
  } = useCardano({
    limitNetwork: NetworkType.TESTNET,
  });

  useEffect(() => {
    if (dAppConnect.current === null) {
      const verifyConnection = (
        walletInfo: IWalletInfoExtended,
        callback: (granted: boolean, autoconnect: boolean) => void,
      ) => {
        setPeerConnectWalletInfo(walletInfo);
        setShowAcceptButton(true);

        setOnPeerConnectAccept(() => () => callback(true, true));
        setOnPeerConnectReject(() => () => callback(false, false));
      };

      const onApiInject = async (name: string) => {
        const api = window.cardano && window.cardano[name];
        if (api) {
          const enabledApi = await api.enable();
          const keriIdentifier =
            await enabledApi.experimental.getKeriIdentifier();

          setPeerConnectWalletInfo((prev) => ({
            ...prev,
            name,
            address: keriIdentifier.id,
            oobi: keriIdentifier.oobi,
          }));

          setWalletIsConnected(true);
          setShowAcceptButton(false);
          setError("");
          setTxStatus("");
        } else {
          setError(`Timeout while connecting P2P ${name} wallet`);
        }
      };

      // @ts-ignore: TS6133
      const onApiEject = (name: string): void => {
        setPeerConnectWalletInfo(defaultWallet);
        setError("");
        setTxStatus("");
        disconnect();
      };

      // @ts-ignore
      const onP2PConnect = (a): void => { };

      initDappConnect(
        "Cip45 sample demo",
        window.location.href,
        verifyConnection,
        onApiInject,
        onApiEject,
        ["wss://tracker.webtorrent.dev:443/announce", "wss://dev.btt.cf-identity-wallet.metadata.dev.cf-deployments.org"],
        onP2PConnect,
      );
    }
  }, []);

  useEffect(() => {
    const previousMetadataError = metadataError;

    try {
      const parsed = parseMetadataEnvelope(payload);
      setMetadataMap(parsed.map);
      setMetadataSummary(parsed.summary);

      if (previousMetadataError) {
        setMetadataError(null);
        setError((prev) => (prev === previousMetadataError ? "" : prev));
      }
    } catch (err) {
      const message = isMetadataParseError(err)
        ? err.message
        : err instanceof Error
          ? err.message
          : "Unknown metadata parsing error.";
      setMetadataError(message);
    }
  }, [payload, metadataError]);

  const disconnectWallet = () => {
    disconnect();
    setPeerConnectWalletInfo(defaultWallet);
    setShowAcceptButton(false);
    setWalletIsConnected(false);
    setSignature("");
    setError("");
    setTxStatus("");
  };

  const resetToDemoPayload = () => {
    setPayload(demoMetadataJson);
    setSignature("");
    setTxStatus("");
    setError("");
  };

  const handleAcceptWallet = () => {
    if (peerConnectWalletInfo) {
      onPeerConnectAccept();
      connect(peerConnectWalletInfo.name).then(async () => {
        if (peerConnectWalletInfo.name === "idw_p2p") {
          const start = Date.now();
          const interval = 100;
          const timeout = 5000;

          const checkApi = setInterval(async () => {
            const api =
              // @ts-ignore
              window.cardano && window.cardano[peerConnectWalletInfo.name];
            if (api || Date.now() - start > timeout) {
              clearInterval(checkApi);
              if (api) {
                const enabledApi = await api.enable();
                const keriIdentifier =
                  await enabledApi.experimental.getKeriIdentifier();
                setPeerConnectWalletInfo((prev) => ({
                  ...prev,
                  address: keriIdentifier.id,
                  oobi: keriIdentifier.oobi,
                }));
                setShowAcceptButton(false);
                setWalletIsConnected(true);
                setError("");
                setTxStatus("");
              } else {
                setError(`Timeout while connecting P2P ${peerConnectWalletInfo.name} wallet`);
                setWalletIsConnected(false);
              }
            }
          }, interval);
        } else {
          setError(`Wrong wallet: ${peerConnectWalletInfo.name}`);
        }
      });
    }
  };

  const signMessageWithWallet = async () => {

    if (
      window.cardano &&
      window.cardano["idw_p2p"]
    ) {
      setError("");
      setTxStatus("");
      const api = window.cardano["idw_p2p"];
      const enabledApi = await api.enable();
      try {
        const signedMessage = await enabledApi.experimental.signKeri(
          peerConnectWalletInfo?.address,
          payload
        );

        setSignature(signedMessage);
        // @ts-ignore
      } catch (e) {
        // @ts-ignore
        setError(e.code === 2
          ? "User declined to sign"
          // @ts-ignore
          : e.info)
      }
    } else {
      setError("Wallet not connected")
    }
  };

  const sendMetadataViaWallet = async () => {
    if (metadataError) {
      setError(metadataError);
      return;
    }

    if (!walletIsConnected) {
      setError("Wallet not connected");
      return;
    }

    if (!window.cardano || !window.cardano["idw_p2p"]) {
      setError("Wallet not connected");
      return;
    }

    setError("");
    setTxStatus("");

    try {
      const enabledApi = await window.cardano["idw_p2p"].enable();
      const txApi = enabledApi.experimental?.tx;

      if (!txApi || typeof txApi.send !== "function") {
        setError("Wallet missing experimental.tx.send helper");
        return;
      }

      const payloadWithMetadata = attachBiometricMetadata({}, metadataMap);
      await txApi.send(payloadWithMetadata);
      setTxStatus("Sent CIP-30 metadata request to wallet. Confirm in the wallet UI.");
    } catch (err) {
      const reason = err && typeof err === "object" && "message" in err
        ? String((err as { message?: unknown }).message)
        : "Failed to send metadata";
      setError(reason);
    }
  };

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold text-center text-gray-800">CIP45 Demo Dapp</h1>
      <p className="mt-4 text-lg text-gray-600 text-center">Scan the QR code with your IDW wallet to proceed.</p>
      <div className="p-4 border-2 border-dashed border-gray-400 rounded-lg flex flex-col items-center">
        <div className="h-8" />
        <QRCode
          value={meerkatAddress}
          size={250}
          fgColor={"black"}
          bgColor={"white"}
          qrStyle={"squares"}
          logoImage={idwLogo}
          logoWidth={60}
          logoHeight={60}
          logoOpacity={1}
          quietZone={10}
        />
        <div className="text-sm font-semibold text-gray-500 mt-2">Meerkat Address: {meerkatAddress}</div>
        <div className="h-12 my-4">
          {
            showAcceptButton ? <button className="bg-blue-500 text-white font-bold py-3 px-6 rounded-lg"
              onClick={handleAcceptWallet} disabled={!showAcceptButton}>
              Accept connection with {peerConnectWalletInfo.name}
            </button> : walletIsConnected ? <button className="bg-red-600 text-white font-bold py-3 px-6 rounded-lg"
              onClick={disconnectWallet}>
              Disconnect Wallet
            </button> : null
          }
        </div>
      </div>
      <div className="my-6 text-center">
        <div className="h-24 mt-2">
          {peerConnectWalletInfo.address.length ? (
            <div className="flex flex-col space-y-2">
              <div className="flex justify-between items-center">
                <p className="text-green-500 w-1/3 text-right pr-2">Connected Wallet:</p>
                <p className="text-gray-800 w-2/3 text-left pl-2">{peerConnectWalletInfo.name}</p>
              </div>
              <div className="flex justify-between items-center">
                <p className="text-gray-800 w-1/3 text-right pr-2">AID:</p>
                <p className="text-gray-800 w-2/3 text-left pl-2">{peerConnectWalletInfo.address}</p>
              </div>
              <div className="flex justify-between items-center">
                <p className="text-gray-800 w-1/3 text-right pr-2">OOBI:</p>
                <p
                  className="text-gray-800 w-2/3 text-left pl-2 w-full break-words"
                >
                  {peerConnectWalletInfo.oobi}
                </p>
              </div>
            </div>
          ) : null}
          {error.length ? <p className="text-red-500">{error}</p> : null}
        </div>
      </div>
      <div className="mt-10 mb-6 p-6 border border-gray-200 rounded-lg bg-gray-50 text-left">
        <h2 className="text-xl font-semibold text-gray-700">Demo Biometric Metadata</h2>
        <p className="mt-2 text-sm text-gray-600">DID: {biometricDid}</p>
        <p className="mt-1 text-sm text-gray-600">Metadata label: {demoMetadataLabel}</p>
        <p className="mt-1 text-sm text-gray-600">Helper storage: {metadataSummary.helperStorage ?? demoHelperStorageMode}</p>
        <p className="mt-1 text-sm text-gray-600">
          Helper entries: {metadataSummary.helperKeys.length ? metadataSummary.helperKeys.join(", ") : "None detected"}
        </p>
        <p className="mt-1 text-sm text-gray-600">Helper URI: {metadataSummary.helperUri ?? "Embedded in metadata"}</p>
        <p className="mt-1 text-sm text-gray-600">Wallet address: {metadataSummary.walletAddress ?? "Unknown"}</p>
        {metadataError ? (
          <p className="mt-2 text-sm text-red-600">{metadataError}</p>
        ) : null}
        <button
          className="mt-4 bg-gray-200 text-gray-800 font-semibold py-2 px-4 rounded-lg"
          onClick={resetToDemoPayload}
        >
          Reset to demo payload
        </button>
      </div>
      <div className="mb-6 text-center">
        <textarea
          className="form-textarea mt-1 block w-full rounded-lg p-4 bg-white text-gray-900"
          rows={4}
          placeholder="Enter payload here..."
          value={payload}
          onChange={(e) => setPayload(e.target.value)}
        />
        <div className="mt-4 flex flex-wrap items-center justify-center gap-4">
          <button className="bg-blue-500 text-white font-bold py-3 px-6 rounded-lg"
            onClick={signMessageWithWallet} disabled={!walletIsConnected || !payload.trim()}>
            Sign Payload
          </button>
          <button className="bg-green-600 text-white font-bold py-3 px-6 rounded-lg"
            onClick={sendMetadataViaWallet}
            disabled={!walletIsConnected || !!metadataError}>
            Send CIP-30 metadata
          </button>
        </div>
        {txStatus ? (
          <p className="mt-4 text-sm text-green-600">{txStatus}</p>
        ) : null}
      </div>
      {
        signature.length ? <>
          <p className="mt-14 bold text-xl text-gray-600 text-left">Signature:</p>
          <div className="mb-6 mt-2 p-4 bg-gray-100 rounded-lg h-24">
            <p className="text-gray-700 w-full break-words">{signature}</p>
          </div>
        </> : null
      }

    </div>
  );
};

export { Demo };

