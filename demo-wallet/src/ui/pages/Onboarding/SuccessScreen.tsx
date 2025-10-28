import { IonButton, IonContent, IonPage } from "@ionic/react";
import { useState } from "react";
import "./SuccessScreen.scss";

interface SuccessScreenProps {
  walletAddress: string;
  onContinue: () => void;
  fastOnboarding?: boolean; // If true, user skipped seed phrase backup
}

const SuccessScreen = ({ walletAddress, onContinue, fastOnboarding }: SuccessScreenProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(walletAddress);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <IonPage className="success-screen">
      <IonContent className="success-content">
        <div className="success-container">
          <div className="celebration">
            <div className="celebration-icon">🎉</div>
            <h1>Your Wallet is Ready!</h1>
          </div>

          <div className="completion-checklist">
            <div className="checklist-item">
              <span className="icon">✅</span>
              <span>Fingerprints registered (10 fingers)</span>
            </div>
            <div className="checklist-item">
              <span className="icon">{fastOnboarding ? "⏱️" : "✅"}</span>
              <span>{fastOnboarding ? "Seed phrase saved (backup later)" : "Backup seed phrase saved"}</span>
            </div>
            <div className="checklist-item">
              <span className="icon">✅</span>
              <span>{fastOnboarding ? "Wallet created" : "Verification passed"}</span>
            </div>
          </div>

          <div className="wallet-address-box">
            <p className="address-label">Your wallet address:</p>
            <div className="address-display">
              <code className="address-text">{walletAddress}</code>
              <IonButton
                fill="clear"
                size="small"
                onClick={handleCopy}
                className="copy-button"
              >
                {copied ? "Copied!" : "Copy"}
              </IonButton>
            </div>
          </div>

          <div className="capabilities">
            <h3>You can now:</h3>
            <ul>
              <li>• Receive ADA and tokens</li>
              <li>• Send transactions with your fingerprints</li>
              <li>• Explore the Cardano ecosystem</li>
            </ul>
          </div>

          <div className="actions">
            <IonButton
              expand="block"
              size="large"
              onClick={onContinue}
              className="start-button"
            >
              Start Using Wallet →
            </IonButton>

            <IonButton fill="clear" size="small" className="help-button">
              Need help? View Tutorial
            </IonButton>
          </div>
        </div>
      </IonContent>
    </IonPage>
  );
};

export { SuccessScreen };
