import { IonText } from "@ionic/react";
import { useState, useEffect } from "react";
import { useAppSelector } from "../../../../store/hooks";
import { getStateCache } from "../../../../store/reducers/stateCache";
import { i18n } from "../../../../i18n";
import { IncomingRequestType } from "../../../../store/reducers/stateCache/stateCache.types";
import {
  CardDetailsAttributes,
  CardDetailsBlock,
} from "../../../components/CardDetails";
import { PageFooter } from "../../../components/PageFooter";
import { PageHeader } from "../../../components/PageHeader";
import { Spinner } from "../../../components/Spinner";
import { Verification } from "../../../components/Verification";
import {
  BiometricVerification,
  VerificationMode,
} from "../../../components/BiometricVerification";
import { biometricDidService } from "../../../../core/biometric";
import { ScrollablePageLayout } from "../../../components/layout/ScrollablePageLayout";
import { RequestProps } from "../IncomingRequest.types";
import "./SignRequest.scss";

const SignRequest = ({
  pageId,
  activeStatus,
  requestData,
  initiateAnimation,
  handleAccept,
  handleCancel,
}: RequestProps<IncomingRequestType.PEER_CONNECT_SIGN>) => {
  const [verifyIsOpen, setVerifyIsOpen] = useState(false);
  const [showBiometricVerification, setShowBiometricVerification] = useState(false);
  const [biometricDid, setBiometricDid] = useState<string | null>(null);
  const stateCache = useAppSelector(getStateCache);
  const authentication = stateCache.authentication;

  // Load biometric DID if enrolled
  useEffect(() => {
    const loadBiometricDid = async () => {
      try {
        const did = await biometricDidService.getCurrentDid();
        setBiometricDid(did);
      } catch (error) {
        console.error("Failed to load biometric DID:", error);
      }
    };
    loadBiometricDid();
  }, []);

  const signDetails = (() => {
    if (!requestData.signTransaction) {
      return {};
    }

    let signContent;
    try {
      signContent = JSON.parse(requestData.signTransaction.payload.payload);
    } catch (error) {
      signContent = requestData.signTransaction.payload.payload;
    }
    return signContent;
  })();

  const signRequest = requestData.signTransaction;
  const logo = requestData.peerConnection.iconB64;

  const handleSign = () => {
    handleAccept();
  };

  const handleBiometricSignClick = () => {
    setShowBiometricVerification(true);
  };

  const handleBiometricVerificationSuccess = () => {
    setShowBiometricVerification(false);
    handleSign();
  };

  const handleBiometricVerificationFailure = (error: string) => {
    console.error("Biometric verification failed:", error);
    // Keep biometric verification open for retry
  };

  const handleBiometricVerificationCancel = () => {
    setShowBiometricVerification(false);
  };

  // Check if biometric DID is available
  const canUseBiometricDid = biometricDid && authentication.biometricDidEnrolled;

  return (
    <>
      {showBiometricVerification && canUseBiometricDid ? (
        <div className="biometric-verification-overlay">
          <BiometricVerification
            mode={VerificationMode.TransactionSign}
            did={biometricDid}
            onSuccess={handleBiometricVerificationSuccess}
            onFailure={handleBiometricVerificationFailure}
            onCancel={handleBiometricVerificationCancel}
          />
        </div>
      ) : null}
      <ScrollablePageLayout
        activeStatus={activeStatus}
        pageId={pageId}
        customClass={`sign-request${initiateAnimation ? " blur" : ""}`}
        header={
          <PageHeader
            onBack={handleCancel}
            title={`${i18n.t("request.sign.title")}`}
          />
        }
        footer={
          <PageFooter
            customClass="sign-footer"
            primaryButtonText={
              canUseBiometricDid
                ? `${i18n.t("biometric.verification.sign.button")}`
                : `${i18n.t("request.button.sign")}`
            }
            primaryButtonAction={
              canUseBiometricDid
                ? handleBiometricSignClick
                : () => setVerifyIsOpen(true)
            }
            secondaryButtonText={`${i18n.t("request.button.dontallow")}`}
            secondaryButtonAction={handleCancel}
          />
        }
      >
        <div className="sign-header">
          <img
            className="sign-owner-logo"
            data-testid="sign-logo"
            src={logo}
            alt={requestData.peerConnection?.name}
          />
          <h2 className="sign-name">{requestData.peerConnection?.name}</h2>
          <p className="sign-link">{requestData.peerConnection?.url}</p>
        </div>
        <div className="sign-content">
          <CardDetailsBlock
            className="sign-identifier"
            title={`${i18n.t("request.sign.identifier")}`}
          >
            <IonText className="identifier">
              {signRequest?.payload.identifier}
            </IonText>
          </CardDetailsBlock>
          <CardDetailsBlock
            className="sign-data"
            title={i18n.t("request.sign.transaction.data")}
          >
            {typeof signDetails === "object" ? (
              <CardDetailsAttributes
                data={signDetails}
                itemProps={{
                  mask: false,
                  fullText: true,
                  copyButton: false,
                  className: "sign-info-item",
                }}
              />
            ) : (
              <IonText className="sign-string">
                {signDetails.toString()}
              </IonText>
            )}
          </CardDetailsBlock>
          {canUseBiometricDid && (
            <div className="sign-passcode-fallback">
              <button
                className="passcode-fallback-link"
                onClick={() => setVerifyIsOpen(true)}
                data-testid="use-passcode-button"
              >
                {i18n.t("biometric.verification.button.usepasscode")}
              </button>
            </div>
          )}
        </div>
      </ScrollablePageLayout>
      <Spinner show={initiateAnimation} />
      <Verification
        verifyIsOpen={verifyIsOpen}
        setVerifyIsOpen={setVerifyIsOpen}
        onVerify={handleSign}
      />
    </>
  );
};

export { SignRequest };
