# 🎨 Design System - Quick Reference

## Overview

This wallet implements a comprehensive design system ensuring pixel-perfect consistency across all 26 pages. The system includes design tokens, utility classes, visual regression testing, and accessibility compliance (WCAG 2.1 AA).

## Quick Start

### Run Design Perfection Workflow

```bash
cd demo-wallet
./scripts/design-perfection.sh
```

This automated workflow will:

1. ✅ Install dependencies (@axe-core/playwright, glob)
2. 🔍 Audit all pages for design inconsistencies
3. 🛠️ Guide you through fixing issues
4. 📸 Generate visual regression baselines
5. ♿ Run accessibility compliance tests
6. ✅ Validate perfection

### Manual Commands

```bash
# Design audit
npm run audit:design

# Visual regression tests
npm run test:e2e:visual

# Accessibility tests
npm run test:e2e:a11y

# Full E2E test suite
npm run test:e2e

# Interactive test UI
npm run test:e2e:ui

# Update screenshot baselines
npm run test:e2e:update-snapshots
```

## Design Tokens

### Spacing (8px base grid)

```scss
var(--spacing-xs)   // 8px
var(--spacing-sm)   // 12px
var(--spacing-md)   // 16px
var(--spacing-lg)   // 24px
var(--spacing-xl)   // 32px
var(--spacing-2xl)  // 40px
var(--spacing-3xl)  // 48px
```

### Typography

```scss
var(--font-size-xs)    // 12px
var(--font-size-sm)    // 14px
var(--font-size-base)  // 16px
var(--font-size-lg)    // 20px
var(--font-size-xl)    // 24px
var(--font-size-2xl)   // 30px
var(--font-size-3xl)   // 36px

var(--font-weight-regular)   // 400
var(--font-weight-medium)    // 500
var(--font-weight-semibold)  // 600
var(--font-weight-bold)      // 700
```

### Border Radius

```scss
var(--radius-sm)    // 4px
var(--radius-md)    // 8px
var(--radius-lg)    // 12px
var(--radius-xl)    // 16px
var(--radius-2xl)   // 24px
var(--radius-full)  // 9999px (circle)
```

### Shadows (Elevation)

```scss
var(--shadow-xs)   // Subtle
var(--shadow-sm)   // Small
var(--shadow-md)   // Medium (default for cards)
var(--shadow-lg)   // Large (hover states)
var(--shadow-xl)   // Extra large
```

### Colors

```scss
// Use Ionic color system
var(--ion-color-primary)
var(--ion-color-secondary)
var(--ion-color-success)
var(--ion-color-warning)
var(--ion-color-danger)
var(--ion-color-light)
var(--ion-color-dark)

// Extended semantic colors
var(--color-success)
var(--color-error)
var(--color-warning)
var(--color-info)

// Gray scale
var(--color-gray-50)  // Lightest
var(--color-gray-100)
var(--color-gray-200)
...
var(--color-gray-900) // Darkest
```

## Utility Classes

### Layout

```html
<div class="page-layout">
  <div class="page-content">
    <div class="container">
      <!-- Your content -->
    </div>
  </div>
</div>
```

### Spacing

```html
<!-- Margin top -->
<div class="mt-xs mt-sm mt-md mt-lg mt-xl mt-2xl"></div>

<!-- Margin bottom -->
<div class="mb-xs mb-sm mb-md mb-lg mb-xl mb-2xl"></div>

<!-- Padding -->
<div class="p-xs p-sm p-md p-lg p-xl p-2xl"></div>
```

### Typography

```html
<h1 class="text-3xl font-bold">Large Heading</h1>
<h2 class="text-2xl font-semibold">Medium Heading</h2>
<p class="text-base font-regular">Body text</p>
<span class="text-sm text-center">Small centered text</span>
```

### Cards

```html
<!-- Basic card -->
<div class="card">
  <h3>Card Title</h3>
  <p>Card content</p>
</div>

<!-- Interactive card with hover effect -->
<div class="card card-interactive">
  <h3>Clickable Card</h3>
</div>

<!-- Card with hover elevation -->
<div class="card card-hover">
  <h3>Hover me!</h3>
</div>
```

### Buttons

