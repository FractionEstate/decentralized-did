# CIP-68 DID Implementation Design

This document outlines the design for implementing Decentralized Identifiers (DIDs) on the Cardano blockchain using the CIP-68 standard.

## 1. Overview

We will leverage the CIP-68 Datum Metadata Standard to represent DIDs and their associated DID Documents as on-chain assets. This approach provides a flexible and extensible way to manage DIDs, allowing for on-chain updates and programmability.

The core idea is to use two tokens for each DID:

1.  **DID User Token:** A standard CIP-68 Non-Fungible Token (NFT) with the `(222)` label. This is the token that a user will hold in their wallet to represent ownership of the DID.
2.  **DID Reference Token:** A CIP-68 Reference NFT with the `(100)` label. This token will be locked at a script address, and its datum will contain the DID Document.

## 2. Token Structure

### 2.1. Policy ID

Both the User Token and the Reference Token for a given DID **MUST** be minted under the same Policy ID. This policy will enforce the rules of our DID method.

### 2.2. Asset Names

-   **DID User Token:** The asset name will be `(222)` followed by a unique identifier for the DID (e.g., a UUID).
    -   Example: `(222)did:cardano:1a2b3c4d`
-   **DID Reference Token:** The asset name will be `(100)` followed by the same unique identifier.
    -   Example: `(100)did:cardano:1a2b3c4d`

This naming convention allows for easy correlation between the user-owned token and its corresponding metadata reference token.

## 3. DID Document Metadata

The DID Document will be stored in the datum of the UTxO containing the **DID Reference Token**. The metadata will follow the structure defined in CIP-68, which is based on CIP-0025, but we will extend it to be compliant with the W3C DID specification.

### 3.1. Datum Structure

The datum will be a Plutus `Datum` with the following structure:

```
datum = #6.121([metadata, version, extra])
```

-   `metadata`: A map containing the DID Document.
-   `version`: An integer representing the version of the DID Document. This will be incremented on each update.
-   `extra`: Optional custom Plutus data. We can use this for future extensions.

### 3.2. Metadata Map (DID Document)

The `metadata` map will contain the fields of a standard W3C DID Document.

Example (simplified):

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1"
  ],
  "id": "did:cardano:1a2b3c4d",
  "verificationMethod": [{
    "id": "did:cardano:1a2b3c4d#key-1",
    "type": "Ed25519VerificationKey2020",
    "controller": "did:cardano:1a2b3c4d",
    "publicKeyMultibase": "zH3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"
  }],
  "authentication": [
    "did:cardano:1a2b3c4d#key-1"
  ],
  "service": [{
    "id": "did:cardano:1a2b3c4d#hub",
    "type": "DecentralizedWebNode",
    "serviceEndpoint": {
      "nodes": ["https://dwn.example.com"]
    }
  }]
}
```

## 4. Minting Process (Initial Creation)

1.  A new, unique identifier for the DID is generated.
2.  A transaction is constructed to mint two tokens:
    -   One **DID User Token** `(222)did:cardano:<uuid>`.
    -   One **DID Reference Token** `(100)did:cardano:<uuid>`.
3.  The **DID User Token** is sent to the user's wallet.
4.  The **DID Reference Token** is sent to a Plutus script address. The transaction output includes a datum containing the initial version of the DID Document.

## 5. DID Document Update Process

To update a DID Document (e.g., rotate a key), the owner of the DID must:

1.  Construct a transaction that spends the UTxO containing the **DID Reference Token**. This will require a signature from the key that controls the script.
2.  The transaction will create a new output at the same script address, containing the same **DID Reference Token** but with a new datum that holds the updated DID Document and an incremented version number.
3.  The Plutus validator script will ensure that only the legitimate owner (controller) of the DID can perform this update.

## 6. DID Resolution

To resolve a DID and retrieve its DID Document:

1.  A client takes the DID string (e.g., `did:cardano:1a2b3c4d`).
2.  The client constructs the asset name for the corresponding **DID Reference Token** (`(100)did:cardano:1a2b3c4d`).
3.  The client queries the Cardano blockchain (using a tool like Blockfrost or a local node) to find the UTxO that holds this specific token.
4.  The client retrieves and decodes the datum from that UTxO.
5.  The `metadata` field of the decoded datum is the DID Document.

This design provides a robust and decentralized way to manage DIDs on Cardano, leveraging the power of Plutus V3 and the CIP-68 standard.
