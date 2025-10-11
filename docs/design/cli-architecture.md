# CLI Architecture and User Experience Design

**Phase 3, Task 1 - CLI Architecture and User Flows**
**Date**: 2025-10-11
**Target**: Production-ready CLI with comprehensive validation, error handling, and developer tooling
**Copyright**: 2025 Decentralized DID Project
**License**: Apache 2.0

---

## Executive Summary

This document defines the architecture for a production-ready CLI that enables biometric DID enrollment, verification, rotation, revocation, and export workflows. The design prioritizes:

1. **Usability**: Clear commands, helpful error messages, progressive disclosure
2. **Reliability**: Comprehensive validation, graceful error handling, safe defaults
3. **Extensibility**: Plugin architecture for storage backends, biometric sources, output formats
4. **Developer Experience**: Rich logging, debugging tools, scripting support

**Key Design Principles**:
- ✅ **Convention over Configuration**: Sensible defaults, minimal required arguments
- ✅ **Progressive Disclosure**: Simple commands for common cases, advanced options for power users
- ✅ **Fail-Fast Validation**: Catch errors early with clear recovery guidance
- ✅ **Open-Source Only**: All dependencies and integrations use open-source tools

---

## 1. Command Structure

### 1.1 Command Hierarchy

```
dec-did                             # Root command (aliased from python -m decentralized_did.cli)
├── enroll                          # Primary enrollment workflow
│   ├── --input <file>              # Biometric input (JSON with minutiae)
│   ├── --wallet <address>          # Cardano wallet address
│   ├── --output <file>             # Metadata output path
│   ├── --format <wallet|cip30>     # Output format
│   ├── --helpers-output <file>     # Helper data output (optional)
│   ├── --helper-uri <uri>          # External helper URI (IPFS, Arweave, etc.)
│   ├── --label <int>               # Metadata label (default: 1990)
│   ├── --quality-threshold <int>   # Minimum quality score (default: 70)
│   └── --dry-run                   # Validate without writing files
│
├── verify                          # Verification workflow
│   ├── --metadata <file>           # Enrolled metadata
│   ├── --input <file>              # New biometric scan
│   ├── --helpers <file>            # External helper data (if needed)
│   └── --show-quality              # Display quality metrics
│
├── rotate                          # Key rotation workflow
│   ├── --metadata <file>           # Existing metadata
│   ├── --input <file>              # New biometric scan
│   ├── --output <file>             # New metadata output
│   └── --reason <string>           # Rotation reason (audit log)
│
├── revoke                          # Revocation workflow
│   ├── --finger-id <id>            # Finger to revoke
│   ├-- --metadata <file>           # Existing metadata
│   ├── --output <file>             # Updated metadata
│   └── --reason <string>           # Revocation reason
│
├── export                          # Export utilities
│   ├── --metadata <file>           # Source metadata
│   ├── --format <json|cbor|yaml>   # Output format
│   ├── --output <file>             # Export destination
│   └── --extract <did|helpers|keys> # What to extract
│
├── validate                        # Schema validation
│   ├── --metadata <file>           # Metadata to validate
│   ├── --helpers <file>            # Helper data to validate
│   └── --schema-version <version>  # Schema version to validate against
│
├── demo-kit                        # Demo artifact generator (existing)
│   ├── --input <file>              # Biometric input
│   ├── --wallet <address>          # Wallet address
│   ├── --output-dir <dir>          # Output directory
│   ├── --zip <file>                # Optional zip archive
│   └── --helper-uri <uri>          # External helper URI
│
├── config                          # Configuration management
│   ├── init                        # Initialize config file
│   ├── show                        # Display current config
│   ├── set <key> <value>           # Set config value
│   └── validate                    # Validate config file
│
└── plugin                          # Plugin management
    ├── list                        # List installed plugins
    ├── install <name>              # Install plugin
    └── validate <path>             # Validate plugin structure
```

### 1.2 Command Aliases

For convenience, common commands have short aliases:

| Full Command | Alias | Description |
|--------------|-------|-------------|
| `dec-did enroll` | `dec-did gen` | Generate enrollment |
| `dec-did verify` | `dec-did check` | Verify biometric |
| `dec-did validate` | `dec-did val` | Validate schema |
| `dec-did export` | `dec-did exp` | Export data |

### 1.3 Global Options

Available across all commands:

```bash
--verbose, -v           # Increase verbosity (can be repeated: -vv, -vvv)
--quiet, -q             # Suppress all output except errors
--config <file>         # Custom config file path
--no-color              # Disable colored output
--json-output           # Machine-readable JSON output
--help, -h              # Show command help
--version               # Show version information
```

---

## 2. User Flow Wireframes

### 2.1 Enrollment Flow (Single Finger)

