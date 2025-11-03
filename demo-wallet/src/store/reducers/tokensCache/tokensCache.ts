/**
 * Tokens cache Redux slice
 * 
 * Manages state for ADA balances, native assets, NFTs, and transaction history
 */

import { createSlice, PayloadAction, createAsyncThunk } from "@reduxjs/toolkit";
import { RootState } from "../../index";
import {
  TokensCacheProps,
  AddressTokenData,
  Balance,
  NFT,
  Transaction,
} from "./tokensCache.types";
import { getTokenService } from "../../../core/cardano/tokenService";

const initialState: TokensCacheProps = {
  addressData: {},
  currentAddress: undefined,
};

// Async thunks
export const fetchBalance = createAsyncThunk(
  "tokensCache/fetchBalance",
  async (address: string, { rejectWithValue }) => {
    try {
      const tokenService = getTokenService();
      const balance = await tokenService.getBalance(address);
      return { address, balance };
    } catch (error: any) {
      return rejectWithValue(error.message || "Failed to fetch balance");
    }
  }
);

export const fetchNFTs = createAsyncThunk(
  "tokensCache/fetchNFTs",
  async (address: string, { rejectWithValue }) => {
    try {
      const tokenService = getTokenService();
      const nfts = await tokenService.getNFTs(address);
      return { address, nfts };
    } catch (error: any) {
      return rejectWithValue(error.message || "Failed to fetch NFTs");
    }
  }
);

export const fetchTransactionHistory = createAsyncThunk(
  "tokensCache/fetchTransactionHistory",
  async (
    { address, limit = 50, offset = 0 }: { address: string; limit?: number; offset?: number },
    { rejectWithValue }
  ) => {
    try {
      const tokenService = getTokenService();
      const transactions = await tokenService.getTransactionHistory(address, limit, offset);
      return { address, transactions };
    } catch (error: any) {
      return rejectWithValue(error.message || "Failed to fetch transaction history");
    }
  }
);

const tokensCacheSlice = createSlice({
  name: "tokensCache",
  initialState,
  reducers: {
    setCurrentAddress: (state, action: PayloadAction<string>) => {
      state.currentAddress = action.payload;
    },
    clearAddressData: (state, action: PayloadAction<string>) => {
      delete state.addressData[action.payload];
    },
    clearAllData: (state) => {
      state.addressData = {};
      state.currentAddress = undefined;
    },
  },
  extraReducers: (builder) => {
    // Fetch balance
    builder.addCase(fetchBalance.pending, (state, action) => {
      const address = action.meta.arg;
      if (!state.addressData[address]) {
        state.addressData[address] = {
          address,
          lastUpdated: Date.now(),
          isLoading: true,
        };
      } else {
        state.addressData[address].isLoading = true;
        state.addressData[address].error = undefined;
      }
    });
    builder.addCase(fetchBalance.fulfilled, (state, action) => {
      const { address, balance } = action.payload;
      state.addressData[address] = {
        ...state.addressData[address],
        balance,
        lastUpdated: Date.now(),
        isLoading: false,
        error: undefined,
      };
    });
    builder.addCase(fetchBalance.rejected, (state, action) => {
      const address = action.meta.arg;
      state.addressData[address] = {
        ...state.addressData[address],
        isLoading: false,
        error: action.payload as string,
      };
    });

    // Fetch NFTs
    builder.addCase(fetchNFTs.pending, (state, action) => {
      const address = action.meta.arg;
      if (!state.addressData[address]) {
        state.addressData[address] = {
          address,
          lastUpdated: Date.now(),
          isLoading: true,
        };
      } else {
        state.addressData[address].isLoading = true;
        state.addressData[address].error = undefined;
      }
    });
    builder.addCase(fetchNFTs.fulfilled, (state, action) => {
      const { address, nfts } = action.payload;
      state.addressData[address] = {
        ...state.addressData[address],
        nfts,
        lastUpdated: Date.now(),
        isLoading: false,
        error: undefined,
      };
    });
    builder.addCase(fetchNFTs.rejected, (state, action) => {
      const address = action.meta.arg;
      state.addressData[address] = {
        ...state.addressData[address],
        isLoading: false,
        error: action.payload as string,
      };
    });

    // Fetch transaction history
    builder.addCase(fetchTransactionHistory.pending, (state, action) => {
      const { address } = action.meta.arg;
      if (!state.addressData[address]) {
        state.addressData[address] = {
          address,
          lastUpdated: Date.now(),
          isLoading: true,
        };
      } else {
        state.addressData[address].isLoading = true;
        state.addressData[address].error = undefined;
      }
    });
    builder.addCase(fetchTransactionHistory.fulfilled, (state, action) => {
      const { address, transactions } = action.payload;
      state.addressData[address] = {
        ...state.addressData[address],
        transactions,
        lastUpdated: Date.now(),
        isLoading: false,
        error: undefined,
      };
    });
    builder.addCase(fetchTransactionHistory.rejected, (state, action) => {
      const { address } = action.meta.arg;
      state.addressData[address] = {
        ...state.addressData[address],
        isLoading: false,
        error: action.payload as string,
      };
    });
  },
});

export const { setCurrentAddress, clearAddressData, clearAllData } = tokensCacheSlice.actions;

// Selectors
export const getTokensCache = (state: RootState) => state.tokensCache;

export const getCurrentAddress = (state: RootState) => state.tokensCache.currentAddress;

export const getAddressData = (address: string) => (state: RootState) =>
  state.tokensCache.addressData[address];

export const getCurrentAddressData = (state: RootState) => {
  const address = state.tokensCache.currentAddress;
  return address ? state.tokensCache.addressData[address] : undefined;
};

export const getBalance = (address: string) => (state: RootState) =>
  state.tokensCache.addressData[address]?.balance;

export const getNFTs = (address: string) => (state: RootState) =>
  state.tokensCache.addressData[address]?.nfts || [];

export const getTransactions = (address: string) => (state: RootState) =>
  state.tokensCache.addressData[address]?.transactions || [];

export default tokensCacheSlice.reducer;
