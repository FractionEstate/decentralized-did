# CIP-30/CIP-45 & Hardware Wallet Integration Research

## Executive Summary

This document compiles comprehensive research on implementing CIP-30/CIP-45 wallet APIs and hardware wallet integration for the BIOVERA wallet, based on analysis of Veridian wallet (Cardano Foundation) and Keystone HQ hardware wallet patterns.

## 1. CIP-30/CIP-45 Implementation Patterns

### 1.1 Veridian Wallet Architecture (KERI-Focused)

**Key Finding**: Veridian implements CIP-45 P2P connection but **DOES NOT** implement standard CIP-30 transaction methods.

#### What Veridian Implements:
```typescript
// ✅ Implements P2P connection
class IdentityWalletConnect extends CardanoPeerConnect {
  // KERI-specific methods
  getKeriIdentifier(): Promise<{ id: string; oobi: string }>
  signKeri(identifier: string, payload: string): Promise<string>

  // ❌ NOT IMPLEMENTED (throws errors)
  signTx(tx: string, partialSign: boolean): Promise<string> {
    throw new Error("Method not implemented.");
  }
  signData(addr: string, payload: string): Promise<Cip30DataSignature> {
    throw new Error("Method not implemented.");
  }
  submitTx(tx: string): Promise<string> {
    throw new Error("Method not implemented.");
  }
}
```

**Why This Matters**: Veridian is focused on **identity** (KERI), not **transactions**. We need both for a full wallet.

### 1.2 Event-Driven Approval Pattern (ADOPT THIS)

**Pattern**: Use event emitters for transaction/signing approval with timeout:

```typescript
// Event-driven signing flow
signKeri = async (identifier: string, payload: string) => {
  let approved: boolean | undefined = undefined;

  const approvalCallback = (approvalStatus: boolean) => {
    approved = approvalStatus;
  };

  // Emit event to UI layer
  this.eventEmitter.emit<PeerConnectSigningEvent>({
    type: PeerConnectionEventTypes.PeerConnectSign,
    payload: { identifier, payload, approvalCallback }
  });

  // Wait for user approval (max 1 hour)
  const startTime = Date.now();
  while (approved === undefined) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    if (Date.now() > startTime + MAX_SIGN_TIME) {
      return { error: TxSignError.TimeOut };
    }
  }

  if (approved) {
    return signWithKey(identifier, payload);
  } else {
    return { error: TxSignError.UserDeclined };
  }
};
```

**Benefits**:
- Clean separation of concerns (wallet logic vs UI)
- Testable (mock event emitter)
- Timeout protection
- Works for hardware wallets (can extend approval time)

### 1.3 Connection Management (ADOPT THIS)

**Pattern**: Singleton PeerConnection with metadata storage:

```typescript
class PeerConnection {
  private static instance: PeerConnection;
  private identityWalletConnect: IdentityWalletConnect | undefined;
  private connectedDAppAddress = "";

  static get peerConnection() {
    if (!this.instance) {
      this.instance = new PeerConnection();
    }
    return this.instance;
  }

  async start(selectedAid: string) {
    const meerkatSeed = await SecureStorage.get(KeyStoreKeys.MEERKAT_SEED);
    this.identityWalletConnect = new IdentityWalletConnect(
      walletInfo, meerkatSeed, announce, selectedAid, eventEmitter
    );

    // Setup connection callbacks
    this.identityWalletConnect.setOnConnect(async (connectMessage) => {
      // Store dApp metadata (name, URL, icon)
      await Agent.agent.peerConnectionMetadataStorage.updatePeerConnectionMetadata(...);
      this.eventEmitter.emit<PeerConnectedEvent>({ ... });
    });
  }

  async connectWithDApp(dAppIdentifier: string) {
    // Check for existing connection metadata
    const existingPeerConnection = await getPeerConnectionMetadata(dAppIdentifier);
    if (!existingPeerConnection) {
      await createPeerConnectionMetadataRecord({ ... });
    }
    const seed = this.identityWalletConnect.connect(dAppIdentifier);
    await SecureStorage.set(KeyStoreKeys.MEERKAT_SEED, seed);
  }
}
```

**Connection Metadata Storage**:
```typescript
interface ConnectionData {
  id: string;           // dApp identifier (meerkat address)
  name?: string;        // dApp name
  url?: string;         // dApp URL
  createdAt?: string;   // Connection timestamp
  iconB64?: string;     // dApp icon (base64)
  selectedAid?: string; // Selected identifier
}
```

