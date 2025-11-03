import { IonRefresher, IonRefresherContent, useIonViewWillEnter } from "@ionic/react";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import {
  fetchNFTs,
  getCurrentAddressData,
  setCurrentAddress,
} from "../../../store/reducers/tokensCache";
import { TabLayout } from "../../components/layout/TabLayout";
import { showError } from "../../utils/error";
import "./NFTs.scss";

// Placeholder address - in production this would come from wallet state
const DEMO_ADDRESS = "addr1qx2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3n0d3vllmyqwsx5wktcd8cc3sq835lu7drv2xwl2wywfgse35a3x";

const NFTs = () => {
  const dispatch = useAppDispatch();
  const addressData = useAppSelector(getCurrentAddressData);

  useIonViewWillEnter(() => {
    // Set current address and load NFT data
    dispatch(setCurrentAddress(DEMO_ADDRESS));
    loadNFTData();
  });

  const loadNFTData = () => {
    try {
      dispatch(fetchNFTs(DEMO_ADDRESS));
    } catch (error) {
      showError("Failed to load NFTs", error, dispatch);
    }
  };

  const handleRefresh = (event: CustomEvent) => {
    loadNFTData();
    setTimeout(() => {
      event.detail.complete();
    }, 1000);
  };

  const handleNFTClick = (nft: any) => {
    // TODO: Navigate to NFT details page
    console.log("NFT clicked:", nft);
  };

  const renderNFTs = () => {
    if (addressData?.isLoading && !addressData?.nfts) {
      return (
        <div className="nfts-loading">
          <div className="loading-grid">
            {[...Array(6)].map((_, index) => (
              <div key={index} className="nft-skeleton"></div>
            ))}
          </div>
          <p>Loading your NFTs...</p>
        </div>
      );
    }

    if (addressData?.error) {
      return (
        <div className="nfts-error">
          <div className="error-icon">🚫</div>
          <div className="error-message">Failed to load NFTs</div>
          <div className="error-details">{addressData.error}</div>
        </div>
      );
    }

    const nfts = addressData?.nfts || [];

    if (nfts.length === 0) {
      return (
        <div className="nfts-empty">
          <div className="empty-icon">🖼️</div>
          <div className="empty-title">No NFTs found</div>
          <div className="empty-description">
            Your NFTs and digital collectibles will appear here
          </div>
        </div>
      );
    }

    return (
      <div className="nfts-grid">
        {nfts.map((nft, index) => (
          <div 
            key={`${nft.asset.policy_id}-${nft.asset.asset_name}-${index}`} 
            className="nft-card"
            onClick={() => handleNFTClick(nft)}
          >
            <div className="nft-image-container">
              {nft.metadata?.image ? (
                <img
                  src={nft.metadata.image.replace("ipfs://", "https://ipfs.io/ipfs/")}
                  alt={nft.display_name}
                  className="nft-image"
                  loading="lazy"
                />
              ) : (
                <div className="nft-placeholder">
                  <span>🖼️</span>
                </div>
              )}
              {nft.is_cip68 && (
                <div className="cip68-badge">CIP-68</div>
              )}
            </div>
            
            <div className="nft-info">
              <div className="nft-name">{nft.display_name}</div>
              {nft.metadata?.description && (
                <div className="nft-description">
                  {nft.metadata.description.length > 60
                    ? `${nft.metadata.description.substring(0, 60)}...`
                    : nft.metadata.description}
                </div>
              )}
              <div className="nft-policy">
                {nft.asset.policy_id.substring(0, 8)}...{nft.asset.policy_id.substring(nft.asset.policy_id.length - 6)}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <TabLayout
      pageId="nfts-page"
      header={true}
      customClass="nfts-page"
      title="NFTs"
    >
      <IonRefresher slot="fixed" onIonRefresh={handleRefresh}>
        <IonRefresherContent />
      </IonRefresher>

      <div className="nfts-content">
        {addressData?.nfts && addressData.nfts.length > 0 && (
          <div className="nfts-stats">
            <span className="nfts-count">
              {addressData.nfts.length} NFT{addressData.nfts.length !== 1 ? 's' : ''}
            </span>
          </div>
        )}
        
        {renderNFTs()}
      </div>
    </TabLayout>
  );
};

export default NFTs;