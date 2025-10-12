import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration for Biometric DID Demo Wallet E2E Tests
 *
 * See https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Test directory
  testDir: './tests/e2e',

  // Test file pattern
  testMatch: '**/*.spec.ts',

  // Maximum time one test can run for
  timeout: 60 * 1000, // 60 seconds

  // Maximum time entire test suite can run
  globalTimeout: 15 * 60 * 1000, // 15 minutes

  // Fail fast on first error
  fullyParallel: false,

  // Number of retries on CI
  retries: process.env.CI ? 2 : 0,

  // Number of workers (parallel tests)
  workers: process.env.CI ? 2 : 1,

  // Reporter to use
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list']
  ],

  // Shared settings for all projects
  use: {
    // Base URL for navigation
    baseURL: process.env.DEMO_WALLET_URL || 'http://localhost:3003',

    // Backend API URL
    extraHTTPHeaders: {
      'X-Test-API-URL': process.env.API_URL || 'http://localhost:8000'
    },

    // Screenshots
    screenshot: 'only-on-failure',

    // Videos
    video: 'retain-on-failure',

    // Traces
    trace: 'on-first-retry',

    // Browser context options
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,

    // Timeouts
    actionTimeout: 10 * 1000, // 10 seconds
    navigationTimeout: 30 * 1000, // 30 seconds
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    // Uncomment to test on Firefox and WebKit
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },

    // Mobile viewports
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },
  ],

  // Development server configuration
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3003',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000, // 2 minutes
  },

  // Output directories
  outputDir: 'test-results/',
});
