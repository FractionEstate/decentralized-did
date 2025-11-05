import { IonSpinner } from "@ionic/react";
import "./LoadingPlaceholder.scss";

interface LoadingPlaceholderProps {
    message?: string;
    size?: "small" | "default" | "large";
    className?: string;
}

/**
 * LoadingPlaceholder Component
 * 
 * Displays a loading spinner with an optional message.
 * Used for async operations and data fetching states.
 * 
 * @example
 * ```tsx
 * <LoadingPlaceholder message="Loading wallet balance..." />
 * ```
 */
const LoadingPlaceholder: React.FC<LoadingPlaceholderProps> = ({
    message = "Loading...",
    size = "default",
    className = "",
}) => {
    return (
        <div className={`loading-placeholder loading-placeholder--${size} ${className}`}>
            <IonSpinner name="crescent" />
            {message && <p className="loading-placeholder-message">{message}</p>}
        </div>
    );
};

export { LoadingPlaceholder };
