import { IonButton, IonIcon } from "@ionic/react";
import { warningOutline, closeOutline } from "ionicons/icons";
import { useState, useEffect } from "react";
import { useHistory } from "react-router-dom";
import { Agent } from "../../../core/agent/agent";
import { MiscRecordId } from "../../../core/agent/agent.types";
import { RoutePath } from "../../../routes";
import "./BackupWarningBanner.scss";

const BackupWarningBanner = () => {
  const [showBanner, setShowBanner] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const history = useHistory();

  useEffect(() => {
    checkBackupStatus();
  }, []);

  const checkBackupStatus = async () => {
    try {
      const record = await Agent.agent.basicStorage.findById(
        MiscRecordId.APP_SEED_PHRASE_BACKED_UP
      );

      if (record && record.content.value === "false") {
        setShowBanner(true);
      }
    } catch (error) {
      // Record doesn't exist = backup is complete (or not relevant)
      setShowBanner(false);
    }
  };

  const handleBackupNow = () => {
    // Navigate to deferred backup page
    history.push(RoutePath.DEFERRED_BACKUP);
  };

  const handleDismiss = () => {
    setDismissed(true);
  };

  if (!showBanner || dismissed) {
    return null;
  }

  return (
    <div className="backup-warning-banner">
      <div className="backup-warning-banner__content">
        <IonIcon
          icon={warningOutline}
          className="backup-warning-banner__icon"
        />
        <div className="backup-warning-banner__text">
          <strong>Backup your recovery phrase</strong>
          <p>You haven't backed up your recovery phrase yet. Do this now to secure your wallet.</p>
        </div>
      </div>
      <div className="backup-warning-banner__actions">
        <IonButton
          size="small"
          fill="solid"
          color="warning"
          onClick={handleBackupNow}
        >
          Backup Now
        </IonButton>
        <IonButton
          size="small"
          fill="clear"
          color="medium"
          onClick={handleDismiss}
          className="backup-warning-banner__dismiss"
        >
          <IonIcon icon={closeOutline} slot="icon-only" />
        </IonButton>
      </div>
    </div>
  );
};

export { BackupWarningBanner };
