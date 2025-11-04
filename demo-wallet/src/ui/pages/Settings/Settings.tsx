import {
  IonButton,
  IonCard,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonToggle,
  useIonViewWillEnter,
} from "@ionic/react";
import {
  settingsOutline,
  personCircleOutline,
  peopleOutline,
  linkOutline,
  trophy,
  documentText,
  globe,
  fingerPrint,
  shield,
  chevronForward,
  informationCircleOutline,
  keyOutline,
  libraryOutline,
  checkboxOutline,
  helpCircleOutline,
  layersOutline,
} from "ionicons/icons";
import { useEffect, useMemo, useState } from "react";
import { useHistory } from "react-router-dom";
import { ConfigurationService } from "../../../core/configuration";
import { OptionalFeature } from "../../../core/configuration/configurationService.types";
import { i18n } from "../../../i18n";
import { TabsRoutePath } from "../../../routes/paths";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import {
  setCurrentRoute,
  showConnections,
} from "../../../store/reducers/stateCache";
import {
  getShowConnectWallet,
  showConnectWallet,
} from "../../../store/reducers/walletConnectionsCache";
import { getBiometricsCache } from "../../../store/reducers/biometricsCache";
import { TabLayout } from "../../components/layout/TabLayout/TabLayout";
import { SubMenu } from "../Menu/components/SubMenu/SubMenu";
import {
  emptySubMenu,
  SubMenuItems,
} from "../Menu/components/SubMenuItems";
import { SubMenuKey } from "../Menu/Menu.types";
import "./Settings.scss";

interface SettingsSectionProps {
  title: string;
  children: React.ReactNode;
}

const SettingsSection: React.FC<SettingsSectionProps> = ({ title, children }) => (
  <div className="settings-section">
    <div className="settings-section-title">{title}</div>
    <IonCard>
      <IonList lines="none">
        {children}
      </IonList>
    </IonCard>
  </div>
);

interface SettingsItemProps {
  icon: string;
  label: string;
  value?: string;
  toggle?: boolean;
  toggleValue?: boolean;
  onToggle?: (value: boolean) => void;
  onClick?: () => void;
  disabled?: boolean;
  href?: string;
}