```
$ dec-did enroll --input finger1.json --wallet addr_test1...

┌─────────────────────────────────────────────────────────────┐
│ Biometric DID Enrollment                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ✓ Loaded biometric data: finger1.json                       │
│   • Finger ID: index_right                                  │
│   • Minutiae count: 42                                      │
│   • Quality score: 85 (good)                                │
│                                                              │
│ ⠿ Generating cryptographic key...                           │
│   • BCH error correction: 10 bits                           │
│   • Key derivation: BLAKE3                                  │
│                                                              │
│ ✓ Enrollment complete!                                      │
│                                                              │
│ DID: did:cardano:addr_test1...#biometric-4f2a8b9c          │
│ Metadata label: 1990                                        │
│ Helper storage: inline (113 bytes)                          │
│                                                              │
│ Metadata written to: metadata.json                          │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ Next steps:                                                  │
│  • Review metadata: dec-did validate --metadata metadata.json│
│  • Test verification: dec-did verify --metadata metadata.json│
│                        --input finger1.json                  │
│  • Submit to Cardano: (use wallet or cardano-cli)          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Enrollment Flow (Multi-Finger with Quality Feedback)

```
$ dec-did enroll --input fingers.json --wallet addr_test1... --verbose

┌─────────────────────────────────────────────────────────────┐
│ Biometric DID Enrollment (Multi-Finger)                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ✓ Loaded biometric data: fingers.json                       │
│                                                              │
│ Finger 1: index_right                                       │
│   • Minutiae: 42                                            │
│   • Quality: 85 ██████████████████░░ (good)                │
│   • Status: ✓ Accepted                                      │
│                                                              │
│ Finger 2: middle_right                                      │
│   • Minutiae: 38                                            │
│   • Quality: 78 ███████████████░░░░░ (good)                │
│   • Status: ✓ Accepted                                      │
│                                                              │
│ Finger 3: ring_right                                        │
│   • Minutiae: 31                                            │
│   • Quality: 65 █████████████░░░░░░░ (fair)                │
│   • Status: ⚠ Accepted (below 70 threshold)                │
│   • Recommendation: Consider re-scanning for better quality │
│                                                              │
│ Finger 4: pinky_right                                       │
│   • Minutiae: 28                                            │
│   • Quality: 45 █████████░░░░░░░░░░░ (poor)                │
│   • Status: ✗ Rejected (below 70 threshold)                │
│                                                              │
│ ⚠ Quality check failed                                      │
│                                                              │
│ 3/4 fingers meet quality threshold (70)                     │
│ Average quality: 69.3 (target: ≥75 for best experience)     │
│                                                              │
│ Options:                                                     │
│  1. Re-scan low-quality fingers (recommended)               │
│  2. Continue with 3 fingers (--allow-partial)               │
│  3. Lower threshold (--quality-threshold 60)                │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Error: Quality check failed. Use --allow-partial to continue with 3/4 fingers.
```

### 2.3 Verification Flow

```
$ dec-did verify --metadata metadata.json --input new_scan.json

┌─────────────────────────────────────────────────────────────┐
│ Biometric Verification                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ✓ Loaded metadata: metadata.json                            │
│   • DID: did:cardano:addr_test1...#biometric-4f2a8b9c       │
│   • Enrolled: 2025-10-11 14:23:45 UTC                       │
│   • Fingers: 4 (index, middle, ring, pinky - right hand)    │
│                                                              │
│ ✓ Loaded verification scan: new_scan.json                   │
│   • Fingers: 4                                              │
│                                                              │
│ ⠿ Verifying biometric match...                              │
│                                                              │
│ Finger 1 (index_right):                                     │
│   ✓ Helper data loaded                                      │
│   ✓ Key reproduced successfully                             │
│   • Quality: 82 (good)                                      │
│   • Noise estimate: 4.2%                                    │
│                                                              │
│ Finger 2 (middle_right):                                    │
│   ✓ Helper data loaded                                      │
│   ✓ Key reproduced successfully                             │
│   • Quality: 79 (good)                                      │
│   • Noise estimate: 5.8%                                    │
│                                                              │
│ Finger 3 (ring_right):                                      │
│   ✓ Helper data loaded                                      │
│   ✓ Key reproduced successfully                             │
│   • Quality: 73 (fair)                                      │
│   • Noise estimate: 8.1%                                    │
│                                                              │
│ Finger 4 (pinky_right):                                     │
│   ✓ Helper data loaded                                      │
│   ✓ Key reproduced successfully                             │
│   • Quality: 76 (good)                                      │
│   • Noise estimate: 6.3%                                    │
│                                                              │
│ ⠿ Aggregating keys...                                       │
│   ✓ Master key aggregated (4/4 fingers)                     │
│   ✓ DID hash verified                                       │
│                                                              │
│ ✅ Verification SUCCESSFUL                                   │
│                                                              │
│ Verification details:                                        │
│   • Fingers matched: 4/4                                    │
│   • Average quality: 77.5                                   │
│   • Average noise: 6.1%                                     │
│   • Verification time: 187 ms                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 Verification Failure Flow

