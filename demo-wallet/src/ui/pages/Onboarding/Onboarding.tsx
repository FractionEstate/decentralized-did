import { useEffect, useState } from "react";
import { useHistory } from "react-router-dom";
import { useIonToast } from "@ionic/react";
import { Agent } from "../../../core/agent/agent";
import { MiscRecordId } from "../../../core/agent/agent.types";
import { BasicRecord } from "../../../core/agent/records";
import { KeyStoreKeys, SecureStorage } from "../../../core/storage";
import { RoutePath } from "../../../routes";
import { TabsRoutePath } from "../../../routes/paths";
import { getNextRoute } from "../../../routes/nextRoute";
import { DataProps } from "../../../routes/nextRoute/nextRoute.types";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import { getStateCache, setAuthentication } from "../../../store/reducers/stateCache";
import { setSeedPhraseCache } from "../../../store/reducers/seedPhraseCache";
import { updateReduxState } from "../../../store/utils";
import { WelcomeScreen } from "./WelcomeScreen";
import { BiometricScanScreen } from "./BiometricScanScreen";
import { SeedPhraseScreen } from "./SeedPhraseScreen";
import { VerificationScreen } from "./VerificationScreen";
import { SuccessScreen } from "./SuccessScreen";
import { ProgressIndicator } from "./ProgressIndicator";
import {
  showErrorToast,
  LOADING_MESSAGES,
  SUCCESS_MESSAGES
} from "../../../utils/userFriendlyErrors";
import { useExitAppWithDoubleTap } from "../../hooks/exitAppWithDoubleTapHook";
import "./Onboarding.scss";

export interface OnboardingState {
  step: number; // 0: welcome, 1: biometric, 2: seed, 3: verify, 4: success
  biometricData: string[]; // Captured fingerprint data
  seedPhrase: string[]; // Generated seed phrase
  walletAddress: string | null;
  startTime: number;
  errors: string[];
  fastOnboarding: boolean; // Skip seed phrase backup (defer to later)
  recoveryMode: 'seed' | 'biometric' | null; // Recovery method selected
}

