# Design Consistency Audit Report

**Generated:** 2025-10-26T05:03:00.251Z

## Summary

- **Total Files Scanned:** 55
- **Files with Issues:** 23
- **Total Issues Found:** 122

### Issues by Type

| Type | Count |
|------|-------|
| borderRadius | 21 |
| color | 48 |
| spacing | 11 |
| shadow | 17 |
| fontSize | 18 |
| zIndex | 7 |

## Priority Files to Fix

Files sorted by number of issues (highest first):

### SimplifiedOnboarding/SeedPhraseScreen.scss (20 issues)

**spacing** (2 occurrences):
- Line 91: `padding: 20px`
  → Use: `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`
- Line 193: `padding: 10px`
  → Use: `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**fontSize** (2 occurrences):
- Line 80: `font-size: 15px`
  → Use: `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`
- Line 136: `font-size: 15px`
  → Use: `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**shadow** (2 occurrences):
- Line 58: `box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05)`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`
- Line 94: `box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05)`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**color** (14 occurrences):
- Line 17: `#333`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 23: `#fff3cd`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 24: `#ffc107`
  → Use: `var(--ion-color-*) or var(--color-*)`
  ... and 11 more

### SimplifiedOnboarding/VerificationScreen.scss (13 issues)

**shadow** (1 occurrences):
- Line 58: `box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05)`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**color** (12 occurrences):
- Line 17: `#333`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 23: `#666`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 30: `#f8d7da`
  → Use: `var(--ion-color-*) or var(--color-*)`
  ... and 9 more

### SimplifiedOnboarding/BiometricScanScreen.scss (12 issues)

**spacing** (3 occurrences):
- Line 132: `padding: 10px`
  → Use: `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`
- Line 204: `gap: 20px`
  → Use: `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`
- Line 219: `gap: 10px`
  → Use: `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**fontSize** (2 occurrences):
- Line 17: `font-size: 3rem`
  → Use: `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`
- Line 52: `font-size: 4rem`
  → Use: `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**borderRadius** (2 occurrences):
- Line 38: `border-radius: 100%`
  → Use: `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`
- Line 102: `border-radius: 999px`
  → Use: `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**shadow** (2 occurrences):
- Line 40: `box-shadow: 0 12px 32px rgba(16, 24, 64, 0.08)`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`
- Line 117: `box-shadow: 0 16px 40px rgba(15, 31, 53, 0.06)`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**color** (3 occurrences):
- Line 40: `rgba(16, 24, 64, 0.08)`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 117: `rgba(15, 31, 53, 0.06)`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 133: `rgba(15, 31, 53, 0.06)`
  → Use: `var(--ion-color-*) or var(--color-*)`

### SimplifiedOnboarding/SuccessScreen.scss (11 issues)

**spacing** (3 occurrences):
- Line 38: `padding: 20px`
  → Use: `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`
- Line 58: `padding: 20px`
  → Use: `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`
- Line 98: `padding: 20px`
  → Use: `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**fontSize** (4 occurrences):
- Line 22: `font-size: 80px`
  → Use: `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`
- Line 28: `font-size: 32px`
  → Use: `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`
- Line 46: `font-size: 15px`
  → Use: `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`
  ... and 1 more

**color** (4 occurrences):
- Line 35: `rgba(255, 255, 255, 0.15)`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 55: `rgba(255, 255, 255, 0.15)`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 76: `rgba(0, 0, 0, 0.2)`
  → Use: `var(--ion-color-*) or var(--color-*)`
  ... and 1 more

### SimplifiedOnboarding/WelcomeScreen.scss (10 issues)

**spacing** (2 occurrences):
- Line 4: `gap: 32px`
  → Use: `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`
- Line 105: `padding: 28px`
  → Use: `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**shadow** (2 occurrences):
- Line 10: `box-shadow: 0 32px 80px rgba(10, 17, 35, 0.45)`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`
- Line 78: `box-shadow: 0 18px 36px rgba(64, 135, 255, 0.35)`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**color** (6 occurrences):
- Line 8: `#252c49`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 8: `#111628`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 10: `rgba(10, 17, 35, 0.45)`
  → Use: `var(--ion-color-*) or var(--color-*)`
  ... and 3 more

### BiometricEnrollment/BiometricEnrollment.scss (10 issues)

**fontSize** (10 occurrences):
- Line 248: `font-size: 2rem`
  → Use: `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`
- Line 314: `font-size: 5rem`
  → Use: `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`
- Line 349: `font-size: 6rem`
  → Use: `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`
  ... and 7 more

### LockPage/LockPage.scss (8 issues)

**shadow** (3 occurrences):
- Line 52: `box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1)`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`
- Line 61: `box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15)`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`
- Line 66: `box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1)`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**color** (3 occurrences):
- Line 52: `rgba(0, 0, 0, 0.1)`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 61: `rgba(0, 0, 0, 0.15)`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 66: `rgba(0, 0, 0, 0.1)`
  → Use: `var(--ion-color-*) or var(--color-*)`

**zIndex** (2 occurrences):
- Line 3: `z-index: 2147483647`
  → Use: `--z-index-dropdown|--z-index-modal|--z-index-tooltip|--z-index-toast`
- Line 77: `z-index: 2147483647`
  → Use: `--z-index-dropdown|--z-index-modal|--z-index-tooltip|--z-index-toast`

### SimplifiedOnboarding/ProgressIndicator.scss (6 issues)

**shadow** (1 occurrences):
- Line 9: `box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1)`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**color** (4 occurrences):
- Line 9: `rgba(0, 0, 0, 0.1)`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 26: `#007aff`
  → Use: `var(--ion-color-*) or var(--color-*)`
- Line 31: `#e0e0e0`
  → Use: `var(--ion-color-*) or var(--color-*)`
  ... and 1 more

**zIndex** (1 occurrences):
- Line 10: `z-index: 1000`
  → Use: `--z-index-dropdown|--z-index-modal|--z-index-tooltip|--z-index-toast`

### NotificationDetails/components/ReceiveCredential/ReceiveCredential.scss (6 issues)

**borderRadius** (6 occurrences):
- Line 177: `border-radius: 5rem`
  → Use: `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`
- Line 187: `border-radius: 5rem`
  → Use: `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`
- Line 222: `border-radius: 4rem`
  → Use: `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`
  ... and 3 more

### NotificationDetails/components/MultiSigRequest/MultiSigRequest.scss (4 issues)

**borderRadius** (3 occurrences):
- Line 26: `border-radius: 1rem`
  → Use: `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`
- Line 75: `border-radius: 2rem`
  → Use: `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`
- Line 169: `border-radius: 4rem`
  → Use: `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**shadow** (1 occurrences):
- Line 30: `box-shadow: none`
  → Use: `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`


## Detailed Findings

<details>
<summary><strong>SimplifiedOnboarding/SeedPhraseScreen.scss</strong> - 20 issues</summary>

**Line 91** (spacing):
```scss
padding: 20px
```
→ **Recommended:** `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**Line 193** (spacing):
```scss
padding: 10px
```
→ **Recommended:** `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**Line 80** (fontSize):
```scss
font-size: 15px
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 136** (fontSize):
```scss
font-size: 15px
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 58** (shadow):
```scss
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05)
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 94** (shadow):
```scss
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05)
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 17** (color):
```scss
#333
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 23** (color):
```scss
#fff3cd
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 24** (color):
```scss
#ffc107
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 42** (color):
```scss
#856404
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 58** (color):
```scss
rgba(0, 0, 0, 0.05)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 70** (color):
```scss
#f8f9fa
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 75** (color):
```scss
#999
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 82** (color):
```scss
#333
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 94** (color):
```scss
rgba(0, 0, 0, 0.05)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 100** (color):
```scss
#333
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 109** (color):
```scss
#666
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 137** (color):
```scss
#333
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 172** (color):
```scss
#007aff
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 180** (color):
```scss
rgba(0, 122, 255, 0.1)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

</details>

<details>
<summary><strong>SimplifiedOnboarding/VerificationScreen.scss</strong> - 13 issues</summary>

**Line 58** (shadow):
```scss
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05)
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 17** (color):
```scss
#333
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 23** (color):
```scss
#666
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 30** (color):
```scss
#f8d7da
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 31** (color):
```scss
#dc3545
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 49** (color):
```scss
#721c24
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 58** (color):
```scss
rgba(0, 0, 0, 0.05)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 72** (color):
```scss
#333
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 88** (color):
```scss
#dc3545
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 94** (color):
```scss
#34c759
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 102** (color):
```scss
#34c759
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 109** (color):
```scss
#dc3545
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 122** (color):
```scss
#666
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

</details>

<details>
<summary><strong>SimplifiedOnboarding/BiometricScanScreen.scss</strong> - 12 issues</summary>

**Line 132** (spacing):
```scss
padding: 10px
```
→ **Recommended:** `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**Line 204** (spacing):
```scss
gap: 20px
```
→ **Recommended:** `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**Line 219** (spacing):
```scss
gap: 10px
```
→ **Recommended:** `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**Line 17** (fontSize):
```scss
font-size: 3rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 52** (fontSize):
```scss
font-size: 4rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 38** (borderRadius):
```scss
border-radius: 100%
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 102** (borderRadius):
```scss
border-radius: 999px
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 40** (shadow):
```scss
box-shadow: 0 12px 32px rgba(16, 24, 64, 0.08)
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 117** (shadow):
```scss
box-shadow: 0 16px 40px rgba(15, 31, 53, 0.06)
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 40** (color):
```scss
rgba(16, 24, 64, 0.08)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 117** (color):
```scss
rgba(15, 31, 53, 0.06)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 133** (color):
```scss
rgba(15, 31, 53, 0.06)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

</details>

<details>
<summary><strong>SimplifiedOnboarding/SuccessScreen.scss</strong> - 11 issues</summary>

**Line 38** (spacing):
```scss
padding: 20px
```
→ **Recommended:** `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**Line 58** (spacing):
```scss
padding: 20px
```
→ **Recommended:** `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**Line 98** (spacing):
```scss
padding: 20px
```
→ **Recommended:** `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**Line 22** (fontSize):
```scss
font-size: 80px
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 28** (fontSize):
```scss
font-size: 32px
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 46** (fontSize):
```scss
font-size: 15px
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 164** (fontSize):
```scss
font-size: 64px
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 35** (color):
```scss
rgba(255, 255, 255, 0.15)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 55** (color):
```scss
rgba(255, 255, 255, 0.15)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 76** (color):
```scss
rgba(0, 0, 0, 0.2)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 95** (color):
```scss
rgba(255, 255, 255, 0.15)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

</details>

<details>
<summary><strong>SimplifiedOnboarding/WelcomeScreen.scss</strong> - 10 issues</summary>

**Line 4** (spacing):
```scss
gap: 32px
```
→ **Recommended:** `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**Line 105** (spacing):
```scss
padding: 28px
```
→ **Recommended:** `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

**Line 10** (shadow):
```scss
box-shadow: 0 32px 80px rgba(10, 17, 35, 0.45)
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 78** (shadow):
```scss
box-shadow: 0 18px 36px rgba(64, 135, 255, 0.35)
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 8** (color):
```scss
#252c49
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 8** (color):
```scss
#111628
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 10** (color):
```scss
rgba(10, 17, 35, 0.45)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 11** (color):
```scss
#ffffff
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 36** (color):
```scss
rgba(255, 255, 255, 0.76)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 51** (color):
```scss
rgba(255, 255, 255, 0.08)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

</details>

<details>
<summary><strong>BiometricEnrollment/BiometricEnrollment.scss</strong> - 10 issues</summary>

**Line 248** (fontSize):
```scss
font-size: 2rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 314** (fontSize):
```scss
font-size: 5rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 349** (fontSize):
```scss
font-size: 6rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 368** (fontSize):
```scss
font-size: 5rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 423** (fontSize):
```scss
font-size: 4rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 493** (fontSize):
```scss
font-size: 5rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 534** (fontSize):
```scss
font-size: 4rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 623** (fontSize):
```scss
font-size: 3rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 637** (fontSize):
```scss
font-size: 4rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

**Line 644** (fontSize):
```scss
font-size: 3rem
```
→ **Recommended:** `--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl`

</details>

<details>
<summary><strong>LockPage/LockPage.scss</strong> - 8 issues</summary>

**Line 52** (shadow):
```scss
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1)
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 61** (shadow):
```scss
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15)
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 66** (shadow):
```scss
box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1)
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 52** (color):
```scss
rgba(0, 0, 0, 0.1)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 61** (color):
```scss
rgba(0, 0, 0, 0.15)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 66** (color):
```scss
rgba(0, 0, 0, 0.1)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 3** (zIndex):
```scss
z-index: 2147483647
```
→ **Recommended:** `--z-index-dropdown|--z-index-modal|--z-index-tooltip|--z-index-toast`

**Line 77** (zIndex):
```scss
z-index: 2147483647
```
→ **Recommended:** `--z-index-dropdown|--z-index-modal|--z-index-tooltip|--z-index-toast`

</details>

<details>
<summary><strong>SimplifiedOnboarding/ProgressIndicator.scss</strong> - 6 issues</summary>

**Line 9** (shadow):
```scss
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1)
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 9** (color):
```scss
rgba(0, 0, 0, 0.1)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 26** (color):
```scss
#007aff
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 31** (color):
```scss
#e0e0e0
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 43** (color):
```scss
#333
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 10** (zIndex):
```scss
z-index: 1000
```
→ **Recommended:** `--z-index-dropdown|--z-index-modal|--z-index-tooltip|--z-index-toast`

</details>

<details>
<summary><strong>NotificationDetails/components/ReceiveCredential/ReceiveCredential.scss</strong> - 6 issues</summary>

**Line 177** (borderRadius):
```scss
border-radius: 5rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 187** (borderRadius):
```scss
border-radius: 5rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 222** (borderRadius):
```scss
border-radius: 4rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 231** (borderRadius):
```scss
border-radius: 4rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 257** (borderRadius):
```scss
border-radius: 2rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 266** (borderRadius):
```scss
border-radius: 5rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

</details>

<details>
<summary><strong>NotificationDetails/components/MultiSigRequest/MultiSigRequest.scss</strong> - 4 issues</summary>

**Line 26** (borderRadius):
```scss
border-radius: 1rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 75** (borderRadius):
```scss
border-radius: 2rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 169** (borderRadius):
```scss
border-radius: 4rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 30** (shadow):
```scss
box-shadow: none
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

</details>

<details>
<summary><strong>SystemThreatAlert/SystemThreatAlert.scss</strong> - 3 issues</summary>

**Line 62** (borderRadius):
```scss
border-radius: 1rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 71** (color):
```scss
rgba(0, 86, 179, 0.2)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

**Line 72** (color):
```scss
rgba(0, 86, 179, 0.2)
```
→ **Recommended:** `var(--ion-color-*) or var(--color-*)`

</details>

<details>
<summary><strong>Menu/components/ConfirmConnectModal/ConfirmConnectModal.scss</strong> - 3 issues</summary>

**Line 79** (borderRadius):
```scss
border-radius: 2rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 92** (borderRadius):
```scss
border-radius: 1rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 83** (shadow):
```scss
box-shadow: none
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

</details>

<details>
<summary><strong>Notifications/Notifications.scss</strong> - 2 issues</summary>

**Line 84** (borderRadius):
```scss
border-radius: 3rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 111** (borderRadius):
```scss
border-radius: 3rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

</details>

<details>
<summary><strong>Menu/components/Settings/Settings.scss</strong> - 2 issues</summary>

**Line 18** (borderRadius):
```scss
border-radius: 1rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 22** (shadow):
```scss
box-shadow: none
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

</details>

<details>
<summary><strong>Menu/components/Profile/Profile.scss</strong> - 2 issues</summary>

**Line 34** (borderRadius):
```scss
border-radius: 1rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 38** (shadow):
```scss
box-shadow: none
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

</details>

<details>
<summary><strong>Connections/Connections.scss</strong> - 2 issues</summary>

**Line 104** (shadow):
```scss
box-shadow: none
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

**Line 56** (zIndex):
```scss
z-index: 2
```
→ **Recommended:** `--z-index-dropdown|--z-index-modal|--z-index-tooltip|--z-index-toast`

</details>

<details>
<summary><strong>ConnectionDetails/components/EditConnectionsModal.scss</strong> - 2 issues</summary>

**Line 60** (borderRadius):
```scss
border-radius: 1rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

**Line 135** (zIndex):
```scss
z-index: 10
```
→ **Recommended:** `--z-index-dropdown|--z-index-modal|--z-index-tooltip|--z-index-toast`

</details>

<details>
<summary><strong>WalletConnect/WalletConnect.scss</strong> - 1 issues</summary>

**Line 31** (borderRadius):
```scss
border-radius: 5rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

</details>

<details>
<summary><strong>NotificationDetails/components/RemoteSignRequest/RemoteSignRequest.scss</strong> - 1 issues</summary>

**Line 39** (borderRadius):
```scss
border-radius: 4rem
```
→ **Recommended:** `--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full`

</details>

<details>
<summary><strong>NotificationDetails/components/CredentialRequest/CredentialRequest.scss</strong> - 1 issues</summary>

**Line 2** (zIndex):
```scss
z-index: 1000
```
→ **Recommended:** `--z-index-dropdown|--z-index-modal|--z-index-tooltip|--z-index-toast`

</details>

<details>
<summary><strong>NotificationDetails/components/CredentialRequest/CredentialRequestInformation/CredentialRequestInformation.scss</strong> - 1 issues</summary>

**Line 36** (spacing):
```scss
margin: 4px
```
→ **Recommended:** `--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl`

</details>

<details>
<summary><strong>Menu/Menu.scss</strong> - 1 issues</summary>

**Line 19** (shadow):
```scss
box-shadow: none
```
→ **Recommended:** `--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl`

</details>

<details>
<summary><strong>IncomingRequest/components/SignRequest.scss</strong> - 1 issues</summary>

**Line 143** (zIndex):
```scss
z-index: 10000
```
→ **Recommended:** `--z-index-dropdown|--z-index-modal|--z-index-tooltip|--z-index-toast`

</details>

## Action Items

1. **Update BiometricEnrollment** (if top priority)
   - Replace hardcoded values with design tokens
   - Test visual appearance after changes

2. **Update remaining pages** (in priority order)
   - Focus on pages with most issues first
   - Maintain consistent patterns

3. **Run visual regression tests**
   ```bash
   npm run test:e2e -- visual-regression/design-consistency.spec.ts
   ```

4. **Generate new screenshot baselines**
   ```bash
   npm run test:e2e -- --update-snapshots
   ```

