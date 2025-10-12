"""
Storage backends for helper data persistence.

Supports multiple storage options:
- Inline: Embed in metadata
- File: Local file system
- IPFS: Decentralized storage
- Arweave: Permanent storage
"""

from .base import StorageBackend, StorageError, StorageReference
from .inline import InlineStorage
from .file import FileStorage
from .ipfs import IPFSStorage
from .factory import (
    create_storage_backend,
    get_available_backends,
    get_backend_info,
    register_backend,
)


__all__ = [
    "StorageBackend",
    "StorageError",
    "StorageReference",
    "InlineStorage",
    "FileStorage",
    "IPFSStorage",
    "create_storage_backend",
    "get_available_backends",
    "get_backend_info",
    "register_backend",
]

from .base import StorageBackend, StorageError, StorageReference
from .inline import InlineStorage
from .file import FileStorage
from .ipfs import IPFSStorage
from .factory import create_storage_backend, get_available_backends

__all__ = [
    "StorageBackend",
    "StorageError",
    "StorageReference",
    "InlineStorage",
    "FileStorage",
    "IPFSStorage",
    "create_storage_backend",
    "get_available_backends",
]
