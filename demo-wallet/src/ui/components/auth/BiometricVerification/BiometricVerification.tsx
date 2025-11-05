/**
 * Biometric DID Verification Component
 * Verifies fingerprint against stored helper data
 * Used for wallet unlock and transaction signing
 */

import { IonIcon, IonSpinner } from "@ionic/react";
import { checkmarkCircle, closeCircle, fingerPrintOutline } from "ionicons/icons";
import { useState, useEffect } from "react";
import { i18n } from "../../../../i18n";
import {
  biometricDidService,
  fingerprintCaptureService,
  FingerId,
} from "../../../../core/biometric";
import "./BiometricVerification.scss";

export enum VerificationMode {
  Unlock = "unlock",
  TransactionSign = "transaction-sign",
}

export interface BiometricVerificationProps {
  mode: VerificationMode;
  did: string;
  onSuccess: () => void;
  onFailure: (error: string) => void;
  onCancel?: () => void;
}

enum VerificationStatus {
  Ready = "ready",
  Capturing = "capturing",
  Verifying = "verifying",
  Success = "success",
  Failed = "failed",
}

export const BiometricVerification = ({
  mode,
  did,
  onSuccess,
  onFailure,
  onCancel,
}: BiometricVerificationProps) => {
  const [status, setStatus] = useState<VerificationStatus>(
    VerificationStatus.Ready
  );
  const [error, setError] = useState<string | undefined>();
  const [matchedFingers, setMatchedFingers] = useState<string[]>([]);
  const [attempts, setAttempts] = useState(0);
  const [webAuthnAvailable, setWebAuthnAvailable] = useState(false);
  const [webAuthnBiometricType, setWebAuthnBiometricType] = useState<string | null>(null);
  const [hasWebAuthnCredential, setHasWebAuthnCredential] = useState(false);

  const MAX_ATTEMPTS = 3;

  // Check WebAuthn availability on mount
  useEffect(() => {
    const checkWebAuthn = async () => {
      const isAvailable = fingerprintCaptureService.isWebAuthnAvailable();
      const biometricType = fingerprintCaptureService.getWebAuthnBiometricType();
      const hasCredential = await biometricDidService.hasWebAuthnCredential();

      setWebAuthnAvailable(isAvailable);
      setWebAuthnBiometricType(biometricType);
      setHasWebAuthnCredential(hasCredential);
    };

    checkWebAuthn();
  }, []);

  const startVerification = async () => {
    if (attempts >= MAX_ATTEMPTS) {
      setError("Maximum verification attempts exceeded. Please use passcode.");
      onFailure("Max attempts exceeded");
      return;
    }

    setStatus(VerificationStatus.Capturing);
    setError(undefined);

    try {
      // Capture a single fingerprint (any finger)
      // In production, this would detect which finger is placed
      // For now, we'll capture one and verify against all enrolled fingers
      const capture = await fingerprintCaptureService.captureFingerprint(
        "left_thumb" as FingerId // Placeholder - real sensor would detect which finger
      );

      // Validate quality
      if (!fingerprintCaptureService.validateQuality(capture)) {
        throw new Error("Poor fingerprint quality. Please try again.");
      }

      setStatus(VerificationStatus.Verifying);

      // Load stored helper data
      const helperData = await biometricDidService.loadHelperData(did);
      if (!helperData) {
        throw new Error("No biometric data found. Please enroll first.");
      }

      // Extract ID hash from DID
      // Format: did:cardano:{network}:{base58_hash}
      const parts = did.split(":");
      const idHash = parts[parts.length - 1];

      if (!idHash || parts.length !== 4) {
        throw new Error("Invalid DID format. Expected: did:cardano:{network}:{hash}");
      }

      // Verify against stored helper data
      const result = await biometricDidService.verify({
        fingers: [
          {
            finger_id: capture.finger_id,
            minutiae: capture.minutiae,
          },
        ],
        helpers: helperData,
        expected_id_hash: idHash,
      });

      if (result.success) {
        setStatus(VerificationStatus.Success);
        setMatchedFingers(result.matched_fingers);
        setTimeout(() => {
          onSuccess();
        }, 1000);
      } else {
        throw new Error("Fingerprint verification failed");
      }
    } catch (error) {
      setStatus(VerificationStatus.Failed);
      const errorMsg =
        error instanceof Error ? error.message : "Verification failed";
      setError(errorMsg);
      setAttempts((prev) => prev + 1);

      if (attempts + 1 >= MAX_ATTEMPTS) {
        setTimeout(() => {
          onFailure("Maximum attempts exceeded");
        }, 2000);
      }
    }
  };

  const startWebAuthnVerification = async () => {
    if (attempts >= MAX_ATTEMPTS) {
      setError("Maximum verification attempts exceeded. Please use passcode.");
      onFailure("Max attempts exceeded");
      return;
    }

    setStatus(VerificationStatus.Verifying);
    setError(undefined);

    try {
      // Load stored WebAuthn credential
      const credential = await biometricDidService.loadWebAuthnCredential();
      if (!credential) {
        throw new Error("No biometric credential found. Please enroll first.");
      }

      // Verify with WebAuthn
      const success = await fingerprintCaptureService.verifyWithWebAuthn(
        credential.credentialId
      );

      if (success) {
        setStatus(VerificationStatus.Success);
        setTimeout(() => {
          onSuccess();
        }, 1000);
      } else {
        throw new Error("Biometric verification failed");
      }
    } catch (error) {
      setStatus(VerificationStatus.Failed);
      const errorMsg =
        error instanceof Error ? error.message : "Verification failed";
      setError(errorMsg);
      setAttempts((prev) => prev + 1);

      if (attempts + 1 >= MAX_ATTEMPTS) {
        setTimeout(() => {
          onFailure("Maximum attempts exceeded");
        }, 2000);
      }
    }
  };

  const retry = () => {
    setStatus(VerificationStatus.Ready);
    setError(undefined);
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
  };

  const getTitle = () => {
    switch (mode) {
      case VerificationMode.Unlock:
        return i18n.t("biometric.verification.unlock.title");
      case VerificationMode.TransactionSign:
        return i18n.t("biometric.verification.sign.title");
      default:
        return i18n.t("biometric.verification.title");
    }
  };

  const getDescription = () => {
    switch (mode) {
      case VerificationMode.Unlock:
        return i18n.t("biometric.verification.unlock.description");
      case VerificationMode.TransactionSign:
        return i18n.t("biometric.verification.sign.description");
      default:
        return i18n.t("biometric.verification.description");
    }
  };

  return (
    <div className="biometric-verification">
      {status === VerificationStatus.Ready && (
        <div className="verification-ready">
          <IonIcon icon={fingerPrintOutline} className="fingerprint-icon" />
          <h2>{getTitle()}</h2>
          <p>{getDescription()}</p>
          {attempts > 0 && (
            <div className="attempts-warning">
              Attempt {attempts + 1} of {MAX_ATTEMPTS}
            </div>
          )}
          <div className="verification-actions">
            {webAuthnAvailable && hasWebAuthnCredential && (
              <button
                className="verify-button webauthn-button"
                onClick={startWebAuthnVerification}
              >
                <IonIcon icon={fingerPrintOutline} slot="start" />
                {webAuthnBiometricType
                  ? `Verify with ${webAuthnBiometricType}`
                  : "Verify with Biometric"}
              </button>
            )}
            <button className="verify-button" onClick={startVerification}>
              {i18n.t("biometric.verification.button.verify")}
            </button>
            {onCancel && (
              <button className="cancel-button" onClick={handleCancel}>
                {i18n.t("biometric.verification.button.cancel")}
              </button>
            )}
          </div>
        </div>
      )}

      {status === VerificationStatus.Capturing && (
        <div className="verification-capturing">
          <IonIcon
            icon={fingerPrintOutline}
            className="fingerprint-icon pulse"
          />
          <h2>{i18n.t("biometric.verification.capturing")}</h2>
          <p>Place your finger on the sensor</p>
          <IonSpinner name="crescent" />
        </div>
      )}

      {status === VerificationStatus.Verifying && (
        <div className="verification-verifying">
          <IonIcon
            icon={fingerPrintOutline}
            className="fingerprint-icon pulse"
          />
          <h2>{i18n.t("biometric.verification.verifying")}</h2>
          <p>Checking fingerprint...</p>
          <IonSpinner name="crescent" />
        </div>
      )}

      {status === VerificationStatus.Success && (
        <div className="verification-success">
          <IonIcon icon={checkmarkCircle} className="success-icon" />
          <h2>{i18n.t("biometric.verification.success")}</h2>
          {matchedFingers.length > 0 && (
            <p className="matched-info">
              Matched: {matchedFingers.join(", ")}
            </p>
          )}
        </div>
      )}

      {status === VerificationStatus.Failed && (
        <div className="verification-failed">
          <IonIcon icon={closeCircle} className="error-icon" />
          <h2>{i18n.t("biometric.verification.failed")}</h2>
          {error && <p className="error-message">{error}</p>}
          {attempts < MAX_ATTEMPTS ? (
            <div className="verification-actions">
              <button className="retry-button" onClick={retry}>
                {i18n.t("biometric.verification.button.retry")}
              </button>
              {onCancel && (
                <button className="cancel-button" onClick={handleCancel}>
                  {i18n.t("biometric.verification.button.usepasscode")}
                </button>
              )}
            </div>
          ) : (
            <div className="max-attempts">
              <p>
                {i18n.t("biometric.verification.maxattempts")}
              </p>
              <button className="cancel-button" onClick={handleCancel}>
                {i18n.t("biometric.verification.button.usepasscode")}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
