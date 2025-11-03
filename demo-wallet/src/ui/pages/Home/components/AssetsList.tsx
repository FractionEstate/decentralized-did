import { IonSpinner } from "@ionic/react";
import { Asset } from "../../../../core/cardano/tokenService";
import "./AssetsList.scss";

interface AssetsListProps {
  assets?: Asset[];
  isLoading?: boolean;
  error?: string;
  onAssetClick?: (asset: Asset) => void;
}

const AssetsList: React.FC<AssetsListProps> = ({ 
  assets, 
  isLoading, 
  error, 
  onAssetClick 
}) => {
  if (isLoading && !assets) {
    return (
      <div className="assets-list loading">
        <IonSpinner name="crescent" />
        <span>Loading assets...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="assets-list error">
        <div className="error-message">Failed to load assets</div>
        <div className="error-details">{error}</div>
      </div>
    );
  }

  if (!assets || assets.length === 0) {
    return (
      <div className="assets-list empty">
        <div className="empty-icon">🪙</div>
        <div className="empty-message">No assets found</div>
        <div className="empty-description">Your native assets will appear here</div>
      </div>
    );
  }

  const handleAssetClick = (asset: Asset) => {
    if (onAssetClick) {
      onAssetClick(asset);
    }
  };

  return (
    <div className="assets-list">
      <div className="assets-header">
        <h3>Assets ({assets.length})</h3>
      </div>
      
      <div className="assets-items">
        {assets.map((asset, index) => (
          <div 
            key={`${asset.policy_id}-${asset.asset_name}-${index}`} 
            className="asset-item"
            onClick={() => handleAssetClick(asset)}
          >
            <div className="asset-info">
              <div className="asset-name">
                {asset.asset_name_ascii || 
                 (asset.asset_name.length > 20 
                   ? `${asset.asset_name.substring(0, 20)}...`
                   : asset.asset_name)}
              </div>
              <div className="asset-policy">
                Policy: {asset.policy_id.substring(0, 8)}...{asset.policy_id.substring(asset.policy_id.length - 6)}
              </div>
            </div>
            
            <div className="asset-balance">
              <div className="asset-quantity">{asset.display_quantity}</div>
              {asset.full_name && asset.full_name !== asset.asset_name && (
                <div className="asset-symbol">{asset.full_name}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AssetsList;