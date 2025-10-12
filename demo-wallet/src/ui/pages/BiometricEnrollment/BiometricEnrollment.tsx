/**
 * Biometric DID Enrollment Page
 * Captures fingerprints, generates DID, and stores helper data
 */

import { IonIcon, IonSpinner } from "@ionic/react";
import { checkmarkCircle, fingerPrintOutline } from "ionicons/icons";
import { useState, useEffect } from "react";
import { Agent } from "../../../core/agent/agent";
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
import {
  biometricDidService,
  fingerprintCaptureService,
  FINGER_IDS,
  FingerId,
  BiometricEnrollmentStatus,
} from "../../../core/biometric";
import "./BiometricEnrollment.scss";

interface EnrollmentState {
  status: BiometricEnrollmentStatus;
  currentFinger: number;
  completedFingers: string[];
  error?: string;
  did?: string;
  idHash?: string;
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

  // Get wallet address (would come from user's wallet)
  // For now, use a test address
  const walletAddress = "addr_test1_demo";

  const totalFingers = FINGER_IDS.length;
  const progress = (enrollmentState.currentFinger / totalFingers) * 100;

  const startEnrollment = async () => {
    setEnrollmentState({
      status: BiometricEnrollmentStatus.InProgress,
      currentFinger: 0,
      completedFingers: [],
    });

    await captureNextFinger();
  };

  const captureNextFinger = async () => {
    const { currentFinger, completedFingers } = enrollmentState;

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

      // Update state
      setEnrollmentState((prev) => ({
        ...prev,
        currentFinger: prev.currentFinger + 1,
        completedFingers: [...prev.completedFingers, fingerId],
      }));

      // Auto-advance to next finger
      setTimeout(() => {
        if (currentFinger + 1 < totalFingers) {
          captureNextFinger();
        } else {
          completeEnrollment();
        }
      }, 500);
    } catch (error) {
      setEnrollmentState((prev) => ({
        ...prev,
        status: BiometricEnrollmentStatus.Failed,
        error: error instanceof Error ? error.message : "Capture failed",
      }));
      setShowErrorAlert(true);
    }
  };

  const completeEnrollment = async () => {
    try {
      // Capture all fingerprints
      const fingers = await fingerprintCaptureService.captureAllFingerprints();

      // Generate biometric DID
      const result = await biometricDidService.generate(
        { fingers },
        walletAddress
      );

      // Store helper data securely
      await biometricDidService.saveHelperData(result.did, result.helpers);

      // Store biometric metadata via wallet connect API
      await Agent.agent.peerConnectionMetadataStorage.createPeerConnectionMetadataRecord(
        {
          id: walletAddress,
          selectedAid: "", // Would be set from actual identifier
          biometricMetadata: {
            did: result.did,
            label: 1990,
            walletAddress: result.wallet_address,
            idHash: result.id_hash,
            helperStorage: "inline",
            helperData: result.helpers,
            metadata: [[1990, result.metadata_cip30_inline]],
            createdAt: new Date().toISOString(),
          },
        }
      );

      setEnrollmentState((prev) => ({
        ...prev,
        status: BiometricEnrollmentStatus.Complete,
        did: result.did,
        idHash: result.id_hash,
      }));

      dispatch(setToastMsg(ToastMsgType.BIOMETRIC_ENROLLMENT_SUCCESS));

      // Navigate to next step
      setTimeout(() => {
        navToNextStep();
      }, 2000);
    } catch (error) {
      setEnrollmentState((prev) => ({
        ...prev,
        status: BiometricEnrollmentStatus.Failed,
        error:
          error instanceof Error ? error.message : "Enrollment failed",
      }));
      setShowErrorAlert(true);
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
          <IonIcon icon={fingerPrintOutline} className="large-icon" />
          <h1>{i18n.t("biometric.enrollment.title")}</h1>
          <p>{i18n.t("biometric.enrollment.description")}</p>
          <div className="finger-count">
            <strong>{totalFingers}</strong> fingerprints will be captured
          </div>
        </div>
      );
    }

    if (status === BiometricEnrollmentStatus.InProgress) {
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
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>

          <div className="current-finger">
            <IonIcon icon={fingerPrintOutline} className="pulse-icon" />
            <h3>Place your finger</h3>
            <p className="finger-name">{fingerName}</p>
          </div>

          <div className="completed-fingers">
            {enrollmentState.completedFingers.map((fingerId) => (
              <div key={fingerId} className="completed-finger">
                <IonIcon icon={checkmarkCircle} />
                <span>{FINGER_NAMES[fingerId as FingerId]}</span>
              </div>
            ))}
          </div>

          <IonSpinner name="crescent" />
        </div>
      );
    }

    if (status === BiometricEnrollmentStatus.Complete) {
      return (
        <div className="enrollment-complete">
          <IonIcon icon={checkmarkCircle} className="success-icon" />
          <h1>Enrollment Complete!</h1>
          <p>Your biometric DID has been created.</p>
          {enrollmentState.did && (
            <div className="did-display">
              <label>Your DID:</label>
              <code>{enrollmentState.did}</code>
            </div>
          )}
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
        primaryButtonText="Skip"
        primaryButtonAction={confirmSkip}
        secondaryButtonText="Cancel"
        secondaryButtonAction={() => setShowSkipAlert(false)}
      />

      <Alert
        isOpen={showErrorAlert}
        setIsOpen={setShowErrorAlert}
        dataTestId="alert-enrollment-error"
        headerText="Enrollment Failed"
        subheaderText={enrollmentState.error || "Please try again."}
        primaryButtonText="Retry"
        primaryButtonAction={retryEnrollment}
        secondaryButtonText="Skip"
        secondaryButtonAction={() => {
          setShowErrorAlert(false);
          handleSkip();
        }}
      />
    </>
  );
};
