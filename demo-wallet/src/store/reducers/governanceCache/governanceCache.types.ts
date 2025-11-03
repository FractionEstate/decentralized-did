import { DRep, Proposal, VotingPower, VoteHistory } from '../../../core/cardano/governanceService';

export interface GovernanceCacheState {
  dreps: {
    [key: string]: DRep[];
  };
  proposals: {
    [status: string]: Proposal[];
  };
  votingPower: {
    [stakeAddress: string]: VotingPower;
  };
  voteHistory: {
    [voter: string]: VoteHistory;
  };
  loading: {
    dreps: boolean;
    proposals: boolean;
    votingPower: boolean;
    voteHistory: boolean;
  };
  error: {
    dreps: string | null;
    proposals: string | null;
    votingPower: string | null;
    voteHistory: string | null;
  };
}

export const initialState: GovernanceCacheState = {
  dreps: {},
  proposals: {},
  votingPower: {},
  voteHistory: {},
  loading: {
    dreps: false,
    proposals: false,
    votingPower: false,
    voteHistory: false,
  },
  error: {
    dreps: null,
    proposals: null,
    votingPower: null,
    voteHistory: null,
  },
};