```
$ dec-did verify --metadata metadata.json --input wrong_person.json

┌─────────────────────────────────────────────────────────────┐
│ Biometric Verification                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ✓ Loaded metadata: metadata.json                            │
│ ✓ Loaded verification scan: wrong_person.json               │
│                                                              │
│ ⠿ Verifying biometric match...                              │
│                                                              │
│ Finger 1 (index_right):                                     │
│   ✓ Helper data loaded                                      │
│   ✗ Key reproduction failed (BCH decoding error)            │
│   • Quality: 81 (good)                                      │
│   • Estimated errors: >10 bits (exceeds BCH capacity)       │
│                                                              │
│ Finger 2 (middle_right):                                    │
│   ✓ Helper data loaded                                      │
│   ✗ Key reproduction failed                                 │
│   • Quality: 78                                             │
│                                                              │
│ Finger 3 (ring_right):                                      │
│   ✓ Helper data loaded                                      │
│   ✗ Key reproduction failed                                 │
│   • Quality: 76                                             │
│                                                              │
│ Finger 4 (pinky_right):                                     │
│   ✓ Helper data loaded                                      │
│   ✗ Key reproduction failed                                 │
│   • Quality: 80                                             │
│                                                              │
│ ❌ Verification FAILED                                       │
│                                                              │
│ Diagnosis:                                                   │
│   • All 4 fingers failed to reproduce keys                  │
│   • Scan quality is good (avg 78.75)                        │
│   • Likely cause: Different person's biometric              │
│                                                              │
│ This is expected behavior - the system correctly rejected   │
│ an impostor biometric.                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Exit code: 1
```

---

## 3. Error Message Taxonomy

### 3.1 Error Categories

Errors are classified into hierarchical categories for consistent handling:

```
┌──────────────────────────────────────────────────────────────┐
│ Error Categories                                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 1. Input Validation Errors (Exit Code: 2)                   │
│    • Invalid file paths                                     │
│    • Malformed JSON                                         │
│    • Schema validation failures                             │
│    • Missing required fields                                │
│                                                              │
│ 2. Quality Errors (Exit Code: 3)                            │
│    • Low biometric quality                                  │
│    • Insufficient minutiae count                            │
│    • Poor scan conditions                                   │
│                                                              │
│ 3. Verification Errors (Exit Code: 4)                       │
│    • Biometric mismatch                                     │
│    • Helper data not found                                  │
│    • DID hash mismatch                                      │
│                                                              │
│ 4. System Errors (Exit Code: 5)                             │
│    • File I/O errors                                        │
│    • Permission denied                                      │
│    • Disk full                                              │
│                                                              │
│ 5. Configuration Errors (Exit Code: 6)                      │
│    • Invalid config file                                    │
│    • Missing configuration                                  │
│    • Conflicting options                                    │
│                                                              │
│ 6. Plugin Errors (Exit Code: 7)                             │
│    • Plugin not found                                       │
│    • Plugin load failure                                    │
│    • Plugin API mismatch                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Error Message Structure

All error messages follow a consistent structure:

```
┌──────────────────────────────────────────────────────────────┐
│ Error Message Structure                                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ❌ [ERROR TYPE]: Brief description                          │
│                                                              │
│ Context:                                                     │
│   • Key: value                                              │
│   • Key: value                                              │
│                                                              │
│ Cause:                                                       │
│   Detailed explanation of what went wrong                   │
│                                                              │
│ Solution:                                                    │
│   1. Step one to resolve                                    │
│   2. Step two to resolve                                    │
│   3. Alternative approach                                   │
│                                                              │
│ Documentation:                                               │
│   https://docs.example.com/error-codes#[CODE]              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.3 Example Error Messages

**Input Validation Error:**
```
❌ VALIDATION ERROR: Invalid biometric input format

Context:
  • File: fingers.json
  • Field: minutiae[2].angle
  • Value: 450
  • Expected: 0-359

Cause:
  Minutiae angle must be in range [0, 359] degrees.
  Found value 450 which is out of bounds.

Solution:
  1. Check minutiae data for finger ID 'ring_right'
  2. Verify angle values are in degrees (0-359)
  3. Re-export minutiae from scanner software

Documentation:
  https://github.com/FractionEstate/decentralized-did/blob/main/docs/biometric-format.md#minutiae-format
```