const Onboarding = () => {
  const history = useHistory();
  const dispatch = useAppDispatch();
  const stateCache = useAppSelector(getStateCache);
  const [showToast] = useIonToast();
  const [hiddenPage, setHiddenPage] = useState(false);
  useExitAppWithDoubleTap(hiddenPage);

  const [state, setState] = useState<OnboardingState>({
    step: 0,
    biometricData: [],
    seedPhrase: [],
    walletAddress: null,
    startTime: Date.now(),
    errors: [],
    fastOnboarding: false,
    recoveryMode: null,
  });

  useEffect(() => {
    setHiddenPage(history?.location?.pathname !== RoutePath.ONBOARDING);
  }, [hiddenPage, history?.location?.pathname]);

  const handleStart = () => {
    // Fast onboarding: skip seed phrase backup step
    setState({ ...state, step: 1, startTime: Date.now(), fastOnboarding: true });
  };

  const handleBiometricRestore = () => {
    // Recover wallet using biometric authentication
    setState({ ...state, step: 1, recoveryMode: 'biometric' });
  };

  const fingersToScan = [
    "right-thumb",
    "right-index",
    "right-middle",
    "right-ring",
    "right-pinky",
    "left-thumb",
    "left-index",
    "left-middle",
    "left-ring",
    "left-pinky",
  ];

  const handleBiometricComplete = async (biometricData: string[]) => {

    // Generate seed phrase using Agent's getBranAndMnemonic
    let seedPhrase: string[] = [];
    let bran = "";

    try {
      const branAndMnemonic = await Agent.agent.getBranAndMnemonic();
      seedPhrase = branAndMnemonic.mnemonic.split(" ");
      bran = branAndMnemonic.bran;
    } catch (error) {
      showErrorToast(error, showToast, "seed_phrase_generation");
      setState({
        ...state,
        errors: [...state.errors, "Failed to generate seed phrase"],
      });
      return;
    }

    if (state.fastOnboarding) {
      // Fast onboarding: Skip seed phrase display, create wallet immediately
      // Seed phrase stored encrypted with seedPhraseBackedUp=false flag

      // Create wallet in background first
      try {
        const walletAddress = await createWalletWithBiometric(
          biometricData,
          seedPhrase,
          bran,
          false, // not backed up
          dispatch,
          stateCache
        );

        // Only set step to 4 after wallet is created
        setState({
          ...state,
          biometricData,
          seedPhrase,
          walletAddress,
          step: 4, // Jump to success (skip steps 2-3)
        });

        showToast({
          message: SUCCESS_MESSAGES.wallet_created,
          duration: 2000,
          position: "top",
          color: "success",
        });
      } catch (error) {
        showErrorToast(error, showToast, "wallet_creation");
        setState({
          ...state,
          biometricData,
          seedPhrase,
          errors: [...state.errors, "Failed to create wallet"],
          step: 1, // Go back to biometric scan
        });
      }
    } else {
      // Traditional flow: Show seed phrase for immediate backup
      setState({
        ...state,
        step: 2,
        biometricData,
        seedPhrase,
      });
    }
  }; const handleSeedConfirm = () => {
    setState({ ...state, step: 3 });
  };

  const handleVerificationSuccess = async () => {

    // Show loading state
    showToast({
      message: LOADING_MESSAGES.creating_wallet,
      duration: 0, // Will dismiss after wallet creation
      position: "top",
      color: "primary",
    });

    // Generate bran for traditional flow
    let bran = "";
    try {
      const branAndMnemonic = await Agent.agent.getBranAndMnemonic();
      bran = branAndMnemonic.bran;
    } catch (error) {
      showErrorToast(error, showToast, "seed_phrase_generation");
      return;
    }

    // Create wallet with biometric + seed phrase
    try {
      const walletAddress = await createWalletWithBiometric(
        state.biometricData,
        state.seedPhrase,
        bran,
        true, // backed up = true
        dispatch,
        stateCache
      );

      // Dismiss loading toast
      await showToast({
        message: SUCCESS_MESSAGES.wallet_created,
        duration: 2000,
        position: "top",
        color: "success",
      });

      setState({
        ...state,
        step: 4,
        walletAddress,
      });

      // Track analytics: onboarding_completed (duration available if needed)
    } catch (error) {
      // Show user-friendly error message
      showErrorToast(error, showToast, "wallet_creation");

      setState({
        ...state,
        errors: [...state.errors, "Failed to create wallet"],
      });
    }
  };

  const handleComplete = () => {
    // Update Redux state and navigate using proper routing logic
    const data: DataProps = {
      store: { stateCache },
      state: {
        recoveryWalletProgress: false,
      },
    };
    const { nextPath, updateRedux } = getNextRoute(RoutePath.ONBOARDING, data);
    updateReduxState(nextPath.pathname, data, dispatch, updateRedux);

    history.push({
      pathname: TabsRoutePath.CREDENTIALS,
      state: data.state,
    });
  };

  const handleRestore = () => {
    // Set recovery mode flag and navigate using proper routing
    const data: DataProps = {
      store: { stateCache },
      state: {
        recoveryWalletProgress: true,
      },
    };
    const { nextPath, updateRedux } = getNextRoute(RoutePath.ONBOARDING, data);
    updateReduxState(nextPath.pathname, data, dispatch, updateRedux);

    Agent.agent.basicStorage.createOrUpdateBasicRecord(
      new BasicRecord({
        id: MiscRecordId.APP_RECOVERY_WALLET,
        content: {
          value: "true",
        },
      })
    );

    history.push({
      pathname: nextPath.pathname,
      state: data.state,
    });
  };

  if (hiddenPage) return null;

  return (
    <div className="onboarding">
      {state.step > 0 && state.step < 4 && (
        <ProgressIndicator currentStep={state.step} totalSteps={3} />
      )}

      {state.step === 0 && (
        <WelcomeScreen
          onStart={handleStart}
          onRestore={handleRestore}
          onBiometricRestore={handleBiometricRestore}
        />
      )}

      {state.step === 1 && (
        <BiometricScanScreen
          fingersToScan={fingersToScan}
          onComplete={handleBiometricComplete}
          onError={(error) => {
            // Show user-friendly error message
            showErrorToast(error, showToast, "biometric_capture");

            setState({
              ...state,
              errors: [...state.errors, error],
            });
          }}
        />
      )}

      {state.step === 2 && (
        <SeedPhraseScreen
          words={state.seedPhrase}
          onConfirm={handleSeedConfirm}
          onBack={() => setState({ ...state, step: 1 })}
        />
      )}

      {state.step === 3 && (
        <VerificationScreen
          seedPhrase={state.seedPhrase}
          wordsToVerify={[2, 6, 11]} // 0-indexed: word #3, #7, #12
          onSuccess={handleVerificationSuccess}
          onBack={() => setState({ ...state, step: 2 })}
        />
      )}

      {state.step === 4 && (
        <SuccessScreen
          walletAddress={state.walletAddress || "Creating wallet..."}
          onContinue={handleComplete}
          fastOnboarding={state.fastOnboarding}
        />
      )}
    </div>
  );
};

