import { config as loadEnv } from "dotenv";
import fs from "fs";
import path from "path";

const repoRootEnv = path.resolve(__dirname, "../../.env.test");
const customEnv = process.env.WALLET_TEST_ENV;
const envPath = customEnv ? path.resolve(customEnv) : repoRootEnv;

if (fs.existsSync(envPath)) {
  loadEnv({ path: envPath });
  // eslint-disable-next-line no-console
  console.info(`[biometric-tests] Loaded environment from ${envPath}`);
} else {
  // eslint-disable-next-line no-console
  console.warn(`[biometric-tests] Missing ${envPath}, using existing process.env values.`);
}

const ensureEnv = (key: string, value: string) => {
  if (!process.env[key] || process.env[key] === "") {
    process.env[key] = value;
  }
};

const secureApiUrl = process.env.SECURE_API_URL;
const mockApiUrl = process.env.MOCK_API_URL;

if (!process.env.BIOMETRIC_API_URL || process.env.BIOMETRIC_API_URL === "") {
  ensureEnv("BIOMETRIC_API_URL", secureApiUrl || mockApiUrl || "http://localhost:8000");
}

if (!process.env.BIOMETRIC_AUTH_URL || process.env.BIOMETRIC_AUTH_URL === "") {
  if (secureApiUrl) {
    ensureEnv("BIOMETRIC_AUTH_URL", secureApiUrl);
  }
}

if (!process.env.BIOMETRIC_API_KEY || process.env.BIOMETRIC_API_KEY === "") {
  const derivedKey = process.env.BIOMETRIC_API_KEY || process.env.API_KEY || process.env.API_SECRET_KEY || "";
  process.env.BIOMETRIC_API_KEY = derivedKey;
}

ensureEnv("RUN_API_TESTS", "false");
ensureEnv("TEST_WALLET_ADDRESS", "addr_test1_demo_integration_testing");
