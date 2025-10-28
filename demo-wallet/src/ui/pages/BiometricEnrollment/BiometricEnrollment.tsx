/**
 * Biometric DID Enrollment Page
 * Captures fingerprints, generates DID, and stores helper data
 */

import { IonIcon, IonSpinner, IonModal } from "@ionic/react";
import { checkmarkCircle, fingerPrintOutline, copyOutline, informationCircleOutline, lockClosedOutline, shieldCheckmarkOutline, helpCircleOutline, closeCircle, openOutline } from "ionicons/icons";
import { useState, useEffect, useRef } from "react";
import { i18n } from "../../../i18n";
import { RoutePath } from "../../../routes";
import { getNextRoute } from "../../../routes/nextRoute";
import { DataProps } from "../../../routes/nextRoute/nextRoute.types";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import { setToastMsg } from "../../../store/reducers/stateCache";
import { updateReduxState } from "../../../store/utils";
import { Alert } from "../../components/Alert";
import { PageFooter } from "../../components/PageFooter";
import { PageHeader } from "../../components/PageHeader";
import { ResponsivePageLayout } from "../../components/layout/ResponsivePageLayout";
import { ToastMsgType } from "../../globals/types";
import { useAppIonRouter } from "../../hooks";
import { getUserFriendlyError, BIOMETRIC_ERRORS } from "../../../utils/userFriendlyErrors";
import { openBrowserLink } from "../../utils/openBrowserLink";
import {
  biometricDidService,
  fingerprintCaptureService,
  FINGER_IDS,
  FingerId,
  BiometricEnrollmentStatus,
} from "../../../core/biometric";
import "./BiometricEnrollment.scss";

/**
 * Generate Cardanoscan explorer URL for a transaction
 * Supports both testnet (preprod) and mainnet
 */
function getCardanoscanUrl(txHash: string, network: string = "testnet"): string {
  const baseUrl = network === "mainnet"
    ? "https://cardanoscan.io/transaction"
    : "https://preprod.cardanoscan.io/transaction";
  return `${baseUrl}/${txHash}`;
}

interface EnrollmentState {
  status: BiometricEnrollmentStatus;
  currentFinger: number;
  completedFingers: string[];
  error?: string;
  did?: string;
  idHash?: string;
  txHash?: string;  // Cardano transaction hash for blockchain enrollment
}

const FINGER_NAMES: Record<FingerId, string> = {
  left_thumb: "Left Thumb",
  left_index: "Left Index",
  left_middle: "Left Middle",
  left_ring: "Left Ring",
  left_little: "Left Little",
  right_thumb: "Right Thumb",
  right_index: "Right Index",
  right_middle: "Right Middle",
  right_ring: "Right Ring",
  right_little: "Right Little",
};

