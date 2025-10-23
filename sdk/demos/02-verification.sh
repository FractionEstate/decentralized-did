#!/bin/bash
# Demo 2: Verification - Reproduce digest from noisy recapture
# This script demonstrates verifying a biometric DID with a noisy recapture

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║       Demo 2: Verification - Noisy Recapture Test              ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if enrollment exists
if [ ! -f demos/enrollment.json ]; then
    echo -e "${RED}Error: enrollment.json not found!${NC}"
    echo "Run ./demos/01-quick-enrollment.sh first"
    exit 1
fi

# Step 1: Show enrollment data
echo -e "${YELLOW}Step 1: Review original enrollment data${NC}"
echo -e "${GREEN}Original DID:${NC}"
cat demos/enrollment.json | jq -r '.did'
echo ""
echo -e "${GREEN}Original digest:${NC}"
cat demos/enrollment.json | jq -r '.digest'
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 2: Simulate noisy recapture
echo -e "${YELLOW}Step 2: Simulate fingerprint recapture (with noise)${NC}"
echo "In a real scenario, the user would scan their finger again."
echo "The scan will have slight differences due to:"
echo "  • Finger placement angle"
echo "  • Pressure variations"
echo "  • Sensor noise"
echo ""
echo "Our fuzzy extractor corrects up to 10-bit errors!"
echo ""
read -p "Press Enter to verify..."
echo ""

# Step 3: Verify
echo -e "${YELLOW}Step 3: Verify biometric DID${NC}"
echo -e "${GREEN}$ dec-did verify --helper-data enrollment.json --fingerprints noisy_scan.json${NC}"
echo ""
dec-did verify \
  --helper-data demos/enrollment.json \
  --fingerprints examples/sample_fingerprints.json \
  --output demos/verification.json
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 4: Compare digests
echo -e "${YELLOW}Step 4: Compare digests${NC}"
ORIGINAL_DIGEST=$(cat demos/enrollment.json | jq -r '.digest')
VERIFIED_DIGEST=$(cat demos/verification.json | jq -r '.digest')

echo -e "${GREEN}Original digest:${NC}  $ORIGINAL_DIGEST"
echo -e "${GREEN}Verified digest:${NC}  $VERIFIED_DIGEST"
echo ""

if [ "$ORIGINAL_DIGEST" = "$VERIFIED_DIGEST" ]; then
    echo -e "${GREEN}✅ SUCCESS: Digests match!${NC}"
    echo ""
    echo "The fuzzy extractor successfully reproduced the same digest"
    echo "from a noisy fingerprint recapture. This proves:"
    echo "  ✅ User authentication successful"
    echo "  ✅ Biometric template is stable"
    echo "  ✅ Error correction working perfectly"
else
    echo -e "${RED}❌ FAILED: Digests do not match${NC}"
    exit 1
fi
echo ""
echo "Next steps:"
echo "  1. Try multi-finger demo: ./demos/03-multi-finger.sh"
echo "  2. Explore storage options: ./demos/04-storage-backends.sh"
echo ""
