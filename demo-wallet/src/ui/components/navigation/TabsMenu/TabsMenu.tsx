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
  wallet,
  walletOutline,
  trophyOutline,
  trophy,
  documentTextOutline,
  documentText,
  globeOutline,
  globe,
} from "ionicons/icons";
import { ComponentType } from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import "./TabsMenu.scss";
import { TabsRoutePath } from "../../../../routes/paths";
import { Identifiers } from "../../../pages/Identifiers";
import { Scan } from "../../../pages/Scan";
import { Notifications } from "../../../pages/Notifications";
import { Menu } from "../../../pages/Menu";
import Tokens from "../../../pages/Tokens/Tokens";
import Staking from "../../../pages/Staking/Staking";
import Governance from "../../../pages/Governance/Governance";
import DAppBrowser from "../../../pages/DAppBrowser/DAppBrowser";
import { BackupWarningBanner } from "../../BackupWarningBanner";
import { useAppSelector } from "../../../../store/hooks";
import { getNotificationsCache } from "../../../../store/reducers/notificationsCache";
import { getShowWelcomePage } from "../../../../store/reducers/stateCache";

type TabConfigBase = {
  path: string;
  component: ComponentType;
  icon: [string, string];
  i18nKey: string;
};

type TabConfig = TabConfigBase & {
  label: string;
};

const FALLBACK_TAB_LABELS: Record<string, string> = {
  [TabsRoutePath.IDENTIFIERS]: "Wallet",
  [TabsRoutePath.TOKENS]: "Tokens",
  [TabsRoutePath.STAKING]: "Staking",
  [TabsRoutePath.GOVERNANCE]: "Governance",
  [TabsRoutePath.DAPP_BROWSER]: "Browser",
  [TabsRoutePath.SCAN]: "Scan",
  [TabsRoutePath.NOTIFICATIONS]: "Notifications",
  [TabsRoutePath.MENU]: "Settings",
};

const tabsRoutesBase: TabConfigBase[] = [
  {
    path: TabsRoutePath.IDENTIFIERS,
    component: Identifiers,
    icon: [fingerPrint, fingerPrintOutline],
    i18nKey: "tabsmenu.label.identifiers",
  },
  {
    path: TabsRoutePath.TOKENS,
    component: Tokens,
    icon: [wallet, walletOutline],
    i18nKey: "tabsmenu.label.tokens",
  },
  {
    path: TabsRoutePath.STAKING,
    component: Staking,
    icon: [trophy, trophyOutline],
    i18nKey: "tabsmenu.label.staking",
  },
  {
    path: TabsRoutePath.GOVERNANCE,
    component: Governance,
    icon: [documentText, documentTextOutline],
    i18nKey: "tabsmenu.label.governance",
  },
  {
    path: TabsRoutePath.DAPP_BROWSER,
    component: DAppBrowser,
    icon: [globe, globeOutline],
    i18nKey: "tabsmenu.label.browser",
  },
  // Credentials tab intentionally hidden (Hyperledger Aries VC flow not active)
  {
    path: TabsRoutePath.SCAN,
    component: Scan,
    icon: [scan, scanOutline],
    i18nKey: "tabsmenu.label.scan",
  },
  {
    path: TabsRoutePath.NOTIFICATIONS,
    component: Notifications,
    icon: [notifications, notificationsOutline],
    i18nKey: "tabsmenu.label.notifications",
  },
  {
    path: TabsRoutePath.MENU,
    component: Menu,
    icon: [apps, appsOutline],
    i18nKey: "tabsmenu.label.menu",
  },
];

// For export to tests
const tabsRoutes = tabsRoutesBase.map((route) => ({
  ...route,
  label: route.i18nKey,
}));

const TabsMenu = () => {
  const location = useLocation();
  const notifications = useAppSelector(getNotificationsCache);
  const notificationsCounter = notifications.filter((notification) => !notification.read).length;
  const showWelcomePage = useAppSelector(getShowWelcomePage);

  // Build tabsRoutes with resolved translations at render time
  const { t } = useTranslation("translation");
  const resolvedTabsRoutes: TabConfig[] = tabsRoutesBase.map((route) => ({
    ...route,
    label: t(route.i18nKey, { defaultValue: FALLBACK_TAB_LABELS[route.path] }) as string,
  }));

  return (
    <IonTabs>
      <IonRouterOutlet animated={false}>
        {/* Render default Identifiers tab when visiting /tabs without a subpath */}
        <Route path={TabsRoutePath.ROOT} component={Identifiers} exact />
        <Route path={TabsRoutePath.IDENTIFIERS} component={Identifiers} exact />
        <Route path={TabsRoutePath.DAPP_BROWSER} component={DAppBrowser} exact />
        <Route path={TabsRoutePath.SCAN} component={Scan} exact />
        <Route path={TabsRoutePath.NOTIFICATIONS} component={Notifications} exact />
        <Route path={TabsRoutePath.MENU} component={Menu} exact />
      </IonRouterOutlet>

      <BackupWarningBanner />

      <IonTabBar
        slot="bottom"
        data-testid="tabs-menu"
        className={showWelcomePage ? "ion-hide" : undefined}
      >
        {resolvedTabsRoutes.map((tabConfig) => {
          const tabId = (tabConfig.path.split("/").filter(Boolean).pop() || "tab").toLowerCase();
          const slug = tabId; // Use stable route-based slug for selectors
          const isActive =
            location.pathname === tabConfig.path ||
            location.pathname.startsWith(`${tabConfig.path}/`);
          return (
            <IonTabButton
              key={tabConfig.path}
              tab={tabId}
              href={tabConfig.path}
              data-testid={`tab-button-${slug}`}
              className={`tab-button-${slug}`}
              aria-label={tabConfig.label}
              aria-current={isActive ? "page" : undefined}
            >
              <div className="border-top" />
              <div className="icon-container">
                {!!notificationsCounter && tabConfig.path === TabsRoutePath.NOTIFICATIONS && (
                  <span
                    className="notifications-counter"
                    aria-live="polite"
                    aria-atomic="true"
                    title={`Unread notifications: ${notificationsCounter > 99 ? "99+" : notificationsCounter}`}
                    aria-label={`Unread notifications: ${notificationsCounter > 99 ? "99+" : notificationsCounter}`}
                  >
                    {notificationsCounter > 99 ? "99+" : notificationsCounter}
                  </span>
                )}
                <IonIcon icon={isActive ? tabConfig.icon[0] : tabConfig.icon[1]} aria-hidden="true" />
              </div>
              <IonLabel>{tabConfig.label}</IonLabel>
            </IonTabButton>
          );
        })}
      </IonTabBar>
    </IonTabs>
  );
};

export { TabsMenu, TabsRoutePath, tabsRoutes };