export const BiometricEnrollment = () => {
  const pageId = "biometric-enrollment";
  const ionRouter = useAppIonRouter();
  const dispatch = useAppDispatch();
  const stateCache = useAppSelector((state) => state.stateCache);

  const [enrollmentState, setEnrollmentState] = useState<EnrollmentState>({
    status: BiometricEnrollmentStatus.NotStarted,
    currentFinger: 0,
    completedFingers: [],
  });

  const [showSkipAlert, setShowSkipAlert] = useState(false);
  const [showErrorAlert, setShowErrorAlert] = useState(false);
  const [webAuthnAvailable, setWebAuthnAvailable] = useState(false);
  const [webAuthnBiometricType, setWebAuthnBiometricType] = useState<string | null>(null);
  const [isGeneratingDid, setIsGeneratingDid] = useState(false);
  const [webAuthnLoading, setWebAuthnLoading] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);

  // Use ref to track current finger index to avoid stale closures
  const currentFingerRef = useRef(0);

  // Get wallet address (would come from user's wallet)
  // For now, use a test address
  const walletAddress = "addr_test1_demo";

  const totalFingers = FINGER_IDS.length;
  const progress = (enrollmentState.currentFinger / totalFingers) * 100;

  // Check WebAuthn availability on mount
  useEffect(() => {
    const available = fingerprintCaptureService.isWebAuthnAvailable();
    const biometricType = fingerprintCaptureService.getWebAuthnBiometricType();
    setWebAuthnAvailable(available);
    setWebAuthnBiometricType(biometricType);
  }, []);

  const startEnrollment = async () => {
    currentFingerRef.current = 0;
    setEnrollmentState({
      status: BiometricEnrollmentStatus.InProgress,
      currentFinger: 0,
      completedFingers: [],
    });

    await captureNextFinger();
  };

  const startWebAuthnEnrollment = async () => {
    try {
      setWebAuthnLoading(true);
      setEnrollmentState({
        status: BiometricEnrollmentStatus.InProgress,
        currentFinger: 0,
        completedFingers: [],
      });

      // Enroll with WebAuthn (Touch ID, Face ID, Windows Hello)
      const { credentialId, publicKey } = await fingerprintCaptureService.enrollWithWebAuthn(
        walletAddress,
        'My Wallet'
      );

      // Save the WebAuthn credential
      await biometricDidService.saveWebAuthnCredential(credentialId, publicKey);

      // Mark enrollment as complete
      setEnrollmentState((prev) => ({
        ...prev,
        status: BiometricEnrollmentStatus.Complete,
        did: `did:webauthn:${walletAddress}`,
      }));

      // Show success toast
      dispatch(setToastMsg(ToastMsgType.BIOMETRIC_ENROLLMENT_SUCCESS));

      // Keep user on success page - they'll click Continue button when ready
    } catch (error) {
      console.error('WebAuthn enrollment error:', error);
      const userError = getUserFriendlyError(error);
      const errorMessage = error instanceof Error ? error.message : 'WebAuthn enrollment failed';
      const biometricError = BIOMETRIC_ERRORS[errorMessage] || userError;

      setEnrollmentState((prev) => ({
        ...prev,
        status: BiometricEnrollmentStatus.Failed,
        error: biometricError.message,
      }));
      setShowErrorAlert(true);
    }
  };

  const captureNextFinger = async () => {
    const currentFinger = currentFingerRef.current;

    if (currentFinger >= totalFingers) {
      await completeEnrollment();
      return;
    }

    const fingerId = FINGER_IDS[currentFinger];

    try {
      // Capture fingerprint from sensor
      const capture = await fingerprintCaptureService.captureFingerprint(
        fingerId
      );

      // Validate quality
      if (!fingerprintCaptureService.validateQuality(capture)) {
        throw new Error(
          `Poor fingerprint quality. Please try again with ${FINGER_NAMES[fingerId]}.`
        );
      }

      // Increment ref and update state
      currentFingerRef.current = currentFinger + 1;
      setEnrollmentState((prev) => ({
        ...prev,
        currentFinger: currentFinger + 1,
        completedFingers: [...prev.completedFingers, fingerId],
      }));

      // Auto-advance to next finger
      setTimeout(() => {
        captureNextFinger();
      }, 500);
    } catch (error) {
      const userError = getUserFriendlyError(error);
      // Check if it's a known biometric error
      const errorMessage = error instanceof Error ? error.message : "Capture failed";
      const biometricError = BIOMETRIC_ERRORS[errorMessage] || userError;

      setEnrollmentState((prev) => ({
        ...prev,
        status: BiometricEnrollmentStatus.Failed,
        error: biometricError.message,
      }));
      setShowErrorAlert(true);
    }
  };

  const completeEnrollment = async () => {
    try {
      // Show loading state during DID generation
      setIsGeneratingDid(true);

      // Capture all fingerprints
      const fingers = await fingerprintCaptureService.captureAllFingerprints();

      // Generate biometric DID (this takes 5-10 seconds)
      const result = await biometricDidService.generate(
        { fingers },
        walletAddress
      );

      // Store helper data securely
      await biometricDidService.saveHelperData(result.did, result.helpers);

      // Store current DID for quick access
      await biometricDidService.saveCurrentDid(result.did);

      // Update enrollment state with success
      setEnrollmentState((prev) => ({
        ...prev,
        status: BiometricEnrollmentStatus.Complete,
        did: result.did,
        idHash: result.id_hash,
        txHash: result.tx_hash,  // Include transaction hash for explorer link
      }));

      // Show success toast
      dispatch(setToastMsg(ToastMsgType.BIOMETRIC_ENROLLMENT_SUCCESS));

      // Keep user on success page - they'll click Continue button when ready
    } catch (error) {
      console.error("Biometric enrollment error:", error);
      const userError = getUserFriendlyError(error);
      const errorMessage = error instanceof Error ? error.message : "Enrollment failed";
      const biometricError = BIOMETRIC_ERRORS[errorMessage] || userError;

      setEnrollmentState((prev) => ({
        ...prev,
        status: BiometricEnrollmentStatus.Failed,
        error: biometricError.message,
      }));
      setShowErrorAlert(true);
    } finally {
      // Always hide loading state
      setIsGeneratingDid(false);
    }
  };

  const navToNextStep = () => {
    const data: DataProps = {
      store: {
        stateCache: {
          ...stateCache,
          authentication: {
            ...stateCache.authentication,
            biometricDidEnrolled: true,
          },
        },
      },
      state: {
        biometricDidCompleted: true,
      },
    };

    const { nextPath, updateRedux } = getNextRoute(
      RoutePath.BIOMETRIC_ENROLLMENT,
      data
    );
    updateReduxState(nextPath.pathname, data, dispatch, updateRedux);
    ionRouter.push(nextPath.pathname, "forward", "push");
  };

  const handleSkip = () => {
    setShowSkipAlert(true);
  };

  const confirmSkip = () => {
    navToNextStep();
  };

  const retryEnrollment = () => {
    setEnrollmentState({
      status: BiometricEnrollmentStatus.NotStarted,
      currentFinger: 0,
      completedFingers: [],
    });
    setShowErrorAlert(false);
  };

  const renderContent = () => {
    const { status, currentFinger } = enrollmentState;

    if (status === BiometricEnrollmentStatus.NotStarted) {
      return (
        <div className="enrollment-intro">
          <IonIcon icon={fingerPrintOutline} className="large-icon" aria-hidden="true" />

          <div className="header-with-help">
            <h1>{i18n.t("biometric.enrollment.title")}</h1>
            <button
              className="help-button"
              onClick={() => setShowHelpModal(true)}
              aria-label="Learn more about biometric enrollment"
            >
              <IonIcon icon={helpCircleOutline} />
            </button>
          </div>

          <p>{i18n.t("biometric.enrollment.description")}</p>

          {/* Quick facts */}
          <div className="quick-facts">
            <div className="fact">
              <IonIcon icon={lockClosedOutline} />
              <div>
                <strong>Secure</strong>
                <p>Your fingerprints never leave this device</p>
              </div>
            </div>
            <div className="fact">
              <IonIcon icon={shieldCheckmarkOutline} />
              <div>
                <strong>Private</strong>
                <p>No personal data required</p>
              </div>
            </div>
            <div className="fact">
              <IonIcon icon={checkmarkCircle} />
              <div>
                <strong>Unique</strong>
                <p>One person, one identity</p>
              </div>
            </div>
          </div>

          {/* WebAuthn Option (if available) */}
          {webAuthnAvailable && webAuthnBiometricType && (
            <div className="enrollment-option webauthn-option">
              <h3>Quick Setup: {webAuthnBiometricType}</h3>
              <p>
                Use your device's built-in biometric authentication for quick and secure enrollment.
              </p>
              <button
                className="webauthn-enroll-button"
                onClick={startWebAuthnEnrollment}
                disabled={webAuthnLoading}
                aria-label={`Enable ${webAuthnBiometricType} for quick biometric authentication`}
              >
                {webAuthnLoading ? (
                  <>
                    <IonSpinner name="crescent" />
                    <span>Enrolling...</span>
                  </>
                ) : (
                  <>
                    <IonIcon icon={fingerPrintOutline} aria-hidden="true" />
                    <span>Enable {webAuthnBiometricType}</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Sensor-based Option */}
          <div className={`enrollment-option sensor-option ${webAuthnAvailable ? 'alternative' : ''}`}>
            {webAuthnAvailable && <h3>Advanced: Fingerprint Sensor</h3>}
            {!webAuthnAvailable && <h3>Fingerprint Sensor Enrollment</h3>}
            <p>
              Use a USB fingerprint sensor for maximum security with {totalFingers} fingerprints.
            </p>
            <div className="finger-count">
              <strong>{totalFingers}</strong> fingerprints will be captured
            </div>
          </div>
        </div>
      );
    }

    if (status === BiometricEnrollmentStatus.InProgress) {
      // Show loading screen during DID generation
      if (isGeneratingDid) {
        return (
          <div className="loading-did">
            <IonSpinner name="crescent" className="large-spinner" />
            <h2>Generating Your Secure Digital ID</h2>
            <p className="loading-message">
              Creating your unique biometric identity...
            </p>
            <p className="loading-time">This may take 5-10 seconds</p>
          </div>
        );
      }

      const currentFingerId = FINGER_IDS[currentFinger];
      const fingerName = FINGER_NAMES[currentFingerId];

      return (
        <div className="enrollment-progress">
          <div className="progress-header">
            <h2>Capturing Fingerprints</h2>
            <div className="progress-counter">
              {currentFinger} / {totalFingers}
            </div>
          </div>

          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
              role="progressbar"
              aria-valuenow={currentFinger}
              aria-valuemin={0}
              aria-valuemax={totalFingers}
              aria-label={`Biometric enrollment progress: ${currentFinger} of ${totalFingers} fingerprints captured`}
            />
          </div>

          {/* Screen reader announcements */}
          <div
            aria-live="polite"
            aria-atomic="true"
            className="sr-only"
          >
            {`Capturing ${fingerName}. ${currentFinger} of ${totalFingers} fingerprints complete.`}
          </div>

          {/* Current finger being captured */}
          <div className="current-finger">
            <IonIcon
              icon={fingerPrintOutline}
              className="pulse-icon"
              aria-hidden="true"
            />
            <h3>Capturing {fingerName}</h3>
            <p className="instruction">Place finger on sensor...</p>
            <p className="progress-text">{currentFinger} of {totalFingers} complete</p>
          </div>

          {/* Checklist of all fingers */}
          <div className="completed-fingers">
            <h4>Fingerprint Progress</h4>
            <div className="finger-list">
              {FINGER_IDS.map((fingerId, idx) => {
                const isCompleted = idx < currentFinger;
                const isCurrent = idx === currentFinger;
                return (
                  <div
                    key={fingerId}
                    className={`finger-item ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}`}
                  >
                    <IonIcon
                      icon={isCompleted ? checkmarkCircle : fingerPrintOutline}
                      className={isCompleted ? 'check-icon' : isCurrent ? 'pulse-small' : 'pending-icon'}
                    />
                    <span className="finger-label">{FINGER_NAMES[fingerId]}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      );
    }

    if (status === BiometricEnrollmentStatus.Complete) {
      return (
        <div className="enrollment-complete-wrapper">
          <div className="enrollment-complete">
            <IonIcon icon={checkmarkCircle} className="success-icon" aria-hidden="true" />
            <h1>🎉 Your Identity is Secure!</h1>

            <div className="success-info">
              <h3>What just happened?</h3>
              <ul>
                <li>
                  <IonIcon icon={checkmarkCircle} />
                  <span><strong>Unique Digital ID created</strong> from your fingerprints</span>
                </li>
                <li>
                  <IonIcon icon={lockClosedOutline} />
                  <span><strong>Privacy protected</strong> - no personal info stored</span>
                </li>
                <li>
                  <IonIcon icon={shieldCheckmarkOutline} />
                  <span><strong>Sybil resistant</strong> - one person, one identity</span>
                </li>
              </ul>
            </div>

            {enrollmentState.did && (
              <div className="did-display">
                <label>Your Digital ID (DID):</label>
                <code className="did-code">{enrollmentState.did}</code>
                <button
                  className="copy-button"
                  onClick={() => {
                    navigator.clipboard.writeText(enrollmentState.did || '');
                    dispatch(setToastMsg(ToastMsgType.COPIED_TO_CLIPBOARD));
                  }}
                  aria-label="Copy DID to clipboard"
                >
                  <IonIcon icon={copyOutline} />
                  <span>Copy</span>
                </button>
              </div>
            )}

            {enrollmentState.txHash && (
              <div className="transaction-explorer">
                <label>Enrollment Transaction:</label>
                <div className="tx-hash-display">
                  <code className="tx-hash-code">{enrollmentState.txHash}</code>
                  <button
                    className="explorer-button"
                    onClick={() => {
                      const explorerUrl = getCardanoscanUrl(enrollmentState.txHash!, "testnet");
                      openBrowserLink(explorerUrl);
                    }}
                    aria-label="View transaction on Cardanoscan explorer"
                    title="View on Cardanoscan"
                  >
                    <IonIcon icon={openOutline} />
                    <span>View on Explorer</span>
                  </button>
                  <button
                    className="copy-button"
                    onClick={() => {
                      navigator.clipboard.writeText(enrollmentState.txHash || '');
                      dispatch(setToastMsg(ToastMsgType.COPIED_TO_CLIPBOARD));
                    }}
                    aria-label="Copy transaction hash to clipboard"
                  >
                    <IonIcon icon={copyOutline} />
                    <span>Copy</span>
                  </button>
                </div>
              </div>
            )}

            <div className="next-steps">
              <h3>What's next?</h3>
              <p>You can now use your fingerprint to:</p>
              <ul>
                <li>🔓 <strong>Unlock your wallet</strong></li>
                <li>✍️ <strong>Sign transactions</strong> securely</li>
                <li>🆔 <strong>Verify your identity</strong></li>
              </ul>
            </div>

            <div className="help-text">
              <IonIcon icon={informationCircleOutline} />
              <p>
                Your DID is stored securely on this device. You can view it anytime in <strong>Settings</strong>.
              </p>
            </div>

            <div className="completion-actions">
              <button
                className="continue-button"
                onClick={navToNextStep}
                aria-label="Continue to next step"
              >
                Continue
              </button>
            </div>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <>
      <ResponsivePageLayout
        pageId={pageId}
        header={<PageHeader currentPath={RoutePath.BIOMETRIC_ENROLLMENT} />}
      >
        {renderContent()}

        {enrollmentState.status === BiometricEnrollmentStatus.NotStarted && (
          <PageFooter
            primaryButtonText="Start Enrollment"
            primaryButtonAction={startEnrollment}
            tertiaryButtonText="Skip"
            tertiaryButtonAction={handleSkip}
          />
        )}
      </ResponsivePageLayout>

      <Alert
        isOpen={showSkipAlert}
        setIsOpen={setShowSkipAlert}
        dataTestId="alert-skip-biometric-enrollment"
        headerText="Skip Biometric Enrollment?"
        subheaderText="You can enroll later in settings."
        confirmButtonText="Skip"
        actionConfirm={confirmSkip}
        cancelButtonText="Cancel"
        actionCancel={() => setShowSkipAlert(false)}
      />

      <Alert
        isOpen={showErrorAlert}
        setIsOpen={setShowErrorAlert}
        dataTestId="alert-enrollment-error"
        headerText="Enrollment Failed"
        subheaderText={enrollmentState.error || "Please try again."}
        confirmButtonText="Retry"
        actionConfirm={retryEnrollment}
        cancelButtonText="Skip"
        actionCancel={() => {
          setShowErrorAlert(false);
          handleSkip();
        }}
      />

      {/* Help Modal */}
      <IonModal
        isOpen={showHelpModal}
        onDidDismiss={() => setShowHelpModal(false)}
        className="help-modal"
      >
        <div className="help-modal-content">
          <div className="help-modal-header">
            <h2>About Biometric Digital IDs</h2>
            <button
              className="close-button"
              onClick={() => setShowHelpModal(false)}
              aria-label="Close help modal"
            >
              <IonIcon icon={closeCircle} />
            </button>
          </div>

          <div className="help-modal-body">
            <section>
              <h3>What is a Biometric DID?</h3>
              <p>
                A Decentralized Identifier (DID) is a unique digital identity created from your
                fingerprints. It's like a digital passport that proves you're you, without revealing
                personal information.
              </p>
            </section>

            <section>
              <h3>How does it work?</h3>
              <ol>
                <li>You scan your fingerprints (10 fingers for maximum security)</li>
                <li>A unique cryptographic ID is generated</li>
                <li>Your fingerprints are stored securely on <strong>this device only</strong></li>
                <li>You can prove your identity by scanning your fingerprint again</li>
              </ol>
            </section>

            <section>
              <h3>Is it safe?</h3>
              <p>
                <strong>Yes!</strong> Your actual fingerprint images are <strong>NEVER</strong> stored
                or transmitted. Only cryptographic keys derived from your fingerprints are used.
              </p>
              <ul className="safety-features">
                <li>
                  <IonIcon icon={lockClosedOutline} />
                  <span><strong>End-to-end encrypted</strong> - No server can access your biometrics</span>
                </li>
                <li>
                  <IonIcon icon={shieldCheckmarkOutline} />
                  <span><strong>Tamper-proof</strong> - Impossible to fake or duplicate</span>
                </li>
                <li>
                  <IonIcon icon={checkmarkCircle} />
                  <span><strong>Revocable</strong> - You can disable it anytime in Settings</span>
                </li>
              </ul>
            </section>

            <section>
              <h3>Why 10 fingerprints?</h3>
              <p>
                Using all 10 fingers provides maximum security and reliability. Even if a few
                fingerprints are slightly different due to cuts or wear, the system can still
                verify your identity.
              </p>
            </section>
          </div>

          <div className="help-modal-footer">
            <button
              className="primary-button"
              onClick={() => setShowHelpModal(false)}
            >
              Got it!
            </button>
          </div>
        </div>
      </IonModal>
    </>
  );
};
