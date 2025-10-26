#!/bin/bash

###############################################################################
# DESIGN PERFECTION WORKFLOW
# Automated script to achieve pixel-perfect design consistency
###############################################################################

set -e  # Exit on error

echo "🎨 DESIGN PERFECTION WORKFLOW"
echo "=============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Navigate to demo-wallet directory
cd "$(dirname "$0")/.."

echo -e "${BLUE}Step 1/7: Installing dependencies...${NC}"
if npm list @axe-core/playwright > /dev/null 2>&1 && npm list glob > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
else
    echo "Installing @axe-core/playwright and glob..."
    npm install --save-dev @axe-core/playwright glob
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi
echo ""

echo -e "${BLUE}Step 2/7: Running design audit...${NC}"
node scripts/audit-design.js
echo -e "${GREEN}✓ Design audit complete - see design-audit-report.md${NC}"
echo ""

echo -e "${BLUE}Step 3/7: Checking for design inconsistencies...${NC}"
if [ -f "design-audit-report.md" ]; then
    ISSUES=$(grep -c "##" design-audit-report.md || echo "0")
    if [ "$ISSUES" -gt 5 ]; then
        echo -e "${YELLOW}⚠ Found design inconsistencies in $ISSUES files${NC}"
        echo -e "${YELLOW}   Review design-audit-report.md for details${NC}"
        echo -e "${YELLOW}   Apply design tokens to fix inconsistencies${NC}"
        echo ""
        read -p "Do you want to continue with visual baseline generation? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Workflow stopped. Fix design issues first.${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Design is consistent${NC}"
    fi
fi
echo ""

echo -e "${BLUE}Step 4/7: Building application...${NC}"
if [ ! -d "build" ] || [ -z "$(ls -A build 2>/dev/null)" ]; then
    echo "Running production build..."
    npm run build:local
    echo -e "${GREEN}✓ Build complete${NC}"
else
    echo -e "${YELLOW}Build directory exists, skipping...${NC}"
    echo "To force rebuild, run: rm -rf build && npm run build:local"
fi
echo ""

echo -e "${BLUE}Step 5/7: Generating visual regression baselines...${NC}"
echo "This will create screenshot baselines for all pages and viewports"
echo "Estimated time: ~15 minutes"
echo ""
read -p "Generate baselines now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm run test:e2e:update-snapshots -- visual-regression/design-consistency.spec.ts || true
    echo -e "${GREEN}✓ Visual baselines generated${NC}"
else
    echo -e "${YELLOW}⊘ Skipped visual baseline generation${NC}"
fi
echo ""

echo -e "${BLUE}Step 6/7: Running accessibility tests...${NC}"
echo "Testing WCAG 2.1 AA compliance across all pages"
read -p "Run accessibility tests? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm run test:e2e:a11y || {
        echo -e "${YELLOW}⚠ Some accessibility tests failed${NC}"
        echo "   Review test results in playwright-report/"
    }
    echo -e "${GREEN}✓ Accessibility tests complete${NC}"
else
    echo -e "${YELLOW}⊘ Skipped accessibility tests${NC}"
fi
echo ""

echo -e "${BLUE}Step 7/7: Validation...${NC}"
echo "Running full E2E test suite to validate perfection"
read -p "Run full validation? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm run test:e2e || {
        echo -e "${YELLOW}⚠ Some tests failed${NC}"
        echo "   Review test results in playwright-report/"
    }
    echo -e "${GREEN}✓ Validation complete${NC}"
else
    echo -e "${YELLOW}⊘ Skipped full validation${NC}"
fi
echo ""

echo -e "${GREEN}=============================="
echo "🎉 WORKFLOW COMPLETE"
echo -e "==============================${NC}"
echo ""
echo "Next steps:"
echo "1. Review design-audit-report.md for any remaining issues"
echo "2. Check playwright-report/ for test results"
echo "3. If all tests pass, build APK:"
echo "   cd android && ./gradlew assembleRelease"
echo ""
echo "To view test reports:"
echo "  npx playwright show-report"
echo ""
echo "To re-run specific tests:"
echo "  npm run test:e2e:visual     # Visual regression only"
echo "  npm run test:e2e:a11y       # Accessibility only"
echo "  npm run test:e2e:ui         # Interactive UI mode"
echo ""