**Quality Error:**
```
❌ QUALITY ERROR: Biometric quality below threshold

Context:
  • Finger: index_right
  • Quality: 62
  • Threshold: 70
  • Minutiae count: 28

Cause:
  Biometric quality score (62) is below the minimum threshold (70).
  This may result in verification failures.

Solution:
  1. Clean the fingerprint scanner
  2. Ensure finger is dry and properly positioned
  3. Retry scan with better pressure/contact
  4. If problem persists, use a different finger
  5. Override threshold with --quality-threshold 60 (not recommended)

Quality Guide:
  • 90-100: Excellent (recommended)
  • 75-89:  Good
  • 60-74:  Fair (may work but risky)
  • <60:    Poor (high failure rate)

Documentation:
  https://github.com/FractionEstate/decentralized-did/blob/main/docs/quality-guidelines.md
```

**System Error:**
```
❌ SYSTEM ERROR: Cannot write output file

Context:
  • File: /protected/metadata.json
  • Operation: write
  • User: current_user

Cause:
  Permission denied when writing to /protected/metadata.json.
  The current user does not have write access to this directory.

Solution:
  1. Choose a different output directory: --output ~/metadata.json
  2. Grant write permission: chmod u+w /protected
  3. Run with elevated privileges: sudo dec-did ... (not recommended)
  4. Use default output location (current directory)

Documentation:
  https://github.com/FractionEstate/decentralized-did/blob/main/docs/troubleshooting.md#permission-errors
```

---

## 4. Progress Indicators and Logging

### 4.1 Logging Levels

Four logging levels with increasing verbosity:

| Level | Flag | Description | Use Case |
|-------|------|-------------|----------|
| **Quiet** | `--quiet, -q` | Errors only | Scripts, CI/CD |
| **Normal** | (default) | Key milestones | Interactive CLI |
| **Verbose** | `--verbose, -v` | Detailed steps | Debugging |
| **Debug** | `-vv` | All operations | Development |

### 4.2 Progress Indicators

**Normal Mode** - Clean, minimal output:
```
$ dec-did enroll --input fingers.json --wallet addr_test1...

✓ Loaded biometric data (4 fingers)
⠿ Generating cryptographic keys...
✓ Enrollment complete

DID: did:cardano:addr_test1...#biometric-4f2a8b9c
Metadata: metadata.json
```

**Verbose Mode** - Detailed progress:
```
$ dec-did enroll --input fingers.json --wallet addr_test1... -v

[2025-10-11 14:23:45] INFO: Starting enrollment process
[2025-10-11 14:23:45] INFO: Loading biometric data from fingers.json
[2025-10-11 14:23:45] DEBUG: Validating JSON schema
[2025-10-11 14:23:45] DEBUG: Found 4 fingers in input
[2025-10-11 14:23:45] INFO: Processing finger: index_right
[2025-10-11 14:23:45] DEBUG:   Minutiae count: 42
[2025-10-11 14:23:45] DEBUG:   Quality score: 85
[2025-10-11 14:23:45] DEBUG:   Quantizing minutiae (grid=0.05, angles=32)
[2025-10-11 14:23:45] DEBUG:   BCH encoding (K=64, N=127, T=10)
[2025-10-11 14:23:45] DEBUG:   Key derivation (BLAKE3)
[2025-10-11 14:23:46] INFO: ✓ Finger index_right enrolled
[2025-10-11 14:23:46] INFO: Processing finger: middle_right
[2025-10-11 14:23:46] DEBUG:   Minutiae count: 38
[2025-10-11 14:23:46] DEBUG:   Quality score: 78
...
[2025-10-11 14:23:48] INFO: Aggregating 4 finger keys
[2025-10-11 14:23:48] DEBUG: XOR aggregation
[2025-10-11 14:23:48] INFO: Building DID
[2025-10-11 14:23:48] DEBUG: DID fragment: #biometric-4f2a8b9c
[2025-10-11 14:23:48] INFO: Writing metadata to metadata.json
[2025-10-11 14:23:48] INFO: ✓ Enrollment complete

DID: did:cardano:addr_test1...#biometric-4f2a8b9c
Metadata: metadata.json
```

