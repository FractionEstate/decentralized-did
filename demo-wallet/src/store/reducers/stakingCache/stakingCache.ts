/**
 * Staking cache Redux slice
 * 
 * Manages state for stake accounts, pools, and rewards
 */

import { createSlice, PayloadAction, createAsyncThunk } from "@reduxjs/toolkit";
import { RootState } from "../../index";
import {
  StakingCacheProps,
  AddressStakingData,
  StakeAccount,
  StakePool,
  Reward,
} from "./stakingCache.types";
import { getStakingService } from "../../../core/cardano/stakingService";

const initialState: StakingCacheProps = {
  addressData: {},
  currentStakeAddress: undefined,
  pools: [],
  poolsLoading: false,
  poolsError: undefined,
  selectedPool: undefined,
};

// Async thunks
export const fetchAccountInfo = createAsyncThunk(
  "stakingCache/fetchAccountInfo",
  async (stakeAddress: string, { rejectWithValue }) => {
    try {
      const stakingService = getStakingService();
      const account = await stakingService.getAccountInfo(stakeAddress);
      return { stakeAddress, account };
    } catch (error: any) {
      return rejectWithValue(error.message || "Failed to fetch account info");
    }
  }
);

export const fetchPoolList = createAsyncThunk(
  "stakingCache/fetchPoolList",
  async (_, { rejectWithValue }) => {
    try {
      const stakingService = getStakingService();
      const pools = await stakingService.getPoolList(50);
      return pools;
    } catch (error: any) {
      return rejectWithValue(error.message || "Failed to fetch pool list");
    }
  }
);

export const fetchRewards = createAsyncThunk(
  "stakingCache/fetchRewards",
  async (stakeAddress: string, { rejectWithValue }) => {
    try {
      const stakingService = getStakingService();
      const rewards = await stakingService.getRewardsHistory(stakeAddress, 20);
      return { stakeAddress, rewards };
    } catch (error: any) {
      return rejectWithValue(error.message || "Failed to fetch rewards");
    }
  }
);

const stakingCacheSlice = createSlice({
  name: "stakingCache",
  initialState,
  reducers: {
    setCurrentStakeAddress: (state, action: PayloadAction<string>) => {
      state.currentStakeAddress = action.payload;
    },
    setSelectedPool: (state, action: PayloadAction<string>) => {
      state.selectedPool = action.payload;
    },
    clearAddressData: (state, action: PayloadAction<string>) => {
      delete state.addressData[action.payload];
    },
    clearAllData: (state) => {
      state.addressData = {};
      state.currentStakeAddress = undefined;
      state.pools = [];
      state.selectedPool = undefined;
    },
  },
  extraReducers: (builder) => {
    // Fetch account info
    builder.addCase(fetchAccountInfo.pending, (state, action) => {
      const stakeAddress = action.meta.arg;
      if (!state.addressData[stakeAddress]) {
        state.addressData[stakeAddress] = {
          stakeAddress,
          lastUpdated: Date.now(),
          isLoading: true,
        };
      } else {
        state.addressData[stakeAddress].isLoading = true;
        state.addressData[stakeAddress].error = undefined;
      }
    });
    builder.addCase(fetchAccountInfo.fulfilled, (state, action) => {
      const { stakeAddress, account } = action.payload;
      state.addressData[stakeAddress] = {
        ...state.addressData[stakeAddress],
        account,
        lastUpdated: Date.now(),
        isLoading: false,
        error: undefined,
      };
    });
    builder.addCase(fetchAccountInfo.rejected, (state, action) => {
      const stakeAddress = action.meta.arg;
      state.addressData[stakeAddress] = {
        ...state.addressData[stakeAddress],
        isLoading: false,
        error: action.payload as string,
      };
    });

    // Fetch pool list
    builder.addCase(fetchPoolList.pending, (state) => {
      state.poolsLoading = true;
      state.poolsError = undefined;
    });
    builder.addCase(fetchPoolList.fulfilled, (state, action) => {
      state.pools = action.payload;
      state.poolsLoading = false;
      state.poolsError = undefined;
    });
    builder.addCase(fetchPoolList.rejected, (state, action) => {
      state.poolsLoading = false;
      state.poolsError = action.payload as string;
    });

    // Fetch rewards
    builder.addCase(fetchRewards.pending, (state, action) => {
      const stakeAddress = action.meta.arg;
      if (state.addressData[stakeAddress]) {
        state.addressData[stakeAddress].isLoading = true;
      }
    });
    builder.addCase(fetchRewards.fulfilled, (state, action) => {
      const { stakeAddress, rewards } = action.payload;
      if (state.addressData[stakeAddress]) {
        state.addressData[stakeAddress].rewards = rewards;
        state.addressData[stakeAddress].lastUpdated = Date.now();
        state.addressData[stakeAddress].isLoading = false;
      }
    });
    builder.addCase(fetchRewards.rejected, (state, action) => {
      const stakeAddress = action.meta.arg;
      if (state.addressData[stakeAddress]) {
        state.addressData[stakeAddress].isLoading = false;
        state.addressData[stakeAddress].error = action.payload as string;
      }
    });
  },
});

export const {
  setCurrentStakeAddress,
  setSelectedPool,
  clearAddressData,
  clearAllData,
} = stakingCacheSlice.actions;

// Selectors
export const getStakingCache = (state: RootState) => state.stakingCache;

export const getCurrentStakeAddress = (state: RootState) =>
  state.stakingCache.currentStakeAddress;

export const getAddressData = (stakeAddress: string) => (state: RootState) =>
  state.stakingCache.addressData[stakeAddress];

export const getPools = (state: RootState) => state.stakingCache.pools;

export const getSelectedPool = (state: RootState) => state.stakingCache.selectedPool;

export default stakingCacheSlice.reducer;