## 2. Hardware Wallet Integration Patterns

### 2.1 Keystone HQ Air-Gapped Approach

**Research Finding**: Keystone repositories not yet indexed, but based on industry standards:

#### QR Code-Based Signing (Air-Gapped):
```
┌─────────────┐                    ┌──────────────┐
│   Wallet    │                    │   Hardware   │
│   (Hot)     │                    │   Device     │
│             │                    │   (Cold)     │
└─────────────┘                    └──────────────┘
       │                                  │
       │  1. Generate unsigned TX         │
       │     (CBOR hex)                   │
       │                                  │
       │  2. Display QR code ────────────>│
       │     (UR encoding)                │
       │                                  │
       │                            3. Scan QR
       │                            4. Sign TX
       │                            5. Display QR
       │<──────────────────────────────── │
       │  6. Scan signed TX               │
       │     (UR encoding)                │
       │                                  │
       │  7. Submit to blockchain         │
       ▼                                  ▼
```

**UR Encoding**: Uniform Resources - Efficient QR code encoding for large data
- Split large transactions into multiple animated QR codes
- Fountain codes for robust transmission
- Standard: https://github.com/BlockchainCommons/Research/blob/master/papers/bcr-2020-005-ur.md

#### USB/Bluetooth Connection (Optional):
```typescript
// USB HID connection
interface HardwareWalletConnection {
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  getPublicKey(path: string): Promise<PublicKey>;
  signTransaction(tx: Transaction, paths: string[]): Promise<Signature[]>;
}
```

### 2.2 Hardware Wallet Integration Architecture

```typescript
// Abstract hardware wallet interface
abstract class HardwareWallet {
  abstract connect(): Promise<void>;
  abstract disconnect(): Promise<void>;
  abstract getExtendedPublicKey(accountIndex: number): Promise<string>;
  abstract signTransaction(txCbor: string, witnessIndexes: number[]): Promise<string[]>;
  abstract signMessage(message: string, addressPath: string): Promise<string>;
}

// Keystone implementation (QR-based)
class KeystoneWallet extends HardwareWallet {
  async connect(): Promise<void> {
    // Scan QR code to get device info
  }

  async signTransaction(txCbor: string, witnessIndexes: number[]): Promise<string[]> {
    // 1. Generate UR-encoded QR code
    const urEncoded = encodeToUR(txCbor, witnessIndexes);

    // 2. Display animated QR codes
    await displayAnimatedQRCodes(urEncoded);

    // 3. Wait for user to scan with hardware device
    // 4. Hardware device signs and displays result QR
    // 5. Scan signed transaction QR codes
    const signedUR = await scanAnimatedQRCodes();

    // 6. Decode UR to get signatures
    return decodeFromUR(signedUR);
  }
}

// Ledger implementation (USB/Bluetooth)
class LedgerWallet extends HardwareWallet {
  private transport: Transport;

  async connect(): Promise<void> {
    this.transport = await TransportWebUSB.create();
  }

  async signTransaction(txCbor: string, witnessIndexes: number[]): Promise<string[]> {
    const cardanoApp = new CardanoApp(this.transport);
    return await cardanoApp.signTransaction(txCbor, witnessIndexes);
  }
}

// Trezor implementation
class TrezorWallet extends HardwareWallet {
  async signTransaction(txCbor: string, witnessIndexes: number[]): Promise<string[]> {
    const result = await TrezorConnect.cardanoSignTransaction({
      transaction: txCbor,
      signingMode: SIGNING_MODE.ORDINARY_TRANSACTION,
    });
    return result.witnesses;
  }
}
```

### 2.3 Integration with CIP-30 API

```typescript
class BioveraCip30Api extends CardanoPeerConnect {
  private hardwareWallet: HardwareWallet | null = null;

  // Set hardware wallet for signing
  setHardwareWallet(wallet: HardwareWallet) {
    this.hardwareWallet = wallet;
  }

  protected async signTx(tx: string, partialSign: boolean): Promise<string> {
    // 1. Show TransactionPreview modal for approval
    const approved = await this.requestApproval({
      type: 'SIGN_TRANSACTION',
      transaction: tx
    });

    if (!approved) {
      return { error: TxSignError.UserDeclined };
    }

    // 2. Sign with hardware wallet if connected
    if (this.hardwareWallet) {
      const signatures = await this.hardwareWallet.signTransaction(
        tx,
        this.getRequiredWitnessIndexes(tx)
      );
      return this.attachWitnesses(tx, signatures);
    }

    // 3. Otherwise, sign with hot wallet
    return await this.hotWallet.signTransaction(tx, partialSign);
  }
}
```

