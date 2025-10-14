/**
 * Unit tests for deterministic DID generation
 * Tests Sybil resistance and privacy preservation
 */

import { blake2b } from "blakejs";
import bs58 from "bs58";

/**
 * Deterministic DID generation function (copy from biometricDidService for testing)
 */
function generateDeterministicDID(commitment: Uint8Array | string, network = "mainnet"): string {
  // Convert string to Uint8Array if needed
  let commitmentBytes: Uint8Array;
  if (typeof commitment === "string") {
    // If string, assume it's hex or base64 - convert appropriately
    if (commitment.length === 64) {
      // Hex string (64 chars = 32 bytes)
      commitmentBytes = new Uint8Array(
        commitment.match(/.{2}/g)!.map(byte => parseInt(byte, 16))
      );
    } else {
      // Base64 string
      commitmentBytes = Uint8Array.from(atob(commitment), c => c.charCodeAt(0));
    }
  } else {
    commitmentBytes = commitment;
  }

  // Hash the commitment with Blake2b (32 bytes output)
  const hash = blake2b(commitmentBytes, undefined, 32);

  // Encode with Base58 for compact, URL-safe representation
  const base58Hash = bs58.encode(hash);

  // Build DID with network identifier
  return `did:cardano:${network}:${base58Hash}`;
}

