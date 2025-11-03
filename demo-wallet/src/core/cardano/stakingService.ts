/**
 * Staking Service for Cardano blockchain
 * 
 * Provides API client for staking operations including:
 * - Stake account queries
 * - Pool selection and metadata
 * - Rewards history
 * - APY calculations
 */

// API base URL - configurable via environment
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8002";

// Type definitions
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

export interface StakingServiceError {
  message: string;
  status?: number;
  detail?: string;
}

/**
 * Staking Service class for managing Cardano staking
 */
export class StakingService {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || API_BASE_URL;
  }

  /**
   * Fetch stake account information
   * @param stakeAddress Cardano stake address (stake1...)
   * @returns StakeAccount with status, delegation, and rewards
   */
  async getAccountInfo(stakeAddress: string): Promise<StakeAccount> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/staking/account/${stakeAddress}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          signal: AbortSignal.timeout(10000), // 10s timeout
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to get account info for ${stakeAddress}:`, error);
      throw this.handleError(error);
    }
  }

  /**
   * Fetch list of active stake pools
   * @param limit Maximum number of pools (1-100)
   * @param offset Pagination offset
   * @returns List of stake pools
   */
  async getPoolList(limit: number = 50, offset: number = 0): Promise<StakePool[]> {
    try {
      const params = new URLSearchParams({
        limit: Math.min(Math.max(limit, 1), 100).toString(),
        offset: Math.max(offset, 0).toString(),
      });

      const response = await fetch(
        `${this.baseUrl}/api/staking/pools?${params}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          signal: AbortSignal.timeout(15000), // 15s timeout for pool list
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to get pool list:", error);
      throw this.handleError(error);
    }
  }

  /**
   * Fetch detailed information for a specific pool
   * @param poolId Pool ID (hex or bech32)
   * @param includeApy Whether to calculate estimated APY
   * @returns Detailed pool information
   */
  async getPoolDetails(poolId: string, includeApy: boolean = true): Promise<StakePool> {
    try {
      const params = new URLSearchParams();
      if (includeApy) {
        params.set("include_apy", "true");
      }

      const response = await fetch(
        `${this.baseUrl}/api/staking/pool/${poolId}?${params}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          signal: AbortSignal.timeout(10000),
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to get pool details for ${poolId}:`, error);
      throw this.handleError(error);
    }
  }

  /**
   * Fetch rewards history for a stake address
   * @param stakeAddress Cardano stake address
   * @param limit Maximum number of rewards (1-100)
   * @returns List of rewards
   */
  async getRewardsHistory(
    stakeAddress: string,
    limit: number = 20
  ): Promise<Reward[]> {
    try {
      const params = new URLSearchParams({
        limit: Math.min(Math.max(limit, 1), 100).toString(),
      });

      const response = await fetch(
        `${this.baseUrl}/api/staking/rewards/${stakeAddress}?${params}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          signal: AbortSignal.timeout(10000),
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(
        `Failed to get rewards history for ${stakeAddress}:`,
        error
      );
      throw this.handleError(error);
    }
  }

  /**
   * Check if staking service is healthy
   * @returns Health status
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/staking/health`, {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Staking service health check failed:", error);
      throw this.handleError(error);
    }
  }

  /**
   * Handle and normalize errors
   */
  private handleError(error: any): StakingServiceError {
    if (error instanceof Error) {
      if (error.name === "AbortError") {
        return {
          message: "Request timeout",
          detail: "The request took too long to complete",
        };
      }
      return {
        message: error.message,
        detail: error.message,
      };
    }
    return {
      message: "Unknown error occurred",
      detail: String(error),
    };
  }

  /**
   * Format APY as percentage
   * @param apy APY as decimal (e.g., 0.045 = 4.5%)
   * @returns Formatted percentage string
   */
  static formatAPY(apy: number): string {
    return `${(apy * 100).toFixed(2)}%`;
  }

  /**
   * Format stake amount in millions
   * @param lovelace Amount in lovelace
   * @returns Formatted string like "50.23M ₳"
   */
  static formatStake(lovelace: string): string {
    const ada = Number(lovelace) / 1_000_000;
    const millions = ada / 1_000_000;
    
    if (millions >= 1) {
      return `${millions.toFixed(2)}M ₳`;
    } else if (ada >= 1000) {
      return `${(ada / 1000).toFixed(2)}K ₳`;
    } else {
      return `${ada.toFixed(2)} ₳`;
    }
  }

  /**
   * Get saturation color indicator
   * @param saturation Saturation as decimal (0-1)
   * @returns Color class name
   */
  static getSaturationColor(saturation: number): string {
    if (saturation >= 0.95) return "danger";
    if (saturation >= 0.80) return "warning";
    if (saturation >= 0.60) return "medium";
    return "success";
  }

  /**
   * Format epoch to approximate date
   * @param epoch Cardano epoch number
   * @returns Approximate date string
   */
  static formatEpochDate(epoch: number): string {
    // Cardano genesis: Dec 13, 2017, ~5 days per epoch
    const genesisTime = new Date("2017-12-13T00:00:00Z").getTime();
    const epochDuration = 5 * 24 * 60 * 60 * 1000; // 5 days in ms
    const epochTime = genesisTime + (epoch * epochDuration);
    const date = new Date(epochTime);
    
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }
}

// Singleton instance
let stakingServiceInstance: StakingService | null = null;

/**
 * Get singleton staking service instance
 */
export function getStakingService(): StakingService {
  if (!stakingServiceInstance) {
    stakingServiceInstance = new StakingService();
  }
  return stakingServiceInstance;
}

/**
 * Reset staking service instance (for testing)
 */
export function resetStakingService(): void {
  stakingServiceInstance = null;
}

// Export default instance
export default getStakingService();