## 3. Implementation Architecture for BIOVERA

### 3.1 Hybrid Approach (Best of Both Worlds)

```
┌──────────────────────────────────────────────────────────────┐
│                      BIOVERA Wallet                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐         ┌──────────────────────────┐  │
│  │  CIP-45 P2P     │         │  iframe dApp Browser     │  │
│  │  (QR Code)      │         │  (postMessage Protocol)  │  │
│  └────────┬────────┘         └────────┬─────────────────┘  │
│           │                           │                     │
│           │                           │                     │
│           └───────────┬───────────────┘                     │
│                       │                                     │
│              ┌────────▼────────┐                            │
│              │   CIP-30 API    │                            │
│              │  Implementation │                            │
│              └────────┬────────┘                            │
│                       │                                     │
│        ┌──────────────┴──────────────┐                     │
│        │                             │                     │
│   ┌────▼─────┐              ┌────────▼────────┐           │
│   │   Hot    │              │    Hardware     │           │
│   │  Wallet  │              │     Wallet      │           │
│   │ (Biometric)│            │ (Keystone/     │           │
│   │           │              │  Ledger/Trezor)│           │
│   └───────────┘              └─────────────────┘           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Component Breakdown

#### A. DAppBrowser Component (Already Created)
- ✅ iframe-based browser
- ✅ URL navigation
- ✅ Connection management UI
- ⏳ **TODO**: CIP-30 API injection via postMessage

#### B. CIP-30 API Layer (Stubs Created)
- ✅ Type definitions
- ✅ Method signatures
- ⏳ **TODO**: Implement actual signing logic
- ⏳ **TODO**: Connect to Cardano Serialization Library
- ⏳ **TODO**: Integrate hardware wallet support

#### C. Hardware Wallet Integration (NEW)
```typescript
// /workspaces/decentralized-did/demo-wallet/src/core/hardware/
├── HardwareWallet.ts          // Abstract base class
├── KeystoneWallet.ts          // QR-based signing
├── LedgerWallet.ts            // USB/Bluetooth
├── TrezorWallet.ts            // USB/Bluetooth
├── HardwareWalletManager.ts   // Singleton for managing connections
└── utils/
    ├── urEncoding.ts          // UR encoding/decoding
    └── qrScanner.ts           // QR code scanning
```

#### D. Transaction Signing Flow
```typescript
// Enhanced TransactionPreview with hardware wallet support
<TransactionPreview
  isOpen={showPreview}
  transactionCbor={pendingTx}
  hardwareWalletConnected={!!hardwareWallet}
  onApprove={(useHardware) => {
    if (useHardware) {
      // Show QR code signing modal
      return signWithHardwareWallet(pendingTx);
    } else {
      // Sign with hot wallet (biometric)
      return signWithBiometric(pendingTx);
    }
  }}
  onReject={() => { ... }}
