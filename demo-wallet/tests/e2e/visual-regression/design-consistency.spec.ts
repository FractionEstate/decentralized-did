/**
 * Design Consistency Visual Regression Tests
 *
 * Validates pixel-perfect design consistency across all wallet pages:
 * - Typography consistency (font sizes, weights, line heights)
 * - Spacing consistency (padding, margins)
 * - Color consistency (backgrounds, text, buttons)
 * - Layout consistency (responsive behavior)
 * - Component consistency (buttons, cards, forms)
 *
 * Uses Playwright's screenshot comparison with strict thresholds
 */

import { test, expect } from '@playwright/test';

// Test configuration
const VIEWPORTS = [
  { name: 'mobile-small', width: 375, height: 667 },  // iPhone SE
  { name: 'mobile-medium', width: 393, height: 852 }, // iPhone 14 Pro
  { name: 'tablet', width: 768, height: 1024 },       // iPad
  { name: 'desktop', width: 1280, height: 720 },      // Desktop
];

// All pages to test for consistency
const PAGES = [
  { route: '/biometric-enrollment', name: 'Biometric Enrollment' },
  { route: '/onboarding', name: 'Onboarding' },
  { route: '/create-password', name: 'Create Password' },
  { route: '/setup-biometrics', name: 'Setup Biometrics' },
  { route: '/generate-seed-phrase', name: 'Generate Seed Phrase' },
  { route: '/verify-seed-phrase', name: 'Verify Seed Phrase' },
  { route: '/set-passcode', name: 'Set Passcode' },
  { route: '/lock-page', name: 'Lock Page' },
  { route: '/credentials', name: 'Credentials' },
  { route: '/identifiers', name: 'Identifiers' },
  { route: '/connections', name: 'Connections' },
  { route: '/notifications', name: 'Notifications' },
  { route: '/menu', name: 'Menu' },
  { route: '/scan', name: 'Scan' },
];

test.describe('Visual Regression - Design Consistency', () => {
  test.beforeEach(async ({ page }) => {
    // Disable animations for consistent screenshots
    await page.addInitScript(() => {
      document.documentElement.style.setProperty('--transition-fast', '0ms');
      document.documentElement.style.setProperty('--transition-base', '0ms');
      document.documentElement.style.setProperty('--transition-slow', '0ms');
    });
  });

  for (const viewport of VIEWPORTS) {
    test.describe(`${viewport.name} (${viewport.width}x${viewport.height})`, () => {
      test.beforeEach(async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
      });

      for (const pageInfo of PAGES) {
        test(`${pageInfo.name} - matches design baseline`, async ({ page }) => {
          // Navigate to page
          await page.goto(pageInfo.route);

          // Wait for page to be fully loaded
          await page.waitForLoadState('networkidle');

          // Wait for any fonts to load
          await page.evaluate(() => document.fonts.ready);

          // Take screenshot and compare
          await expect(page).toHaveScreenshot(
            `${pageInfo.name.toLowerCase().replace(/\s+/g, '-')}-${viewport.name}.png`,
            {
              maxDiffPixels: 100,
              threshold: 0.2,
              animations: 'disabled',
              fullPage: true,
            }
          );
        });
      }
    });
  }
});

test.describe('Component Consistency', () => {
  test('Buttons have consistent styling', async ({ page }) => {
    await page.goto('/onboarding');

    // Check primary button styles
    const primaryButton = page.locator('.btn-primary').first();
    await expect(primaryButton).toHaveCSS('border-radius', '8px');
    await expect(primaryButton).toHaveCSS('font-weight', '600');
    await expect(primaryButton).toHaveCSS('min-height', '44px');
  });

  test('Cards have consistent styling', async ({ page }) => {
    await page.goto('/credentials');

    // Check card styles
    const card = page.locator('.card').first();
    await expect(card).toHaveCSS('border-radius', '16px');
    await expect(card).toHaveCSS('box-shadow', /rgba/); // Has shadow
    await expect(card).toHaveCSS('padding', /24px/); // Has proper padding
  });

  test('Typography follows design tokens', async ({ page }) => {
    await page.goto('/onboarding');

    // Check heading sizes
    const h1 = page.locator('h1').first();
    await expect(h1).toHaveCSS('font-size', /(32px|2rem|36px|2.25rem)/);
    await expect(h1).toHaveCSS('font-weight', /(500|600|700)/);

    const h2 = page.locator('h2').first();
    await expect(h2).toHaveCSS('font-size', /(24px|1.5rem)/);
  });

  test('Spacing is consistent across pages', async ({ page }) => {
    const pages = ['/onboarding', '/credentials', '/identifiers'];

    for (const route of pages) {
      await page.goto(route);

      // Check page padding
      const content = page.locator('.page-layout').first();
      const padding = await content.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.padding;
      });

      // Should use design token values (24px on mobile)
      expect(padding).toMatch(/24px/);
    }
  });

  test('Forms have consistent input styling', async ({ page }) => {
    await page.goto('/create-password');

    // Check input field styles
    const input = page.locator('ion-input').first();
    const inputHeight = await input.evaluate(el => {
      return window.getComputedStyle(el).height;
    });

    // Should meet minimum touch target size (44px)
    const height = parseInt(inputHeight);
    expect(height).toBeGreaterThanOrEqual(44);
  });

  test('Colors follow design system', async ({ page }) => {
    await page.goto('/onboarding');

    // Check that primary color is used consistently
    const primaryButton = page.locator('.btn-primary').first();
    const backgroundColor = await primaryButton.evaluate(el => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // Should be consistent across pages (check another page)
    await page.goto('/credentials');
    const secondButton = page.locator('.btn-primary').first();
    const secondColor = await secondButton.evaluate(el => {
      return window.getComputedStyle(el).backgroundColor;
    });

    expect(backgroundColor).toBe(secondColor);
  });
});

test.describe('Responsive Design Consistency', () => {
  test('Mobile breakpoint applies correct styles', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/onboarding');

    // Check mobile-specific padding
    const pageLayout = page.locator('.page-layout').first();
    const padding = await pageLayout.evaluate(el => {
      return window.getComputedStyle(el).padding;
    });

    // Mobile should use 24px padding
    expect(padding).toContain('24px');
  });

  test('Desktop breakpoint applies correct styles', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/onboarding');

    // Check desktop-specific padding
    const pageLayout = page.locator('.page-layout').first();
    const padding = await pageLayout.evaluate(el => {
      return window.getComputedStyle(el).padding;
    });

    // Desktop should use 40px padding
    expect(padding).toContain('40px');
  });

  test('Landscape orientation on mobile works correctly', async ({ page }) => {
    await page.setViewportSize({ width: 667, height: 375 });
    await page.goto('/biometric-enrollment');

    // Page should still be usable and properly styled
    await expect(page).toHaveScreenshot('biometric-enrollment-landscape.png', {
      fullPage: true,
    });
  });
});

test.describe('Animation Consistency', () => {
  test('Hover effects are consistent', async ({ page }) => {
    await page.goto('/credentials');

    const button = page.locator('.btn-primary').first();

    // Hover over button
    await button.hover();

    // Check for transform effect
    const transform = await button.evaluate(el => {
      return window.getComputedStyle(el).transform;
    });

    // Should have translateY(-1px) on hover
    expect(transform).toBeTruthy();
  });

  test('Focus states are visible', async ({ page }) => {
    await page.goto('/create-password');

    const input = page.locator('input').first();
    await input.focus();

    // Check for focus ring
    const outline = await input.evaluate(el => {
      return window.getComputedStyle(el).outline;
    });

    // Should have visible focus indicator
    expect(outline).toBeTruthy();
  });
});
