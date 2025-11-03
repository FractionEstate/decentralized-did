import { IonIcon, IonSpinner } from "@ionic/react";
import { eye, eyeOff } from "ionicons/icons";
import { useState } from "react";
import "./BalanceCard.scss";

interface BalanceCardProps {
  balance?: {
    ada_amount: string;
    ada_lovelace: string;
    total_assets: number;
  };
  isLoading?: boolean;
  error?: string;
}

const BalanceCard: React.FC<BalanceCardProps> = ({ balance, isLoading, error }) => {
  const [showBalance, setShowBalance] = useState(true);

  const toggleBalanceVisibility = () => {
    setShowBalance(!showBalance);
  };

  if (isLoading && !balance) {
    return (
      <div className="balance-card loading">
        <IonSpinner name="crescent" />
        <span>Loading balance...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="balance-card error">
        <div className="error-message">Failed to load balance</div>
        <div className="error-details">{error}</div>
      </div>
    );
  }

  if (!balance) {
    return (
      <div className="balance-card empty">
        <div className="empty-message">No balance data available</div>
      </div>
    );
  }

  return (
    <div className="balance-card">
      <div className="balance-header">
        <div className="balance-title">Total Balance</div>
        <button 
          className="visibility-toggle" 
          onClick={toggleBalanceVisibility}
          aria-label={showBalance ? "Hide balance" : "Show balance"}
        >
          <IonIcon icon={showBalance ? eye : eyeOff} />
        </button>
      </div>
      
      <div className="balance-amount">
        {showBalance ? (
          <>
            <div className="ada-amount">{balance.ada_amount} ₳</div>
            <div className="ada-lovelace">{balance.ada_lovelace} lovelace</div>
          </>
        ) : (
          <div className="ada-amount hidden">••••• ₳</div>
        )}
      </div>

      {balance.total_assets > 0 && (
        <div className="additional-assets">
          <span>+ {balance.total_assets} asset{balance.total_assets !== 1 ? 's' : ''}</span>
        </div>
      )}
    </div>
  );
};

export default BalanceCard;