**Debug Mode** - Everything including internals:
```
$ dec-did enroll --input fingers.json --wallet addr_test1... -vv

[2025-10-11 14:23:45.123] DEBUG: sys.argv: ['dec-did', 'enroll', '--input', 'fingers.json', ...]
[2025-10-11 14:23:45.125] DEBUG: Working directory: /home/user/biometric-did
[2025-10-11 14:23:45.126] DEBUG: Python: 3.11.13
[2025-10-11 14:23:45.127] DEBUG: Platform: Linux-5.15.0-x86_64
[2025-10-11 14:23:45.128] DEBUG: Loading configuration from ~/.dec-did/config.toml
[2025-10-11 14:23:45.130] DEBUG: Config: {'default_label': 1990, 'quality_threshold': 70, ...}
[2025-10-11 14:23:45.132] INFO: Starting enrollment process
[2025-10-11 14:23:45.134] DEBUG: Opening file: fingers.json
[2025-10-11 14:23:45.145] DEBUG: JSON parsed: 4 fingers, wallet=addr_test1...
[2025-10-11 14:23:45.146] DEBUG: Validating against schema version 1.0
[2025-10-11 14:23:45.158] DEBUG: Schema validation passed
[2025-10-11 14:23:45.159] INFO: Processing finger: index_right
[2025-10-11 14:23:45.160] DEBUG:   Raw minutiae: [(x=120, y=85, angle=45), ...]
[2025-10-11 14:23:45.161] DEBUG:   Quantization grid: 0.05 (20x20 cells)
[2025-10-11 14:23:45.162] DEBUG:   Angle bins: 32 (11.25° per bin)
[2025-10-11 14:23:45.163] DEBUG:   Quantized: [0x1A4F, 0x0B23, ...]
[2025-10-11 14:23:45.164] DEBUG:   Binary representation: 64 bits
[2025-10-11 14:23:45.165] DEBUG:   BCH encoder initialized (primitive=0x89, gf2^7)
[2025-10-11 14:23:45.167] DEBUG:   Syndrome: [0x3A, 0x7F, ...]
[2025-10-11 14:23:45.168] DEBUG:   Salt (32 bytes): 4a7f9e...
[2025-10-11 14:23:45.170] DEBUG:   KDF input: biometric=..., salt=4a7f9e..., personalization=...
[2025-10-11 14:23:45.172] DEBUG:   BLAKE3 key (32 bytes): a3f4c8...
...
```

### 4.3 Spinner Animations

For long-running operations, animated spinners provide feedback:

```python
# Normal mode
⠿ Generating cryptographic keys...    # Dots animation (⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏)

# Verbose mode (with elapsed time)
⠿ Generating cryptographic keys... (2.3s)

# Progress bar for batch operations
Enrolling 10 users:
[████████████████████░░░░░░] 80% (8/10) - ETA: 4s
```

### 4.4 Structured Logging (JSON Output)

For machine consumption (CI/CD, monitoring):

```bash
$ dec-did enroll --input fingers.json --wallet addr_test1... --json-output

{"timestamp": "2025-10-11T14:23:45.123Z", "level": "INFO", "event": "enrollment_started", "input": "fingers.json"}
{"timestamp": "2025-10-11T14:23:45.145Z", "level": "DEBUG", "event": "biometric_loaded", "fingers": 4, "format": "minutiae"}
{"timestamp": "2025-10-11T14:23:45.167Z", "level": "INFO", "event": "finger_processed", "finger_id": "index_right", "quality": 85, "duration_ms": 22}
{"timestamp": "2025-10-11T14:23:48.234Z", "level": "INFO", "event": "enrollment_complete", "did": "did:cardano:addr_test1...#biometric-4f2a8b9c", "duration_ms": 3111}
```

---

## 5. Configuration File Format

### 5.1 Configuration File Locations

Search order (first found is used):

1. `$DEC_DID_CONFIG` (environment variable)
2. `./dec-did.toml` (current directory)
3. `~/.dec-did/config.toml` (user home)
4. `/etc/dec-did/config.toml` (system-wide)

### 5.2 Configuration Schema (TOML Format)

**Rationale**: TOML chosen for:
- ✅ Human-readable and writable
- ✅ Strong typing (integers, booleans, arrays)
- ✅ Hierarchical sections
- ✅ Wide Python support (`tomli`/`tomllib`)
- ✅ Open-source (MIT license)

**Example Configuration:**

