import { IonRefresher, IonRefresherContent, useIonViewWillEnter } from "@ionic/react";
import { useEffect, useState } from "react";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import {
  fetchBalance,
  fetchNFTs,
  fetchTransactionHistory,
  getCurrentAddressData,
  setCurrentAddress,
} from "../../../store/reducers/tokensCache";
import { TabLayout } from "../../components/layout/TabLayout";
import { PageHeader } from "../../components/PageHeader";
import { showError } from "../../utils/error";
import "./Tokens.scss";

// Placeholder address - in production this would come from wallet state
const DEMO_ADDRESS = "addr1qx2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3n0d3vllmyqwsx5wktcd8cc3sq835lu7drv2xwl2wywfgse35a3x";

const Tokens = () => {
  const dispatch = useAppDispatch();
  const addressData = useAppSelector(getCurrentAddressData);
  const [activeTab, setActiveTab] = useState<"balance" | "nfts" | "history">("balance");

  useIonViewWillEnter(() => {
    // Set current address and load data
    dispatch(setCurrentAddress(DEMO_ADDRESS));
    loadTokenData();
  });

  const loadTokenData = () => {
    try {
      dispatch(fetchBalance(DEMO_ADDRESS));
      dispatch(fetchNFTs(DEMO_ADDRESS));
      dispatch(fetchTransactionHistory({ address: DEMO_ADDRESS, limit: 50 }));
    } catch (error) {
      showError("Failed to load token data", error, dispatch);
    }
  };

  const handleRefresh = (event: CustomEvent) => {
    loadTokenData();
    setTimeout(() => {
      event.detail.complete();
    }, 1000);
  };

  const renderBalance = () => {
    if (addressData?.isLoading && !addressData?.balance) {
      return <div className="loading-placeholder">Loading balance...</div>;
    }

    if (addressData?.error) {
      return <div className="error-message">{addressData.error}</div>;
    }

    if (!addressData?.balance) {
      return <div className="empty-state">No balance data available</div>;
    }

    const { balance } = addressData;

    return (
      <div className="balance-container">
        <div className="ada-balance">
          <div className="balance-label">ADA Balance</div>
          <div className="balance-amount">{balance.ada_amount} ₳</div>
          <div className="balance-lovelace">{balance.ada_lovelace} lovelace</div>
        </div>

        {balance.total_assets > 0 && (
          <div className="assets-section">
            <div className="section-header">Native Assets ({balance.total_assets})</div>
            <div className="assets-list">
              {balance.assets.map((asset, index) => (
                <div key={`${asset.policy_id}-${asset.asset_name}-${index}`} className="asset-item">
                  <div className="asset-name">
                    {asset.asset_name_ascii || asset.asset_name.substring(0, 16) + "..."}
                  </div>
                  <div className="asset-quantity">{asset.display_quantity}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderNFTs = () => {
    if (addressData?.isLoading && !addressData?.nfts) {
      return <div className="loading-placeholder">Loading NFTs...</div>;
    }

    if (addressData?.error) {
      return <div className="error-message">{addressData.error}</div>;
    }

    const nfts = addressData?.nfts || [];

    if (nfts.length === 0) {
      return <div className="empty-state">No NFTs found</div>;
    }

    return (
      <div className="nfts-container">
        <div className="nfts-grid">
          {nfts.map((nft, index) => (
            <div key={`${nft.asset.policy_id}-${nft.asset.asset_name}-${index}`} className="nft-card">
              {nft.metadata?.image && (
                <img
                  src={nft.metadata.image.replace("ipfs://", "https://ipfs.io/ipfs/")}
                  alt={nft.display_name}
                  className="nft-image"
                />
              )}
              <div className="nft-name">{nft.display_name}</div>
              {nft.metadata?.description && (
                <div className="nft-description">{nft.metadata.description}</div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderHistory = () => {
    if (addressData?.isLoading && !addressData?.transactions) {
      return <div className="loading-placeholder">Loading transactions...</div>;
    }

    if (addressData?.error) {
      return <div className="error-message">{addressData.error}</div>;
    }

    const transactions = addressData?.transactions || [];

    if (transactions.length === 0) {
      return <div className="empty-state">No transactions found</div>;
    }

    return (
      <div className="transactions-container">
        <div className="transactions-list">
          {transactions.map((tx) => (
            <div key={tx.tx_hash} className="transaction-item">
              <div className="tx-hash">
                {tx.tx_hash.substring(0, 16)}...{tx.tx_hash.substring(tx.tx_hash.length - 8)}
              </div>
              <div className="tx-details">
                {tx.block_height && <span>Block: {tx.block_height}</span>}
                {tx.fee_ada && <span>Fee: {tx.fee_ada} ₳</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <TabLayout
      pageId="tokens-page"
      header={true}
      customClass="tokens-page"
      title="Tokens"
    >
      <IonRefresher slot="fixed" onIonRefresh={handleRefresh}>
        <IonRefresherContent />
      </IonRefresher>

      <div className="tokens-tabs">
        <button
          className={`tab-button ${activeTab === "balance" ? "active" : ""}`}
          onClick={() => setActiveTab("balance")}
        >
          Balance
        </button>
        <button
          className={`tab-button ${activeTab === "nfts" ? "active" : ""}`}
          onClick={() => setActiveTab("nfts")}
        >
          NFTs
        </button>
        <button
          className={`tab-button ${activeTab === "history" ? "active" : ""}`}
          onClick={() => setActiveTab("history")}
        >
          History
        </button>
      </div>

      <div className="tokens-content">
        {activeTab === "balance" && renderBalance()}
        {activeTab === "nfts" && renderNFTs()}
        {activeTab === "history" && renderHistory()}
      </div>
    </TabLayout>
  );
};

export default Tokens;
