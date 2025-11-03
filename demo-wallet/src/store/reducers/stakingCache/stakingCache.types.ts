/**
 * Staking cache types for Redux store
 */

export interface StakeAccount {
  stake_address: string;
  status: string;
  delegated_pool?: string;
  total_balance: string;
  total_balance_ada: string;
  available_rewards: string;
  rewards_ada: string;
  delegated_amount: string;
  is_delegated: boolean;
}

export interface StakePool {
  pool_id: string;
  pool_id_bech32: string;
  ticker?: string;
  name?: string;
  description?: string;
  homepage?: string;
  active_stake: string;
  active_stake_ada: string;
  live_stake: string;
  live_saturation: number;
  saturation_percentage: string;
  margin: number;
  margin_percentage: string;
  fixed_cost: string;
  fixed_cost_ada: string;
  blocks_minted: number;
  blocks_epoch: number;
  live_delegators: number;
  estimated_apy?: number;
}

export interface Reward {
  epoch: number;
  amount: string;
  amount_ada: string;
  pool_id: string;
  earned_epoch: number;
}

export interface AddressStakingData {
  stakeAddress: string;
  account?: StakeAccount;
  rewards?: Reward[];
  lastUpdated: number;
  isLoading: boolean;
  error?: string;
}

export interface StakingCacheProps {
  addressData: Record<string, AddressStakingData>;
  currentStakeAddress?: string;
  pools: StakePool[];
  poolsLoading: boolean;
  poolsError?: string;
  selectedPool?: string;
}
