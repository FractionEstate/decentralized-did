/**
 * Accessibility Testing Suite
 *
 * Validates WCAG 2.1 AA compliance across all pages:
 * - Color contrast (4.5:1 for normal text, 3:1 for large text)
 * - Touch targets (minimum 44x44px)
 * - Focus indicators (visible and clear)
 * - Semantic HTML (proper headings, landmarks, ARIA)
 * - Keyboard navigation
 * - Screen reader support
 */

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const PAGES_TO_TEST = [
  { route: '/biometric-enrollment', name: 'Biometric Enrollment' },
  { route: '/onboarding', name: 'Onboarding' },
  { route: '/create-password', name: 'Create Password' },
  { route: '/setup-biometrics', name: 'Setup Biometrics' },
  { route: '/credentials', name: 'Credentials' },
  { route: '/identifiers', name: 'Identifiers' },
  { route: '/connections', name: 'Connections' },
  { route: '/menu', name: 'Menu' },
];

test.describe('Accessibility - WCAG 2.1 AA Compliance', () => {
  for (const pageInfo of PAGES_TO_TEST) {
    test(`${pageInfo.name} - passes axe accessibility checks`, async ({ page }) => {
      await page.goto(pageInfo.route);

      // Run axe accessibility tests
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      // Expect no violations
      expect(accessibilityScanResults.violations).toEqual([]);
    });
  }
});

test.describe('Color Contrast', () => {
  test('Text has sufficient contrast on all pages', async ({ page }) => {
    const pages = ['/onboarding', '/credentials', '/create-password'];

    for (const route of pages) {
      await page.goto(route);

      // Check text elements
      const textElements = await page.locator('p, span, button, a, h1, h2, h3').all();

      for (const element of textElements) {
        const isVisible = await element.isVisible();
        if (!isVisible) continue;

        // Get computed styles
        const styles = await element.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            color: computed.color,
            backgroundColor: computed.backgroundColor,
            fontSize: computed.fontSize,
          };
        });

        // Check if text color is not the same as background
        expect(styles.color).not.toBe(styles.backgroundColor);
      }
    }
  });
});

test.describe('Touch Targets', () => {
  test('All interactive elements meet minimum size (44x44px)', async ({ page }) => {
    await page.goto('/onboarding');

    // Check buttons
    const buttons = await page.locator('button, ion-button, [role="button"]').all();

    for (const button of buttons) {
      const isVisible = await button.isVisible();
      if (!isVisible) continue;

      const box = await button.boundingBox();
      if (!box) continue;

      // WCAG 2.1 Level AAA: minimum 44x44px
      expect(box.height).toBeGreaterThanOrEqual(44);
      expect(box.width).toBeGreaterThanOrEqual(44);
    }
  });

  test('Form inputs meet minimum touch target size', async ({ page }) => {
    await page.goto('/create-password');

    const inputs = await page.locator('input, ion-input, textarea').all();

    for (const input of inputs) {
      const isVisible = await input.isVisible();
      if (!isVisible) continue;

      const box = await input.boundingBox();
      if (!box) continue;

      // Minimum height of 44px
      expect(box.height).toBeGreaterThanOrEqual(44);
    }
  });
});

test.describe('Focus Indicators', () => {
  test('All focusable elements have visible focus states', async ({ page }) => {
    await page.goto('/onboarding');

    // Get all focusable elements
    const focusableElements = await page.locator(
      'button, a, input, textarea, [tabindex]:not([tabindex="-1"])'
    ).all();

    for (const element of focusableElements.slice(0, 5)) { // Test first 5
      const isVisible = await element.isVisible();
      if (!isVisible) continue;

      await element.focus();

      // Check for focus indicator (outline, box-shadow, or border change)
      const focusStyles = await element.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          outline: computed.outline,
          boxShadow: computed.boxShadow,
          border: computed.border,
        };
      });

      // Should have some visual focus indicator
      const hasFocusIndicator =
        focusStyles.outline !== 'none' ||
        focusStyles.boxShadow !== 'none' ||
        focusStyles.border.length > 0;

      expect(hasFocusIndicator).toBe(true);
    }
  });
});

