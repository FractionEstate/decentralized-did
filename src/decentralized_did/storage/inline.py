"""
Inline storage backend.

Embeds helper data directly in metadata (no external storage).
This is the default and simplest backend - no additional configuration needed.
"""

from __future__ import annotations

import json
from typing import Dict, Any

from .base import StorageBackend, StorageReference, StorageError


class InlineStorage(StorageBackend):
    """
    Inline storage backend that embeds helper data in metadata.

    This backend doesn't actually "store" anything externally - it just
    returns the helper data as the URI, which can be embedded directly
    in the metadata structure.

    Advantages:
    - No external dependencies
    - No network requests
    - Instant retrieval
    - No storage costs

    Disadvantages:
    - Increases metadata size
    - May hit blockchain transaction size limits
    - No separation of public/private data
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        """
        Initialize inline storage.

        Config options:
            compress (bool): Whether to compress helper data (default: False)
            max_size (int): Maximum size in bytes (default: None, no limit)
        """
        super().__init__(config)
        self.compress = self.config.get("compress", False)
        self.max_size = self.config.get("max_size")

    def store(self, helper_data: Dict[str, Any]) -> StorageReference:
        """
        "Store" helper data by serializing to JSON.

        Args:
            helper_data: Helper data dictionary

        Returns:
            StorageReference with inline data as URI

        Raises:
            StorageError: If data exceeds max_size
        """
        try:
            # Serialize to JSON
            json_data = json.dumps(
                helper_data, separators=(',', ':'), sort_keys=True)

            # Check size limit
            if self.max_size and len(json_data) > self.max_size:
                raise StorageError(
                    f"Helper data size ({len(json_data)} bytes) exceeds max_size ({self.max_size} bytes)",
                    backend="inline"
                )

                # Return reference with embedded data (data: URI scheme)
            return StorageReference(
                backend="inline",
                uri=f"data:application/json,{json_data}",  # Data URI scheme
                metadata={
                    "size": len(json_data),
                    "compressed": self.compress,
                }
            )

        except (TypeError, ValueError) as e:  # JSON encoding errors
            raise StorageError(
                f"Failed to serialize helper data: {e}", backend="inline", cause=e)
        except Exception as e:
            raise StorageError(
                f"Inline storage failed: {e}", backend="inline", cause=e)

    def retrieve(self, reference: StorageReference) -> Dict[str, Any]:
        """
        Retrieve helper data from inline reference.

        Args:
            reference: Storage reference with embedded data

        Returns:
            Helper data dictionary

        Raises:
            StorageError: If deserialization fails
        """
        if reference.backend != "inline":
            raise StorageError(
                f"Invalid backend type: expected 'inline', got '{reference.backend}'",
                backend="inline"
            )

        try:
            # Extract JSON from data: URI scheme
            uri = reference.uri
            if uri.startswith("data:"):
                # data:application/json,{json_data}
                json_data = uri.split(",", 1)[1]
            else:
                # Plain JSON string (backwards compatibility)
                json_data = uri

            return json.loads(json_data)

        except json.JSONDecodeError as e:
            raise StorageError(
                f"Failed to deserialize helper data: {e}", backend="inline", cause=e)
        except Exception as e:
            raise StorageError(
                f"Inline retrieval failed: {e}", backend="inline", cause=e)

    def delete(self, reference: StorageReference) -> bool:
        """
        Delete is a no-op for inline storage.

        Args:
            reference: Storage reference (ignored)

        Returns:
            True (always succeeds, nothing to delete)
        """
        # No external storage to delete
        return True

    def health_check(self) -> bool:
        """
        Health check for inline storage.

        Returns:
            True (inline storage always available)
        """
        # Inline storage has no external dependencies
        return True

    def supports_deletion(self) -> bool:
        """
        Inline storage doesn't require deletion.

        Returns:
            False (deletion not applicable)
        """
        return False
