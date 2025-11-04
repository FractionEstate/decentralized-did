import { IonRefresher, IonRefresherContent, IonIcon, useIonViewWillEnter } from "@ionic/react";
import { albumsOutline, imagesOutline, timeOutline } from "ionicons/icons";
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
  const [isRefreshing, setIsRefreshing] = useState(false);

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
    setIsRefreshing(true);
    loadTokenData();
    setTimeout(() => {
      event.detail.complete();
      setIsRefreshing(false);
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
      <div className="balance-view">
        {/* Primary ADA Balance Card */}
        <div className="balance-card-primary">
          <div className="balance-label">Total Balance</div>
          <div className="balance-amount">{balance.ada_amount} <span className="currency">₳</span></div>
          <div className="balance-lovelace">{balance.ada_lovelace.toLocaleString()} lovelace</div>
        </div>

        {balance.total_assets > 0 && (
          <div className="assets-section">
            <h3 className="section-header">Native Assets ({balance.total_assets})</h3>
            <div className="assets-list">
              {balance.assets.map((asset, index) => (
                <div key={`${asset.policy_id}-${asset.asset_name}-${index}`} className="asset-item">
                  <div className="asset-icon">
                    <IonIcon icon={albumsOutline} />
                  </div>
                  <div className="asset-info">
                    <div className="asset-name">
                      {asset.asset_name_ascii || asset.asset_name.substring(0, 20) + "..."}
                    </div>
                    <div className="asset-policy">Policy: {asset.policy_id.substring(0, 12)}...</div>
                  </div>
                  <div className="asset-amount">{asset.display_quantity}</div>
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
      return (
        <div className="empty-state">
          <IonIcon icon={imagesOutline} className="empty-icon" />
          <div className="empty-title">No NFTs Found</div>
          <div className="empty-description">
            Your wallet doesn't contain any NFTs yet.
          </div>
        </div>
      );
    }

    return (
      <div className="nfts-view">
        <h3 className="section-header">NFT Collection ({nfts.length})</h3>
        <div className="nfts-grid">
          {nfts.map((nft, index) => (
            <div key={`${nft.asset.policy_id}-${nft.asset.asset_name}-${index}`} className="nft-card">
              {nft.metadata?.image && (
                <div className="nft-image-container">
                  <img
                    src={nft.metadata.image.replace("ipfs://", "https://ipfs.io/ipfs/")}
                    alt={nft.display_name}
                    className="nft-image"
                  />
                </div>
              )}
              <div className="nft-info">
                <div className="nft-name">{nft.display_name}</div>
                {nft.metadata?.description && (
                  <div className="nft-description">{nft.metadata.description.substring(0, 80)}{nft.metadata.description.length > 80 ? '...' : ''}</div>
                )}
              </div>
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
      return (
        <div className="empty-state">
          <IonIcon icon={timeOutline} className="empty-icon" />
          <div className="empty-title">No Transactions</div>
          <div className="empty-description">
            Transaction history will appear here.
          </div>
        </div>
      );
    }

    return (
      <div className="history-view">
        <h3 className="section-header">Recent Transactions ({transactions.length})</h3>
        <div className="transactions-list">
          {transactions.map((tx) => (
            <div key={tx.tx_hash} className="transaction-item">
              <div className="tx-icon">
                <IonIcon icon={timeOutline} />
              </div>
              <div className="tx-info">
                <div className="tx-hash">
                  {tx.tx_hash.substring(0, 12)}...{tx.tx_hash.substring(tx.tx_hash.length - 6)}
                </div>
                <div className="tx-details">
                  {tx.block_height && <span>Block {tx.block_height.toLocaleString()}</span>}
                  {tx.block_height && tx.fee_ada && <span className="tx-separator">•</span>}
                  {tx.fee_ada && <span>Fee: {tx.fee_ada} ₳</span>}
                </div>
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
      header={false}
      customClass="tokens-page"
      theme="dark"
    >
      <IonRefresher slot="fixed" onIonRefresh={handleRefresh}>
        <IonRefresherContent />
      </IonRefresher>

      <div className="tokens-tabs">
        <button
          className={`tab-button ${activeTab === "balance" ? "active" : ""}`}
          onClick={() => setActiveTab("balance")}
        >
          <IonIcon icon={albumsOutline} />
          <span>Balance</span>
        </button>
        <button
          className={`tab-button ${activeTab === "nfts" ? "active" : ""}`}
          onClick={() => setActiveTab("nfts")}
        >
          <IonIcon icon={imagesOutline} />
          <span>NFTs</span>
        </button>
        <button
          className={`tab-button ${activeTab === "history" ? "active" : ""}`}
          onClick={() => setActiveTab("history")}
        >
          <IonIcon icon={timeOutline} />
          <span>History</span>
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
