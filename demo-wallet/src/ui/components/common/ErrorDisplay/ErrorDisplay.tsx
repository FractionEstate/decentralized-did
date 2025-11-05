import { IonIcon, IonButton } from "@ionic/react";
import { alertCircleOutline, refreshOutline } from "ionicons/icons";
import "./ErrorDisplay.scss";

interface ErrorDisplayProps {
    error: string | Error;
    onRetry?: () => void;
    className?: string;
    title?: string;
}

/**
 * ErrorDisplay Component
 * 
 * Displays error messages with an optional retry button.
 * Handles both string and Error object inputs.
 * 
 * @example
 * ```tsx
 * <ErrorDisplay
 *   error="Failed to load data"
 *   onRetry={handleRetry}
 *   title="Connection Error"
 * />
 * ```
 */
const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
    error,
    onRetry,
    className = "",
    title = "Something went wrong",
}) => {
    const errorMessage = typeof error === "string" ? error : error.message;

    return (
        <div className={`error-display ${className}`}>
            <IonIcon icon={alertCircleOutline} className="error-display-icon" />
            <h3 className="error-display-title">{title}</h3>
            <p className="error-display-message">{errorMessage}</p>
            {onRetry && (
                <IonButton onClick={onRetry} fill="outline" className="error-display-retry">
                    <IonIcon slot="start" icon={refreshOutline} />
                    Try Again
                </IonButton>
            )}
        </div>
    );
};

export { ErrorDisplay };
