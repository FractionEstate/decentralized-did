"""
Abstract base class for storage backends.

Defines the interface that all storage backends must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class StorageReference:
    """
    Reference to stored helper data.

    Attributes:
        backend: Storage backend type (inline, file, ipfs, arweave)
        uri: Resource identifier (file path, IPFS CID, Arweave TX ID, etc.)
        metadata: Additional backend-specific metadata
    """
    backend: str
    uri: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "backend": self.backend,
            "uri": self.uri,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StorageReference:
        """Create from dictionary."""
        return cls(
            backend=data["backend"],
            uri=data["uri"],
            metadata=data.get("metadata"),
        )


class StorageError(Exception):
    """Base exception for storage backend errors."""

    def __init__(self, message: str, backend: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.backend = backend
        self.cause = cause


class StorageBackend(ABC):
    """
    Abstract base class for helper data storage backends.

    All storage backends must implement:
    - store(): Save helper data and return reference
    - retrieve(): Load helper data by reference
    - delete(): Remove helper data (if supported)
    - health_check(): Verify backend is operational
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize storage backend with configuration.

        Args:
            config: Backend-specific configuration options
        """
        self.config = config or {}
        self.backend_type = self.__class__.__name__.replace(
            "Storage", "").lower()

    @abstractmethod
    def store(self, helper_data: Dict[str, Any]) -> StorageReference:
        """
        Store helper data and return a reference.

        Args:
            helper_data: Helper data dictionary to store

        Returns:
            StorageReference with URI and metadata

        Raises:
            StorageError: If storage operation fails
        """
        pass

    @abstractmethod
    def retrieve(self, reference: StorageReference) -> Dict[str, Any]:
        """
        Retrieve helper data by reference.

        Args:
            reference: Storage reference from previous store() call

        Returns:
            Helper data dictionary

        Raises:
            StorageError: If retrieval fails or data not found
        """
        pass

    @abstractmethod
    def delete(self, reference: StorageReference) -> bool:
        """
        Delete helper data by reference.

        Args:
            reference: Storage reference to delete

        Returns:
            True if deleted, False if not found or not supported

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if storage backend is operational.

        Returns:
            True if backend is healthy, False otherwise
        """
        pass

    def supports_deletion(self) -> bool:
        """
        Check if backend supports deletion.

        Returns:
            True if delete() is supported
        """
        return True

    def get_backend_type(self) -> str:
        """
        Get the backend type identifier.

        Returns:
            Backend type string (inline, file, ipfs, arweave)
        """
        return self.backend_type
