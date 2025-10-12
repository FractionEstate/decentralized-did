import { useState } from "react";
import { useHistory } from "react-router-dom";
import { useIonToast } from "@ionic/react";
import { RoutePath } from "../../../routes";
import { TabsRoutePath } from "../../../routes/paths";
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
import "./SimplifiedOnboarding.scss";

export interface OnboardingState {
  step: number; // 0: welcome, 1: biometric, 2: seed, 3: verify, 4: success
  biometricData: string[]; // Captured fingerprint data
  seedPhrase: string[]; // Generated seed phrase
  walletAddress: string | null;
  startTime: number;
  errors: string[];
}

const SimplifiedOnboarding = () => {
  const history = useHistory();
  const [showToast] = useIonToast();
  const [state, setState] = useState<OnboardingState>({
    step: 0,
    biometricData: [],
    seedPhrase: [],
    walletAddress: null,
    startTime: Date.now(),
    errors: [],
  });

  const handleStart = () => {
    console.log("Onboarding started");
    // Track analytics: onboarding_started
    setState({ ...state, step: 1, startTime: Date.now() });
  };

  const handleBiometricComplete = (biometricData: string[]) => {
    console.log("Biometric capture complete:", biometricData.length, "fingers");
    // Track analytics: step_1_biometric_completed

    // Generate seed phrase (12 words from BIP39 wordlist)
    const seedPhrase = generateSeedPhrase(12);

    setState({
      ...state,
      step: 2,
      biometricData,
      seedPhrase,
    });
  };

  const handleSeedConfirm = () => {
    console.log("Seed phrase confirmed");
    // Track analytics: step_2_seed_confirmed
    setState({ ...state, step: 3 });
  };

  const handleVerificationSuccess = async () => {
    console.log("Verification successful");
    // Track analytics: step_3_verification_success

    // Show loading state
    showToast({
      message: LOADING_MESSAGES.creating_wallet,
      duration: 0, // Will dismiss after wallet creation
      position: "top",
      color: "primary",
    });

    // Create wallet with biometric + seed phrase
    try {
      const walletAddress = await createWalletWithBiometric(
        state.biometricData,
        state.seedPhrase
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

      // Track analytics: onboarding_completed
      const duration = Date.now() - state.startTime;
      console.log("Onboarding completed in", duration, "ms");
    } catch (error) {
      console.error("Wallet creation failed:", error);
      
      // Show user-friendly error message
      showErrorToast(error, showToast, "wallet_creation");
      
      setState({
        ...state,
        errors: [...state.errors, "Failed to create wallet"],
      });
    }
  };

  const handleComplete = () => {
    console.log("User clicked Start Using Wallet");
    // Navigate to main wallet screen
    history.push(TabsRoutePath.CREDENTIALS); // Main credentials screen
  };

  const handleRestore = () => {
    console.log("User wants to restore existing wallet");
    // Navigate to restore flow
    history.push(RoutePath.GENERATE_SEED_PHRASE); // Or restore route
  };

  return (
    <div className="simplified-onboarding">
      {state.step > 0 && state.step < 4 && (
        <ProgressIndicator currentStep={state.step} totalSteps={3} />
      )}

      {state.step === 0 && (
        <WelcomeScreen onStart={handleStart} onRestore={handleRestore} />
      )}

      {state.step === 1 && (
        <BiometricScanScreen
          fingersToScan={["right-index", "right-middle", "right-thumb"]}
          onComplete={handleBiometricComplete}
          onError={(error) => {
            console.error("Biometric capture failed:", error);
            
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

      {state.step === 4 && state.walletAddress && (
        <SuccessScreen
          walletAddress={state.walletAddress}
          onContinue={handleComplete}
        />
      )}
    </div>
  );
};

// Helper function to generate BIP39 seed phrase
function generateSeedPhrase(wordCount: 12 | 24 = 12): string[] {
  // Simple BIP39 wordlist (first 24 words for demo)
  const bip39Words = [
    "castle", "ocean", "rainbow", "mountain", "grape", "window",
    "bridge", "sunset", "tree", "music", "cloud", "river",
    "forest", "garden", "sunrise", "valley", "winter", "spring",
    "summer", "autumn", "meadow", "horizon", "desert", "island"
  ];

  // In production, use proper BIP39 library with cryptographic randomness
  // For now, return demo words
  return bip39Words.slice(0, wordCount);
}

// Helper function to create wallet with biometric authentication
async function createWalletWithBiometric(
  biometricData: string[],
  seedPhrase: string[]
): Promise<string> {
  // In production, call backend API:
  // POST /api/v2/wallet/create
  // Body: { biometricData, seedPhrase }
  // Returns: { address, did }

  // For demo, return mock address
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve("addr1q9xyz...abc123");
    }, 1000);
  });
}

export { SimplifiedOnboarding };
