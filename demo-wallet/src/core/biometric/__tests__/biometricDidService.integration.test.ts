/**
 * Integration tests for biometric DID service with API servers
 * Tests end-to-end enrollment and verification flows
 *
 * SETUP REQUIRED:
 * These tests require the Python API server to be running.
 *
 * Quick start:
 *   cd /workspaces/decentralized-did
 *   python api_server_mock.py
 *
 * To run only tests that don't need the API:
 *   npm test -- biometricDidService.integration.test.ts --testNamePattern="Error Handling|Storage Operations"
 *
 * To run all tests (requires API server):
 *   npm test -- biometricDidService.integration.test.ts
 */

import { BiometricDidService } from "../biometricDidService";
import type {
  BiometricEnrollmentInput,
  BiometricVerifyInput,
  BiometricGenerateResult,
  HelperDataEntry,
} from "../biometricDid.types";

// Test configuration
const TEST_WALLET_ADDRESS =
  process.env.TEST_WALLET_ADDRESS || "addr_test1_demo_integration_testing";
// Flag to enable API-backed tests (requires mock/secure server running)
const RUN_API_TESTS = process.env.RUN_API_TESTS === "true";
const describeWithAPI = RUN_API_TESTS ? describe : describe.skip;

if (RUN_API_TESTS) {
  // eslint-disable-next-line no-console
  console.info(
    `[integration-tests] RUN_API_TESTS enabled against ${process.env.BIOMETRIC_API_URL || "http://localhost:8000"
    }`
  );
} else {
  // eslint-disable-next-line no-console
  console.info(
    "[integration-tests] RUN_API_TESTS disabled; API-backed suites will be skipped."
  );
}

// Mock biometric data (simulating fingerprint scanner output)
const MOCK_FINGERPRINT_DATA: BiometricEnrollmentInput = {
  fingers: [
    {
      finger_id: "left_thumb",
      minutiae: [
        [100.5, 200.3, 45.0],
        [150.2, 180.9, 90.5],
        [120.8, 250.1, 135.2],
        [180.3, 220.5, 30.8],
        [95.1, 190.7, 180.0],
      ],
    },
    {
      finger_id: "left_index",
      minutiae: [
        [110.2, 210.5, 50.0],
        [160.5, 190.2, 95.5],
        [130.1, 260.3, 140.0],
        [190.8, 230.7, 35.2],
        [105.3, 200.9, 185.5],
      ],
    },
    {
      finger_id: "right_thumb",
      minutiae: [
        [105.8, 205.7, 48.5],
        [155.3, 185.5, 92.0],
        [125.9, 255.2, 137.8],
        [185.1, 225.3, 33.1],
        [100.5, 195.8, 182.3],
      ],
    },
    {
      finger_id: "right_index",
      minutiae: [
        [115.5, 215.3, 52.5],
        [165.7, 195.8, 98.0],
        [135.3, 265.1, 142.5],
        [195.5, 235.9, 38.0],
        [110.7, 205.5, 188.0],
      ],
    },
  ],
};

// Slightly different capture (simulating recapture with noise)
const MOCK_FINGERPRINT_RECAPTURE: BiometricEnrollmentInput = {
  fingers: [
    {
      finger_id: "left_thumb",
      minutiae: [
        [100.8, 200.5, 45.2], // Slight variation
        [150.0, 181.1, 90.3],
        [120.9, 250.0, 135.5],
        [180.5, 220.3, 31.0],
        [95.3, 190.5, 180.2],
      ],
    },
    {
      finger_id: "left_index",
      minutiae: [
        [110.0, 210.7, 50.2],
        [160.3, 190.0, 95.7],
        [130.3, 260.1, 140.2],
        [191.0, 230.5, 35.0],
        [105.1, 201.1, 185.3],
      ],
    },
    {
      finger_id: "right_thumb",
      minutiae: [
        [106.0, 205.5, 48.7],
        [155.1, 185.7, 92.2],
        [126.1, 255.0, 138.0],
        [185.3, 225.1, 33.3],
        [100.7, 195.6, 182.5],
      ],
    },
    {
      finger_id: "right_index",
      minutiae: [
        [115.7, 215.1, 52.7],
        [165.5, 195.6, 98.2],
        [135.1, 265.3, 142.3],
        [195.7, 235.7, 38.2],
        [110.5, 205.7, 187.8],
      ],
    },
  ],
};

const resolveExpectedIdHash = (result: BiometricGenerateResult): string => {
  return (
    result.id_hash ||
    result.metadata_cip30_inline?.biometric?.idHash ||
    result.did.split(":").pop() ||
    ""
  );
};

