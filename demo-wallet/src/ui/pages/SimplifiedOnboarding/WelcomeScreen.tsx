import { IonButton, IonContent, IonPage } from "@ionic/react";
import "./WelcomeScreen.scss";

interface WelcomeScreenProps {
  onStart: () => void;
  onRestore: () => void;
}

const WelcomeScreen = ({ onStart, onRestore }: WelcomeScreenProps) => {
  return (
    <IonPage className="welcome-screen">
      <IonContent className="welcome-content">
        <div className="welcome-container">
          <div className="welcome-header">
            <div className="logo">🔐</div>
            <h1>Biometric Wallet</h1>
            <p className="tagline">Your fingerprints are your keys</p>
          </div>

          <div className="value-prop">
            <h2>Create your wallet in just 3 simple steps</h2>
            <div className="benefits">
              <div className="benefit-item">
                <span className="icon">⏱️</span>
                <span>Takes less than 2 minutes</span>
              </div>
              <div className="benefit-item">
                <span className="icon">🔒</span>
                <span>Military-grade security</span>
              </div>
              <div className="benefit-item">
                <span className="icon">📱</span>
                <span>No passwords to remember</span>
              </div>
            </div>
          </div>

          <div className="actions">
            <IonButton
              expand="block"
              size="large"
              className="primary-button"
              onClick={onStart}
            >
              Get Started →
            </IonButton>

            <IonButton
              fill="clear"
              size="small"
              className="secondary-button"
              onClick={onRestore}
            >
              Already have a wallet? Restore
            </IonButton>
          </div>
        </div>
      </IonContent>
    </IonPage>
  );
};

export { WelcomeScreen };
