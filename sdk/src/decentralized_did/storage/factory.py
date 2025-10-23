"""
Storage backend factory and registry.

Provides factory functions for creating storage backends and checking availability.
"""

from __future__ import annotations

from typing import Dict, Any, List, Type, Optional

from .base import StorageBackend, StorageError
from .inline import InlineStorage
from .file import FileStorage
from .ipfs import IPFSStorage


# Registry of available backends
BACKEND_REGISTRY: Dict[str, Type[StorageBackend]] = {
    "inline": InlineStorage,
    "file": FileStorage,
    "ipfs": IPFSStorage,
}


def create_storage_backend(
    backend_type: str,
    config: Optional[Dict[str, Any]] = None
) -> StorageBackend:
    """
    Create a storage backend instance.

    Args:
        backend_type: Backend type (inline, file, ipfs, arweave)
        config: Backend-specific configuration

    Returns:
        Initialized storage backend instance

    Raises:
        StorageError: If backend type is unknown or initialization fails

    Example:
        >>> backend = create_storage_backend("file", {"base_path": "~/my-storage"})
        >>> ref = backend.store(helper_data)
        >>> data = backend.retrieve(ref)
    """
    backend_type = backend_type.lower()

    if backend_type not in BACKEND_REGISTRY:
        available = ", ".join(BACKEND_REGISTRY.keys())
        raise StorageError(
            f"Unknown storage backend: '{backend_type}'. "
            f"Available backends: {available}"
        )

    backend_class = BACKEND_REGISTRY[backend_type]

    try:
        return backend_class(config)
    except Exception as e:
        raise StorageError(
            f"Failed to initialize {backend_type} backend: {e}",
            backend=backend_type,
            cause=e
        )


def get_available_backends() -> List[str]:
    """
    Get list of available storage backends.

    Returns:
        List of backend type strings

    Example:
        >>> backends = get_available_backends()
        >>> print(backends)
        ['inline', 'file', 'ipfs']
    """
    available = []

    for backend_type, backend_class in BACKEND_REGISTRY.items():
        try:
            # Try to instantiate with minimal config
            backend = backend_class({})
            # If it works, backend is available
            available.append(backend_type)
        except Exception:
            # Backend not available (missing dependencies, etc.)
            pass

    return available


def get_backend_info(backend_type: str) -> Dict[str, Any]:
    """
    Get information about a storage backend.

    Args:
        backend_type: Backend type

    Returns:
        Dictionary with backend information:
        - name: Backend name
        - available: Whether backend is available
        - class: Backend class name
        - supports_deletion: Whether deletion is supported

    Raises:
        StorageError: If backend type is unknown
    """
    backend_type = backend_type.lower()

    if backend_type not in BACKEND_REGISTRY:
        available = ", ".join(BACKEND_REGISTRY.keys())
        raise StorageError(
            f"Unknown storage backend: '{backend_type}'. "
            f"Available backends: {available}"
        )

    backend_class = BACKEND_REGISTRY[backend_type]

    # Check if backend is available
    available = False
    try:
        backend = backend_class({})
        available = True
        supports_deletion = backend.supports_deletion()
    except Exception:
        supports_deletion = False

    return {
        "name": backend_type,
        "available": available,
        "class": backend_class.__name__,
        "supports_deletion": supports_deletion,
    }


def register_backend(backend_type: str, backend_class: Type[StorageBackend]) -> None:
    """
    Register a custom storage backend.

    This allows plugins to register new storage backends dynamically.

    Args:
        backend_type: Backend type identifier (e.g., "s3", "dropbox")
        backend_class: StorageBackend subclass

    Raises:
        StorageError: If backend_type is invalid or already registered

    Example:
        >>> class S3Storage(StorageBackend):
        ...     # Implementation
        ...     pass
        >>> register_backend("s3", S3Storage)
    """
    backend_type = backend_type.lower()

    if not backend_type.isalnum():
        raise StorageError(
            f"Invalid backend type: '{backend_type}'. "
            "Backend type must be alphanumeric."
        )

    if backend_type in BACKEND_REGISTRY:
        raise StorageError(
            f"Backend type '{backend_type}' is already registered. "
            "Use a different name or unregister the existing backend first."
        )

    if not issubclass(backend_class, StorageBackend):
        raise StorageError(
            f"Backend class must be a subclass of StorageBackend, "
            f"got {backend_class.__name__}"
        )

    BACKEND_REGISTRY[backend_type] = backend_class
