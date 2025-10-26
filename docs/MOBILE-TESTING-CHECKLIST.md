# Biometric Enrollment - Mobile Responsiveness Testing Checklist

## ✅ CSS Implementation Complete
All mobile-responsive media queries have been added to `BiometricEnrollment.scss`:
- **Tablet (≤768px)**: Adjusted spacing, font sizes, single-column layouts
- **Small Phones (≤375px)**: iPhone SE optimization, compact typography
- **Landscape (≤600px height)**: Optimized for horizontal orientation
- **Touch Targets**: All buttons/interactive elements ≥44x44px (WCAG AAA)

## Device Testing Required

### 1. Physical Device Testing
Test on actual devices to validate real-world UX:

#### iOS Devices
- [ ] **iPhone 14 Pro** (393×852, iOS 17+)
  - Portrait: Verify finger checklist grid, success screen scroll
  - Landscape: Verify help modal fits, DID code wraps correctly
  - Touch: Test all buttons (WebAuthn, Copy DID, Help, Close)

- [ ] **iPhone SE 3rd Gen** (375×667, iOS 16+)
  - Portrait: Smallest target device, verify no text truncation
  - Landscape: Critical - verify pulse icon doesn't overflow
  - Accessibility: Test with larger text size (Settings → Display → Text Size)

- [ ] **iPad Mini** (744×1133, iPadOS 17+)
  - Portrait: Verify 1-column layout on narrow width
  - Landscape: Verify 3-column quick-facts grid
  - Split-screen: Test with 1/3 width Safari window

#### Android Devices
- [ ] **Samsung Galaxy S23** (360×800, Android 14+)
  - Portrait: Verify Material Design alignment
  - Landscape: Test navigation bar overlap
  - Dark Mode: Verify color contrast (enable system dark theme)

- [ ] **Google Pixel 7** (412×915, Android 13+)
  - Portrait: Standard Android reference device
  - Gesture Navigation: Verify no conflicts with edge swipes

- [ ] **Budget Phone** (≤360×640, Android 11+)
  - Critical: Minimum supported device, verify readability
  - Performance: Ensure animations don't lag (pulse, transitions)

### 2. Browser Testing
Test across mobile browsers:

- [ ] **iOS Safari** (primary target)
  - WebAuthn enrollment flow
  - Copy DID button (clipboard API)
  - Help modal scroll behavior

- [ ] **Chrome Mobile** (Android)
  - Progressive Web App mode (Add to Home Screen)
  - Fingerprint capture via USB OTG

- [ ] **Firefox Mobile** (Android)
  - Verify CSS custom properties work (`--ion-color-*`)
  - Test landscape rotation

### 3. Accessibility Testing

#### Screen Reader
- [ ] **VoiceOver (iOS)**
  - Enable: Settings → Accessibility → VoiceOver
  - Test: Navigate enrollment intro → progress → success
  - Verify: `aria-live` announcements ("Capturing Left Thumb... 1 of 10")
  - Verify: `role="progressbar"` reads correctly

- [ ] **TalkBack (Android)**
  - Enable: Settings → Accessibility → TalkBack
  - Test: Help button → Modal open/close
  - Verify: `.sr-only` content is read but not visible

#### Touch Targets (WCAG 2.1 Level AAA)
- [ ] **Measure Interactive Elements**
  - Use: Chrome DevTools → Toggle device toolbar → Inspect element
  - Verify: All buttons/links are ≥44×44px
  - Check: Help button (top-right)
  - Check: WebAuthn Enroll button
  - Check: Copy DID button
  - Check: Close help modal button

#### Zoom & Text Scaling
- [ ] **iOS Dynamic Type**
  - Settings → Display & Brightness → Text Size
  - Test at **Largest** setting
  - Verify: No text truncation, layouts don't break

- [ ] **Android Display Size**
  - Settings → Display → Display Size → **Large**
  - Verify: Buttons remain on-screen

