import json
from typing import Dict, Any


def create_user_nft_metadata(name: str, description: str, image_uri: str) -> Dict[str, Any]:
    """
    Creates the metadata for the user-facing CIP-68 NFT (222).

    Args:
        name: The name of the NFT.
        description: A description of the NFT.
        image_uri: The URI of the NFT's image.

    Returns:
        A dictionary representing the user NFT metadata.
    """
    return {
        "name": name,
        "description": description,
        "image": image_uri,
        "mediaType": "image/png",
    }


def create_reference_nft_metadata(did_document: Dict[str, Any], user_nft_name: str) -> Dict[str, Any]:
    """
    Creates the metadata for the reference CIP-68 NFT (100), which holds the DID document.

    Args:
        did_document: The DID document to be stored in the datum.
        user_nft_name: The name of the corresponding user NFT.

    Returns:
        A dictionary representing the reference NFT metadata.
    """
    return {
        "name": f"DID Reference for {user_nft_name}",
        "description": "This token contains the on-chain DID document in its datum.",
        "did_document": did_document,
        "version": "1.0"
    }


def main():
    """
    An example of how to use the metadata generator.
    """
    # 1. Define the core DID Document
    did_document = {
        "@context": [
            "https://www.w3.org/ns/did/v1",
            "https://w3id.org/security/suites/ed25519-2020/v1"
        ],
        "id": "did:cardano:example:1a2b3c4d",
        "verificationMethod": [{
            "id": "did:cardano:example:1a2b3c4d#keys-1",
            "type": "Ed25519VerificationKey2020",
            "controller": "did:cardano:example:1a2b3c4d",
            "publicKeyMultibase": "zH3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"
        }],
        "authentication": [
            "did:cardano:example:1a2b3c4d#keys-1"
        ]
    }

    # 2. Define properties for the user-facing NFT
    user_nft_name = "My DID"
    user_nft_description = "This NFT represents my decentralized identity on Cardano."
    user_nft_image_uri = "ipfs://QmWm7gZf3gY9ZJ9gZf3gY9ZJ9gZf3gY9ZJ9gZf3gY9ZJ9"

    # 3. Generate metadata for both tokens
    user_nft_metadata = create_user_nft_metadata(
        user_nft_name, user_nft_description, user_nft_image_uri)
    reference_nft_metadata = create_reference_nft_metadata(
        did_document, user_nft_name)

    print("--- User NFT Metadata (222) ---")
    print(json.dumps(user_nft_metadata, indent=4))
    print("\n--- Reference NFT Metadata (100) ---")
    print(json.dumps(reference_nft_metadata, indent=4))


if __name__ == "__main__":
    main()
