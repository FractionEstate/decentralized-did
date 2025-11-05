import { IonRefresher, IonRefresherContent, IonIcon, useIonViewWillEnter } from "@ionic/react";
import { albumsOutline, imagesOutline, timeOutline } from "ionicons/icons";
import { useEffect, useState } from "react";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import {
  fetchBalance,
  fetchNFTs,
  fetchTransactionHistory,
  getCurrentAddress,
  getCurrentAddressData,
} from "../../../store/reducers/tokensCache";
import { TabLayout } from "../../components/layout/TabLayout/TabLayout";
import { EmptyState } from "../../components/common/EmptyState";
import { LoadingPlaceholder } from "../../components/common/LoadingPlaceholder";
import { ErrorDisplay } from "../../components/common/ErrorDisplay";
import { showError } from "../../utils/error";
import "./Wallet.scss";

// Current address now comes from store; if missing, UI prompts to connect

const Wallet = () => {
  const dispatch = useAppDispatch();
  const currentAddress = useAppSelector(getCurrentAddress);
  const addressData = useAppSelector(getCurrentAddressData);
  const [activeTab, setActiveTab] = useState<"balance" | "nfts" | "history">("balance");
  const [isRefreshing, setIsRefreshing] = useState(false);

  useIonViewWillEnter(() => {
    if (currentAddress) {
      loadTokenData(currentAddress);
    }
  });

  const loadTokenData = (address?: string) => {
    try {
      const addr = address || currentAddress;
      if (!addr) return;
      dispatch(fetchBalance(addr));
      dispatch(fetchNFTs(addr));
      dispatch(fetchTransactionHistory({ address: addr, limit: 50 }));
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
      return <LoadingPlaceholder message="Loading wallet balance..." />;
    }

    if (addressData?.error) {
      return <ErrorDisplay error={addressData.error} onRetry={loadTokenData} />;
    }

    if (!addressData?.balance) {
      return (
        <EmptyState
          icon={albumsOutline}
          title="No Balance Data"
          description="Unable to load wallet balance. Please try refreshing."
          actionLabel="Retry"
          onAction={loadTokenData}
        />
      );
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
      return <LoadingPlaceholder message="Loading NFT collection..." />;
    }

    if (addressData?.error) {
      return <ErrorDisplay error={addressData.error} onRetry={loadTokenData} />;
    }

    const nfts = addressData?.nfts || [];

    if (nfts.length === 0) {
      return (
        <EmptyState
          icon={imagesOutline}
          title="No NFTs Found"
          description="Your wallet doesn't contain any NFTs yet."
        />
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
      return <LoadingPlaceholder message="Loading transaction history..." />;
    }

    if (addressData?.error) {
      return <ErrorDisplay error={addressData.error} onRetry={loadTokenData} />;
    }

    const transactions = addressData?.transactions || [];

    if (transactions.length === 0) {
      return (
        <EmptyState
          icon={timeOutline}
          title="No Transactions"
          description="Transaction history will appear here."
        />
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
      pageId="wallet-page"
      header={false}
      customClass="wallet-page"
      theme="dark"
    >
      <IonRefresher slot="fixed" onIonRefresh={handleRefresh}>
        <IonRefresherContent />
      </IonRefresher>

      {!currentAddress ? (
        <div className="wallet-content">
          <EmptyState
            icon={albumsOutline}
            title="No Wallet Connected"
            description="Connect or select a wallet to view your balance, NFTs, and history."
          />
        </div>
      ) : (
        <>
          <div className="wallet-tabs">
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

          <div className="wallet-content">
            {activeTab === "balance" && renderBalance()}
            {activeTab === "nfts" && renderNFTs()}
            {activeTab === "history" && renderHistory()}
          </div>
        </>
      )}
    </TabLayout>
  );
};

export default Wallet;
