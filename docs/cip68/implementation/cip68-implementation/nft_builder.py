from pycardano import (
    TransactionBuilder,
    TransactionOutput,
    Address,
    Value,
    Asset,
    AssetName,
    MultiAsset,
    Mint,
    ScriptAll,
    Datum,
    plutus_json_to_cbor,
    BlockFrostChainContext,
    Network,
)
from pycardano.api import ApiUrls
from metadata_generator import create_reference_nft_metadata, create_user_nft_metadata

# This is a placeholder for the actual minting policy script.
# In a real implementation, this would be loaded from a Plutus script file.


class MintingPolicy(ScriptAll):
    def __init__(self):
        super().__init__([])


def build_minting_transaction(
    payment_address: Address,
    user_nft_name_str: str,
    did_document: dict,
    policy: MintingPolicy,
    network,
    context,
) -> TransactionBuilder:
    """
    Builds a transaction to mint a CIP-68 reference and user NFT.

    Args:
        payment_address: The address to send the NFTs to.
        user_nft_name_str: The user-chosen string for the NFT name.
        did_document: The DID document to be placed in the datum.
        policy: The minting policy script.
        network: The Cardano network.
        context: The Blockfrost context.

    Returns:
        A configured TransactionBuilder instance.
    """
    builder = TransactionBuilder(context)
    builder.add_input_address(payment_address)

    policy_id = policy.hash()

    # 1. Construct asset names according to CIP-68
    user_nft_name_bytes = f"{(222).to_bytes(1, 'big').hex()}{user_nft_name_str.encode('utf-8').hex()}".encode('utf-8')
    reference_nft_name_bytes = f"{(100).to_bytes(1, 'big').hex()}{user_nft_name_str.encode('utf-8').hex()}".encode('utf-8')

    user_asset = Asset(policy_id, AssetName(user_nft_name_bytes))
    reference_asset = Asset(policy_id, AssetName(reference_nft_name_bytes))

    # 2. Create the multi-asset minting structure
    multi_asset = MultiAsset.from_primitive({
        policy_id.to_primitive(): {
            reference_asset.asset_name.to_primitive(): 1,
            user_asset.asset_name.to_primitive(): 1,
        }
    })

    builder.mint = multi_asset
    builder.minting_script = policy

    # 3. Create the datum for the reference NFT
    # The datum is the CIP-68 (100) metadata, which contains the DID document.
    reference_metadata = create_reference_nft_metadata(
        did_document, user_nft_name_str)
    builder.add_json_datum(reference_metadata)
    datum_hash = Datum(reference_metadata).hash()

    # 4. Create outputs
    # Output for the user NFT (sent to the user's address)
    user_nft_output = TransactionOutput(
        address=payment_address,
        amount=Value(
            coin=2000000,  # 2 ADA, adjustable
            multi_asset=MultiAsset.from_primitive(
                {policy_id.to_primitive(): {user_asset.asset_name.to_primitive(): 1}})
        )
    )
    builder.add_output(user_nft_output)

    # Output for the reference NFT (sent to the user's address with datum)
    # In a real scenario, this might go to a script address.
    reference_nft_output = TransactionOutput(
        address=payment_address,
        amount=Value(
            coin=2000000,  # 2 ADA, adjustable
            multi_asset=MultiAsset.from_primitive(
                {policy_id.to_primitive(): {reference_asset.asset_name.to_primitive(): 1}})
        ),
        datum_hash=datum_hash
    )
    builder.add_output(reference_nft_output)

    return builder


def main():
    """
    An example of how to use the NFT builder.
    This is a placeholder and will not run without a configured environment
    (e.g., Blockfrost context, payment keys, and a running node).
    """
    print("This script demonstrates building a CIP-68 NFT minting transaction.")
    print("It is a placeholder and requires a live Cardano environment to execute.")

    # Mock data for demonstration
    try:
        # This will fail if pycardano is not fully configured, which is expected.
        from pycardano import Network, BlockFrostChainContext

        # Replace with your actual Blockfrost project ID and network
        PROJECT_ID = "your_blockfrost_project_id"
        NETWORK = Network.TESTNET
        CONTEXT = BlockFrostChainContext(
            PROJECT_ID, base_url=ApiUrls[NETWORK.name].value)

        # Replace with your actual payment address and signing key
        payment_address = Address.from_primitive("addr_test1...")

        did_document = {
            "@context": ["https://www.w3.org/ns/did/v1"],
            "id": "did:cardano:testnet:example123",
            "verificationMethod": [],
        }

        builder = build_minting_transaction(
            payment_address=payment_address,
            user_nft_name_str="MyDID",
            did_document=did_document,
            policy=MintingPolicy(),
            network=NETWORK,
            context=CONTEXT,
        )

        print("\n--- Transaction Builder ---")
        print(builder)
        print("\nTransaction building demonstration complete.")

    except (ImportError, NameError, Exception) as e:
        print(
            f"\nCould not run full demonstration due to missing configuration or error: {e}")
        print("This is expected if you haven't set up a full pycardano environment.")


if __name__ == "__main__":
    main()
