/**
 * CIP-30 Type Definitions
 * Cardano dApp-Wallet Web Bridge
 *
 * Spec: https://cips.cardano.org/cips/cip30/
 */

/**
 * Paginate type for paginated results
 */
export interface Paginate {
  page: number;
  limit: number;
}

/**
 * CBOR hex-encoded data
 */
export type Cbor<T> = string;

/**
 * Address in CBOR format
 */
export type Address = Cbor<string>;

/**
 * Transaction in CBOR format
 */
export type Transaction = Cbor<string>;

/**
 * Data signature result from signData()
 */
export interface DataSignature {
  signature: string; // CBOR hex
  key: string; // CBOR hex - public key
}

/**
 * Collateral UTxO
 */
export interface Collateral {
  amount: string; // Lovelace amount
  txHash: string;
  outputIndex: number;
}

/**
 * Network ID
 * 0 = testnet
 * 1 = mainnet
 */
export type NetworkId = 0 | 1;

/**
 * API Version
 */
export interface ApiVersion {
  major: number;
  minor: number;
  patch: number;
}

/**
 * Wallet API error codes
 */
export enum APIErrorCode {
  InvalidRequest = -1,
  InternalError = -2,
  Refused = -3,
  AccountChange = -4,
  DataSignError = 1,
  ProofGeneration = 2,
  AddressNotPOS = 3,
  UserDeclined = 4,
  TxSendError = 5,
}

/**
 * Wallet API error
 */
export class APIError extends Error {
  code: APIErrorCode;
  info: string;

  constructor(code: APIErrorCode, info: string) {
    super(info);
    this.code = code;
    this.info = info;
    this.name = "APIError";
  }
}

/**
 * Transaction send options
 */
export interface TxSendOptions {
  returnTxHash?: boolean;
}

/**
 * CIP-95 DRep public key
 */
export interface DRepKey {
  keyHash: string; // hex
  publicKey: string; // CBOR hex
}

/**
 * CIP-95 Registered pub stake keys
 */
export interface RegisteredPubStakeKey {
  stakeKeyHash: string; // hex
  publicKey: string; // CBOR hex
}
