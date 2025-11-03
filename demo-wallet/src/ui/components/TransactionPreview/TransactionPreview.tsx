/**
 * Transaction Preview Component
 *
 * Displays transaction details in human-readable format before signing.
 * Shows inputs, outputs, fees, and metadata.
 */

import { useState, useEffect } from "react";
import {
  IonModal,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonButtons,
  IonButton,
  IonIcon,
  IonList,
  IonItem,
  IonLabel,
  IonNote,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonBadge,
  IonSpinner,
} from "@ionic/react";
import { closeOutline, checkmarkCircle, alertCircle, informationCircle } from "ionicons/icons";
import "./TransactionPreview.scss";

/**
 * Transaction input/output
 */
export interface TxIO {
  address: string;
  amount: string; // lovelace
  assets?: Record<string, string>; // policyId.assetName -> amount
}

/**
 * Transaction details
 */
export interface TransactionDetails {
  inputs: TxIO[];
  outputs: TxIO[];
  fee: string; // lovelace
  metadata?: Record<string, any>;
  certificates?: string[];
  withdrawals?: Record<string, string>;
  mint?: Record<string, string>;
}

/**
 * Transaction Preview props
 */
export interface TransactionPreviewProps {
  isOpen: boolean;
  transactionCbor: string; // CBOR hex-encoded transaction
  onApprove: () => void;
  onReject: () => void;
}

/**
 * Format lovelace to ADA
 */
const formatAda = (lovelace: string): string => {
  const ada = parseInt(lovelace) / 1_000_000;
  return `${ada.toLocaleString()} ADA`;
};

/**
 * Shorten address for display
 */
const shortenAddress = (address: string): string => {
  if (address.length <= 20) return address;
  return `${address.substring(0, 10)}...${address.substring(address.length - 10)}`;
};

/**
 * Transaction Preview Component
 */