/>
```

### 3.3 Dependencies Required

```json
{
  "dependencies": {
    // CIP-45 P2P Connection
    "@fabianbormann/cardano-peer-connect": "^3.x",
    "@cardano-foundation/cardano-connect-with-wallet": "^0.x",

    // Cardano Serialization
    "@emurgo/cardano-serialization-lib-browser": "^12.x",

    // Hardware Wallets
    "@keystonehq/bc-ur-registry-cardano": "^1.x",  // Keystone UR encoding
    "@keystonehq/animated-qr": "^0.x",             // Animated QR codes
    "@ledgerhq/hw-transport-webusb": "^6.x",      // Ledger USB
    "@ledgerhq/hw-app-cardano": "^6.x",           // Ledger Cardano app
    "trezor-connect": "^9.x",                      // Trezor Connect

    // QR Code Scanning
    "@capacitor-mlkit/barcode-scanning": "^6.x",  // Already installed
    "react-qr-code": "^2.x"                        // QR code display
  }
}
```

## 4. Implementation Phases

### Phase 1: CIP-30 API Full Implementation (3-5 days)
1. Install Cardano Serialization Library
2. Implement CBOR encoding/decoding
3. Implement all CIP-30 methods (not stubs)
4. Connect to wallet services (UTXOs, addresses, balance)
5. Implement transaction builder
6. Test with TransactionPreview component

### Phase 2: CIP-30 Injection Protocol (2-3 days)
1. Design postMessage protocol
2. Inject wallet API into iframe `window.cardano`
3. Handle API calls from dApp
4. Implement response/error handling
5. Test with CIP-45 sample dApp

### Phase 3: Hardware Wallet Support (5-7 days)
1. Implement abstract HardwareWallet interface
2. Implement KeystoneWallet (QR-based)
   - UR encoding/decoding
   - Animated QR code display
   - QR code scanning
3. Implement LedgerWallet (USB)
4. Implement TrezorWallet (USB)
5. Create HardwareWalletManager singleton
6. Integrate with CIP-30 API
7. Update TransactionPreview for hardware signing
8. Test all hardware wallet flows

### Phase 4: Integration & Testing (2-3 days)
1. E2E tests for dApp browser
2. E2E tests for hardware wallets
3. Integration tests for CIP-30 API
4. Performance optimization
5. Security audit

## 5. Security Considerations

### 5.1 dApp Browser Sandboxing
```typescript
<iframe
  src={dappUrl}
  sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
  // ❌ DO NOT add "allow-same-origin" and "allow-scripts" together without CSP
/>
```

**Content Security Policy**:
```typescript
const cspHeader = `
  default-src 'none';
  script-src 'self' ${trustedOrigins.join(' ')};
  connect-src 'self' https://cardano-mainnet.blockfrost.io;
  img-src 'self' data: https:;
  style-src 'self' 'unsafe-inline';
`;
```

### 5.2 Hardware Wallet Security
- **Air-gapped**: Keystone never connects to internet (QR codes only)
- **USB Secure Element**: Ledger/Trezor use secure chips
- **Pin Protection**: All hardware wallets require PIN
- **Seed Never Leaves Device**: Private keys never exported

### 5.3 Transaction Validation
```typescript
// ALWAYS validate transaction before signing
async function validateTransaction(txCbor: string): Promise<ValidationResult> {
  const tx = CardanoSerializationLib.Transaction.from_bytes(
    Buffer.from(txCbor, 'hex')
  );

  // 1. Check outputs go to expected addresses
  // 2. Validate amounts don't exceed balance
  // 3. Check metadata is not malicious
  // 4. Verify no hidden outputs
  // 5. Calculate and display fees

  return { valid: true, warnings: [], errors: [] };
}
```

## 6. Recommendations

### ✅ ADOPT from Veridian:
1. **Event-Driven Approval Pattern** - Clean UI/wallet separation
2. **Singleton PeerConnection** - Reliable connection management
3. **Connection Metadata Storage** - Track dApp connections
4. **Experimental API Container** - Extensibility for custom features
5. **Meerkat Seed Storage** - Secure P2P seed persistence

### ❌ IMPROVE from Veridian:
1. **Implement Full CIP-30 Methods** - Not just stubs
2. **Add Transaction Signing** - Critical for dApp ecosystem
3. **Blockchain Submission** - Connect to Koios/Blockfrost
4. **Hardware Wallet Support** - Essential for high-value transactions

### 🆕 ADD for BIOVERA:
1. **Hybrid P2P + iframe** - Support both connection types
2. **Hardware Wallet Integration** - Keystone, Ledger, Trezor
3. **Biometric Hot Wallet** - Fast signing for small transactions
4. **Smart Signing Strategy** - Auto-select hot vs hardware based on amount

## 7. Next Steps

1. **Install Dependencies** (15 min)
2. **Implement CIP-30 API** (2-3 days)
3. **Test with Sample dApp** (1 day)
4. **Add Hardware Wallet Support** (5-7 days)
5. **Security Audit** (2-3 days)
6. **Production Deployment** (1 day)

**Total Estimated Time**: 2-3 weeks for full implementation

---

**References**:
- CIP-30: https://cips.cardano.org/cips/cip30/
- CIP-45: https://cips.cardano.org/cips/cip45/
- CIP-95: https://cips.cardano.org/cips/cip95/
- Cardano Serialization Lib: https://github.com/Emurgo/cardano-serialization-lib
- Keystone SDK: https://github.com/KeystoneHQ
- BC-UR Spec: https://github.com/BlockchainCommons/Research
