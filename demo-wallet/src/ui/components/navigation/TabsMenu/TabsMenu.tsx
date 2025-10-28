import {
  IonIcon,
  IonLabel,
  IonRouterOutlet,
  IonTabBar,
  IonTabButton,
  IonTabs,
} from "@ionic/react";
import { Route } from "react-router";
import {
  notifications,
  notificationsOutline,
  fingerPrint,
  fingerPrintOutline,
  scan,
  scanOutline,
  apps,
  appsOutline,
} from "ionicons/icons";
import { ComponentType } from "react";
import { useLocation } from "react-router-dom";
import { i18n } from "../../../../i18n";
import "./TabsMenu.scss";
import { TabsRoutePath } from "../../../../routes/paths";
import { Identifiers } from "../../../pages/Identifiers";
import { Scan } from "../../../pages/Scan";
import { Notifications } from "../../../pages/Notifications";
import { Menu } from "../../../pages/Menu";
import { BackupWarningBanner } from "../../BackupWarningBanner";
import { useAppSelector } from "../../../../store/hooks";
import { getNotificationsCache } from "../../../../store/reducers/notificationsCache";
import { getShowWelcomePage } from "../../../../store/reducers/stateCache";

type TabConfig = {
  label: string;
  path: string;
  component: ComponentType;
  icon: [string, string];
};

const tabsRoutes: TabConfig[] = [
  {
    label: i18n.t("tabsmenu.label.identifiers"),
    path: TabsRoutePath.IDENTIFIERS,
    component: Identifiers,
    icon: [fingerPrint, fingerPrintOutline],
  },
  // Credentials tab intentionally hidden (Hyperledger Aries VC flow not active)
  {
    label: i18n.t("tabsmenu.label.scan"),
    path: TabsRoutePath.SCAN,
    component: Scan,
    icon: [scan, scanOutline],
  },
  {
    label: i18n.t("tabsmenu.label.notifications"),
    path: TabsRoutePath.NOTIFICATIONS,
    component: Notifications,
    icon: [notifications, notificationsOutline],
  },
  {
    label: i18n.t("tabsmenu.label.menu"),
    path: TabsRoutePath.MENU,
    component: Menu,
    icon: [apps, appsOutline],
  },
];

const TabsMenu = ({ tab, path }: { tab: ComponentType; path: string }) => {
  const location = useLocation();
  const notifications = useAppSelector(getNotificationsCache);
  const notificationsCounter = notifications.filter((notification) => !notification.read).length;
  const showWelcomePage = useAppSelector(getShowWelcomePage);

  return (
    <IonTabs>
      <IonRouterOutlet animated={false}>
        <Route path={path} component={tab} exact />
      </IonRouterOutlet>

      <BackupWarningBanner />

      <IonTabBar
        slot="bottom"
        data-testid="tabs-menu"
        className={showWelcomePage ? "ion-hide" : undefined}
      >
        {tabsRoutes.map((tabConfig) => (
          <IonTabButton
            key={tabConfig.path}
            tab={tabConfig.label}
            href={tabConfig.path}
            data-testid={`tab-button-${tabConfig.label.toLowerCase().replace(/\s/g, "-")}`}
            className={`tab-button-${tabConfig.label.toLowerCase().replace(/\s/g, "-")}`}
          >
            <div className="border-top" />
            <div className="icon-container">
              {!!notificationsCounter && tabConfig.path === TabsRoutePath.NOTIFICATIONS && (
                <span className="notifications-counter">
                  {notificationsCounter > 99 ? "99+" : notificationsCounter}
                </span>
              )}
              <IonIcon
                icon={tabConfig.path === location.pathname ? tabConfig.icon[0] : tabConfig.icon[1]}
              />
            </div>
            <IonLabel>{tabConfig.label}</IonLabel>
          </IonTabButton>
        ))}
      </IonTabBar>
    </IonTabs>
  );
};

export { TabsMenu, TabsRoutePath, tabsRoutes };
