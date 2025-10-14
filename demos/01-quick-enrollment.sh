#!/bin/bash
# Demo 1: Quick Enrollment - Basic biometric DID generation
# This script demonstrates the simplest workflow: enroll a single finger and generate a DID

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║       Demo 1: Quick Enrollment - Single Finger DID             ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Show help
echo -e "${YELLOW}Step 1: View available commands${NC}"
echo -e "${GREEN}$ dec-did --help${NC}"
dec-did --help
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 2: Generate biometric DID
echo -e "${YELLOW}Step 2: Generate biometric DID from fingerprint${NC}"
echo -e "${GREEN}$ dec-did generate --wallet-address addr1qx2kd88... --output enrollment.json${NC}"
echo ""
echo "Using sample fingerprint data..."
dec-did generate \
  --wallet-address "addr1qx2kd88c92haap2ymqnx04dx5ptdmr0pmagy7rzcsdqg2mkmv50k0" \
  --fingerprints examples/sample_fingerprints.json \
  --output demos/enrollment.json
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 3: Show generated files
echo -e "${YELLOW}Step 3: Examine generated enrollment data${NC}"
echo -e "${GREEN}$ cat enrollment.json | jq .${NC}"
cat demos/enrollment.json | jq .
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 4: Extract DID
echo -e "${YELLOW}Step 4: Extract the generated DID${NC}"
DID=$(cat demos/enrollment.json | jq -r '.did')
echo -e "${GREEN}Generated DID:${NC}"
echo "  $DID"
echo ""
echo -e "${GREEN}✅ Enrollment complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Store helper data securely (enrollment.json)"
echo "  2. Use DID for identity verification"
echo "  3. Run verification demo: ./demos/02-verification.sh"
echo ""
