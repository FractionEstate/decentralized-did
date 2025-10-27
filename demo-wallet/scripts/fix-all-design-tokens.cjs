#!/usr/bin/env node

/**
 * Comprehensive design token fix for all remaining issues
 */

const fs = require('fs');
const path = require('path');

const fixes = [
  // ReceiveCredential.scss
  {
    file: 'src/ui/pages/NotificationDetails/components/ReceiveCredential/ReceiveCredential.scss',
    replacements: [
      ['border-radius: 5rem', 'border-radius: var(--radius-full)'],
      ['border-radius: 4rem', 'border-radius: var(--radius-full)'],
      ['border-radius: 2rem', 'border-radius: var(--radius-2xl)'],
    ]
  },
  // MultiSigRequest.scss
  {
    file: 'src/ui/pages/NotificationDetails/components/MultiSigRequest/MultiSigRequest.scss',
    replacements: [
      ['border-radius: 1rem', 'border-radius: var(--radius-xl)'],
      ['border-radius: 2rem', 'border-radius: var(--radius-2xl)'],
      ['border-radius: 4rem', 'border-radius: var(--radius-full)'],
      ['box-shadow: none', 'box-shadow: var(--shadow-none)'],
    ]
  },
  // SystemThreatAlert.scss
  {
    file: 'src/ui/components/SystemThreatAlert/SystemThreatAlert.scss',
    replacements: [
      ['border-radius: 1rem', 'border-radius: var(--radius-xl)'],
      ['rgba(0, 86, 179, 0.2)', 'rgba(var(--ion-color-primary-rgb), 0.2)'],
    ]
  },
  // WelcomeScreen.scss - gradient colors
  {
    file: 'src/ui/pages/SimplifiedOnboarding/WelcomeScreen.scss',
    replacements: [
      ['#252c49', 'var(--ion-color-dark)'],
      ['#111628', 'var(--ion-color-darker)'],
      ['#ffffff', 'var(--ion-color-light-contrast)'],
    ]
  },
  // ConfirmConnectModal.scss
  {
    file: 'src/ui/pages/Menu/components/ConfirmConnectModal/ConfirmConnectModal.scss',
    replacements: [
      ['border-radius: 2rem', 'border-radius: var(--radius-2xl)'],
      ['border-radius: 1rem', 'border-radius: var(--radius-xl)'],
      ['box-shadow: none', 'box-shadow: var(--shadow-none)'],
    ]
  },
  // Notifications.scss
  {
    file: 'src/ui/pages/Notifications/Notifications.scss',
    replacements: [
      ['border-radius: 3rem', 'border-radius: var(--radius-full)'],
    ]
  },
  // Settings.scss
  {
    file: 'src/ui/pages/Menu/components/Settings/Settings.scss',
    replacements: [
      ['border-radius: 1rem', 'border-radius: var(--radius-xl)'],
      ['box-shadow: none', 'box-shadow: var(--shadow-none)'],
    ]
  },
  // Profile.scss
  {
    file: 'src/ui/pages/Menu/components/Profile/Profile.scss',
    replacements: [
      ['border-radius: 1rem', 'border-radius: var(--radius-xl)'],
      ['box-shadow: none', 'box-shadow: var(--shadow-none)'],
    ]
  },
  // Connections.scss
  {
    file: 'src/ui/pages/Connections/Connections.scss',
    replacements: [
      ['box-shadow: none', 'box-shadow: var(--shadow-none)'],
      ['z-index: 2', 'z-index: var(--z-index-dropdown)'],
    ]
  },
  // EditConnectionsModal.scss
  {
    file: 'src/ui/pages/ConnectionDetails/components/EditConnectionsModal.scss',
    replacements: [
      ['border-radius: 1rem', 'border-radius: var(--radius-xl)'],
      ['z-index: 10', 'z-index: var(--z-index-modal)'],
    ]
  },
  // ConnectionDetails.scss
  {
    file: 'src/ui/pages/ConnectionDetails/ConnectionDetails.scss',
    replacements: [
      ['border-radius: 3rem', 'border-radius: var(--radius-full)'],
      ['z-index: 100', 'z-index: var(--z-index-modal)'],
    ]
  },
  // IdentifierDetails.scss
  {
    file: 'src/ui/pages/IdentifierDetails/IdentifierDetails.scss',
    replacements: [
      ['border-radius: 3rem', 'border-radius: var(--radius-full)'],
    ]
  },
  // Identifiers.scss
  {
    file: 'src/ui/pages/Identifiers/Identifiers.scss',
    replacements: [
      ['box-shadow: none', 'box-shadow: var(--shadow-none)'],
    ]
  },
  // Credentials.scss
  {
    file: 'src/ui/pages/Credentials/Credentials.scss',
    replacements: [
      ['box-shadow: none', 'box-shadow: var(--shadow-none)'],
    ]
  },
  // LockPage.scss
  {
    file: 'src/ui/pages/LockPage/LockPage.scss',
    replacements: [
      ['z-index: 2147483647', 'z-index: var(--z-index-max)'],
    ]
  },
  // SimplifiedOnboarding/SeedPhraseScreen.scss
  {
    file: 'src/ui/pages/SimplifiedOnboarding/SeedPhraseScreen.scss',
    replacements: [
      ['color: #856404', 'color: var(--ion-color-warning-shade)'],
      ['color: #007aff', 'color: var(--ion-color-primary)'],
      ['rgba(0, 122, 255, 0.1)', 'rgba(var(--ion-color-primary-rgb), 0.1)'],
    ]
  },
  // BiometricScanScreen - remaining spacing issues
  {
    file: 'src/ui/pages/SimplifiedOnboarding/BiometricScanScreen.scss',
    replacements: [
      ['padding: 4px 0', 'padding: var(--spacing-2xs) 0'],
      ['padding: 2px 6px', 'padding: var(--spacing-2xs) var(--spacing-xs)'],
      ['spacing: 1', 'spacing: var(--spacing-2xs)'],
    ]
  },
];

console.log('🔧 Starting comprehensive design token fixes...\n');

let totalFiles = 0;
let totalReplacements = 0;
let errors = [];

fixes.forEach(({ file, replacements }) => {
  const filePath = path.join(__dirname, '..', file);

  if (!fs.existsSync(filePath)) {
    console.log(`⚠️  File not found: ${file}`);
    errors.push(file);
    return;
  }

  let content = fs.readFileSync(filePath, 'utf8');
  let fileReplacements = 0;

  replacements.forEach(([oldStr, newStr]) => {
    const count = (content.match(new RegExp(oldStr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length;
    if (count > 0) {
      content = content.replaceAll(oldStr, newStr);
      fileReplacements += count;
    }
  });

  if (fileReplacements > 0) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`✅ ${file} (${fileReplacements} replacements)`);
    totalFiles++;
    totalReplacements += fileReplacements;
  } else {
    console.log(`⏭️  ${file} (already clean)`);
  }
});

console.log('\n✨ Complete!');
console.log(`   Files modified: ${totalFiles}`);
console.log(`   Total replacements: ${totalReplacements}`);
if (errors.length > 0) {
  console.log(`   Errors: ${errors.length} files not found`);
}
console.log('\n📝 Next: Run npm run audit:design to verify');
