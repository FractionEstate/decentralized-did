#!/bin/bash
# Demo 4: Storage Backends - Inline vs External helper data storage
# This script demonstrates different storage strategies for helper data

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║       Demo 4: Storage Backends - Inline vs External            ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Explain storage options
echo -e "${YELLOW}Step 1: Storage backend options${NC}"
echo ""
echo "Three storage strategies:"
echo ""
echo "1. Inline Storage (default)"
echo "   • Helper data embedded in Cardano metadata"
echo "   • ✅ Simple, no external dependencies"
echo "   • ✅ Atomic with transaction"
echo "   • ❌ Limited to 16 KB (Cardano constraint)"
echo ""
echo "2. File Storage"
echo "   • Helper data stored in local filesystem"
echo "   • ✅ No size limits"
echo "   • ✅ Fast access"
echo "   • ❌ Requires backup strategy"
echo ""
echo "3. IPFS Storage"
echo "   • Helper data on decentralized storage"
echo "   • ✅ Content-addressed (CID)"
echo "   • ✅ Decentralized, censorship-resistant"
echo "   • ❌ Requires IPFS node access"
echo ""
read -p "Press Enter to try each backend..."
echo ""

# Step 2: Inline storage (default)
echo -e "${YELLOW}Step 2: Generate with inline storage (default)${NC}"
echo -e "${GREEN}$ dec-did generate --storage inline --output inline.json${NC}"
echo ""
dec-did generate \
  --wallet-address "addr1qx2kd88c92haap2ymqnx04dx5ptdmr0pmagy7rzcsdqg2mkmv50k0" \
  --fingerprints examples/sample_fingerprints.json \
  --storage inline \
  --output demos/inline.json
echo ""
echo -e "${GREEN}Helper data included in metadata:${NC}"
cat demos/inline.json | jq '.helperStorage'
echo ""
INLINE_SIZE=$(cat demos/inline.json | wc -c)
echo "Total size: $INLINE_SIZE bytes (well under 16 KB limit)"
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 3: File storage
echo -e "${YELLOW}Step 3: Generate with file storage${NC}"
echo -e "${GREEN}$ dec-did generate --storage file --storage-path ./helper_data/ --output file.json${NC}"
echo ""
mkdir -p demos/helper_data
dec-did generate \
  --wallet-address "addr1qx2kd88c92haap2ymqnx04dx5ptdmr0pmagy7rzcsdqg2mkmv50k0" \
  --fingerprints examples/sample_fingerprints.json \
  --storage file \
  --storage-path demos/helper_data \
  --output demos/file.json
echo ""
echo -e "${GREEN}Helper data stored externally:${NC}"
cat demos/file.json | jq '.helperStorage, .helperUri'
echo ""
echo "Helper files created:"
ls -lh demos/helper_data/
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 4: IPFS storage (simulated)
echo -e "${YELLOW}Step 4: IPFS storage (demonstration)${NC}"
echo -e "${GREEN}$ dec-did generate --storage ipfs --ipfs-api /ip4/127.0.0.1/tcp/5001${NC}"
echo ""
echo "Note: This requires a running IPFS daemon."
echo "Starting local IPFS simulation..."
echo ""
echo "Would generate metadata like:"
echo '{'
echo '  "helperStorage": "external",'
echo '  "helperUri": "ipfs://QmX7K8eFJm9vVPqS8wP3ZYcZ9...",'
echo '  "did": "did:cardano:addr1qx...#digest"'
echo '}'
echo ""
echo -e "${GREEN}Benefits of IPFS:${NC}"
echo "  ✅ Content-addressed: CID proves data integrity"
echo "  ✅ Decentralized: No single point of failure"
echo "  ✅ Public pinning services available (Pinata, Infura)"
echo "  ✅ Works with Cardano metadata (URI reference)"
echo ""
read -p "Press Enter to compare..."
echo ""

# Step 5: Comparison
echo -e "${YELLOW}Step 5: Storage backend comparison${NC}"
echo ""
printf "%-15s %-10s %-15s %-20s\n" "Backend" "Size Limit" "Decentralized" "Best For"
printf "%-15s %-10s %-15s %-20s\n" "-------" "----------" "-------------" "--------"
printf "%-15s %-10s %-15s %-20s\n" "Inline" "16 KB" "✅ Yes" "Simple enrollment"
printf "%-15s %-10s %-15s %-20s\n" "File" "Unlimited" "❌ No" "Desktop wallets"
printf "%-15s %-10s %-15s %-20s\n" "IPFS" "Unlimited" "✅ Yes" "Public DIDs"
echo ""
echo -e "${GREEN}✅ Storage demo complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Create demo kit: dec-did demo-kit"
echo "  2. Explore SDK: python examples/sdk_demo.py"
echo "  3. Read docs: docs/SDK.md"
echo ""
