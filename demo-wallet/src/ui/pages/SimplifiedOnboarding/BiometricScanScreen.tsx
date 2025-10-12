import { useState, useEffect } from "react";
import { IonButton, IonContent, IonPage, IonProgressBar } from "@ionic/react";
import "./BiometricScanScreen.scss";

interface BiometricScanScreenProps {
  fingersToScan: string[]; // e.g., ["right-index", "right-middle", "right-thumb"]
  onComplete: (biometricData: string[]) => void;
  onError: (error: string) => void;
}

const BiometricScanScreen = ({
  fingersToScan,
  onComplete,
  onError,
}: BiometricScanScreenProps) => {
  const [currentFingerIndex, setCurrentFingerIndex] = useState(0);
  const [capturedData, setCapturedData] = useState<string[]>([]);
  const [scanning, setScanning] = useState(false);
  const [scanSuccess, setScanSuccess] = useState(false);

  const currentFinger = fingersToScan[currentFingerIndex];
  const progress = (currentFingerIndex + 1) / fingersToScan.length;

  const fingerDisplayNames: Record<string, string> = {
    "right-index": "RIGHT INDEX",
    "right-middle": "RIGHT MIDDLE",
    "right-thumb": "RIGHT THUMB",
    "left-index": "LEFT INDEX",
    "left-middle": "LEFT MIDDLE",
    "left-thumb": "LEFT THUMB",
  };

  const captureFinger = async () => {
    setScanning(true);
    setScanSuccess(false);

    try {
      // Simulate biometric capture
      // In production, call WebAuthn or backend API
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Mock biometric data (base64 encoded minutiae)
      const mockData = btoa(`fingerprint-${currentFinger}-${Date.now()}`);

      const newCapturedData = [...capturedData, mockData];
      setCapturedData(newCapturedData);

      setScanning(false);
      setScanSuccess(true);

      // Auto-advance after 1 second
      setTimeout(() => {
        if (currentFingerIndex < fingersToScan.length - 1) {
          setCurrentFingerIndex(currentFingerIndex + 1);
          setScanSuccess(false);
        } else {
          // All fingers captured
          onComplete(newCapturedData);
        }
      }, 1000);
    } catch (error) {
      setScanning(false);
      onError("Fingerprint capture failed. Please try again.");
    }
  };

  // Auto-start capture for first finger
  useEffect(() => {
    if (currentFingerIndex === 0 && capturedData.length === 0 && !scanning) {
      setTimeout(() => captureFinger(), 500);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <IonPage className="biometric-scan-screen">
      <IonContent className="scan-content">
        <div className="scan-container">
          <h1>📸 Scan Your Fingerprints</h1>

          <div className="fingerprint-visual">
            {scanning ? (
              <div className="scanning-animation">
                <div className="fingerprint-icon">👆</div>
                <div className="scan-line"></div>
              </div>
            ) : scanSuccess ? (
              <div className="success-icon">✓</div>
            ) : (
              <div className="fingerprint-icon">👆</div>
            )}
          </div>

          <div className="instruction">
            <h2>
              {scanning
                ? "Scanning..."
                : scanSuccess
                  ? "Success!"
                  : `Place your ${fingerDisplayNames[currentFinger]} finger`}
            </h2>
          </div>

          <div className="progress-section">
            <IonProgressBar value={progress} className="scan-progress-bar" />
            <p className="progress-text">
              Scanning {currentFingerIndex + 1} of {fingersToScan.length} fingers
            </p>
          </div>

          <div className="finger-checklist">
            <h3>Fingers to scan:</h3>
            {fingersToScan.map((finger, index) => (
              <div key={finger} className="finger-item">
                <span className="checkbox">
                  {index < currentFingerIndex
                    ? "✅"
                    : index === currentFingerIndex
                      ? scanning
                        ? "●"
                        : "○"
                      : "○"}
                </span>
                <span className="finger-name">
                  {fingerDisplayNames[finger]}
                  {index < currentFingerIndex && " (done)"}
                  {index === currentFingerIndex && scanning && " (scanning...)"}
                  {index > currentFingerIndex && " (next)"}
                </span>
              </div>
            ))}
          </div>

          <div className="tip">
            <p>💡 Tip: Press firmly but gently</p>
          </div>

          {!scanning && !scanSuccess && currentFingerIndex > 0 && (
            <IonButton fill="outline" onClick={captureFinger}>
              Retry Scan
            </IonButton>
          )}
        </div>
      </IonContent>
    </IonPage>
  );
};

export { BiometricScanScreen };
