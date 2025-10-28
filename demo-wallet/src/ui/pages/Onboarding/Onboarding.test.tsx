import { fireEvent, render, screen } from "@testing-library/react";
import { act } from "react";
import { Provider } from "react-redux";
import { createMemoryHistory } from "history";
import { Router } from "react-router-dom";
import { TabsRoutePath, RoutePath } from "../../../routes/paths";
import { store } from "../../../store";
import { Onboarding } from "./Onboarding";

const presentToastMock = jest.fn().mockResolvedValue(undefined);

jest.mock("@ionic/react", () => {
  const actual = jest.requireActual("@ionic/react");
  return {
    ...actual,
    useIonToast: () => [presentToastMock],
  };
});

jest.mock("./BiometricScanScreen", () => {
  return {
    BiometricScanScreen: ({ fingersToScan, onComplete }: any) => (
      <div data-testid="biometric-scan-mock">
        <span data-testid="finger-count">{fingersToScan.length}</span>
        <button
          type="button"
          onClick={() =>
            onComplete(
              fingersToScan.map((finger: string, index: number) => `biometric-${finger}-${index}`)
            )
          }
        >
          Complete Scan
        </button>
      </div>
    ),
  };
});

jest.mock("./SeedPhraseScreen", () => {
  return {
    SeedPhraseScreen: ({ words, onConfirm }: any) => (
      <div data-testid="seed-screen-mock">
        <span data-testid="seed-count">{words.length}</span>
        <button type="button" onClick={onConfirm}>
          Confirm Seed
        </button>
      </div>
    ),
  };
});

jest.mock("./VerificationScreen", () => {
  return {
    VerificationScreen: ({ seedPhrase, wordsToVerify, onSuccess }: any) => (
      <div data-testid="verification-screen-mock">
        <span data-testid="verification-seed-count">{seedPhrase.length}</span>
        <span data-testid="words-to-verify">{wordsToVerify.join(",")}</span>
        <button type="button" onClick={onSuccess}>
          Submit Verification
        </button>
      </div>
    ),
  };
});

jest.mock("./SuccessScreen", () => {
  return {
    SuccessScreen: ({ walletAddress, onContinue }: any) => (
      <div data-testid="success-screen-mock">
        <span data-testid="wallet-address">{walletAddress}</span>
        <button type="button" onClick={onContinue}>
          Continue to Credentials
        </button>
      </div>
    ),
  };
});

describe("Onboarding", () => {
  beforeEach(() => {
    presentToastMock.mockClear();
  });

  test("shows biometric scan with ten fingers after starting", () => {
    const history = createMemoryHistory({ initialEntries: [RoutePath.ONBOARDING] });

    render(
      <Provider store={store}>
        <Router history={history}>
          <Onboarding />
        </Router>
      </Provider>
    );

    fireEvent.click(screen.getByText("Get Started"));

    expect(screen.getByTestId("finger-count")).toHaveTextContent("10");
    expect(screen.getByText("Step 1 of 3")).toBeInTheDocument();
  });

  test("completes the onboarding flow and navigates to credentials", async () => {
    jest.useFakeTimers();
    const history = createMemoryHistory({ initialEntries: [RoutePath.ONBOARDING] });

    try {
      render(
        <Provider store={store}>
          <Router history={history}>
            <Onboarding />
          </Router>
        </Provider>
      );

      fireEvent.click(screen.getByText("Get Started"));

      fireEvent.click(screen.getByText("Complete Scan"));

      expect(await screen.findByText("Step 2 of 3")).toBeInTheDocument();
      expect(await screen.findByTestId("seed-count")).toHaveTextContent("12");

      fireEvent.click(screen.getByText("Confirm Seed"));

      expect(await screen.findByText("Step 3 of 3")).toBeInTheDocument();
      expect(await screen.findByTestId("verification-seed-count")).toHaveTextContent("12");
      expect(screen.getByTestId("words-to-verify")).toHaveTextContent("2,6,11");

      await act(async () => {
        fireEvent.click(screen.getByText("Submit Verification"));
      });

      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      expect(await screen.findByTestId("wallet-address")).toHaveTextContent(
        "addr1q9xyz...abc123"
      );
      expect(presentToastMock).toHaveBeenCalledTimes(2);

      expect(screen.queryByText("Step 3 of 3")).not.toBeInTheDocument();
      fireEvent.click(screen.getByText("Continue to Credentials"));

      expect(history.location.pathname).toBe(TabsRoutePath.CREDENTIALS);
      expect(jest.getTimerCount()).toBe(0);
    } finally {
      jest.runOnlyPendingTimers();
      jest.useRealTimers();
    }
  });
});
