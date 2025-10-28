import { useState } from "react";
import { IonButton, IonCheckbox, IonContent, IonPage } from "@ionic/react";
import "./SeedPhraseScreen.scss";

interface SeedPhraseScreenProps {
  words: string[];
  onConfirm: () => void;
  onBack: () => void;
}

const SeedPhraseScreen = ({ words, onConfirm, onBack }: SeedPhraseScreenProps) => {
  const [confirmed, setConfirmed] = useState(false);
  const [showWords, setShowWords] = useState(true);

  const handleCheckboxChange = (checked: boolean) => {
    setConfirmed(checked);
  };

  return (
    <IonPage className="seed-phrase-screen">
      <IonContent className="seed-content">
        <div className="seed-container">
          <h1>📝 Your Backup Seed Phrase</h1>

          <div className="warning-box">
            <p className="warning-icon">⚠️</p>
            <p className="warning-text">
              <strong>IMPORTANT:</strong> Write these words on paper.
              <br />
              This is the ONLY way to recover your wallet if you lose access.
            </p>
          </div>

          <div className={`seed-phrase-grid ${!showWords ? "blurred" : ""}`}>
            {words.map((word, index) => (
              <div key={index} className="seed-word-item">
                <span className="word-number">{index + 1}.</span>
                <span className="word-text">{word}</span>
              </div>
            ))}
          </div>

          <div className="instructions">
            <h3>✏️ Get a pen and paper:</h3>
            <ol>
              <li>Write each word in order</li>
              <li>Double-check your writing</li>
              <li>Store it somewhere safe</li>
            </ol>
          </div>

          <div className="confirmation">
            <label className="confirmation-checkbox">
              <IonCheckbox
                checked={confirmed}
                onIonChange={(e) => handleCheckboxChange(e.detail.checked)}
              />
              <span className="confirmation-text">
                I have written down all {words.length} words and stored them safely
              </span>
            </label>
          </div>

          <div className="actions">
            <IonButton
              expand="block"
              size="large"
              disabled={!confirmed}
              onClick={onConfirm}
              className="next-button"
            >
              Next →
            </IonButton>

            <IonButton fill="clear" size="small" onClick={onBack}>
              ← Back
            </IonButton>
          </div>

          <div className="options">
            <button
              className="toggle-words"
              onClick={() => setShowWords(!showWords)}
            >
              {showWords ? "Hide words" : "Show words"}
            </button>
            {words.length === 12 && (
              <button className="switch-length">
                Need 24 words instead?
              </button>
            )}
          </div>
        </div>
      </IonContent>
    </IonPage>
  );
};

export { SeedPhraseScreen };