```html
<!-- Primary button -->
<button class="btn btn-primary">Primary Action</button>

<!-- Secondary button -->
<button class="btn btn-secondary">Secondary Action</button>

<!-- Outline button -->
<button class="btn btn-outline">Outline Action</button>

<!-- Size variants -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary btn-md">Medium (default)</button>
<button class="btn btn-primary btn-lg">Large</button>
```

### Progress Bars

```html
<div class="progress-bar">
  <div
    class="progress-fill"
    style="width: 60%"
  ></div>
</div>
```

### Badges

```html
<span class="badge badge-success">Success</span>
<span class="badge badge-error">Error</span>
<span class="badge badge-warning">Warning</span>
<span class="badge badge-info">Info</span>
```

### Icons

```html
<ion-icon class="icon-sm"></ion-icon>
<!-- 16px -->
<ion-icon class="icon-md"></ion-icon>
<!-- 24px -->
<ion-icon class="icon-lg"></ion-icon>
<!-- 32px -->
<ion-icon class="icon-xl"></ion-icon>
<!-- 48px -->
<ion-icon class="icon-2xl"></ion-icon>
<!-- 64px -->
```

### Animations

```html
<div class="animate-fadeIn">Fades in</div>
<div class="animate-fadeInScale">Fades in with scale</div>
<div class="animate-slideInUp">Slides up</div>
<ion-icon class="icon-pulse"></ion-icon>
```

## Converting Existing Code

### ❌ Before (Inconsistent)

```scss
.my-component {
  padding: 24px;
  margin-bottom: 16px;
  font-size: 1.25rem;
  font-weight: 600;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: #ffffff;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  }
}
```

### ✅ After (Using Design System)

```scss
.my-component {
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  background: var(--ion-color-light);
  transition: var(--button-transition);

  &:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
  }
}
```

### ✅✅ Best (Using Utility Classes)

```html
<div class="card card-hover p-lg mb-md">
  <h3 class="text-lg font-semibold">Component Title</h3>
  <p class="text-base">Component content</p>
</div>
```

## Testing

### Visual Regression Testing

Tests all pages across 4 viewports (375px, 393px, 768px, 1280px):

```bash
# Run visual tests
npm run test:e2e:visual

# Update baselines (after intentional design changes)
npm run test:e2e:update-snapshots
```

### Accessibility Testing

Validates WCAG 2.1 AA compliance:

```bash
# Run accessibility tests
npm run test:e2e:a11y
```

Tests include:

- ✅ Color contrast (4.5:1 ratio)
- ✅ Touch targets (44x44px minimum)
- ✅ Focus indicators (visible on all interactive elements)
- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ Semantic HTML (proper headings, landmarks)
- ✅ ARIA attributes (roles, labels, live regions)
- ✅ Screen reader support (alt text, skip links)

### Design Audit

Scan all pages for hardcoded values:

```bash
npm run audit:design
```

Generates `design-audit-report.md` with:

- Files with most issues (prioritized fix list)
- Line-by-line recommendations
- Design token suggestions
- Action items

## File Structure

```
demo-wallet/
├── src/ui/
│   ├── design-tokens.scss        # 375 lines - All design tokens
│   ├── utilities.scss             # 420 lines - Utility classes
│   ├── App.scss                   # Imports design system
│   └── pages/                     # 26 page directories
├── tests/e2e/visual-regression/
│   ├── design-consistency.spec.ts # Visual regression tests
│   └── accessibility.spec.ts      # WCAG 2.1 AA tests
├── scripts/
│   ├── audit-design.js            # Design audit automation
│   └── design-perfection.sh       # Complete workflow
└── playwright.config.ts           # Enhanced with 7 test environments
```

## Accessibility Guidelines

### Minimum Touch Targets

All interactive elements must be **at least 44x44px** (WCAG 2.1 Level AA):

```scss
button,
a,
input {
  min-height: var(--touch-target-min); // 44px
}
```

### Focus Indicators

All focusable elements must have visible focus states:

```scss
.focus-visible:focus-visible {
  outline: var(--focus-ring-width) var(--focus-ring-style) var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
}
```

### Color Contrast

- Normal text: **4.5:1** minimum
- Large text (18pt+): **3:1** minimum
- Use design system colors (pre-validated)

### Semantic HTML