### 4. Orientation Testing
- [ ] **Portrait → Landscape Rotation**
  - During finger capture: Verify current finger icon resizes
  - During success screen: Verify DID code stays readable
  - Help modal: Verify scroll works when content overflows

- [ ] **Landscape → Portrait Rotation**
  - Verify: State persists (doesn't restart enrollment)
  - Check: No layout flash/reflow

### 5. Edge Cases

#### Long Content
- [ ] **DID Code Overflow**
  - Generate DID, verify `did:cardano:mainnet:zQm...` wraps correctly
  - Test: Copy button doesn't overlap code
  - Font size: Verify legibility at 0.7rem (small phones)

#### Network Conditions
- [ ] **Slow 3G**
  - Chrome DevTools → Network → Slow 3G
  - Test: Loading spinner shows during DID generation
  - Verify: No "frozen" state

#### Interrupted Flows
- [ ] **Background App**
  - Start enrollment → Switch to home screen → Return
  - Verify: Progress saved (currentFinger index intact)

### 6. Performance

#### Frame Rate
- [ ] **Pulse Animation**
  - Chrome DevTools → Performance → Record
  - Target: 60fps on pulse-small animation
  - Check: No dropped frames on Pixel 7

#### Bundle Size
- [ ] **CSS Impact**
  - Before: Check baseline BiometricEnrollment.css size
  - After: Verify mobile media queries add <5KB

### 7. Visual Regression

#### Screenshot Comparison
- [ ] **Percy.io / Chromatic**
  - Capture: Enrollment intro (375px, 768px, 1024px)
  - Capture: Progress screen with 5 fingers completed
  - Capture: Success screen with DID displayed
  - Capture: Help modal open

## Testing Tools

### Emulators (Quick Testing)
```bash
# Chrome DevTools
# - Toggle device toolbar (Cmd+Shift+M / Ctrl+Shift+M)
# - Select: iPhone SE, iPhone 14 Pro, Pixel 7, Galaxy S23
# - Test: Responsive + Touch

# iOS Simulator (macOS only)
npx cap open ios
# Run in Xcode simulator (iPhone 14 Pro, iPad Mini)

# Android Emulator
npx cap open android
# Run in Android Studio emulator (Pixel 7 API 34)
```

### Physical Device Debugging
```bash
# iOS Safari (macOS)
# 1. Enable Web Inspector: iPhone Settings → Safari → Advanced → Web Inspector
# 2. macOS Safari → Develop → [Your iPhone] → BiometricEnrollment
# 3. Use console/inspector to debug

# Android Chrome
# 1. Enable USB Debugging: Settings → About → Tap Build Number 7x
# 2. Settings → Developer Options → USB Debugging ON
# 3. chrome://inspect → Devices → Inspect target page
```

## Success Criteria
All checklist items must pass before marking Item 8 complete:

1. ✅ No horizontal scroll on any viewport ≥320px
2. ✅ All text readable without zooming
3. ✅ Touch targets ≥44×44px (WCAG AAA)
4. ✅ Help modal scrolls on short viewports
5. ✅ DID code wraps correctly on small screens
6. ✅ Screen readers announce progress updates
7. ✅ Orientation changes don't break layout
8. ✅ Animations maintain 60fps on mid-range devices

## Automated Testing (Future)
```typescript
// Playwright mobile viewport test
test.describe('BiometricEnrollment Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE

  test('should display enrollment intro correctly', async ({ page }) => {
    await page.goto('/biometric-enrollment');
    await expect(page.locator('.large-icon')).toHaveCSS('font-size', '4rem');
    await expect(page.locator('.webauthn-enroll-button')).toHaveCSS('min-height', '44px');
  });
});
```

## Completion Status
- **CSS Implementation**: ✅ Complete (Jan 2025)
- **Device Testing**: ⏳ Pending
- **Accessibility Testing**: ⏳ Pending
- **Performance Validation**: ⏳ Pending

**Estimated Testing Time**: 2-3 hours (with physical devices)
**Priority**: Critical (Production blocker)