const SettingsItem: React.FC<SettingsItemProps> = ({
  icon,
  label,
  value,
  toggle,
  toggleValue,
  onToggle,
  onClick,
  disabled,
  href
}) => {
  const handleClick = () => {
    if (href) {
      window.open(href, '_blank');
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <IonItem
      button={!!onClick || !!href}
      onClick={handleClick}
      disabled={disabled}
      className="settings-item"
    >
      <IonIcon icon={icon} slot="start" className="settings-item-icon" />
      <IonLabel>
        <div className="settings-item-label">{label}</div>
        {value && <div className="settings-item-value">{value}</div>}
      </IonLabel>
      {toggle && onToggle && (
        <IonToggle
          slot="end"
          checked={toggleValue}
          onIonChange={(e: any) => onToggle(e.detail.checked)}
        />
      )}
      {!toggle && (onClick || href) && (
        <IonIcon icon={chevronForward} slot="end" className="settings-chevron" />
      )}
    </IonItem>
  );
};

const Settings = () => {
  const pageId = "settings-page";
  const dispatch = useAppDispatch();
  const history = useHistory();
  const showWalletConnect = useAppSelector(getShowConnectWallet);
  const biometricsCache = useAppSelector(getBiometricsCache);
  const [showSubMenu, setShowSubMenu] = useState(false);
  const [selectedOption, setSelectedOption] = useState<SubMenuKey | undefined>();

  useIonViewWillEnter(() => {
    // Route tracking is deferred via middleware to prevent render-cycle warnings
    // dispatch(setCurrentRoute({ path: TabsRoutePath.MENU }));
  });

  const backHardwareConfig = useMemo(
    () => ({
      prevent: !showSubMenu,
    }),
    [showSubMenu]
  );

  // Advanced Features Navigation
  const handleStakingClick = () => {
    history.push(TabsRoutePath.STAKING);
  };

  const handleGovernanceClick = () => {
    history.push(TabsRoutePath.GOVERNANCE);
  };

  const handleBrowserClick = () => {
    history.push(TabsRoutePath.DAPP_BROWSER);
  };

  const handleBiometricIdentitiesClick = () => {
    history.push(TabsRoutePath.IDENTIFIERS);
  };

  // Settings Navigation
  const handleOpenUrl = (key: SubMenuKey) => {
    switch (key) {
      case SubMenuKey.Connections: {
        dispatch(showConnections(true));
        break;
      }
      default:
        return;
    }
  };

  useEffect(() => {
    if (showWalletConnect) {
      showSelectedOption(SubMenuKey.ConnectWallet);
      dispatch(showConnectWallet(false));
    }
  }, [dispatch, showWalletConnect]);

  const showSelectedOption = (key: SubMenuKey) => {
    if ([SubMenuKey.Connections].includes(key)) {
      handleOpenUrl(key);
    }
    if (!subMenuItems.has(key)) return;
    setShowSubMenu(true);
    setSelectedOption(key);
  };

  const closeSetting = () => setShowSubMenu(false);
  const subMenuItems = SubMenuItems(showSelectedOption, closeSetting);

  const selectSubmenu =
    selectedOption !== undefined
      ? subMenuItems.get(selectedOption) || emptySubMenu
      : emptySubMenu;

  // Biometrics toggle handler
  const handleBiometricsToggle = (enabled: boolean) => {
    // TODO: Implement biometrics toggle functionality
    console.log("Biometrics toggle:", enabled);
  };

  return (
    <>
      <TabLayout
        pageId={pageId}
        hardwareBackButtonConfig={backHardwareConfig}
        header={false}
        customClass="settings-page"
      >
        <div className="settings-content">
          {/* Account Section */}
          <SettingsSection title="Account">
            <SettingsItem
              icon={personCircleOutline}
              label={i18n.t("tabs.menu.tab.items.profile.title")}
              onClick={() => showSelectedOption(SubMenuKey.Profile)}
            />
            <SettingsItem
              icon={peopleOutline}
              label={i18n.t("tabs.menu.tab.items.connections.title")}
              onClick={() => showSelectedOption(SubMenuKey.Connections)}
            />
            {!ConfigurationService.env.features.cut.includes(OptionalFeature.ConnectWallet) && (
              <SettingsItem
                icon={linkOutline}
                label={String(i18n.t("tabs.menu.tab.items.connectwallet.title"))}
                value={String(i18n.t("tabs.menu.tab.items.connectwallet.sublabel"))}
                onClick={() => showSelectedOption(SubMenuKey.ConnectWallet)}
              />
            )}
          </SettingsSection>

          {/* Security Section */}
          <SettingsSection title="Security & Privacy">
            <SettingsItem
              icon={shield}
              label="Change Passcode"
              onClick={() => showSelectedOption(SubMenuKey.Settings)}
            />
            <SettingsItem
              icon={keyOutline}
              label="Recovery Seed Phrase"
              onClick={() => showSelectedOption(SubMenuKey.Settings)}
            />
            <SettingsItem
              icon={fingerPrint}
              label="Biometric Authentication"
              toggle={true}
              toggleValue={biometricsCache.enabled}
              onToggle={handleBiometricsToggle}
            />
          </SettingsSection>

          {/* Advanced Features Section */}
          <SettingsSection title="Advanced Features">
            <SettingsItem
              icon={fingerPrint}
              label="Biometric Identities"
              value="Manage your DID credentials"
              onClick={handleBiometricIdentitiesClick}
            />
            <SettingsItem
              icon={trophy}
              label="Staking"
              value="Earn rewards with ADA"
              onClick={handleStakingClick}
            />
            <SettingsItem
              icon={documentText}
              label="Governance"
              value="Participate in Cardano voting"
              onClick={handleGovernanceClick}
            />
            <SettingsItem
              icon={globe}
              label="DApp Browser"
              value="Explore decentralized applications"
              onClick={handleBrowserClick}
            />
          </SettingsSection>

          {/* Support Section */}
          <SettingsSection title="Support & About">
            <SettingsItem
              icon={libraryOutline}
              label="Documentation"
              href="https://docs.cardano.org/"
            />
            <SettingsItem
              icon={checkboxOutline}
              label="Terms of Service"
              onClick={() => showSelectedOption(SubMenuKey.Settings)}
            />
            <SettingsItem
              icon={helpCircleOutline}
              label="Contact Support"
              href="mailto:support@biovera.com"
            />
            <SettingsItem
              icon={layersOutline}
              label="Version"
              value="1.0.0" // TODO: Get from package.json
            />
          </SettingsSection>
        </div>
      </TabLayout>

      <SubMenu
        showSubMenu={showSubMenu}
        setShowSubMenu={setShowSubMenu}
        nestedMenu={selectSubmenu.nestedMenu}
        closeButtonLabel={selectSubmenu.closeButtonLabel}
        closeButtonAction={selectSubmenu.closeButtonAction}
        title={selectSubmenu.title ? String(i18n.t(selectSubmenu.title)) : undefined}
        additionalButtons={selectSubmenu.additionalButtons}
        actionButton={selectSubmenu.actionButton}
        actionButtonAction={selectSubmenu.actionButtonAction}
        actionButtonLabel={selectSubmenu.actionButtonLabel}
        pageId={selectSubmenu.pageId}
        switchView={showSelectedOption}
        renderAsModal={selectSubmenu.renderAsModal}
      >
        <selectSubmenu.Component />
      </SubMenu>
    </>
  );
};

export default Settings;