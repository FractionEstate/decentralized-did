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
jest.mock("../../../pages/Identifiers", () => ({
  Identifiers: () => <div data-testid="identifiers-page">Identifiers</div>,
}));
jest.mock("../../../pages/Scan", () => ({
  Scan: () => <div data-testid="scan-page">Scan</div>,
}));
jest.mock("../../../pages/Notifications", () => ({
  Notifications: () => (
    <div data-testid="notifications-page">Notifications</div>
  ),
}));
jest.mock("../../../pages/Menu", () => ({
  Menu: () => <div data-testid="menu-page">Menu</div>,
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
    history.push(TabsRoutePath.IDENTIFIERS);

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
      i18n.t("tabsmenu.label.identifiers"),
      i18n.t("tabsmenu.label.scan"),
      i18n.t("tabsmenu.label.notifications"),
      i18n.t("tabsmenu.label.menu"),
    ];

    // Verify labels are on screen
    translatedLabels.forEach((label) => {
      expect(getByText(label)).toBeVisible();
    });

    // Click each tab by its stable slug-based test id
    const slugs = [
      "identifiers",
      "scan",
      "notifications",
      "menu",
    ];
    slugs.forEach((slug) => {
      act(() => {
        fireEvent.click(getByTestId(`tab-button-${slug}`));
      });
    });
  });

  test("Render notification", async () => {
    const state = {
      ...initialState,
      stateCache: {
        ...initialState.stateCache,
        routes: [TabsRoutePath.NOTIFICATIONS],
      },
      notificationsCache: {
        notifications: notificationsFix,
      },
    };

    const storeMocked = {
      ...mockStore(state),
      dispatch: dispatchMock,
    };

    const history = createMemoryHistory();
    history.push(TabsRoutePath.NOTIFICATIONS);

    const { getAllByText } = render(
      <IonReactMemoryRouter history={history}>
        <Provider store={storeMocked}>
          <TabsMenu />
        </Provider>
      </IonReactMemoryRouter>
    );

    await waitForIonicReact();

    expect(getAllByText(notificationsFix.length).length).toBeGreaterThan(0);
  });

  test("Render 99+ notification", async () => {
    const state = {
      ...initialState,
      stateCache: {
        ...initialState.stateCache,
        routes: [TabsRoutePath.NOTIFICATIONS],
      },
      notificationsCache: {
        notifications: new Array(100).fill(notificationsFix[0]),
      },
    };

    const storeMocked = {
      ...mockStore(state),
      dispatch: dispatchMock,
    };

    const history = createMemoryHistory();
    history.push(TabsRoutePath.NOTIFICATIONS);

    const { getAllByText } = render(
      <IonReactMemoryRouter history={history}>
        <Provider store={storeMocked}>
          <TabsMenu />
        </Provider>
      </IonReactMemoryRouter>
    );

    await waitForIonicReact();

    expect(getAllByText("99+").length).toBeGreaterThan(0);
  });
});
