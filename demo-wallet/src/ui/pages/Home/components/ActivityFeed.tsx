import { IonSpinner } from "@ionic/react";
import { Transaction } from "../../../../core/cardano/tokenService";
import "./ActivityFeed.scss";

interface ActivityFeedProps {
  transactions?: Transaction[];
  isLoading?: boolean;
  error?: string;
  onTransactionClick?: (transaction: Transaction) => void;
}

const ActivityFeed: React.FC<ActivityFeedProps> = ({ 
  transactions, 
  isLoading, 
  error, 
  onTransactionClick 
}) => {
  if (isLoading && !transactions) {
    return (
      <div className="activity-feed loading">
        <IonSpinner name="crescent" />
        <span>Loading activity...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="activity-feed error">
        <div className="error-message">Failed to load activity</div>
        <div className="error-details">{error}</div>
      </div>
    );
  }

  if (!transactions || transactions.length === 0) {
    return (
      <div className="activity-feed empty">
        <div className="empty-icon">📊</div>
        <div className="empty-message">No activity yet</div>
        <div className="empty-description">Your transaction history will appear here</div>
      </div>
    );
  }

  const formatDate = (timestamp?: number): string => {
    if (!timestamp) return "Unknown date";
    
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return "Less than 1 hour ago";
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
  };

  const handleTransactionClick = (transaction: Transaction) => {
    if (onTransactionClick) {
      onTransactionClick(transaction);
    }
  };

  // Show only the most recent 5 transactions for the home feed
  const recentTransactions = transactions.slice(0, 5);

  return (
    <div className="activity-feed">
      <div className="activity-header">
        <h3>Recent Activity</h3>
        {transactions.length > 5 && (
          <button className="view-all-button">View All</button>
        )}
      </div>
      
      <div className="activity-items">
        {recentTransactions.map((transaction) => (
          <div 
            key={transaction.tx_hash} 
            className="activity-item"
            onClick={() => handleTransactionClick(transaction)}
          >
            <div className="activity-icon">
              <div className="tx-indicator"></div>
            </div>
            
            <div className="activity-info">
              <div className="activity-title">Transaction</div>
              <div className="activity-hash">
                {transaction.tx_hash.substring(0, 8)}...{transaction.tx_hash.substring(transaction.tx_hash.length - 8)}
              </div>
              <div className="activity-time">{formatDate(transaction.block_time)}</div>
            </div>
            
            <div className="activity-details">
              {transaction.block_height && (
                <div className="block-height">Block {transaction.block_height}</div>
              )}
              {transaction.fee_ada && (
                <div className="fee">Fee: {transaction.fee_ada} ₳</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActivityFeed;