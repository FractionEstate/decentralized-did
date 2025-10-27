#!/usr/bin/env node

/**
 * Auto-fix design token issues across all SCSS files
 * Based on the design audit report
 */

const fs = require('fs');
const path = require('path');

// Design token mappings
const replacements = {
  // Spacing mappings (8px-based grid)
  'padding: 2px': 'padding: var(--spacing-2xs)',
  'padding: 4px': 'padding: var(--spacing-2xs)',
  'padding: 6px': 'padding: var(--spacing-2xs)',
  'padding: 10px': 'padding: var(--spacing-xs)',
  'padding: 12px': 'padding: var(--spacing-sm)',
  'padding: 16px': 'padding: var(--spacing-md)',
  'padding: 20px': 'padding: var(--spacing-lg)',
  'padding: 24px': 'padding: var(--spacing-xl)',
  'padding: 28px': 'padding: var(--spacing-2xl)',
  'padding: 32px': 'padding: var(--spacing-2xl)',
  'gap: 10px': 'gap: var(--spacing-xs)',
  'gap: 12px': 'gap: var(--spacing-sm)',
  'gap: 16px': 'gap: var(--spacing-md)',
  'gap: 20px': 'gap: var(--spacing-lg)',
  'gap: 24px': 'gap: var(--spacing-xl)',
  'gap: 28px': 'gap: var(--spacing-2xl)',
  'gap: 32px': 'gap: var(--spacing-2xl)',
  'margin-bottom: 24px': 'margin-bottom: var(--spacing-xl)',
  'margin-bottom: 12px': 'margin-bottom: var(--spacing-sm)',
  'margin-bottom: 16px': 'margin-bottom: var(--spacing-md)',
  'margin-bottom: 20px': 'margin-bottom: var(--spacing-lg)',

  // Font sizes
  'font-size: 12px': 'font-size: var(--font-size-xs)',
  'font-size: 14px': 'font-size: var(--font-size-sm)',
  'font-size: 15px': 'font-size: var(--font-size-base)',
  'font-size: 16px': 'font-size: var(--font-size-base)',
  'font-size: 18px': 'font-size: var(--font-size-lg)',
  'font-size: 20px': 'font-size: var(--font-size-lg)',
  'font-size: 24px': 'font-size: var(--font-size-xl)',
  'font-size: 30px': 'font-size: var(--font-size-2xl)',
  'font-size: 32px': 'font-size: var(--font-size-2xl)',
  'font-size: 36px': 'font-size: var(--font-size-3xl)',
  'font-size: 2rem': 'font-size: var(--font-size-2xl)',
  'font-size: 3rem': 'font-size: var(--font-size-3xl)',
  'font-size: 4rem': 'font-size: var(--font-size-3xl)',
  'font-size: 5rem': 'font-size: var(--font-size-3xl)',
  'font-size: 6rem': 'font-size: var(--font-size-3xl)',
  'font-size: 64px': 'font-size: var(--font-size-3xl)',
  'font-size: 80px': 'font-size: var(--font-size-3xl)',
  'font-size: 1rem': 'font-size: var(--font-size-base)',

  // Border radius
  'border-radius: 4px': 'border-radius: var(--radius-sm)',
  'border-radius: 6px': 'border-radius: var(--radius-md)',
  'border-radius: 8px': 'border-radius: var(--radius-lg)',
  'border-radius: 12px': 'border-radius: var(--radius-xl)',
  'border-radius: 16px': 'border-radius: var(--radius-2xl)',
  'border-radius: 100%': 'border-radius: var(--radius-full)',
  'border-radius: 1rem': 'border-radius: var(--radius-xl)',
  'border-radius: 2rem': 'border-radius: var(--radius-2xl)',
  'border-radius: 4rem': 'border-radius: var(--radius-full)',
  'border-radius: 5rem': 'border-radius: var(--radius-full)',
  'border-radius: 4px': 'border-radius: var(--radius-sm)',
  'border-radius: 8px': 'border-radius: var(--radius-md)',
  'border-radius: 12px': 'border-radius: var(--radius-lg)',
  'border-radius: 16px': 'border-radius: var(--radius-xl)',
  'border-radius: 24px': 'border-radius: var(--radius-2xl)',
  'border-radius: 100%': 'border-radius: var(--radius-full)',
  'border-radius: 999px': 'border-radius: var(--radius-full)',
  'border-radius: 50%': 'border-radius: var(--radius-full)',

  // Shadows (simplified - will need manual review for exact matches)
  'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05)': 'box-shadow: var(--shadow-sm)',
  'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1)': 'box-shadow: var(--shadow-sm)',
  'box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1)': 'box-shadow: var(--shadow-md)',
  'box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15)': 'box-shadow: var(--shadow-md)',
  'box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1)': 'box-shadow: var(--shadow-sm)',
  'box-shadow: 0 12px 32px rgba(16, 24, 64, 0.08)': 'box-shadow: var(--shadow-lg)',
  'box-shadow: 0 16px 40px rgba(15, 31, 53, 0.06)': 'box-shadow: var(--shadow-md)',
  'box-shadow: 0 18px 36px rgba(64, 135, 255, 0.35)': 'box-shadow: var(--shadow-lg)',
  'box-shadow: 0 32px 80px rgba(10, 17, 35, 0.45)': 'box-shadow: var(--shadow-xl)',

  // Common hardcoded colors
  'color: #333': 'color: var(--ion-text-color)',
  'color: #666': 'color: var(--ion-color-medium)',
  'color: #999': 'color: var(--ion-color-medium)',
  'color: #721c24': 'color: var(--ion-color-danger-shade)',
  'color: #34c759': 'color: var(--ion-color-success)',
  'color: #dc3545': 'color: var(--ion-color-danger)',
  'color: #007aff': 'color: var(--ion-color-primary)',
  'color: #856404': 'color: var(--ion-color-warning-shade)',
  'background: #fff3cd': 'background: var(--ion-color-warning-tint)',
  'background: #f8d7da': 'background: var(--ion-color-danger-tint)',
  'background: #d4edda': 'background: var(--ion-color-success-tint)',
  'background: #f8f9fa': 'background: var(--ion-color-light)',
  'background: white': 'background: var(--ion-background-color)',
  'background: #ffffff': 'background: var(--ion-background-color)',
  'background-color: #ffffff': 'background-color: var(--ion-background-color)',
  'border: 2px solid #ffc107': 'border: 2px solid var(--ion-color-warning)',
  'border: 2px solid #dc3545': 'border: 2px solid var(--ion-color-danger)',
  'border: 2px solid #28a745': 'border: 2px solid var(--ion-color-success)',
  'border: 2px solid #34c759': 'border: 2px solid var(--ion-color-success)',
  'border-bottom: 1px solid rgba(15, 31, 53, 0.06)': 'border-bottom: 1px solid var(--ion-color-light)',
  '--background: rgba(96, 125, 139, 0.16)': '--background: var(--ion-color-light)',

  // Gradient colors from WelcomeScreen
  'linear-gradient(135deg, #252c49, #111628)': 'linear-gradient(135deg, var(--ion-color-dark), var(--ion-color-darker))',
  'rgba(255, 255, 255, 0.76)': 'rgba(var(--ion-color-light-rgb), 0.76)',
  'rgba(255, 255, 255, 0.08)': 'rgba(var(--ion-color-light-rgb), 0.08)',
  'rgba(255, 255, 255, 0.15)': 'rgba(var(--ion-color-light-rgb), 0.15)',
  'rgba(0, 0, 0, 0.2)': 'rgba(var(--ion-color-dark-rgb), 0.2)',
  'rgba(0, 122, 255, 0.1)': 'rgba(var(--ion-color-primary-rgb), 0.1)',
  'rgba(0, 86, 179, 0.2)': 'rgba(var(--ion-color-primary-rgb), 0.2)',

  // Z-index
  'z-index: 2147483647': 'z-index: var(--z-index-max)',
  'z-index: 10000': 'z-index: var(--z-index-modal)',
  'z-index: 9999': 'z-index: var(--z-index-modal)',
  'z-index: 1000': 'z-index: var(--z-index-dropdown)',
};

// Files to process (from audit report)
const filesToFix = [
  'src/ui/pages/SimplifiedOnboarding/SeedPhraseScreen.scss',
  'src/ui/pages/SimplifiedOnboarding/VerificationScreen.scss',
  'src/ui/pages/SimplifiedOnboarding/SuccessScreen.scss',
  'src/ui/pages/SimplifiedOnboarding/BiometricScanScreen.scss',
  'src/ui/pages/SimplifiedOnboarding/WelcomeScreen.scss',
  'src/ui/pages/BiometricEnrollment/BiometricEnrollment.scss',
  'src/ui/pages/LockPage/LockPage.scss',
  'src/ui/pages/SimplifiedOnboarding/ProgressIndicator.scss',
  'src/ui/pages/GenerateSeedPhrase/GenerateSeedPhrase.scss',
  'src/ui/components/BiometricVerification/BiometricVerification.scss',
  'src/ui/pages/VerifySeedPhrase/VerifySeedPhrase.scss',
  'src/ui/pages/SetPasscode/SetPasscode.scss',
  'src/ui/pages/CreatePassword/CreatePassword.scss',
  'src/ui/pages/Credentials/Credentials.scss',
  'src/ui/components/EmptyStates/EmptyStates.scss',
  'src/ui/pages/Menu/Menu.scss',
  'src/ui/components/SeedPhraseDisplay/SeedPhraseDisplay.scss',
  'src/ui/components/ErrorBanner/ErrorBanner.scss',
  'src/ui/pages/Onboarding/Onboarding.scss',
  'src/ui/pages/VerifyRecoverySeedPhrase/VerifyRecoverySeedPhrase.scss',
  'src/ui/components/Footer/Footer.scss',
  'src/ui/pages/Scan/Scan.scss',
  'src/ui/pages/Identifiers/Identifiers.scss',
];

let totalReplacements = 0;
let filesModified = 0;

console.log('🔧 Starting automated design token fixes...\n');

filesToFix.forEach((relativePath) => {
  const filePath = path.join(__dirname, '..', relativePath);

  if (!fs.existsSync(filePath)) {
    console.log(`⚠️  File not found: ${relativePath}`);
    return;
  }

  let content = fs.readFileSync(filePath, 'utf8');
  let replacementsInFile = 0;
  const originalContent = content;

  // Apply all replacements
  Object.entries(replacements).forEach(([oldValue, newValue]) => {
    const regex = new RegExp(oldValue.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
    const matches = (content.match(regex) || []).length;
    if (matches > 0) {
      content = content.replace(regex, newValue);
      replacementsInFile += matches;
    }
  });

  if (content !== originalContent) {
    fs.writeFileSync(filePath, content, 'utf8');
    filesModified++;
    totalReplacements += replacementsInFile;
    console.log(`✅ ${relativePath} (${replacementsInFile} replacements)`);
  } else {
    console.log(`⏭️  ${relativePath} (already clean)`);
  }
});

console.log(`\n✨ Complete!`);
console.log(`   Files modified: ${filesModified}`);
console.log(`   Total replacements: ${totalReplacements}`);
console.log(`\n📝 Next step: Review changes and run visual regression tests\n`);