```toml
# dec-did configuration file
# Version: 1.0
# Documentation: https://github.com/FractionEstate/decentralized-did/docs/configuration.md

[general]
# Default metadata label for Cardano transactions
default_label = 1990

# Default output format (wallet|cip30)
default_format = "wallet"

# Enable colored output
color = true

# Default logging level (quiet|normal|verbose|debug)
log_level = "normal"

[biometric]
# Minimum quality threshold for enrollment (0-100)
quality_threshold = 70

# Allow partial finger matching (true|false)
allow_partial = false

# Minimum fingers required for partial matching
min_fingers = 2

# BCH error correction parameters
[biometric.bch]
k = 64  # Message bits
n = 127 # Codeword bits
t = 10  # Error correction capacity

[storage]
# Default helper data storage mode (inline|external)
default_mode = "inline"

# Default helper URI template (used when --helper-uri not specified)
# Placeholders: {did}, {timestamp}, {hash}
default_uri_template = "ipfs://{hash}"

# Storage backends configuration
[storage.backends]
# IPFS configuration
[storage.backends.ipfs]
enabled = true
api_url = "http://localhost:5001"
gateway_url = "https://ipfs.io"
pin = true  # Pin uploaded content

# Arweave configuration
[storage.backends.arweave]
enabled = false
gateway_url = "https://arweave.net"
wallet_path = "~/.arweave/wallet.json"

# File system configuration
[storage.backends.file]
enabled = true
base_path = "~/.dec-did/helpers"
create_subdirs = true  # Create year/month/day subdirectories

[validation]
# Enable strict schema validation
strict = true

# Schema version to validate against
schema_version = "1.0"

# Warn on deprecated fields
warn_deprecated = true

[output]
# Default output directory
default_dir = "./output"

# Pretty-print JSON (indent=2)
pretty_json = true

# Create backup files (.bak) before overwriting
create_backups = true

[plugins]
# Plugin directories to search
plugin_dirs = [
    "~/.dec-did/plugins",
    "/usr/local/share/dec-did/plugins"
]

# Auto-load plugins on startup
auto_load = true

# List of enabled plugins
enabled = [
    "ipfs-storage",
    "quality-analyzer"
]

[security]
# Require confirmation before overwriting files
confirm_overwrite = true

# Enable audit logging
audit_log = true
audit_log_path = "~/.dec-did/audit.log"

# Require explicit consent for external helper storage
confirm_external_helpers = true

[development]
# Enable development mode (more verbose errors)
dev_mode = false

# Enable performance profiling
profile = false

# Enable debug assertions
debug = false
```

### 5.3 Configuration Validation

```bash
# Initialize default configuration
$ dec-did config init
✓ Created default configuration: ~/.dec-did/config.toml

# Show current configuration
$ dec-did config show
Configuration loaded from: ~/.dec-did/config.toml

[general]
default_label = 1990
default_format = "wallet"
...

# Set configuration value
$ dec-did config set biometric.quality_threshold 75
✓ Updated biometric.quality_threshold: 70 → 75

# Validate configuration
$ dec-did config validate
✓ Configuration is valid

# Validate with strict checks
$ dec-did config validate --strict
⚠ Warning: biometric.quality_threshold (75) differs from recommended (70)
⚠ Warning: storage.backends.arweave.enabled is false (limited storage options)
✓ Configuration is valid (2 warnings)
```

---

## 6. Plugin Architecture

### 6.1 Plugin Types

Three types of plugins extend CLI functionality:

```
┌──────────────────────────────────────────────────────────────┐
│ Plugin Types                                                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 1. Storage Backend Plugins                                  │
│    • Implement custom helper data storage (e.g., S3, IPFS)  │
│    • Interface: store(), retrieve(), delete()               │
│    • Examples: ipfs-storage, arweave-storage, http-storage  │
│                                                              │
│ 2. Biometric Source Plugins                                 │
│    • Import biometric data from various formats             │
│    • Interface: load(), validate(), convert()               │
│    • Examples: nist-loader, iso-loader, custom-format       │
│                                                              │
│ 3. Output Formatter Plugins                                 │
│    • Export metadata in custom formats                      │
│    • Interface: format(), validate()                        │
│    • Examples: cbor-formatter, yaml-formatter, protobuf     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Plugin Structure

Plugins follow a standard directory structure:

```
my-plugin/
├── plugin.toml              # Plugin metadata
├── __init__.py              # Plugin entry point
├── storage.py               # Plugin implementation
├── requirements.txt         # Dependencies (optional)
├── tests/                   # Plugin tests
│   └── test_storage.py
├── docs/                    # Plugin documentation
│   └── README.md
└── LICENSE                  # Plugin license (must be OSS)
```

**Plugin Metadata (`plugin.toml`):**

```toml
[plugin]
name = "ipfs-storage"
version = "1.0.0"
description = "IPFS helper data storage backend"
author = "Your Name"
license = "Apache-2.0"
homepage = "https://github.com/your/plugin"

[plugin.api]
type = "storage"
version = "1.0"

[plugin.dependencies]
python = ">=3.9"
packages = [
    "ipfshttpclient>=0.8.0"
]

[plugin.config]
# Plugin-specific configuration schema
[plugin.config.ipfs]
api_url = "http://localhost:5001"
gateway_url = "https://ipfs.io"
pin = true
timeout = 60
```

### 6.3 Plugin API

**Storage Backend Interface:**

```python
from typing import Protocol

