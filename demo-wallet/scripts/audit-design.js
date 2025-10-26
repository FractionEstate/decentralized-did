#!/usr/bin/env node

/**
 * Design Consistency Audit Script
 *
 * Scans all page SCSS files for design inconsistencies:
 * - Hardcoded spacing values (should use --spacing-*)
 * - Hardcoded font sizes (should use --font-size-*)
 * - Hardcoded border-radius (should use --radius-*)
 * - Inconsistent shadows (should use --shadow-*)
 * - Hardcoded colors (should use CSS variables)
 *
 * Generates a report with findings and recommendations
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

const PAGES_DIR = path.join(__dirname, '../../../src/ui/pages');
const OUTPUT_FILE = path.join(__dirname, '../../../design-audit-report.md');

// Patterns to detect
const PATTERNS = {
  hardcodedSpacing: /(?:padding|margin|gap):\s*(\d+(?:px|rem|em))/g,
  hardcodedFontSize: /font-size:\s*(\d+(?:px|rem|em))/g,
  hardcodedBorderRadius: /border-radius:\s*(\d+(?:px|rem|%))/g,
  hardcodedShadow: /box-shadow:\s*([^;]+)/g,
  hardcodedColor: /#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)/g,
  hardcodedZIndex: /z-index:\s*(\d+)/g,
};

// Design tokens that should be used
const RECOMMENDATIONS = {
  spacing: '--spacing-xs|--spacing-sm|--spacing-md|--spacing-lg|--spacing-xl|--spacing-2xl',
  fontSize: '--font-size-xs|--font-size-sm|--font-size-base|--font-size-md|--font-size-lg|--font-size-xl|--font-size-2xl',
  borderRadius: '--radius-sm|--radius-md|--radius-lg|--radius-xl|--radius-2xl|--radius-full',
  shadow: '--shadow-xs|--shadow-sm|--shadow-md|--shadow-lg|--shadow-xl',
  color: 'var(--ion-color-*) or var(--color-*)',
  zIndex: '--z-index-dropdown|--z-index-modal|--z-index-tooltip|--z-index-toast',
};

class DesignAuditor {
  constructor() {
    this.findings = [];
    this.stats = {
      totalFiles: 0,
      filesWithIssues: 0,
      totalIssues: 0,
      issuesByType: {},
    };
  }

  async audit() {
    console.log('🔍 Starting design consistency audit...\n');

    // Find all SCSS files in pages directory
    const scssFiles = glob.sync(`${PAGES_DIR}/**/*.scss`);
    this.stats.totalFiles = scssFiles.length;

    console.log(`Found ${scssFiles.length} SCSS files to audit\n`);

    for (const file of scssFiles) {
      this.auditFile(file);
    }

    this.generateReport();
    console.log(`\n✅ Audit complete! Report saved to: ${OUTPUT_FILE}`);
    console.log(`\n📊 Summary:`);
    console.log(`   Files scanned: ${this.stats.totalFiles}`);
    console.log(`   Files with issues: ${this.stats.filesWithIssues}`);
    console.log(`   Total issues found: ${this.stats.totalIssues}`);
  }

  auditFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf-8');
    const relativePath = path.relative(PAGES_DIR, filePath);
    const fileFindings = [];

    // Check for hardcoded spacing
    let matches = content.matchAll(PATTERNS.hardcodedSpacing);
    for (const match of matches) {
      // Skip if already using CSS variables
      if (match[0].includes('var(--')) continue;

      fileFindings.push({
        type: 'spacing',
        line: this.getLineNumber(content, match.index),
        code: match[0],
        recommendation: RECOMMENDATIONS.spacing,
      });
    }

    // Check for hardcoded font sizes
    matches = content.matchAll(PATTERNS.hardcodedFontSize);
    for (const match of matches) {
      if (match[0].includes('var(--')) continue;

      fileFindings.push({
        type: 'fontSize',
        line: this.getLineNumber(content, match.index),
        code: match[0],
        recommendation: RECOMMENDATIONS.fontSize,
      });
    }

    // Check for hardcoded border-radius
    matches = content.matchAll(PATTERNS.hardcodedBorderRadius);
    for (const match of matches) {
      if (match[0].includes('var(--')) continue;

      fileFindings.push({
        type: 'borderRadius',
        line: this.getLineNumber(content, match.index),
        code: match[0],
        recommendation: RECOMMENDATIONS.borderRadius,
      });
    }

    // Check for hardcoded shadows
    matches = content.matchAll(PATTERNS.hardcodedShadow);
    for (const match of matches) {
      if (match[0].includes('var(--')) continue;

      fileFindings.push({
        type: 'shadow',
        line: this.getLineNumber(content, match.index),
        code: match[0],
        recommendation: RECOMMENDATIONS.shadow,
      });
    }

    // Check for hardcoded colors
    matches = content.matchAll(PATTERNS.hardcodedColor);
    for (const match of matches) {
      // Skip if in a comment or already in a variable definition
      const lineContent = this.getLineContent(content, match.index);
      if (lineContent.includes('//') || lineContent.includes('/*') || lineContent.includes('--')) {
        continue;
      }

      fileFindings.push({
        type: 'color',
        line: this.getLineNumber(content, match.index),
        code: match[0],
        recommendation: RECOMMENDATIONS.color,
      });
    }

    // Check for hardcoded z-index
    matches = content.matchAll(PATTERNS.hardcodedZIndex);
    for (const match of matches) {
      if (match[0].includes('var(--')) continue;

      fileFindings.push({
        type: 'zIndex',
        line: this.getLineNumber(content, match.index),
        code: match[0],
        recommendation: RECOMMENDATIONS.zIndex,
      });
    }

    if (fileFindings.length > 0) {
      this.findings.push({
        file: relativePath,
        fullPath: filePath,
        issues: fileFindings,
      });
      this.stats.filesWithIssues++;
      this.stats.totalIssues += fileFindings.length;

      // Count issues by type
      for (const finding of fileFindings) {
        this.stats.issuesByType[finding.type] =
          (this.stats.issuesByType[finding.type] || 0) + 1;
      }
    }
  }

  getLineNumber(content, index) {
    return content.substring(0, index).split('\n').length;
  }

  getLineContent(content, index) {
    const lines = content.split('\n');
    const lineNumber = this.getLineNumber(content, index) - 1;
    return lines[lineNumber] || '';
  }

  generateReport() {
    let report = '# Design Consistency Audit Report\n\n';
    report += `**Generated:** ${new Date().toISOString()}\n\n`;
    report += '## Summary\n\n';
    report += `- **Total Files Scanned:** ${this.stats.totalFiles}\n`;
    report += `- **Files with Issues:** ${this.stats.filesWithIssues}\n`;
    report += `- **Total Issues Found:** ${this.stats.totalIssues}\n\n`;

    report += '### Issues by Type\n\n';
    report += '| Type | Count |\n';
    report += '|------|-------|\n';
    for (const [type, count] of Object.entries(this.stats.issuesByType)) {
      report += `| ${type} | ${count} |\n`;
    }
    report += '\n';

    report += '## Priority Files to Fix\n\n';
    report += 'Files sorted by number of issues (highest first):\n\n';

    const sortedFindings = [...this.findings].sort((a, b) => b.issues.length - a.issues.length);

    for (const finding of sortedFindings.slice(0, 10)) {
      report += `### ${finding.file} (${finding.issues.length} issues)\n\n`;

      // Group by type
      const byType = {};
      for (const issue of finding.issues) {
        if (!byType[issue.type]) byType[issue.type] = [];
        byType[issue.type].push(issue);
      }

      for (const [type, issues] of Object.entries(byType)) {
        report += `**${type}** (${issues.length} occurrences):\n`;
        for (const issue of issues.slice(0, 3)) {
          report += `- Line ${issue.line}: \`${issue.code}\`\n`;
          report += `  → Use: \`${issue.recommendation}\`\n`;
        }
        if (issues.length > 3) {
          report += `  ... and ${issues.length - 3} more\n`;
        }
        report += '\n';
      }
    }

    report += '\n## Detailed Findings\n\n';

    for (const finding of sortedFindings) {
      report += `<details>\n`;
      report += `<summary><strong>${finding.file}</strong> - ${finding.issues.length} issues</summary>\n\n`;

      for (const issue of finding.issues) {
        report += `**Line ${issue.line}** (${issue.type}):\n`;
        report += `\`\`\`scss\n${issue.code}\n\`\`\`\n`;
        report += `→ **Recommended:** \`${issue.recommendation}\`\n\n`;
      }

      report += `</details>\n\n`;
    }

    report += '## Action Items\n\n';
    report += '1. **Update BiometricEnrollment** (if top priority)\n';
    report += '   - Replace hardcoded values with design tokens\n';
    report += '   - Test visual appearance after changes\n\n';
    report += '2. **Update remaining pages** (in priority order)\n';
    report += '   - Focus on pages with most issues first\n';
    report += '   - Maintain consistent patterns\n\n';
    report += '3. **Run visual regression tests**\n';
    report += '   ```bash\n';
    report += '   npm run test:e2e -- visual-regression/design-consistency.spec.ts\n';
    report += '   ```\n\n';
    report += '4. **Generate new screenshot baselines**\n';
    report += '   ```bash\n';
    report += '   npm run test:e2e -- --update-snapshots\n';
    report += '   ```\n\n';

    fs.writeFileSync(OUTPUT_FILE, report);
  }
}

// Run audit
const auditor = new DesignAuditor();
auditor.audit().catch(console.error);
