import { IonButton, IonIcon } from "@ionic/react";
import {
  fingerPrintSharp,
  shieldCheckmarkOutline,
  timeOutline,
  keyOutline,
  lockClosedOutline,
} from "ionicons/icons";
import "./WelcomeScreen.scss";

interface WelcomeScreenProps {
  onStart: () => void; // Create new wallet (fast onboarding)
  onRestore: () => void; // Recover with seed phrase
  onBiometricRestore?: () => void; // Recover with biometry
}

const WelcomeScreen = ({ onStart, onRestore, onBiometricRestore }: WelcomeScreenProps) => {
  return (
    <div className="welcome-screen simplified-onboarding__panel">
      <div className="welcome-screen__header">
        <IonIcon
          icon={fingerPrintSharp}
          className="welcome-screen__header-icon"
        />
        <h1 className="welcome-screen__title">Biometric Wallet</h1>
        <p className="welcome-screen__subtitle">
          Secure your decentralized identity in a few guided steps.
        </p>
      </div>

      <div className="welcome-screen__benefits">
        <div className="welcome-screen__benefit">
          <IonIcon
            icon={timeOutline}
            className="welcome-screen__benefit-icon"
          />
          <span>Finish onboarding in under 5 minutes</span>
        </div>
        <div className="welcome-screen__benefit">
          <IonIcon
            icon={shieldCheckmarkOutline}
            className="welcome-screen__benefit-icon"
          />
          <span>Deterministic, tamper-proof identity</span>
        </div>
        <div className="welcome-screen__benefit">
          <IonIcon
            icon={fingerPrintSharp}
            className="welcome-screen__benefit-icon"
          />
          <span>Biometric login across all ten fingerprints</span>
        </div>
      </div>

      <div className="welcome-screen__actions">
        <IonButton
          expand="block"
          className="welcome-screen__primary"
          onClick={onStart}
        >
          <IonIcon slot="start" icon={fingerPrintSharp} />
          Create Wallet
        </IonButton>

        <div className="welcome-screen__restore-options">
          <p className="welcome-screen__restore-label">Already have a wallet?</p>
          <IonButton
            fill="outline"
            expand="block"
            className="welcome-screen__secondary"
            onClick={onRestore}
          >
            <IonIcon slot="start" icon={keyOutline} />
            Recover with Seed Phrase
          </IonButton>
          {onBiometricRestore && (
            <IonButton
              fill="outline"
              expand="block"
              className="welcome-screen__secondary"
              onClick={onBiometricRestore}
            >
              <IonIcon slot="start" icon={lockClosedOutline} />
              Recover with Biometry
            </IonButton>
          )}
        </div>
      </div>
    </div>
  );
};

export { WelcomeScreen };
