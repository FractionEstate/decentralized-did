#!/usr/bin/env node

/**
 * Automated Design Token Replacement Script
 *
 * Applies design tokens to SCSS files automatically
 * Handles the most common patterns found in the audit
 */

import fs from 'fs';
import path from 'path';
import { glob } from 'glob';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PAGES_DIR = path.join(__dirname, '../src/ui/pages');

// Token replacement patterns (ordered by priority)
const REPLACEMENTS = [
  // Spacing replacements
  { pattern: /padding:\s*48px/g, replacement: 'padding: var(--spacing-3xl)' },
  { pattern: /margin:\s*48px/g, replacement: 'margin: var(--spacing-3xl)' },
  { pattern: /padding:\s*40px/g, replacement: 'padding: var(--spacing-2xl)' },
  { pattern: /margin:\s*40px/g, replacement: 'margin: var(--spacing-2xl)' },
  { pattern: /padding:\s*32px/g, replacement: 'padding: var(--spacing-xl)' },
  { pattern: /margin:\s*32px/g, replacement: 'margin: var(--spacing-xl)' },
  { pattern: /padding:\s*2rem/g, replacement: 'padding: var(--spacing-xl)' },
  { pattern: /margin:\s*2rem/g, replacement: 'margin: var(--spacing-xl)' },
  { pattern: /padding:\s*24px/g, replacement: 'padding: var(--spacing-lg)' },
  { pattern: /margin:\s*24px/g, replacement: 'margin: var(--spacing-lg)' },
  { pattern: /padding:\s*1\.5rem/g, replacement: 'padding: var(--spacing-lg)' },
  { pattern: /margin:\s*1\.5rem/g, replacement: 'margin: var(--spacing-lg)' },
  { pattern: /padding:\s*16px/g, replacement: 'padding: var(--spacing-md)' },
  { pattern: /margin:\s*16px/g, replacement: 'margin: var(--spacing-md)' },
  { pattern: /padding:\s*1rem/g, replacement: 'padding: var(--spacing-md)' },
  { pattern: /margin:\s*1rem/g, replacement: 'margin: var(--spacing-md)' },
  { pattern: /padding:\s*12px/g, replacement: 'padding: var(--spacing-sm)' },
  { pattern: /margin:\s*12px/g, replacement: 'margin: var(--spacing-sm)' },
  { pattern: /padding:\s*0\.75rem/g, replacement: 'padding: var(--spacing-sm)' },
  { pattern: /margin:\s*0\.75rem/g, replacement: 'margin: var(--spacing-sm)' },
  { pattern: /padding:\s*8px/g, replacement: 'padding: var(--spacing-xs)' },
  { pattern: /margin:\s*8px/g, replacement: 'margin: var(--spacing-xs)' },
  { pattern: /padding:\s*0\.5rem/g, replacement: 'padding: var(--spacing-xs)' },
  { pattern: /margin:\s*0\.5rem/g, replacement: 'margin: var(--spacing-xs)' },
  { pattern: /gap:\s*24px/g, replacement: 'gap: var(--spacing-lg)' },
  { pattern: /gap:\s*16px/g, replacement: 'gap: var(--spacing-md)' },
  { pattern: /gap:\s*12px/g, replacement: 'gap: var(--spacing-sm)' },
  { pattern: /gap:\s*8px/g, replacement: 'gap: var(--spacing-xs)' },
  { pattern: /gap:\s*1\.5rem/g, replacement: 'gap: var(--spacing-lg)' },
  { pattern: /gap:\s*1rem/g, replacement: 'gap: var(--spacing-md)' },
  { pattern: /gap:\s*0\.75rem/g, replacement: 'gap: var(--spacing-sm)' },
  { pattern: /gap:\s*0\.5rem/g, replacement: 'gap: var(--spacing-xs)' },

  // Font size replacements
  { pattern: /font-size:\s*36px/g, replacement: 'font-size: var(--font-size-3xl)' },
  { pattern: /font-size:\s*2\.25rem/g, replacement: 'font-size: var(--font-size-3xl)' },
  { pattern: /font-size:\s*30px/g, replacement: 'font-size: var(--font-size-2xl)' },
  { pattern: /font-size:\s*1\.875rem/g, replacement: 'font-size: var(--font-size-2xl)' },
  { pattern: /font-size:\s*28px/g, replacement: 'font-size: var(--font-size-2xl)' },
  { pattern: /font-size:\s*24px/g, replacement: 'font-size: var(--font-size-xl)' },
  { pattern: /font-size:\s*1\.5rem/g, replacement: 'font-size: var(--font-size-xl)' },
  { pattern: /font-size:\s*20px/g, replacement: 'font-size: var(--font-size-lg)' },
  { pattern: /font-size:\s*1\.25rem/g, replacement: 'font-size: var(--font-size-lg)' },
  { pattern: /font-size:\s*18px/g, replacement: 'font-size: var(--font-size-md)' },
  { pattern: /font-size:\s*1\.125rem/g, replacement: 'font-size: var(--font-size-md)' },
  { pattern: /font-size:\s*16px/g, replacement: 'font-size: var(--font-size-base)' },
  { pattern: /font-size:\s*1rem/g, replacement: 'font-size: var(--font-size-base)' },
  { pattern: /font-size:\s*14px/g, replacement: 'font-size: var(--font-size-sm)' },
  { pattern: /font-size:\s*0\.875rem/g, replacement: 'font-size: var(--font-size-sm)' },
  { pattern: /font-size:\s*12px/g, replacement: 'font-size: var(--font-size-xs)' },
  { pattern: /font-size:\s*0\.75rem/g, replacement: 'font-size: var(--font-size-xs)' },

  // Font weight replacements
  { pattern: /font-weight:\s*700/g, replacement: 'font-weight: var(--font-weight-bold)' },
  { pattern: /font-weight:\s*600/g, replacement: 'font-weight: var(--font-weight-semibold)' },
  { pattern: /font-weight:\s*500/g, replacement: 'font-weight: var(--font-weight-medium)' },
  { pattern: /font-weight:\s*400/g, replacement: 'font-weight: var(--font-weight-regular)' },

  // Border radius replacements
  { pattern: /border-radius:\s*24px/g, replacement: 'border-radius: var(--radius-2xl)' },
  { pattern: /border-radius:\s*16px/g, replacement: 'border-radius: var(--radius-xl)' },
  { pattern: /border-radius:\s*12px/g, replacement: 'border-radius: var(--radius-lg)' },
  { pattern: /border-radius:\s*8px/g, replacement: 'border-radius: var(--radius-md)' },
  { pattern: /border-radius:\s*4px/g, replacement: 'border-radius: var(--radius-sm)' },
  { pattern: /border-radius:\s*9999px/g, replacement: 'border-radius: var(--radius-full)' },
  { pattern: /border-radius:\s*50%/g, replacement: 'border-radius: var(--radius-full)' },

  // Line height replacements
  { pattern: /line-height:\s*1\.75/g, replacement: 'line-height: var(--line-height-relaxed)' },
  { pattern: /line-height:\s*1\.6/g, replacement: 'line-height: var(--line-height-relaxed)' },
  { pattern: /line-height:\s*1\.5/g, replacement: 'line-height: var(--line-height-normal)' },
  { pattern: /line-height:\s*1\.3/g, replacement: 'line-height: var(--line-height-tight)' },
  { pattern: /line-height:\s*1\.25/g, replacement: 'line-height: var(--line-height-tight)' },
];