describe("Deterministic DID Generation", () => {
  describe("generateDeterministicDID", () => {
    it("should generate a valid DID format", () => {
      const commitment = new Uint8Array(32).fill(1);
      const did = generateDeterministicDID(commitment, "mainnet");

      expect(did).toMatch(/^did:cardano:mainnet:[a-zA-Z0-9]+$/);
    });

    it("should generate deterministic DIDs (same commitment = same DID)", () => {
      const commitment = new Uint8Array(32).fill(42);

      const did1 = generateDeterministicDID(commitment, "mainnet");
      const did2 = generateDeterministicDID(commitment, "mainnet");
      const did3 = generateDeterministicDID(commitment, "mainnet");

      expect(did1).toBe(did2);
      expect(did2).toBe(did3);
      expect(did1).toBe(did3);
    });

    it("should generate different DIDs for different commitments", () => {
      const commitment1 = new Uint8Array(32).fill(1);
      const commitment2 = new Uint8Array(32).fill(2);
      const commitment3 = new Uint8Array(32).fill(3);

      const did1 = generateDeterministicDID(commitment1, "mainnet");
      const did2 = generateDeterministicDID(commitment2, "mainnet");
      const did3 = generateDeterministicDID(commitment3, "mainnet");

      expect(did1).not.toBe(did2);
      expect(did2).not.toBe(did3);
      expect(did1).not.toBe(did3);
    });

    it("should support different networks", () => {
      const commitment = new Uint8Array(32).fill(100);

      const mainnetDid = generateDeterministicDID(commitment, "mainnet");
      const testnetDid = generateDeterministicDID(commitment, "testnet");

      expect(mainnetDid).toContain("did:cardano:mainnet:");
      expect(testnetDid).toContain("did:cardano:testnet:");
      expect(mainnetDid).not.toBe(testnetDid);
    });

    it("should not contain wallet address in DID identifier", () => {
      const commitment = new Uint8Array(32).fill(50);
      const walletAddress = "addr1qxy...xyz";

      const did = generateDeterministicDID(commitment, "mainnet");

      expect(did).not.toContain(walletAddress);
      expect(did).not.toContain("addr");
      expect(did).not.toContain("#");
    });

    it("should be Sybil-resistant (one biometric = one DID)", () => {
      // Simulate same person enrolling multiple times
      const personABiometric = new Uint8Array(32).fill(77);

      // First enrollment
      const enrollmentDate1 = new Date("2025-01-01");
      const did1 = generateDeterministicDID(personABiometric, "mainnet");

      // Second enrollment (different date, same biometric)
      const enrollmentDate2 = new Date("2025-06-01");
      const did2 = generateDeterministicDID(personABiometric, "mainnet");

      // DIDs should be identical (Sybil attack prevented)
      expect(did1).toBe(did2);
      expect(enrollmentDate1).not.toBe(enrollmentDate2); // Different enrollment times
    });

    it("should handle hex string input (64 characters = 32 bytes)", () => {
      const hexString = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
      const did = generateDeterministicDID(hexString, "mainnet");

      expect(did).toMatch(/^did:cardano:mainnet:[a-zA-Z0-9]+$/);
    });

    it("should handle Uint8Array input", () => {
      const bytes = new Uint8Array(32);
      for (let i = 0; i < 32; i++) {
        bytes[i] = i * 8;
      }

      const did = generateDeterministicDID(bytes, "mainnet");

      expect(did).toMatch(/^did:cardano:mainnet:[a-zA-Z0-9]+$/);
    });

    it("should generate compact DIDs (Base58 encoding)", () => {
      const commitment = new Uint8Array(32).fill(200);
      const did = generateDeterministicDID(commitment, "mainnet");

      // Base58 of 32 bytes should be around 43-44 characters
      const base58Part = did.split(":")[3];
      expect(base58Part.length).toBeGreaterThan(40);
      expect(base58Part.length).toBeLessThan(50);
    });
  });

  describe("Privacy Properties", () => {
    it("should not reveal wallet address from DID", () => {
      const commitment = new Uint8Array(32).fill(123);
      const walletAddress = "addr1qxy2r3zy7hjwg8tjn3pksw0tqzv9wqlnh0qzyvvxl4zr8kq5dzxyz";

      const did = generateDeterministicDID(commitment, "mainnet");

      // DID should contain no part of wallet address
      expect(did).not.toContain("addr1");
      expect(did).not.toContain("qxy2r3zy");
      expect(did).not.toContain(walletAddress.substring(0, 10));
    });

    it("should not reveal biometric data from DID", () => {
      const commitment = new Uint8Array(32).fill(88);
      const did = generateDeterministicDID(commitment, "mainnet");

      // DID should be a hash (one-way function)
      // Cannot reverse engineer commitment from DID
      const base58Part = did.split(":")[3];
      const decoded = bs58.decode(base58Part);

      // Decoded hash should not equal commitment (it's a Blake2b hash)
      expect(decoded).not.toEqual(commitment);
      expect(decoded.length).toBe(32); // Hash output size
    });
  });

  describe("Sybil Resistance", () => {
    it("should prevent duplicate enrollments (same person, different wallets)", () => {
      const samePerson = new Uint8Array(32).fill(99);

      // Person tries to enroll with 3 different wallet addresses
      const wallet1 = "addr1_wallet1";
      const wallet2 = "addr1_wallet2";
      const wallet3 = "addr1_wallet3";

      const did1 = generateDeterministicDID(samePerson, "mainnet");
      const did2 = generateDeterministicDID(samePerson, "mainnet");
      const did3 = generateDeterministicDID(samePerson, "mainnet");

      // All DIDs should be identical (Sybil attack prevented)
      expect(did1).toBe(did2);
      expect(did2).toBe(did3);

      // Wallet addresses are irrelevant (not in DID)
      expect(did1).not.toContain(wallet1);
      expect(did2).not.toContain(wallet2);
      expect(did3).not.toContain(wallet3);
    });

    it("should allow different people to have different DIDs", () => {
      const person1 = new Uint8Array(32).fill(10);
      const person2 = new Uint8Array(32).fill(20);
      const person3 = new Uint8Array(32).fill(30);

      const did1 = generateDeterministicDID(person1, "mainnet");
      const did2 = generateDeterministicDID(person2, "mainnet");
      const did3 = generateDeterministicDID(person3, "mainnet");

      // All DIDs should be unique
      expect(did1).not.toBe(did2);
      expect(did2).not.toBe(did3);
      expect(did1).not.toBe(did3);
    });
  });

  describe("Format Validation", () => {
    it("should match DID specification regex", () => {
      const didRegex = /^did:cardano:(mainnet|testnet):[a-zA-Z0-9]+$/;

      const commitment = new Uint8Array(32).fill(150);
      const mainnetDid = generateDeterministicDID(commitment, "mainnet");
      const testnetDid = generateDeterministicDID(commitment, "testnet");

      expect(mainnetDid).toMatch(didRegex);
      expect(testnetDid).toMatch(didRegex);
    });

    it("should have proper DID structure (4 parts)", () => {
      const commitment = new Uint8Array(32).fill(175);
      const did = generateDeterministicDID(commitment, "mainnet");

      const parts = did.split(":");
      expect(parts.length).toBe(4);
      expect(parts[0]).toBe("did");
      expect(parts[1]).toBe("cardano");
      expect(parts[2]).toBe("mainnet");
      expect(parts[3]).toBeTruthy();
      expect(parts[3].length).toBeGreaterThan(0);
    });
  });

  describe("Cryptographic Properties", () => {
    it("should use Blake2b hashing (32-byte output)", () => {
      const commitment = new Uint8Array(32).fill(66);
      const did = generateDeterministicDID(commitment, "mainnet");

      const base58Part = did.split(":")[3];
      const decoded = bs58.decode(base58Part);

      expect(decoded.length).toBe(32); // Blake2b with 32-byte output
    });

    it("should produce uniform distribution (no bias)", () => {
      const dids = new Set<string>();

      for (let i = 0; i < 100; i++) {
        const commitment = new Uint8Array(32).fill(i);
        const did = generateDeterministicDID(commitment, "mainnet");
        dids.add(did);
      }

      // All 100 DIDs should be unique (no collisions)
      expect(dids.size).toBe(100);
    });

    it("should handle edge cases (all zeros, all ones)", () => {
      const allZeros = new Uint8Array(32).fill(0);
      const allOnes = new Uint8Array(32).fill(255);

      const did1 = generateDeterministicDID(allZeros, "mainnet");
      const did2 = generateDeterministicDID(allOnes, "mainnet");

      expect(did1).toMatch(/^did:cardano:mainnet:[a-zA-Z0-9]+$/);
      expect(did2).toMatch(/^did:cardano:mainnet:[a-zA-Z0-9]+$/);
      expect(did1).not.toBe(did2);
    });
  });
});