```html
<!-- ✅ Good -->
<button>Click me</button>
<input
  type="text"
  id="name"
  aria-label="Your name"
/>
<nav aria-label="Main navigation">
  <!-- ❌ Bad -->
  <div onclick="...">Click me</div>
  <input />
  <!-- No label -->
  <div class="nav"></div>
</nav>
```

## Dark Mode Support

All design tokens include dark mode overrides:

```scss
@media (prefers-color-scheme: dark) {
  :root {
    --card-background: var(--ion-color-neutral-800);
    --shadow-md: 0 4px 8px 0 rgba(0, 0, 0, 0.5);
    // Automatically applied
  }
}
```

## Reduced Motion Support

Respects user's motion preferences (WCAG 2.1):

```scss
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Browser Support

Tested on:

- ✅ Chrome (Desktop + Android)
- ✅ Firefox (Desktop)
- ✅ Safari (Desktop + iOS)
- ✅ Mobile devices (iPhone SE, 12, Pixel 5, iPad Pro)

## Performance

- CSS custom properties (native, no JavaScript)
- Utility classes reduce CSS bundle size
- Animations use GPU-accelerated properties (transform, opacity)
- Lazy-loaded components
- Optimized for 60fps animations

## Common Patterns

### Full-Page Layout

```html
<div class="page-layout">
  <div class="page-content">
    <h1 class="text-3xl font-bold mb-xl">Page Title</h1>

    <div class="card mb-lg">
      <h2 class="text-xl font-semibold mb-md">Section</h2>
      <p class="text-base mb-md">Content</p>
      <button class="btn btn-primary">Action</button>
    </div>
  </div>
</div>
```

### Form Layout

```html
<form class="card p-xl">
  <h2 class="text-2xl font-semibold mb-lg">Form Title</h2>

  <div class="mb-md">
    <label
      for="field1"
      class="text-base font-medium"
      >Field Label</label
    >
    <input
      type="text"
      id="field1"
      class="mt-sm"
    />
  </div>

  <button
    type="submit"
    class="btn btn-primary btn-lg"
  >
    Submit
  </button>
</form>
```

### List of Cards

```html
<div class="page-content">
  <div
    class="card card-interactive mb-md"
    *ngFor="let item of items"
  >
    <div class="mb-sm">
      <h3 class="text-lg font-semibold">{{item.title}}</h3>
      <p class="text-sm text-gray-600">{{item.description}}</p>
    </div>
    <span class="badge badge-success">{{item.status}}</span>
  </div>
</div>
```

## Troubleshooting

### Issue: Styles not applying

**Solution:** Make sure design-tokens.scss and utilities.scss are imported in App.scss:

```scss
@import "./design-tokens.scss";
@import "./utilities.scss";
```

### Issue: Visual tests failing

**Solution:** Regenerate baselines after intentional design changes:

```bash
npm run test:e2e:update-snapshots
```

### Issue: Accessibility tests failing

**Solution:** Check specific failures in playwright-report/:

```bash
npx playwright show-report
```

### Issue: Design audit shows many issues

**Solution:** Fix priority pages first (listed at top of report):

```bash
npm run audit:design
# Review design-audit-report.md
# Fix top 5 pages
# Re-run audit
```

## Support

- **Documentation:** `/demo-wallet/DESIGN-SYSTEM-IMPLEMENTATION.md`
- **Design Tokens:** `/demo-wallet/src/ui/design-tokens.scss`
- **Utilities:** `/demo-wallet/src/ui/utilities.scss`
- **Tests:** `/demo-wallet/tests/e2e/visual-regression/`
- **Audit:** Run `npm run audit:design`

## Changelog

### v1.0.0 (2025-01-XX)

- ✅ Initial design system implementation
- ✅ 100+ design tokens defined
- ✅ 50+ utility classes created
- ✅ Visual regression testing setup (7 environments)
- ✅ Accessibility testing (WCAG 2.1 AA)
- ✅ Design audit automation
- ✅ Dark mode support
- ✅ Reduced motion support
- ✅ Mobile device configurations

---

**Remember:** Consistency is perfection. Use design tokens everywhere. Never hardcode values. Test with Playwright. Validate with design audit. Ship with confidence. 🚀