class TokenReplacer {
  constructor() {
    this.stats = {
      totalFiles: 0,
      modifiedFiles: 0,
      totalReplacements: 0,
    };
  }

  async replace() {
    console.log('🔧 Starting automated design token replacement...\n');

    // Find all SCSS files in pages directory
    const scssFiles = await glob(`${PAGES_DIR}/**/*.scss`);
    this.stats.totalFiles = scssFiles.length;

    console.log(`Found ${scssFiles.length} SCSS files to process\n`);

    for (const file of scssFiles) {
      this.processFile(file);
    }

    console.log(`\n✅ Token replacement complete!`);
    console.log(`\n📊 Summary:`);
    console.log(`   Files processed: ${this.stats.totalFiles}`);
    console.log(`   Files modified: ${this.stats.modifiedFiles}`);
    console.log(`   Total replacements: ${this.stats.totalReplacements}`);
  }

  processFile(filePath) {
    let content = fs.readFileSync(filePath, 'utf-8');
    const originalContent = content;
    let fileReplacements = 0;

    // Apply all replacement patterns
    for (const { pattern, replacement } of REPLACEMENTS) {
      const matches = content.match(pattern);
      if (matches) {
        content = content.replace(pattern, replacement);
        fileReplacements += matches.length;
      }
    }

    // Only write if changes were made
    if (content !== originalContent) {
      fs.writeFileSync(filePath, content, 'utf-8');
      this.stats.modifiedFiles++;
      this.stats.totalReplacements += fileReplacements;

      const relativePath = path.relative(PAGES_DIR, filePath);
      console.log(`✓ ${relativePath} - ${fileReplacements} replacements`);
    }
  }
}

// Run replacement
const replacer = new TokenReplacer();
replacer.replace().catch(console.error);