class StorageBackend(Protocol):
    """Storage backend plugin interface."""

    def store(self, data: bytes, metadata: dict) -> str:
        """
        Store helper data and return URI.

        Args:
            data: Helper data bytes
            metadata: Additional metadata (did, timestamp, etc.)

        Returns:
            URI where data is stored (e.g., ipfs://Qm...)
        """
        ...

    def retrieve(self, uri: str) -> bytes:
        """
        Retrieve helper data from URI.

        Args:
            uri: Storage URI

        Returns:
            Helper data bytes
        """
        ...

    def delete(self, uri: str) -> bool:
        """
        Delete helper data (optional operation).

        Args:
            uri: Storage URI

        Returns:
            True if deleted, False otherwise
        """
        ...

    def health_check(self) -> bool:
        """Check if storage backend is accessible."""
        ...
```

**Example Plugin Implementation:**

```python
# ipfs_storage/__init__.py

import ipfshttpclient
from decentralized_did.plugins import StorageBackend, register_plugin

class IPFSStorage(StorageBackend):
    """IPFS storage backend plugin."""

    def __init__(self, config: dict):
        self.api_url = config.get("api_url", "http://localhost:5001")
        self.pin = config.get("pin", True)
        self.client = ipfshttpclient.connect(self.api_url)

    def store(self, data: bytes, metadata: dict) -> str:
        """Store data in IPFS and return CID."""
        result = self.client.add_bytes(data)
        cid = result

        if self.pin:
            self.client.pin.add(cid)

        return f"ipfs://{cid}"

    def retrieve(self, uri: str) -> bytes:
        """Retrieve data from IPFS."""
        cid = uri.replace("ipfs://", "")
        return self.client.cat(cid)

    def delete(self, uri: str) -> bool:
        """Unpin data from IPFS."""
        cid = uri.replace("ipfs://", "")
        try:
            self.client.pin.rm(cid)
            return True
        except Exception:
            return False

    def health_check(self) -> bool:
        """Check IPFS daemon is running."""
        try:
            self.client.version()
            return True
        except Exception:
            return False

# Register plugin
register_plugin("ipfs-storage", IPFSStorage)
```

### 6.4 Plugin Management

```bash
# List installed plugins
$ dec-did plugin list
Installed plugins:
  ✓ ipfs-storage (1.0.0) - IPFS helper data storage
  ✓ quality-analyzer (0.9.0) - Enhanced quality metrics
  ✗ arweave-storage (1.0.0) - Not configured

# Install plugin from directory
$ dec-did plugin install ./my-plugin
✓ Validated plugin structure
✓ Installed dependencies
✓ Registered plugin: my-plugin (1.0.0)

# Validate plugin
$ dec-did plugin validate ./my-plugin
✓ Plugin metadata is valid
✓ Required API methods implemented
✓ Dependencies satisfied
✓ Tests pass (12/12)
```

---

## 7. Implementation Roadmap

### 7.1 Phase 3 Implementation Plan

**Task 1** (Current): ✅ CLI Architecture Design
**Task 2**: JSON Schema Validation
**Task 3**: Storage Backend Implementation
**Task 4**: Advanced CLI Features
**Task 5**: Developer SDK
**Task 6**: CLI Documentation

### 7.2 Backward Compatibility

The new CLI architecture maintains 100% backward compatibility:

```bash
# Old commands (still work)
python -m decentralized_did.cli generate --input ...
python -m decentralized_did.cli verify --metadata ...
python -m decentralized_did.cli demo-kit --input ...

# New commands (preferred)
dec-did enroll --input ...
dec-did verify --metadata ...
dec-did demo-kit --input ...

