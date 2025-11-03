/**
 * Token Service for Cardano blockchain
 * 
 * Provides API client for token management operations including:
 * - ADA balance queries
 * - Native asset tracking
 * - NFT metadata fetching (CIP-25/CIP-68)
 * - Transaction history
 */

// API base URL - configurable via environment
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8002";

// Type definitions
export interface Asset {
  policy_id: string;
  asset_name: string;
  asset_name_ascii?: string;
  fingerprint?: string;
  quantity: string;
  decimals: number;
  display_quantity: string;
  full_name: string;
}

export interface NFTMetadata {
  name?: string;
  image?: string;
  description?: string;
  media_type?: string;
  attributes?: Record<string, any>;
}

export interface NFT {
  asset: Asset;
  metadata?: NFTMetadata;
  display_name: string;
  is_cip68: boolean;
}

export interface Balance {
  ada_lovelace: string;
  ada_amount: string;
  total_assets: number;
  assets: Asset[];
}

export interface Transaction {
  tx_hash: string;
  block_time?: number;
  block_height?: number;
  epoch?: number;
  fee?: string;
  fee_ada?: string;
}

export interface TokenServiceError {
  message: string;
  status?: number;
  detail?: string;
}

/**
 * Token Service class for managing Cardano tokens
 */
export class TokenService {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || API_BASE_URL;
  }

  /**
   * Fetch balance for a Cardano address
   * @param address Cardano payment or stake address
   * @returns Balance with ADA and native assets
   */
  async getBalance(address: string): Promise<Balance> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/tokens/balance/${address}`,
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
      console.error(`Failed to get balance for ${address}:`, error);
      throw this.handleError(error);
    }
  }

  /**
   * Fetch NFTs owned by an address
   * @param address Cardano address
   * @returns List of NFTs with metadata
   */
  async getNFTs(address: string): Promise<NFT[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/tokens/nfts/${address}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          signal: AbortSignal.timeout(15000), // 15s timeout for metadata
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to get NFTs for ${address}:`, error);
      throw this.handleError(error);
    }
  }

  /**
   * Fetch transaction history for an address
   * @param address Cardano address
   * @param limit Maximum number of transactions (1-100)
   * @param offset Pagination offset
   * @returns List of transactions
   */
  async getTransactionHistory(
    address: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<Transaction[]> {
    try {
      const params = new URLSearchParams({
        limit: Math.min(Math.max(limit, 1), 100).toString(),
        offset: Math.max(offset, 0).toString(),
      });

      const response = await fetch(
        `${this.baseUrl}/api/tokens/history/${address}?${params}`,
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
        `Failed to get transaction history for ${address}:`,
        error
      );
      throw this.handleError(error);
    }
  }

  /**
   * Check if token service is healthy
   * @returns Health status
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/tokens/health`, {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Token service health check failed:", error);
      throw this.handleError(error);
    }
  }

  /**
   * Handle and normalize errors
   */
  private handleError(error: any): TokenServiceError {
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
   * Format ADA amount from lovelace
   * @param lovelace Amount in lovelace
   * @returns Formatted ADA amount string
   */
  static formatADA(lovelace: string): string {
    const ada = Number(lovelace) / 1_000_000;
    return ada.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 6,
    });
  }

  /**
   * Format asset quantity with decimals
   * @param quantity Raw quantity string
   * @param decimals Number of decimal places
   * @returns Formatted quantity string
   */
  static formatAssetQuantity(quantity: string, decimals: number): string {
    if (decimals === 0) {
      return Number(quantity).toLocaleString();
    }
    const divisor = Math.pow(10, decimals);
    const amount = Number(quantity) / divisor;
    return amount.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  /**
   * Format timestamp to readable date
   * @param timestamp Unix timestamp in seconds
   * @returns Formatted date string
   */
  static formatDate(timestamp: number): string {
    return new Date(timestamp * 1000).toLocaleString();
  }

  /**
   * Truncate asset name for display
   * @param name Asset name
   * @param maxLength Maximum length
   * @returns Truncated name
   */
  static truncateName(name: string, maxLength: number = 16): string {
    if (name.length <= maxLength) {
      return name;
    }
    return name.substring(0, maxLength) + "...";
  }
}

// Singleton instance
let tokenServiceInstance: TokenService | null = null;

/**
 * Get singleton token service instance
 */
export function getTokenService(): TokenService {
  if (!tokenServiceInstance) {
    tokenServiceInstance = new TokenService();
  }
  return tokenServiceInstance;
}

/**
 * Reset token service instance (for testing)
 */
export function resetTokenService(): void {
  tokenServiceInstance = null;
}

// Export default instance
export default getTokenService();
