import { IonRouterOutlet } from "@ionic/react";
import { lazy, Suspense, useEffect, useRef, useLayoutEffect } from "react";
import { Redirect, Route } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../store/hooks";
import {
  getRoutes,
  getStateCache,
  setCurrentRoute,
} from "../store/reducers/stateCache";
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
  const dispatch = useAppDispatch();
  const routes = useAppSelector(getRoutes);

  const { nextPath } = getNextRoute(RoutePath.ROOT, {
    store: { stateCache },
  });

  // Use useLayoutEffect to dispatch BEFORE paint but AFTER DOM measurements
  // This prevents render cycle conflicts by ensuring state is updated before other renders
  useLayoutEffect(() => {
    if (!routes.length) {
      dispatch(setCurrentRoute({ path: nextPath.pathname }));
    }
  }, [routes, nextPath.pathname, dispatch]);

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
          path={RoutePath.TABS_MENU}
          component={TabsMenu}
          exact
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
        <Redirect
          exact
          from="/"
          to={nextPath}
        />
      </Suspense>
    </IonRouterOutlet>
  );
};

export { RoutePath, Routes };