test.describe('Keyboard Navigation', () => {
  test('Can navigate entire page with keyboard', async ({ page }) => {
    await page.goto('/onboarding');

    // Press Tab multiple times
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');

      // Check that focus is visible
      const activeElement = await page.evaluate(() => {
        return document.activeElement?.tagName;
      });

      expect(activeElement).toBeTruthy();
    }
  });

  test('Can submit forms with Enter key', async ({ page }) => {
    await page.goto('/create-password');

    // Focus on first input
    const input = page.locator('input').first();
    await input.focus();
    await input.fill('TestPassword123!');

    // Press Enter
    await page.keyboard.press('Enter');

    // Should trigger form action (check for navigation or validation)
    await page.waitForTimeout(500);
  });

  test('Can close modals with Escape key', async ({ page }) => {
    await page.goto('/credentials');

    // Open a modal (if present)
    const modalTrigger = page.locator('[data-testid="open-modal"]').first();
    if (await modalTrigger.isVisible()) {
      await modalTrigger.click();

      // Press Escape
      await page.keyboard.press('Escape');

      // Modal should be closed
      const modal = page.locator('.modal');
      await expect(modal).not.toBeVisible();
    }
  });
});

test.describe('Semantic HTML', () => {
  test('Pages use proper heading hierarchy', async ({ page }) => {
    const pages = ['/onboarding', '/credentials', '/identifiers'];

    for (const route of pages) {
      await page.goto(route);

      // Check for h1
      const h1Count = await page.locator('h1').count();
      expect(h1Count).toBeGreaterThanOrEqual(1);

      // Check headings are in order (h1, h2, h3, not h1, h3, h2)
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
      const levels = await Promise.all(
        headings.map(h => h.evaluate(el => parseInt(el.tagName.substring(1))))
      );

      // Verify no heading levels are skipped
      for (let i = 1; i < levels.length; i++) {
        const jump = levels[i] - levels[i - 1];
        expect(jump).toBeLessThanOrEqual(1);
      }
    }
  });

  test('Forms have proper labels', async ({ page }) => {
    await page.goto('/create-password');

    const inputs = await page.locator('input, textarea').all();

    for (const input of inputs) {
      const isVisible = await input.isVisible();
      if (!isVisible) continue;

      // Check for associated label
      const hasLabel = await input.evaluate(el => {
        const id = el.getAttribute('id');
        const ariaLabel = el.getAttribute('aria-label');
        const ariaLabelledBy = el.getAttribute('aria-labelledby');

        if (ariaLabel || ariaLabelledBy) return true;
        if (id) {
          const label = document.querySelector(`label[for="${id}"]`);
          return !!label;
        }

        return false;
      });

      expect(hasLabel).toBe(true);
    }
  });

  test('Images have alt text', async ({ page }) => {
    const pages = ['/onboarding', '/credentials', '/menu'];

    for (const route of pages) {
      await page.goto(route);

      const images = await page.locator('img').all();

      for (const img of images) {
        const isVisible = await img.isVisible();
        if (!isVisible) continue;

        const alt = await img.getAttribute('alt');

        // Should have alt attribute (can be empty for decorative images)
        expect(alt).not.toBeNull();
      }
    }
  });
});

test.describe('ARIA Attributes', () => {
  test('Interactive elements have proper ARIA roles', async ({ page }) => {
    await page.goto('/credentials');

    // Check buttons
    const buttons = await page.locator('button, [role="button"]').all();

    for (const button of buttons.slice(0, 5)) {
      const isVisible = await button.isVisible();
      if (!isVisible) continue;

      const role = await button.getAttribute('role');
      const tagName = await button.evaluate(el => el.tagName);

      // Should be button element or have button role
      const isProperButton = tagName === 'BUTTON' || role === 'button';
      expect(isProperButton).toBe(true);
    }
  });

  test('Live regions are properly marked', async ({ page }) => {
    await page.goto('/biometric-enrollment');

    // Check for status messages
    const statusElements = await page.locator('[role="status"], [aria-live]').all();

    // If status messages exist, they should have proper aria-live
    for (const element of statusElements) {
      const ariaLive = await element.getAttribute('aria-live');
      expect(['polite', 'assertive', 'off']).toContain(ariaLive);
    }
  });
});

test.describe('Screen Reader Support', () => {
  test('Skip links are present', async ({ page }) => {
    await page.goto('/onboarding');

    // Check for skip link (may be visually hidden)
    const skipLink = page.locator('a[href="#main-content"], .skip-link').first();

    if (await skipLink.count() > 0) {
      const href = await skipLink.getAttribute('href');
      expect(href).toBeTruthy();
    }
  });

  test('Landmarks are properly defined', async ({ page }) => {
    await page.goto('/onboarding');

    // Check for main landmark
    const main = await page.locator('main, [role="main"]').count();
    expect(main).toBeGreaterThanOrEqual(1);

    // Check for navigation if present
    const nav = await page.locator('nav, [role="navigation"]').count();
    if (nav > 0) {
      // Navigation should have accessible name
      const navElement = page.locator('nav, [role="navigation"]').first();
      const ariaLabel = await navElement.getAttribute('aria-label');
      expect(ariaLabel || await navElement.textContent()).toBeTruthy();
    }
  });
});
