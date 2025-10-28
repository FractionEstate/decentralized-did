import { useState } from "react";
import { IonButton, IonContent, IonInput, IonPage } from "@ionic/react";
import "./VerificationScreen.scss";

interface VerificationScreenProps {
  seedPhrase: string[];
  wordsToVerify: number[]; // Array of indices (0-based)
  onSuccess: () => void;
  onBack: () => void;
}

const VerificationScreen = ({
  seedPhrase,
  wordsToVerify,
  onSuccess,
  onBack,
}: VerificationScreenProps) => {
  const [inputs, setInputs] = useState<Record<number, string>>({});
  const [errors, setErrors] = useState<Record<number, boolean>>({});
  const [attempted, setAttempted] = useState(false);

  const handleInputChange = (index: number, value: string) => {
    setInputs({ ...inputs, [index]: value.trim().toLowerCase() });
    // Clear error when user types
    if (errors[index]) {
      setErrors({ ...errors, [index]: false });
    }
  };

  const handleVerify = () => {
    setAttempted(true);
    const newErrors: Record<number, boolean> = {};
    let hasError = false;

    wordsToVerify.forEach((wordIndex) => {
      const userInput = (inputs[wordIndex] || "").toLowerCase();
      const correctWord = seedPhrase[wordIndex].toLowerCase();

      if (userInput !== correctWord) {
        newErrors[wordIndex] = true;
        hasError = true;
      }
    });

    if (hasError) {
      setErrors(newErrors);
    } else {
      // All correct!
      onSuccess();
    }
  };

  const allFieldsFilled = wordsToVerify.every(
    (index) => inputs[index]?.trim().length > 0
  );

  return (
    <IonPage className="verification-screen">
      <IonContent className="verification-content">
        <div className="verification-container">
          <h1>✓ Quick Verification</h1>

          <p className="intro-text">
            Let's make sure you wrote everything down correctly. Enter these{" "}
            {wordsToVerify.length} words:
          </p>

          {attempted && Object.keys(errors).length > 0 && (
            <div className="error-box">
              <p className="error-icon">❌</p>
              <p className="error-text">
                The words you entered don't match. Please check your backup
                and try again.
              </p>
            </div>
          )}

          <div className="verification-inputs">
            {wordsToVerify.map((wordIndex) => (
              <div key={wordIndex} className="input-group">
                <label className="input-label">Word #{wordIndex + 1}:</label>
                <IonInput
                  type="text"
                  placeholder="_________________"
                  value={inputs[wordIndex] || ""}
                  onIonInput={(e) =>
                    handleInputChange(wordIndex, e.detail.value || "")
                  }
                  className={`word-input ${errors[wordIndex] ? "error" : ""
                    } ${inputs[wordIndex] &&
                      inputs[wordIndex].toLowerCase() ===
                      seedPhrase[wordIndex].toLowerCase()
                      ? "success"
                      : ""
                    }`}
                />
                {inputs[wordIndex] &&
                  inputs[wordIndex].toLowerCase() ===
                  seedPhrase[wordIndex].toLowerCase() && (
                    <span className="check-icon">✓</span>
                  )}
                {errors[wordIndex] && (
                  <p className="field-error">Word #{wordIndex + 1} is incorrect</p>
                )}
              </div>
            ))}
          </div>

          <div className="tip">
            <p>💡 Tip: Check your written backup</p>
          </div>

          <div className="actions">
            <IonButton
              expand="block"
              size="large"
              disabled={!allFieldsFilled}
              onClick={handleVerify}
              className="verify-button"
            >
              Verify →
            </IonButton>

            <IonButton fill="clear" size="small" onClick={onBack}>
              ← Back to seed phrase
            </IonButton>
          </div>
        </div>
      </IonContent>
    </IonPage>
  );
};

export { VerificationScreen };
