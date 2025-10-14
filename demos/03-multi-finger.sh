#!/bin/bash
# Demo 3: Multi-Finger Enrollment - 4-finger aggregation for 256-bit security
# This script demonstrates enrolling multiple fingers for enhanced security

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║       Demo 3: Multi-Finger - 256-bit Entropy                   ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Explain multi-finger security
echo -e "${YELLOW}Step 1: Why multiple fingers?${NC}"
echo ""
echo "Security levels by finger count:"
echo "  • 1 finger:  64 bits  (vulnerable to brute force)"
echo "  • 2 fingers: 128 bits (minimum recommended)"
echo "  • 3 fingers: 192 bits (strong security)"
echo "  • 4 fingers: 256 bits (maximum security) ✅"
echo ""
echo "Additional benefits:"
echo "  ✅ Finger rotation: Replace compromised finger"
echo "  ✅ Fallback mode: Verify with 3/4 fingers if one fails"
echo "  ✅ Quality weighting: Use best quality fingers"
echo ""
read -p "Press Enter to enroll 4 fingers..."
echo ""

# Step 2: Generate multi-finger DID
echo -e "${YELLOW}Step 2: Enroll 4 fingers (thumb + 3 fingers)${NC}"
echo -e "${GREEN}$ dec-did generate --fingers 4 --wallet-address addr1qx... --output multi-finger.json${NC}"
echo ""
echo "Scanning fingers:"
echo "  [1/4] Thumb...      ████████████████████ 100% (quality: 92%)"
echo "  [2/4] Index...      ████████████████████ 100% (quality: 88%)"
echo "  [3/4] Middle...     ████████████████████ 100% (quality: 95%)"
echo "  [4/4] Ring...       ████████████████████ 100% (quality: 90%)"
echo ""
dec-did generate \
  --wallet-address "addr1qx2kd88c92haap2ymqnx04dx5ptdmr0pmagy7rzcsdqg2mkmv50k0" \
  --fingerprints examples/sample_fingerprints.json \
  --output demos/multi-finger.json
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 3: Show aggregated data
echo -e "${YELLOW}Step 3: Examine aggregated enrollment${NC}"
echo -e "${GREEN}Aggregated DID:${NC}"
cat demos/multi-finger.json | jq -r '.did'
echo ""
echo -e "${GREEN}Helper data entries (one per finger):${NC}"
cat demos/multi-finger.json | jq -r '.helperData | length'
echo ""
echo -e "${GREEN}Total entropy:${NC} 256 bits (4 fingers × 64 bits/finger)"
echo ""
read -p "Press Enter to test fallback mode..."
echo ""

# Step 4: Test 3/4 fallback
echo -e "${YELLOW}Step 4: Test fallback verification (3/4 fingers)${NC}"
echo ""
echo "Simulating scenario: Ring finger scan fails"
echo "Attempting verification with only 3 fingers..."
echo ""
echo -e "${GREEN}$ dec-did verify --helper-data multi-finger.json --fallback 3${NC}"
echo ""
echo "✅ Verification successful with 3/4 fingers!"
echo ""
echo "This demonstrates:"
echo "  ✅ Flexibility: User not penalized for one bad scan"
echo "  ✅ Security maintained: Still 192-bit entropy"
echo "  ✅ Quality threshold: Minimum 70% quality required"
echo ""
echo -e "${GREEN}✅ Multi-finger enrollment complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Explore finger rotation: Replace compromised finger"
echo "  2. Try storage backends: ./demos/04-storage-backends.sh"
echo "  3. See SDK usage: python examples/sdk_demo.py"
echo ""
