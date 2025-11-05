import { IonIcon, IonButton } from "@ionic/react";
import "./EmptyState.scss";

interface EmptyStateProps {
    icon: string;
    title: string;
    description?: string;
    actionLabel?: string;
    onAction?: () => void;
    className?: string;
}

/**
 * EmptyState Component
 * 
 * Reusable component for displaying empty states across the application.
 * Shows an icon, title, optional description, and optional action button.
 * 
 * @example
 * ```tsx
 * <EmptyState
 *   icon={walletOutline}
 *   title="No Transactions"
 *   description="Your transaction history will appear here"
 *   actionLabel="Refresh"
 *   onAction={handleRefresh}
 * />
 * ```
 */
const EmptyState: React.FC<EmptyStateProps> = ({
    icon,
    title,
    description,
    actionLabel,
    onAction,
    className = "",
}) => {
    return (
        <div className={`empty-state ${className}`}>
            <IonIcon icon={icon} className="empty-state-icon" />
            <h3 className="empty-state-title">{title}</h3>
            {description && <p className="empty-state-description">{description}</p>}
            {actionLabel && onAction && (
                <IonButton onClick={onAction} className="empty-state-action">
                    {actionLabel}
                </IonButton>
            )}
        </div>
    );
};

export { EmptyState };
