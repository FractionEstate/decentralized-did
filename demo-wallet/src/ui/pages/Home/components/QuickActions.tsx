import { IonIcon } from "@ionic/react";
import { send, download, card } from "ionicons/icons";
import "./QuickActions.scss";

interface QuickActionsProps {
  onSend?: () => void;
  onReceive?: () => void;
  onBuy?: () => void;
}

const QuickActions: React.FC<QuickActionsProps> = ({ onSend, onReceive, onBuy }) => {
  const handleSend = () => {
    if (onSend) {
      onSend();
    } else {
      // TODO: Implement send functionality
      console.log("Send action clicked");
    }
  };

  const handleReceive = () => {
    if (onReceive) {
      onReceive();
    } else {
      // TODO: Implement receive functionality
      console.log("Receive action clicked");
    }
  };

  const handleBuy = () => {
    if (onBuy) {
      onBuy();
    } else {
      // TODO: Implement buy functionality
      console.log("Buy action clicked");
    }
  };

  return (
    <div className="quick-actions">
      <button className="action-button send" onClick={handleSend}>
        <div className="action-icon">
          <IonIcon icon={send} />
        </div>
        <span className="action-label">Send</span>
      </button>
      
      <button className="action-button receive" onClick={handleReceive}>
        <div className="action-icon">
          <IonIcon icon={download} />
        </div>
        <span className="action-label">Receive</span>
      </button>
      
      <button className="action-button buy" onClick={handleBuy}>
        <div className="action-icon">
          <IonIcon icon={card} />
        </div>
        <span className="action-label">Buy</span>
      </button>
    </div>
  );
};

export default QuickActions;