# Aliases
dec-did gen --input ...   # Same as enroll
dec-did check --metadata ... # Same as verify
```

### 7.3 Migration Path

Users can migrate gradually:

1. **Phase 1**: Use existing CLI with new features
2. **Phase 2**: Adopt configuration files (optional)
3. **Phase 3**: Install plugins (optional)
4. **Phase 4**: Use new command names (optional)

No breaking changes - old workflows continue to work.

---

## 8. Standards and Best Practices

### 8.1 Command-Line Interface Guidelines

Following industry standards:

- ✅ **POSIX**: Standard option syntax (`-v`, `--verbose`)
- ✅ **GNU**: Long options, `--help`, `--version`
- ✅ **XDG Base Directory**: Config in `~/.config/dec-did/`
- ✅ **Exit Codes**: Standard codes (0=success, 1=general, 2=usage, etc.)
- ✅ **Environment Variables**: `DEC_DID_*` prefix
- ✅ **Pipes**: Support stdin/stdout pipelines

### 8.2 User Experience Principles

- ✅ **Progressive Disclosure**: Simple by default, powerful when needed
- ✅ **Fail-Fast**: Validate early, provide clear error messages
- ✅ **Helpful Defaults**: Sensible defaults, minimal required arguments
- ✅ **Discoverability**: `--help` at every level, examples in output
- ✅ **Consistency**: Uniform command structure, predictable behavior
- ✅ **Accessibility**: Color-blind safe, screen-reader friendly

### 8.3 Security Considerations

- ✅ **Input Validation**: Comprehensive validation before processing
- ✅ **Safe Defaults**: Secure by default (quality thresholds, confirmations)
- ✅ **Audit Logging**: Optional audit trail for compliance
- ✅ **No Secrets in CLI**: Never pass secrets as command-line arguments
- ✅ **Permission Checks**: Verify file permissions before writing
- ✅ **Dependency Scanning**: Only open-source, audited dependencies

---

## 9. Documentation Requirements

### 9.1 User Documentation

- `README.md`: Quick start guide
- `docs/cli-reference.md`: Complete command reference
- `docs/configuration.md`: Configuration file guide
- `docs/plugins.md`: Plugin development guide
- `docs/troubleshooting.md`: Common issues and solutions
- `docs/examples/`: Real-world usage examples

### 9.2 Developer Documentation

- `ARCHITECTURE.md`: System architecture
- `CONTRIBUTING.md`: Contribution guidelines
- `API.md`: Plugin API reference
- `TESTING.md`: Testing guide
- `CHANGELOG.md`: Version history

### 9.3 In-CLI Help

Every command provides comprehensive help:

```bash
$ dec-did --help
$ dec-did enroll --help
$ dec-did config --help
```

Help output includes:
- Command description
- Usage examples
- Argument descriptions
- Default values
- Related commands
- Documentation links

---

## 10. Testing Strategy

### 10.1 Test Coverage

- Unit tests: Core functionality (90%+ coverage)
- Integration tests: End-to-end workflows
- CLI tests: Command-line interface
- Plugin tests: Plugin API and implementations
- Documentation tests: Example commands in docs

### 10.2 Test Scenarios

1. **Happy Path**: Successful enrollment, verification
2. **Error Handling**: Invalid inputs, missing files, quality failures
3. **Edge Cases**: Boundary conditions, empty inputs, large files
4. **Performance**: Large datasets, batch operations
5. **Compatibility**: Old vs new CLI syntax
6. **Security**: Input injection, path traversal, permission checks

### 10.3 Continuous Integration

All tests run automatically on:
- Every commit (pre-commit hooks)
- Pull requests (CI/CD pipeline)
- Release candidates (full test suite)

---

## 11. Conclusion

This CLI architecture provides a **production-ready foundation** for biometric DID operations with:

- ✅ **Comprehensive Command Structure**: Enrollment, verification, rotation, revocation, export
- ✅ **Excellent User Experience**: Clear output, helpful errors, progress feedback
- ✅ **Flexible Configuration**: TOML config files with sensible defaults
- ✅ **Extensible Plugin System**: Storage backends, biometric sources, output formatters
- ✅ **Strong Error Handling**: Taxonomy-based errors with recovery guidance
- ✅ **Open-Source Only**: All dependencies and integrations are FOSS
- ✅ **Backward Compatible**: Existing workflows continue to work

### 11.1 Next Steps

**Phase 3, Task 2**: Implement JSON Schema validation
**Phase 3, Task 3**: Implement storage backends (IPFS, Arweave, file system)
**Phase 3, Task 4**: Implement advanced CLI features (dry-run, batch, progress bars)

### 11.2 Sign-Off

**Phase 3, Task 1**: ✅ **COMPLETE**

The CLI architecture design is comprehensive, practical, and ready for implementation.

---

## Appendix A: Command Reference Quick Guide

```bash
# Enrollment
dec-did enroll --input scan.json --wallet addr_test1...
dec-did enroll --input scan.json --wallet addr_test1... --helpers-output helpers.json --helper-uri ipfs://...

# Verification
dec-did verify --metadata metadata.json --input new_scan.json
dec-did verify --metadata metadata.json --input new_scan.json --helpers helpers.json

# Rotation
dec-did rotate --metadata old.json --input new_scan.json --output new.json --reason "Annual rotation"

# Revocation
dec-did revoke --finger-id index_right --metadata metadata.json --output updated.json --reason "Injury"

# Export
dec-did export --metadata metadata.json --format cbor --output metadata.cbor
dec-did export --metadata metadata.json --extract did

# Validation
dec-did validate --metadata metadata.json
dec-did validate --helpers helpers.json

# Configuration
dec-did config init
dec-did config show
dec-did config set biometric.quality_threshold 75

# Plugins
dec-did plugin list
dec-did plugin install ./my-plugin

# Demo Kit
dec-did demo-kit --wallet addr_test1... --output-dir demo --zip demo.zip
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-11
**Status**: Final
**Review**: Architecture design complete, ready for implementation
