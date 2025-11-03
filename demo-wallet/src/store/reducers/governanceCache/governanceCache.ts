import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { getGovernanceService } from '../../../core/cardano/governanceService';
import { GovernanceCacheState, initialState } from './governanceCache.types';
import type { RootState } from '../../index';

// Async thunks
export const fetchDReps = createAsyncThunk(
  'governanceCache/fetchDReps',
  async ({ limit = 20, offset = 0 }: { limit?: number; offset?: number }) => {
    const service = getGovernanceService();
    const dreps = await service.getDReps(limit, offset);
    return { dreps, key: `${limit}_${offset}` };
  }
);

export const fetchProposals = createAsyncThunk(
  'governanceCache/fetchProposals',
  async ({ status, limit = 20, offset = 0 }: { 
    status?: 'active' | 'passed' | 'rejected' | 'expired'; 
    limit?: number; 
    offset?: number;
  }) => {
    const service = getGovernanceService();
    const proposals = await service.getProposals(status, limit, offset);
    return { proposals, key: status || 'all' };
  }
);

export const fetchVotingPower = createAsyncThunk(
  'governanceCache/fetchVotingPower',
  async (stakeAddress: string) => {
    const service = getGovernanceService();
    const votingPower = await service.getVotingPower(stakeAddress);
    return { votingPower, stakeAddress };
  }
);

export const fetchVoteHistory = createAsyncThunk(
  'governanceCache/fetchVoteHistory',
  async ({ voter, limit = 20 }: { voter: string; limit?: number }) => {
    const service = getGovernanceService();
    const voteHistory = await service.getVoteHistory(voter, limit);
    return { voteHistory, voter };
  }
);

// Slice
const governanceCacheSlice = createSlice({
  name: 'governanceCache',
  initialState,
  reducers: {
    clearGovernanceCache: () => initialState,
    clearError: (state, action: PayloadAction<keyof GovernanceCacheState['error']>) => {
      state.error[action.payload] = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch DReps
    builder.addCase(fetchDReps.pending, (state) => {
      state.loading.dreps = true;
      state.error.dreps = null;
    });
    builder.addCase(fetchDReps.fulfilled, (state, action) => {
      state.loading.dreps = false;
      state.dreps[action.payload.key] = action.payload.dreps;
    });
    builder.addCase(fetchDReps.rejected, (state, action) => {
      state.loading.dreps = false;
      state.error.dreps = action.error.message || 'Failed to fetch DReps';
    });

    // Fetch Proposals
    builder.addCase(fetchProposals.pending, (state) => {
      state.loading.proposals = true;
      state.error.proposals = null;
    });
    builder.addCase(fetchProposals.fulfilled, (state, action) => {
      state.loading.proposals = false;
      state.proposals[action.payload.key] = action.payload.proposals;
    });
    builder.addCase(fetchProposals.rejected, (state, action) => {
      state.loading.proposals = false;
      state.error.proposals = action.error.message || 'Failed to fetch proposals';
    });

    // Fetch Voting Power
    builder.addCase(fetchVotingPower.pending, (state) => {
      state.loading.votingPower = true;
      state.error.votingPower = null;
    });
    builder.addCase(fetchVotingPower.fulfilled, (state, action) => {
      state.loading.votingPower = false;
      state.votingPower[action.payload.stakeAddress] = action.payload.votingPower;
    });
    builder.addCase(fetchVotingPower.rejected, (state, action) => {
      state.loading.votingPower = false;
      state.error.votingPower = action.error.message || 'Failed to fetch voting power';
    });

    // Fetch Vote History
    builder.addCase(fetchVoteHistory.pending, (state) => {
      state.loading.voteHistory = true;
      state.error.voteHistory = null;
    });
    builder.addCase(fetchVoteHistory.fulfilled, (state, action) => {
      state.loading.voteHistory = false;
      state.voteHistory[action.payload.voter] = action.payload.voteHistory;
    });
    builder.addCase(fetchVoteHistory.rejected, (state, action) => {
      state.loading.voteHistory = false;
      state.error.voteHistory = action.error.message || 'Failed to fetch vote history';
    });
  },
});

// Selectors
export const selectDReps = (state: RootState, key: string = '20_0') => 
  state.governanceCache.dreps[key] || [];

export const selectProposals = (state: RootState, status: string = 'all') =>
  state.governanceCache.proposals[status] || [];

export const selectVotingPower = (state: RootState, stakeAddress: string) =>
  state.governanceCache.votingPower[stakeAddress];

export const selectVoteHistory = (state: RootState, voter: string) =>
  state.governanceCache.voteHistory[voter];

export const selectGovernanceLoading = (state: RootState) =>
  state.governanceCache.loading;

export const selectGovernanceError = (state: RootState) =>
  state.governanceCache.error;

export const { clearGovernanceCache, clearError } = governanceCacheSlice.actions;
export default governanceCacheSlice.reducer;
