import { IonRouterOutlet } from "@ionic/react";
import { lazy, Suspense } from "react";
import { Redirect, Route } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../store/hooks";
import { getRoutes, getStateCache } from "../store/reducers/stateCache";
import { ErrorBoundary } from "../ui/components/ErrorBoundary";
import { LoadingSkeleton } from "../ui/components/LoadingSkeleton";
import { TabsMenu, tabsRoutes } from "../ui/components/navigation/TabsMenu";

// Code splitting: Lazy load route components to reduce initial bundle size
const CreatePassword = lazy(() => import("../ui/pages/CreatePassword").then(m => ({ default: m.CreatePassword })));
const CredentialDetails = lazy(() => import("../ui/pages/CredentialDetails").then(m => ({ default: m.CredentialDetails })));
const DeferredBackup = lazy(() => import("../ui/pages/DeferredBackup").then(m => ({ default: m.DeferredBackup })));
const GenerateSeedPhrase = lazy(() => import("../ui/pages/GenerateSeedPhrase").then(m => ({ default: m.GenerateSeedPhrase })));
const IdentifierDetails = lazy(() => import("../ui/pages/IdentifierDetails").then(m => ({ default: m.IdentifierDetails })));
const NotificationDetails = lazy(() => import("../ui/pages/NotificationDetails").then(m => ({ default: m.NotificationDetails })));
const Onboarding = lazy(() => import("../ui/pages/Onboarding").then(m => ({ default: m.Onboarding })));
const SetPasscode = lazy(() => import("../ui/pages/SetPasscode").then(m => ({ default: m.SetPasscode })));
const SetupBiometrics = lazy(() => import("../ui/pages/SetupBiometrics/SetupBiometrics").then(m => ({ default: m.SetupBiometrics })));
const BiometricEnrollment = lazy(() => import("../ui/pages/BiometricEnrollment").then(m => ({ default: m.BiometricEnrollment })));
const VerifyRecoverySeedPhrase = lazy(() => import("../ui/pages/VerifyRecoverySeedPhrase").then(m => ({ default: m.VerifyRecoverySeedPhrase })));
const VerifySeedPhrase = lazy(() => import("../ui/pages/VerifySeedPhrase").then(m => ({ default: m.VerifySeedPhrase })));

import { getNextRoute } from "./nextRoute";
import { RoutePath, TabsRoutePath } from "./paths";

// Loading fallback component with skeleton animation
const LoadingFallback = () => (
  <div style={{ padding: "1rem" }}>
    <LoadingSkeleton variant="page" count={3} animated={true} />
  </div>
);

const Routes = () => {
  const stateCache = useAppSelector(getStateCache);
  const routes = useAppSelector(getRoutes);

  const { nextPath } = getNextRoute(RoutePath.ROOT, {
    store: { stateCache },
  });

  // Compute initial redirect target without dispatching on first render.
  // If the next root is tabs, go directly to the default tab to avoid showing
  // bare "/tabs" in the URL.
  const initialRedirectPath =
    nextPath.pathname === RoutePath.TABS_MENU
      ? TabsRoutePath.IDENTIFIERS
      : nextPath.pathname;

  return (
    <IonRouterOutlet animated={false}>
      <Suspense fallback={<LoadingFallback />}>
        <Route
          path={RoutePath.SET_PASSCODE}
          exact
          render={() => <SetPasscode />}
        />
        <Route
          path={RoutePath.ONBOARDING}
          exact
          render={() => <Onboarding />}
        />
        <Route
          path={RoutePath.GENERATE_SEED_PHRASE}
          exact
          render={() => <GenerateSeedPhrase />}
        />
        <Route
          path={RoutePath.VERIFY_SEED_PHRASE}
          exact
          render={() => <VerifySeedPhrase />}
        />
        <Route
          path={RoutePath.DEFERRED_BACKUP}
          exact
          render={() => <DeferredBackup />}
        />
        <Route
          path={RoutePath.CREATE_PASSWORD}
          exact
          render={() => <CreatePassword />}
        />
        <Route
          path={RoutePath.VERIFY_RECOVERY_SEED_PHRASE}
          exact
          render={() => <VerifyRecoverySeedPhrase />}
        />

        {tabsRoutes.map((tab, index: number) => {
          return (
            <Route
              key={index}
              path={tab.path}
              exact
              render={() => (
                <TabsMenu
                  tab={tab.component}
                  path={tab.path}
                />
              )}
            />
          );
        })}
        <Route
          path={TabsRoutePath.IDENTIFIER_DETAILS}
          exact
          render={() => <IdentifierDetails />}
        />
        <Route
          path={RoutePath.SETUP_BIOMETRICS}
          exact
          render={() => <SetupBiometrics />}
        />
        <Route
          path={RoutePath.BIOMETRIC_ENROLLMENT}
          exact
          render={() => <BiometricEnrollment />}
        />
        <Route
          path={TabsRoutePath.CREDENTIAL_DETAILS}
          exact
          render={() => <CredentialDetails />}
        />
        <Route
          path={TabsRoutePath.NOTIFICATION_DETAILS}
          exact
          render={() => <NotificationDetails />}
        />
        <Redirect exact from="/" to={initialRedirectPath} />
      </Suspense>
    </IonRouterOutlet>
  );
};

export { RoutePath, Routes };
