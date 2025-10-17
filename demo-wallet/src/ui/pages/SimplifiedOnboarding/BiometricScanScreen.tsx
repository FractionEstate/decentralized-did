import { useCallback, useEffect, useMemo, useState } from "react";
import { IonButton, IonIcon, IonProgressBar } from "@ionic/react";
import { fingerPrintSharp, refreshOutline } from "ionicons/icons";
import "./BiometricScanScreen.scss";

interface BiometricScanScreenProps {
  fingersToScan: string[];
  onComplete: (biometricData: string[]) => void;
  onError: (error: string) => void;
}

const displayNameMap: Record<string, string> = {
  "right-thumb": "RIGHT THUMB",
  "right-index": "RIGHT INDEX",
  "right-middle": "RIGHT MIDDLE",
  "right-ring": "RIGHT RING",
  "right-pinky": "RIGHT PINKY",
  "left-thumb": "LEFT THUMB",
  "left-index": "LEFT INDEX",
  "left-middle": "LEFT MIDDLE",
  "left-ring": "LEFT RING",
  "left-pinky": "LEFT PINKY",
};

const formatFingerName = (finger: string) =>
  displayNameMap[finger] ?? finger.replace(/-/g, " ").toUpperCase();

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
  const totalFingers = fingersToScan.length;
  const progress = useMemo(() => {
    const denominator = Math.max(totalFingers, 1);
    return (currentFingerIndex + 1) / denominator;
  }, [currentFingerIndex, totalFingers]);

  const captureFinger = useCallback(async () => {
    if (!currentFinger) {
      return;
    }

    setScanning(true);
    setScanSuccess(false);

    try {
      await new Promise((resolve) => setTimeout(resolve, 1800));

      const mockData = btoa(`fingerprint-${currentFinger}-${Date.now()}`);
      const nextData = [...capturedData, mockData];

      setCapturedData(nextData);
      setScanning(false);
      setScanSuccess(true);

      setTimeout(() => {
        if (currentFingerIndex < fingersToScan.length - 1) {
          setCurrentFingerIndex((prev) => prev + 1);
          setScanSuccess(false);
        } else {
          onComplete(nextData);
        }
      }, 800);
    } catch (error) {
      setScanning(false);
      onError("Fingerprint capture failed. Please try again.");
    }
  }, [
    capturedData,
    currentFinger,
    currentFingerIndex,
    totalFingers,
    onComplete,
    onError,
  ]);

  useEffect(() => {
    if (!currentFinger || scanning || scanSuccess) {
      return undefined;
    }

    if (capturedData.length === currentFingerIndex) {
      const delay = currentFingerIndex === 0 ? 400 : 600;
      const timer = setTimeout(() => {
        captureFinger();
      }, delay);

      return () => clearTimeout(timer);
    }

    return undefined;
  }, [
    captureFinger,
    capturedData.length,
    currentFinger,
    currentFingerIndex,
    scanSuccess,
    scanning,
  ]);

  return (
    <div className="simplified-onboarding__panel biometric-scan-screen">
      <div className="scan-heading">
        <IonIcon icon={fingerPrintSharp} className="scan-heading__icon" />
        <h1>Scan your fingerprints</h1>
        <p>
          Capture each finger once. Maintain even pressure on the sensor for a
          clean biometric commitment.
        </p>
      </div>

      <div className="fingerprint-visual" aria-live="polite">
        {scanning ? (
          <div className="scanning-animation">
            <IonIcon icon={fingerPrintSharp} className="fingerprint-icon" />
            <div className="scan-line" />
          </div>
        ) : scanSuccess ? (
          <div className="success-icon" role="status">
            ✓
          </div>
        ) : (
          <IonIcon icon={fingerPrintSharp} className="fingerprint-icon" />
        )}
      </div>

      <div className="instruction">
        <h2>
          {scanning
            ? "Scanning..."
            : scanSuccess
              ? "Captured"
              : currentFinger
                ? `Place your ${formatFingerName(currentFinger)} finger`
                : "All fingers captured"}
        </h2>
      </div>

      <div className="progress-section">
        <IonProgressBar value={progress} className="scan-progress-bar" />
        <p className="progress-text">
          Finger {Math.min(currentFingerIndex + 1, totalFingers)} of {totalFingers}
        </p>
      </div>

      <div className="finger-checklist">
        <h3>Fingers remaining</h3>
        {fingersToScan.map((finger, index) => {
          const status =
            index < currentFingerIndex
              ? "done"
              : index === currentFingerIndex
                ? "active"
                : "pending";

          return (
            <div key={finger} className={`finger-item finger-item--${status}`}>
              <span className="finger-item__status">
                {status === "done" && "✓"}
                {status === "active" && "•"}
              </span>
              <span className="finger-item__name">
                {formatFingerName(finger)}
              </span>
            </div>
          );
        })}
      </div>

      <div className="tip">
        <p>Tip: Keep each finger steady and aligned with the sensor.</p>
      </div>

      {!scanning && !scanSuccess && currentFinger && (
        <IonButton
          fill="outline"
          onClick={captureFinger}
          className="retry-button"
        >
          <IonIcon icon={refreshOutline} slot="start" />
          Retry
        </IonButton>
      )}
    </div>
  );
};

export { BiometricScanScreen };
