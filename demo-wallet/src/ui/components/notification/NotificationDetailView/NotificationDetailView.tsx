import { ElementType, useEffect, useMemo } from "react";
import {
    KeriaNotification,
    NotificationRoute,
} from "../../../../core/agent/services/keriaNotificationService.types";
import { RemoteSignRequest } from "../../../pages/NotificationDetails/components/RemoteSignRequest";
import { RemoteMessage } from "../../../pages/NotificationDetails/components/RemoteMessage";
import { CredentialRequest } from "../../../pages/NotificationDetails/components/CredentialRequest";
import { MultiSigRequest } from "../../../pages/NotificationDetails/components/MultiSigRequest";
import { ReceiveCredential } from "../../../pages/NotificationDetails/components/ReceiveCredential";
import { RemoteConnectInstructions } from "../../../pages/NotificationDetails/components/RemoteConnectInstructions";

export interface NotificationDetailViewProps {
    notification: KeriaNotification;
    onBack: () => void;
}

export const NotificationDetailView: React.FC<NotificationDetailViewProps> = ({
    notification,
    onBack,
}) => {
    const pageId = "notification-details";

    const unsupportedRoutes = useMemo(
        () => [
            NotificationRoute.MultiSigRpy,
            NotificationRoute.ExnIpexOffer,
            NotificationRoute.ExnIpexAgree,
            NotificationRoute.LocalAcdcRevoked,
        ],
        []
    );

    const mapping: Record<NotificationRoute, ElementType | null> = useMemo(
        () => ({
            [NotificationRoute.MultiSigIcp]: MultiSigRequest,
            [NotificationRoute.ExnIpexGrant]: ReceiveCredential,
            [NotificationRoute.ExnIpexApply]: CredentialRequest,
            [NotificationRoute.MultiSigExn]: ReceiveCredential,
            [NotificationRoute.RemoteSignReq]: RemoteSignRequest,
            [NotificationRoute.HumanReadableMessage]: RemoteMessage,
            [NotificationRoute.LocalSingletonConnectInstructions]: RemoteConnectInstructions,
            [NotificationRoute.MultiSigRpy]: null,
            [NotificationRoute.ExnIpexOffer]: null,
            [NotificationRoute.ExnIpexAgree]: null,
            [NotificationRoute.LocalAcdcRevoked]: null,
        }),
        []
    );

    useEffect(() => {
        if (!notification || unsupportedRoutes.includes(notification.a?.r as NotificationRoute)) {
            onBack();
        }
    }, [notification, onBack, unsupportedRoutes]);

    if (!notification || unsupportedRoutes.includes(notification.a?.r as NotificationRoute)) {
        return null;
    }

    const Component = mapping[notification.a?.r as NotificationRoute];
    if (!Component) return null;

    return (
        <Component
            pageId={pageId}
            activeStatus={!!notification}
            notificationDetails={notification}
            handleBack={onBack}
            {...(notification.a?.r === NotificationRoute.MultiSigExn ? { multisigExn: true } : {})}
        />
    );
};