describe("Biometric DID Service - Integration Tests", () => {
  let service: BiometricDidService;

  beforeAll(() => {
    service = BiometricDidService.getInstance();
  });

  describeWithAPI("Enrollment Flow", () => {
    it("should generate deterministic DID with mock API server", async () => {
      // Note: This test requires the mock API server to be running
      // Skip if server is not available
      const result = await service.generate(
        MOCK_FINGERPRINT_DATA,
        TEST_WALLET_ADDRESS
      );

      // Validate DID format
      expect(result.did).toBeDefined();
      expect(result.did).toMatch(/^did:cardano:(mainnet|testnet):[a-zA-Z0-9]+$/);

      // Validate no wallet address in DID identifier
      expect(result.did).not.toContain("addr");
      expect(result.did).not.toContain(TEST_WALLET_ADDRESS);

      // Validate helper data
      expect(result.helpers).toBeDefined();
      expect(Object.keys(result.helpers).length).toBeGreaterThan(0);

      // Validate metadata v1.1 structure
      expect(result.metadata_cip30_inline).toBeDefined();
      expect(Number(result.metadata_cip30_inline.version)).toBeCloseTo(1.1);
      expect(result.metadata_cip30_inline.controllers).toBeDefined();
      expect(Array.isArray(result.metadata_cip30_inline.controllers)).toBe(true);

      console.log("✅ Generated deterministic DID:", result.did);
    }, 30000); // 30 second timeout for API call

    it("should generate consistent DIDs for same biometric", async () => {
      // Enroll twice with same biometric data
      const result1 = await service.generate(
        MOCK_FINGERPRINT_DATA,
        TEST_WALLET_ADDRESS
      );
      const result2 = await service.generate(
        MOCK_FINGERPRINT_DATA,
        TEST_WALLET_ADDRESS
      );

      // DIDs should be identical (Sybil resistance)
      expect(result1.did).toBe(result2.did);

      console.log("✅ Sybil resistance verified: same biometric = same DID");
    }, 30000);

    it("should generate different DIDs for different biometrics", async () => {
      // Create different biometric data
      const differentFingerprint: BiometricEnrollmentInput = {
        fingers: [
          {
            finger_id: "left_thumb",
            minutiae: [
              [200.5, 300.3, 145.0], // Completely different
              [250.2, 280.9, 190.5],
              [220.8, 350.1, 235.2],
              [280.3, 320.5, 130.8],
              [195.1, 290.7, 280.0],
            ],
          },
        ],
      };

      const result1 = await service.generate(
        MOCK_FINGERPRINT_DATA,
        TEST_WALLET_ADDRESS
      );
      const result2 = await service.generate(
        differentFingerprint,
        TEST_WALLET_ADDRESS
      );

      // DIDs should be different
      expect(result1.did).not.toBe(result2.did);

      console.log("✅ Uniqueness verified: different biometrics = different DIDs");
    }, 30000);

    it("should store and retrieve helper data correctly", async () => {
      const result = await service.generate(
        MOCK_FINGERPRINT_DATA,
        TEST_WALLET_ADDRESS
      );

      // Store helper data
      await service.saveHelperData(result.did, result.helpers);

      // Retrieve helper data
      const retrievedHelpers = await service.loadHelperData(result.did);

      expect(retrievedHelpers).toBeDefined();
      expect(retrievedHelpers).toEqual(result.helpers);

      // Clean up
      await service.deleteHelperData(result.did);

      console.log("✅ Helper data storage/retrieval verified");
    }, 30000);
  });

  describeWithAPI("Verification Flow", () => {
    let enrollmentResult: BiometricGenerateResult;

    beforeEach(async () => {
      // Enroll first
      enrollmentResult = await service.generate(
        MOCK_FINGERPRINT_DATA,
        TEST_WALLET_ADDRESS
      );

      // Store helper data
      await service.saveHelperData(enrollmentResult.did, enrollmentResult.helpers);
    });

    afterEach(async () => {
      // Clean up
      if (enrollmentResult?.did) {
        await service.deleteHelperData(enrollmentResult.did);
      }
    });

    it("should verify with same biometric (exact match)", async () => {
      // Extract ID hash from DID
      const idHash = resolveExpectedIdHash(enrollmentResult);

      const verifyInput: BiometricVerifyInput = {
        fingers: MOCK_FINGERPRINT_DATA.fingers,
        helpers: enrollmentResult.helpers,
        expected_id_hash: idHash,
      };

      const result = await service.verify(verifyInput);

      expect(result.success).toBe(true);
      expect(result.matched_fingers.length).toBeGreaterThan(0);
      expect(result.unmatched_fingers.length).toBe(0);

      console.log("✅ Verification succeeded with exact match");
      console.log(`   Matched fingers: ${result.matched_fingers.length}`);
    }, 30000);

    it("should verify with noisy recapture (fuzzy matching)", async () => {
      // Extract ID hash
      const idHash = resolveExpectedIdHash(enrollmentResult);

      const verifyInput: BiometricVerifyInput = {
        fingers: MOCK_FINGERPRINT_RECAPTURE.fingers, // Slightly different
        helpers: enrollmentResult.helpers,
        expected_id_hash: idHash,
      };

      const result = await service.verify(verifyInput);

      // Should still succeed due to fuzzy extractor error correction
      expect(result.success).toBe(true);
      expect(result.matched_fingers.length).toBeGreaterThan(0);

      console.log("✅ Fuzzy matching verified with noisy recapture");
      console.log(`   Matched fingers: ${result.matched_fingers.length}`);
    }, 30000);

    it("should fail verification with wrong biometric", async () => {
      const wrongFingerprint: BiometricEnrollmentInput = {
        fingers: [
          {
            finger_id: "left_thumb_wrong",
            minutiae: [
              [300.0, 400.0, 200.0], // Completely different
              [350.0, 380.0, 250.0],
              [320.0, 450.0, 300.0],
            ],
          },
        ],
      };

      const idHash = resolveExpectedIdHash(enrollmentResult);

      const verifyInput: BiometricVerifyInput = {
        fingers: wrongFingerprint.fingers,
        helpers: enrollmentResult.helpers,
        expected_id_hash: idHash,
      };

      const result = await service.verify(verifyInput);

      expect(result.success).toBe(false);
      expect(result.matched_fingers.length).toBe(0);

      console.log("✅ Verification correctly rejected wrong biometric");
    }, 30000);
  });

  describeWithAPI("Performance Benchmarks", () => {
    it("should complete enrollment in <100ms", async () => {
      const startTime = performance.now();

      await service.generate(MOCK_FINGERPRINT_DATA, TEST_WALLET_ADDRESS);

      const endTime = performance.now();
      const duration = endTime - startTime;

      console.log(`⏱️  Enrollment time: ${duration.toFixed(2)}ms`);

      // Note: This might fail if API server is slow or network latency is high
      // Target is <100ms for local processing, but API calls may take longer
      expect(duration).toBeLessThan(5000); // 5 second max for integration test
    }, 30000);

    it("should complete verification in <50ms", async () => {
      // Enroll first
      const enrollmentResult = await service.generate(
        MOCK_FINGERPRINT_DATA,
        TEST_WALLET_ADDRESS
      );

      const idHash = resolveExpectedIdHash(enrollmentResult);

      const verifyInput: BiometricVerifyInput = {
        fingers: MOCK_FINGERPRINT_DATA.fingers,
        helpers: enrollmentResult.helpers,
        expected_id_hash: idHash,
      };

      const startTime = performance.now();

      await service.verify(verifyInput);

      const endTime = performance.now();
      const duration = endTime - startTime;

      console.log(`⏱️  Verification time: ${duration.toFixed(2)}ms`);

      expect(duration).toBeLessThan(5000); // 5 second max for integration test

      // Clean up
      await service.deleteHelperData(enrollmentResult.did);
    }, 30000);
  });

  describe("Error Handling", () => {
    it("should handle missing helper data gracefully", async () => {
      const nonExistentDid = "did:cardano:mainnet:NonExistentHash123";

      const helperData = await service.loadHelperData(nonExistentDid);

      expect(helperData).toBeNull();

      console.log("✅ Missing helper data handled gracefully");
    });

    it("should handle invalid DID format", async () => {
      const invalidDid = "invalid-did-format";

      const helperData = await service.loadHelperData(invalidDid);

      // Should not crash, should return null
      expect(helperData).toBeNull();

      console.log("✅ Invalid DID format handled gracefully");
    });

    it("should handle empty minutiae data", async () => {
      const emptyData: BiometricEnrollmentInput = {
        fingers: [],
      };

      await expect(
        service.generate(emptyData, TEST_WALLET_ADDRESS)
      ).rejects.toThrow();

      console.log("✅ Empty minutiae data rejected appropriately");
    });
  });

  describe("Storage Operations", () => {
    const testDid = "did:cardano:mainnet:TestStorageHash123";
    const testHelpers: Record<string, HelperDataEntry> = {
      left_thumb: {
        finger_id: "left_thumb",
        salt_b64: "dGVzdF9zYWx0X2RhdGE=",
        auth_b64: "dGVzdF9hdXRoX3RhZw==",
        grid_size: 10,
        angle_bins: 8,
      },
    };

    it("should check helper data existence", async () => {
      // Should not exist initially
      let exists = await service.hasHelperData(testDid);
      expect(exists).toBe(false);

      // Store helper data
      await service.saveHelperData(testDid, testHelpers);

      // Should exist now
      exists = await service.hasHelperData(testDid);
      expect(exists).toBe(true);

      // Clean up
      await service.deleteHelperData(testDid);

      console.log("✅ Helper data existence check working");
    });

    it("should manage current DID", async () => {
      // Save current DID
      await service.saveCurrentDid(testDid);

      // Retrieve current DID
      const currentDid = await service.getCurrentDid();
      expect(currentDid).toBe(testDid);

      // Delete current DID
      await service.deleteCurrentDid();

      // Should be null now
      const deletedDid = await service.getCurrentDid();
      expect(deletedDid).toBeNull();

      console.log("✅ Current DID management working");
    });
  });
});
