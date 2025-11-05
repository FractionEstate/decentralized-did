import { fireEvent, render } from "@testing-library/react";
import { createMemoryHistory } from "history";
import { Provider } from "react-redux";
import configureStore from "redux-mock-store";
import { IonReactMemoryRouter } from "@ionic/react-router";
import { waitForIonicReact } from "@ionic/react-test-utils";
import { act } from "react";
import { TabsMenu, TabsRoutePath, tabsRoutes } from "./TabsMenu";
import { notificationsFix } from "../../../__fixtures__/notificationsFix";
import { i18n } from "../../../../i18n";

// Mock heavy tab pages to avoid deep Redux selector dependencies in this unit test
jest.mock("../../../pages/Wallet/Wallet", () => ({
  __esModule: true,
  default: () => <div data-testid="tokens-page">Tokens</div>,
}));
jest.mock("../../../pages/Identifiers", () => ({
  Identifiers: () => <div data-testid="identifiers-page">Identifiers</div>,
}));
jest.mock("../../../pages/DAppBrowser/DAppBrowser", () => ({
  __esModule: true,
  default: () => <div data-testid="dapp-browser-page">DApp Browser</div>,
}));
jest.mock("../../../pages/Governance/Governance", () => ({
  __esModule: true,
  default: () => <div data-testid="governance-page">Governance</div>,
}));
jest.mock("../../../pages/Staking/Staking", () => ({
  __esModule: true,
  default: () => <div data-testid="staking-page">Staking</div>,
}));
jest.mock("../../../pages/Settings", () => ({
  Settings: () => <div data-testid="settings-page">Settings</div>,
}));
// Legacy page mocks
jest.mock("../../../pages/Home", () => ({
  Home: () => <div data-testid="home-page">Home</div>,
}));
jest.mock("../../../pages/NFTs", () => ({
  NFTs: () => <div data-testid="nfts-page">NFTs</div>,
}));
jest.mock("../../../pages/Scan", () => ({
  Scan: () => <div data-testid="scan-page">Scan</div>,
}));
jest.mock("../../../pages/Notifications", () => ({
  Notifications: () => (
    <div data-testid="notifications-page">Notifications</div>
  ),
}));

describe("Tab menu", () => {
  const mockStore = configureStore();
  const dispatchMock = jest.fn();
  const initialState = {
    stateCache: {
      routes: ["/"],
      authentication: {
        loggedIn: true,
        time: 0,
        passcodeIsSet: true,
        seedPhraseIsSet: true,
        passwordIsSet: false,
        passwordIsSkipped: true,
        ssiAgentIsSet: true,
        ssiAgentUrl: "http://keria.com",
        recoveryWalletProgress: false,
        loginAttempt: {
          attempts: 0,
          lockedUntil: 0,
        },
      },
    },
    seedPhraseCache: {
      seedPhrase: "",
      bran: "",
    },
    notificationsCache: {
      notifications: [],
    },
  };

  const storeMocked = {
    ...mockStore(initialState),
    dispatch: dispatchMock,
  };

  test("Render", async () => {
    const history = createMemoryHistory();
    history.push(TabsRoutePath.TOKENS);

    const { getByTestId, getByText } = render(
      <IonReactMemoryRouter history={history}>
        <Provider store={storeMocked}>
          <TabsMenu />
        </Provider>
      </IonReactMemoryRouter>
    );

    await waitForIonicReact();

    // Use translated labels for testing (resolved at render time in component)
    const translatedLabels = [
      i18n.t("tabsmenu.label.wallet"),
      i18n.t("tabsmenu.label.identity"),
      i18n.t("tabsmenu.label.browser"),
      i18n.t("tabsmenu.label.governance"),
      i18n.t("tabsmenu.label.staking"),
      i18n.t("tabsmenu.label.settings"),
    ];

    // Verify labels are on screen
    translatedLabels.forEach((label) => {
      expect(getByText(label)).toBeVisible();
    });

    // Click each tab by its stable slug-based test id
    const slugs = [
      "tokens",
      "identifiers",
      "dapp-browser",
      "governance",
      "staking",
      "menu",
    ];
    slugs.forEach((slug) => {
      act(() => {
        fireEvent.click(getByTestId(`tab-button-${slug}`));
      });
    });
  });

  test("Render new tab structure", async () => {
    const history = createMemoryHistory();
    history.push(TabsRoutePath.TOKENS);

    const { getByTestId } = render(
      <IonReactMemoryRouter history={history}>
        <Provider store={storeMocked}>
          <TabsMenu />
        </Provider>
      </IonReactMemoryRouter>
    );

    await waitForIonicReact();

    // Verify all main navigation tabs are present
    expect(getByTestId("tab-button-tokens")).toBeVisible();
    expect(getByTestId("tab-button-identifiers")).toBeVisible();
    expect(getByTestId("tab-button-dapp-browser")).toBeVisible();
    expect(getByTestId("tab-button-governance")).toBeVisible();
    expect(getByTestId("tab-button-staking")).toBeVisible();
    expect(getByTestId("tab-button-menu")).toBeVisible();
  });
});
