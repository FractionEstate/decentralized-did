/**
 * Token cache types for Redux store
 */

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

export interface AddressTokenData {
  address: string;
  balance?: Balance;
  nfts?: NFT[];
  transactions?: Transaction[];
  lastUpdated: number;
  isLoading: boolean;
  error?: string;
}

export interface TokensCacheProps {
  addressData: Record<string, AddressTokenData>;
  currentAddress?: string;
}
