import { configureStore } from "@reduxjs/toolkit";
import { seedPhraseCacheSlice } from "./reducers/seedPhraseCache";
import { stateCacheSlice } from "./reducers/stateCache";
import { identifiersCacheSlice } from "./reducers/identifiersCache";
import { credsCacheSlice } from "./reducers/credsCache";
import { connectionsCacheSlice } from "./reducers/connectionsCache";
import { walletConnectionsCacheSlice } from "./reducers/walletConnectionsCache";
import { viewTypeCacheSlice } from "./reducers/viewTypeCache";
import { biometricsCacheSlice } from "./reducers/biometricsCache";
import { credsArchivedCacheSlice } from "./reducers/credsArchivedCache";
import { ssiAgentSlice } from "./reducers/ssiAgent";
import { notificationsCacheSlice } from "./reducers/notificationsCache";
import tokensCacheReducer from "./reducers/tokensCache";
import { setCurrentRoute } from "./reducers/stateCache/stateCache";

const store = configureStore({
  reducer: {
    stateCache: stateCacheSlice.reducer,
    seedPhraseCache: seedPhraseCacheSlice.reducer,
    identifiersCache: identifiersCacheSlice.reducer,
    credsCache: credsCacheSlice.reducer,
    credsArchivedCache: credsArchivedCacheSlice.reducer,
    connectionsCache: connectionsCacheSlice.reducer,
    walletConnectionsCache: walletConnectionsCacheSlice.reducer,
    viewTypeCache: viewTypeCacheSlice.reducer,
    biometricsCache: biometricsCacheSlice.reducer,
    ssiAgentCache: ssiAgentSlice.reducer,
    notificationsCache: notificationsCacheSlice.reducer,
    tokensCache: tokensCacheReducer,
  },
  middleware: (getDefaultMiddleware) => {
    const defaultMiddleware = getDefaultMiddleware({
      serializableCheck: {
        // Ignore these field paths in all actions
        ignoredActionPaths: [
          "payload.signTransaction.payload.approvalCallback",
        ],
      },
    });

    // Middleware to defer setCurrentRoute actions to avoid render-cycle warnings.
    // Uses queueMicrotask to execute after the current task but before the next paint,
    // giving Ionic time to complete its render cycle.
    const deferRouteMiddleware = () => (next: any) => (action: any) => {
      try {
        if (action && action.type === setCurrentRoute.type) {
          // In test environments, avoid deferring to prevent act() warnings
          if (process.env.NODE_ENV === "test") {
            return next(action);
          }
          // Queue in the microtask queue to avoid state updates during Ionic render
          if (typeof queueMicrotask !== "undefined") {
            queueMicrotask(() => next(action));
          } else {
            // Fallback for older browsers
            Promise.resolve().then(() => next(action));
          }
          return;
        }
      } catch (e) {
        // If anything goes wrong, fallback to forwarding the action
      }
      return next(action);
    };

    return defaultMiddleware.concat(deferRouteMiddleware);
  },
});

type RootState = ReturnType<typeof store.getState>;
type AppDispatch = typeof store.dispatch;

export type { RootState, AppDispatch };

export { store };
