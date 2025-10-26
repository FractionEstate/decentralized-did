import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration for Biometric DID Demo Wallet E2E Tests
 *
 * Enhanced with:
 * - Visual regression testing (screenshot comparison)
 * - Mobile device emulation
 * - Comprehensive browser coverage
 * - Accessibility testing setup
 *
 * See https://playwright.dev/docs/test-configuration
 */
const availableProjects = [
  // Desktop Browsers
  {
    name: 'chromium',
    use: {
      ...devices['Desktop Chrome'],
    },
  },
  {
    name: 'firefox',
    use: {
      ...devices['Desktop Firefox'],
    },
  },
  {
    name: 'webkit',
    use: {
      ...devices['Desktop Safari'],
    },
  },

  // Mobile Devices
  {
    name: 'iphone-12',
    use: {
      ...devices['iPhone 12'],
    },
  },
  {
    name: 'iphone-se',
    use: {
      ...devices['iPhone SE'],
    },
  },
  {
    name: 'pixel-5',
    use: {
      ...devices['Pixel 5'],
    },
  },
  {
    name: 'ipad-pro',
    use: {
      ...devices['iPad Pro'],
    },
  },
];

const parseBrowserSelection = () => {
  const selection = process.env.PLAYWRIGHT_BROWSERS;
  if (!selection) {
    return availableProjects;
  }

  const tokens = selection
    .split(',')
    .map(token => token.trim().toLowerCase())
    .filter(Boolean);

  const filtered = availableProjects.filter(project => tokens.includes(project.name.toLowerCase()));

  if (filtered.length === 0) {
    return availableProjects.filter(project => project.name === 'chromium');
  }

  return filtered;
};

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

    // Screenshots (enable for visual regression)
    screenshot: 'on',

    // Videos (record all tests)
    video: 'on',

    // Traces (detailed debugging)
    trace: 'on',

    // Browser context options
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,

    // Timeouts
    actionTimeout: 10 * 1000, // 10 seconds
    navigationTimeout: 30 * 1000, // 30 seconds

    // Animations (disable for consistent screenshots)
    hasTouch: false,
    isMobile: false,

    // Locale and timezone for consistent testing
    locale: 'en-US',
    timezoneId: 'UTC',
  },

  // Visual comparison settings
  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 100,
      threshold: 0.2,
      animations: 'disabled',
    },
  },

  // Configure projects for major browsers
  projects: parseBrowserSelection(),

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