export const TransactionPreview: React.FC<TransactionPreviewProps> = ({
  isOpen,
  transactionCbor,
  onApprove,
  onReject,
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [txDetails, setTxDetails] = useState<TransactionDetails | null>(null);

  /**
   * Decode transaction CBOR
   */
  useEffect(() => {
    if (!isOpen || !transactionCbor) {
      return;
    }

    const decodeTx = async () => {
      try {
        setLoading(true);
        setError(null);

        // TODO: Implement proper CBOR decoding with @emurgo/cardano-serialization-lib-browser
        // For now, return mock data
        console.warn("Transaction decoding not fully implemented - showing mock data");

        // Mock transaction details
        const mockDetails: TransactionDetails = {
          inputs: [
            {
              address: "addr1qx2kd28nq8ac5prwg32hhvudlwggpgfp8utlyqxu6wqgz62f79qsdmm5dsknt9ecr5w468r9ey0fxwkdrwh08ly3tu9sy0f4qd",
              amount: "5000000", // 5 ADA
            },
          ],
          outputs: [
            {
              address: "addr1q9vlxm7u9vvx3w0x8r5q5j5x2x7x5x8x9x0x1x2x3x4x5x6x7x8x9x0x1x2x3x4x5x6x7x8x9x0x1x2x3x4x5",
              amount: "2000000", // 2 ADA
            },
            {
              address: "addr1qx2kd28nq8ac5prwg32hhvudlwggpgfp8utlyqxu6wqgz62f79qsdmm5dsknt9ecr5w468r9ey0fxwkdrwh08ly3tu9sy0f4qd",
              amount: "2823157", // Change: 2.823157 ADA
            },
          ],
          fee: "176843", // 0.176843 ADA
          metadata: {
            "1990": {
              version: 1,
              type: "biometric-enrollment",
            },
          },
        };

        setTxDetails(mockDetails);
        setLoading(false);
      } catch (err) {
        setError(`Failed to decode transaction: ${err instanceof Error ? err.message : String(err)}`);
        setLoading(false);
      }
    };

    decodeTx();
  }, [isOpen, transactionCbor]);

  /**
   * Calculate total output amount
   */
  const calculateTotalOutput = (): string => {
    if (!txDetails) return "0";
    const total = txDetails.outputs.reduce((sum, output) => {
      return sum + parseInt(output.amount);
    }, 0);
    return total.toString();
  };

  /**
   * Check if transaction has metadata
   */
  const hasMetadata = (): boolean => {
    return !!(txDetails?.metadata && Object.keys(txDetails.metadata).length > 0);
  };

  /**
   * Check if transaction has certificates (staking operations)
   */
  const hasCertificates = (): boolean => {
    return !!(txDetails?.certificates && txDetails.certificates.length > 0);
  };

  return (
    <IonModal isOpen={isOpen} onDidDismiss={onReject} className="transaction-preview-modal">
      <IonHeader>
        <IonToolbar>
          <IonTitle>Review Transaction</IonTitle>
          <IonButtons slot="end">
            <IonButton onClick={onReject}>
              <IonIcon slot="icon-only" icon={closeOutline} />
            </IonButton>
          </IonButtons>
        </IonToolbar>
      </IonHeader>

      <IonContent className="transaction-preview-content">
        {loading && (
          <div className="loading-container">
            <IonSpinner name="crescent" />
            <p>Decoding transaction...</p>
          </div>
        )}

        {error && (
          <IonCard color="danger">
            <IonCardHeader>
              <IonCardTitle>
                <IonIcon icon={alertCircle} /> Error
              </IonCardTitle>
            </IonCardHeader>
            <IonCardContent>{error}</IonCardContent>
          </IonCard>
        )}

        {!loading && !error && txDetails && (
          <>
            {/* Summary Card */}
            <IonCard className="summary-card">
              <IonCardHeader>
                <IonCardTitle>Transaction Summary</IonCardTitle>
              </IonCardHeader>
              <IonCardContent>
                <div className="summary-row">
                  <span className="label">Total Output:</span>
                  <span className="value">{formatAda(calculateTotalOutput())}</span>
                </div>
                <div className="summary-row">
                  <span className="label">Network Fee:</span>
                  <span className="value fee">{formatAda(txDetails.fee)}</span>
                </div>
                <div className="summary-row total">
                  <span className="label">Total Cost:</span>
                  <span className="value">
                    {formatAda((parseInt(calculateTotalOutput()) + parseInt(txDetails.fee)).toString())}
                  </span>
                </div>
              </IonCardContent>
            </IonCard>

            {/* Inputs */}
            <IonCard>
              <IonCardHeader>
                <IonCardTitle>
                  Inputs ({txDetails.inputs.length})
                  <IonBadge color="primary" className="count-badge">
                    {txDetails.inputs.length}
                  </IonBadge>
                </IonCardTitle>
              </IonCardHeader>
              <IonCardContent>
                <IonList>
                  {txDetails.inputs.map((input, index) => (
                    <IonItem key={index} lines={index === txDetails.inputs.length - 1 ? "none" : "full"}>
                      <IonLabel className="ion-text-wrap">
                        <h3>{shortenAddress(input.address)}</h3>
                        <p className="amount-text">{formatAda(input.amount)}</p>
                      </IonLabel>
                    </IonItem>
                  ))}
                </IonList>
              </IonCardContent>
            </IonCard>

            {/* Outputs */}
            <IonCard>
              <IonCardHeader>
                <IonCardTitle>
                  Outputs ({txDetails.outputs.length})
                  <IonBadge color="success" className="count-badge">
                    {txDetails.outputs.length}
                  </IonBadge>
                </IonCardTitle>
              </IonCardHeader>
              <IonCardContent>
                <IonList>
                  {txDetails.outputs.map((output, index) => (
                    <IonItem key={index} lines={index === txDetails.outputs.length - 1 ? "none" : "full"}>
                      <IonLabel className="ion-text-wrap">
                        <h3>{shortenAddress(output.address)}</h3>
                        <p className="amount-text">{formatAda(output.amount)}</p>
                        {output.assets && Object.keys(output.assets).length > 0 && (
                          <IonNote color="medium">+ {Object.keys(output.assets).length} native assets</IonNote>
                        )}
                      </IonLabel>
                    </IonItem>
                  ))}
                </IonList>
              </IonCardContent>
            </IonCard>

            {/* Metadata */}
            {hasMetadata() && (
              <IonCard>
                <IonCardHeader>
                  <IonCardTitle>
                    <IonIcon icon={informationCircle} /> Metadata
                  </IonCardTitle>
                </IonCardHeader>
                <IonCardContent>
                  <pre className="metadata-json">{JSON.stringify(txDetails.metadata, null, 2)}</pre>
                </IonCardContent>
              </IonCard>
            )}

            {/* Certificates */}
            {hasCertificates() && (
              <IonCard>
                <IonCardHeader>
                  <IonCardTitle>Certificates ({txDetails.certificates?.length})</IonCardTitle>
                </IonCardHeader>
                <IonCardContent>
                  <IonList>
                    {txDetails.certificates?.map((cert, index) => (
                      <IonItem key={index}>
                        <IonLabel className="ion-text-wrap">
                          <p>{cert}</p>
                        </IonLabel>
                      </IonItem>
                    ))}
                  </IonList>
                </IonCardContent>
              </IonCard>
            )}

            {/* Warning notice */}
            <IonCard color="warning" className="warning-card">
              <IonCardContent>
                <IonIcon icon={alertCircle} /> <strong>Review Carefully</strong>
                <p>
                  Once signed, this transaction cannot be reversed. Verify all addresses and amounts before
                  proceeding.
                </p>
              </IonCardContent>
            </IonCard>
          </>
        )}
      </IonContent>

      {/* Action buttons */}
      <div className="action-buttons">
        <IonButton expand="block" color="danger" onClick={onReject} disabled={loading}>
          Reject
        </IonButton>
        <IonButton expand="block" color="success" onClick={onApprove} disabled={loading || !!error}>
          <IonIcon slot="start" icon={checkmarkCircle} />
          Approve & Sign
        </IonButton>
      </div>
    </IonModal>
  );
};

export default TransactionPreview;
