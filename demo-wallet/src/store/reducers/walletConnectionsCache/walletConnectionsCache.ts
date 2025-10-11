import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { RootState } from "../../index";
import {
  ConnectionData,
  WalletConnectState,
} from "./walletConnectionsCache.types";
import type { StoredBiometricMetadata } from "../../../core/cardano/walletConnect/peerConnection.types";

const initialState: WalletConnectState = {
  walletConnections: [],
  connectedWallet: null,
  pendingConnection: null,
  isConnecting: false,
  showConnectWallet: false,
};
const walletConnectionsCacheSlice = createSlice({
  name: "walletConnectionsCache",
  initialState,
  reducers: {
    setWalletConnectionsCache: (
      state,
      action: PayloadAction<ConnectionData[]>
    ) => {
      state.walletConnections = action.payload;
    },
    setConnectedWallet: (
      state,
      action: PayloadAction<ConnectionData | null>
    ) => {
      state.connectedWallet = action.payload;
    },
    setPendingConnection: (
      state,
      action: PayloadAction<ConnectionData | null>
    ) => {
      if (state.pendingConnection?.id !== action.payload?.id) {
        state.isConnecting = false;
      }

      state.pendingConnection = action.payload;
    },
    setIsConnecting: (state, action: PayloadAction<boolean>) => {
      state.isConnecting = action.payload;
    },
    showConnectWallet: (state, action: PayloadAction<boolean>) => {
      state.showConnectWallet = action.payload;
    },
    updateWalletConnectionMetadata: (
      state,
      action: PayloadAction<{
        id: string;
        biometricMetadata: StoredBiometricMetadata;
      }>
    ) => {
      const { id, biometricMetadata } = action.payload;
      state.walletConnections = state.walletConnections.map((connection) =>
        connection.id === id
          ? { ...connection, biometricMetadata }
          : connection
      );
      if (state.connectedWallet?.id === id) {
        state.connectedWallet = {
          ...state.connectedWallet,
          biometricMetadata,
        };
      }
      if (state.pendingConnection?.id === id) {
        state.pendingConnection = {
          ...state.pendingConnection,
          biometricMetadata,
        };
      }
    },
    clearWalletConnection: () => initialState,
  },
});

export { initialState, walletConnectionsCacheSlice };

export const {
  setWalletConnectionsCache,
  setConnectedWallet,
  setPendingConnection,
  setIsConnecting,
  showConnectWallet,
  updateWalletConnectionMetadata,
  clearWalletConnection,
} = walletConnectionsCacheSlice.actions;

const getWalletConnectionsCache = (state: RootState) =>
  state.walletConnectionsCache.walletConnections;

const getConnectedWallet = (state: RootState) =>
  state.walletConnectionsCache?.connectedWallet;

const getPendingConnection = (state: RootState) =>
  state.walletConnectionsCache.pendingConnection;

const getIsConnecting = (state: RootState) =>
  state.walletConnectionsCache.isConnecting;

const getShowConnectWallet = (state: RootState) =>
  state.walletConnectionsCache.showConnectWallet;

export {
  getWalletConnectionsCache,
  getConnectedWallet,
  getPendingConnection,
  getIsConnecting,
  getShowConnectWallet,
};