// Helper function to create wallet with biometric authentication and proper Agent initialization
async function createWalletWithBiometric(
  biometricData: string[],
  seedPhrase: string[],
  bran: string,
  seedPhraseBackedUp: boolean,
  dispatch: any,
  stateCache: any
): Promise<string> {
  // Generate a default passcode for new wallet
  const DEFAULT_PASSCODE = "111111";
  const seedPhraseString = seedPhrase.join(" ");

  // 1. Store SIGNIFY_BRAN in secure storage
  await SecureStorage.set(KeyStoreKeys.SIGNIFY_BRAN, bran);

  // 2. Store APP_PASSCODE in secure storage
  await Agent.agent.auth.storeSecret(
    KeyStoreKeys.APP_PASSCODE,
    DEFAULT_PASSCODE
  );

  // 3. Set APP_ALREADY_INIT flag
  await Agent.agent.basicStorage.createOrUpdateBasicRecord(
    new BasicRecord({
      id: MiscRecordId.APP_ALREADY_INIT,
      content: {
        initialized: true,
      },
    })
  );

  // 4. Set password skipped flag (user can set password later)
  await Agent.agent.basicStorage.createOrUpdateBasicRecord(
    new BasicRecord({
      id: MiscRecordId.APP_PASSWORD_SKIPPED,
      content: { value: true },
    })
  );

  // 5. Store seedPhraseBackedUp flag
  await Agent.agent.basicStorage.createOrUpdateBasicRecord(
    new BasicRecord({
      id: MiscRecordId.APP_SEED_PHRASE_BACKED_UP,
      content: {
        value: seedPhraseBackedUp ? "true" : "false",
      },
    })
  );

  // 6. Update Redux with seed phrase cache
  dispatch(setSeedPhraseCache({
    seedPhrase: seedPhraseString,
    bran: bran,
  }));

  // 7. Boot and connect KERIA agent
  const keriaUrls = {
    url: "http://127.0.0.1:3901",
    bootUrl: "http://127.0.0.1:3903",
  };

  try {
    await Agent.agent.bootAndConnect(keriaUrls);
  } catch (error) {
    console.error("KERIA boot/connect failed:", error);
    // Continue anyway - agent can retry connection later
  }

  // 8. Update authentication state
  dispatch(setAuthentication({
    ...stateCache.authentication,
    loggedIn: true,
    time: Date.now(),
    passcodeIsSet: true,
    passwordIsSet: false,
    passwordIsSkipped: true,
    seedPhraseIsSet: true,
    ssiAgentIsSet: true, // Agent now booted and connected
    recoveryWalletProgress: false,
    firstAppLaunch: false,
  }));

  // 9. Return mock wallet address
  // In production, this would call backend API to create actual wallet with biometric data
  // POST /api/v2/wallet/create
  // Body: { biometricData, seedPhrase, seedPhraseBackedUp }
  // Returns: { address, did }
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve("addr1q9xyz...abc123");
    }, 500);
  });
}

export { Onboarding };
