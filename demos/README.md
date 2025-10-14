# Interactive Demos

This directory contains interactive shell script demonstrations of the biometric DID toolkit.

## 🎬 Available Demos

### 1. Quick Enrollment (`01-quick-enrollment.sh`)
**Duration**: ~2 minutes
**Demonstrates**: Basic biometric DID generation

Shows the simplest workflow: scan a fingerprint, generate a DID, and store helper data.

```bash
./demos/01-quick-enrollment.sh
```

**What you'll learn:**
- How to use the `dec-did generate` command
- What enrollment data looks like
- How DIDs are formatted (`did:cardano:...`)
- Where helper data is stored

---

### 2. Verification (`02-verification.sh`)
**Duration**: ~2 minutes
**Demonstrates**: Reproducible digest verification

Shows how the fuzzy extractor reproduces the same digest from a noisy recapture.

```bash
./demos/02-verification.sh
```

**What you'll learn:**
- How to use the `dec-did verify` command
- How error correction handles noisy scans
- What happens when digests match/mismatch
- Proof of stable biometric authentication

**Prerequisites**: Run demo 1 first to create enrollment data.

---

### 3. Multi-Finger Enrollment (`03-multi-finger.sh`)
**Duration**: ~3 minutes
**Demonstrates**: 4-finger aggregation for 256-bit security

Shows how multiple fingers are combined for enhanced security and reliability.

```bash
./demos/03-multi-finger.sh
```

**What you'll learn:**
- Security levels by finger count (1-4 fingers)
- How XOR-based aggregation works
- Fallback mode (verify with 3/4 fingers)
- Quality-weighted authentication
- Finger rotation capabilities

---

### 4. Storage Backends (`04-storage-backends.sh`)
**Duration**: ~4 minutes
**Demonstrates**: Inline vs external helper data storage

Compares three storage strategies and their trade-offs.

```bash
./demos/04-storage-backends.sh
```

**What you'll learn:**
- Inline storage (embedded in metadata)
- File storage (local filesystem)
- IPFS storage (decentralized)
- Size limits and constraints
- When to use each backend

---

## 🚀 Quick Start

### Run All Demos
```bash
# Make scripts executable
chmod +x demos/*.sh

# Run demos in sequence
./demos/01-quick-enrollment.sh
./demos/02-verification.sh
./demos/03-multi-finger.sh
./demos/04-storage-backends.sh
```

### Requirements
- Python 3.11+ with toolkit installed (`pip install -e .`)
- `jq` for JSON parsing (`apt install jq` or `brew install jq`)
- Bash shell (Linux, macOS, WSL)
- Sample fingerprint data (`examples/sample_fingerprints.json`)

---

## 📁 Demo Output Files

After running demos, you'll find these files in `demos/`:

```
demos/
├── enrollment.json        # Single-finger enrollment (demo 1)
├── verification.json      # Verification result (demo 2)
├── multi-finger.json      # 4-finger enrollment (demo 3)
├── inline.json            # Inline storage example (demo 4)
├── file.json              # File storage example (demo 4)
└── helper_data/           # External helper data files (demo 4)
```

All output files are `.gitignore`d and won't be committed.

---

## 🎓 Educational Value

These demos are designed to:

1. **Show, don't tell**: Actual commands with real output
2. **Interactive pace**: Pause for explanations between steps
3. **Progressive complexity**: Build from simple to advanced
4. **Practical scenarios**: Real-world use cases and trade-offs
5. **Visual feedback**: Colors and formatting for clarity

---

## 🎥 Recording Demos

### For Asciinema (Terminal Cast)
```bash
# Install asciinema
pip install asciinema

# Record a demo
asciinema rec demo1.cast -c "./demos/01-quick-enrollment.sh"

# Upload to asciinema.org
asciinema upload demo1.cast
```

### For Documentation/README
```bash
# Run demo and capture output
./demos/01-quick-enrollment.sh | tee demo1-output.txt

# Or capture as markdown
./demos/01-quick-enrollment.sh 2>&1 | sed 's/\x1b\[[0-9;]*m//g' > demo1.md
```

---

## 🛠️ Customization

### Modify Wallet Address
Edit the `--wallet-address` parameter in each script:

```bash
--wallet-address "addr1qx2kd88c92haap2ymqnx04dx5ptdmr0pmagy7rzcsdqg2mkmv50k0"
```

### Use Your Own Fingerprints
Replace `examples/sample_fingerprints.json` with your own data:

```bash
--fingerprints /path/to/your/fingerprints.json
```

### Adjust Output Paths
Change `--output` to save files elsewhere:

```bash
--output /tmp/my-enrollment.json
```

---

## 🐛 Troubleshooting

### "dec-did: command not found"
Install the toolkit in development mode:
```bash
pip install -e .
```

### "jq: command not found"
Install jq for JSON parsing:
```bash
# Debian/Ubuntu
sudo apt install jq

# macOS
brew install jq

# Or remove jq usage (display raw JSON)
cat file.json  # instead of: cat file.json | jq .
```

### "sample_fingerprints.json not found"
Ensure you're running from the repository root:
```bash
cd /path/to/decentralized-did
./demos/01-quick-enrollment.sh
```

---

## 📚 Related Resources

- **SDK Examples**: `examples/sdk_demo.py` - Python API usage
- **API Reference**: `docs/SDK.md` - Comprehensive documentation
- **CLI Reference**: `dec-did --help` - Command-line options
- **Architecture**: `docs/architecture.md` - System design

---

## 🤝 Contributing

Want to add more demos?

1. Create `demos/05-your-demo.sh`
2. Follow the existing format (colors, steps, explanations)
3. Update this README with demo description
4. Test thoroughly before committing
5. Make executable: `chmod +x demos/05-your-demo.sh`

See `.github/copilot-instructions.md` for coding standards.
