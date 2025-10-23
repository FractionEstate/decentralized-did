"""Storage backends for helper data persistence.

This module provides pluggable storage backends for biometric helper data,
supporting both centralized and decentralized storage options.

Available Backends
------------------
InlineStorage : class
    Embed helper data directly in Cardano transaction metadata (< 16 KB limit)
FileStorage : class
    Store helper data in local filesystem with atomic writes
IPFSStorage : class
    Store helper data on IPFS decentralized network

Factory Functions
-----------------
create_storage_backend : function
    Create storage backend instance from configuration
get_available_backends : function
    List all registered storage backends
get_backend_info : function
    Get detailed information about a specific backend
register_backend : function
    Register custom storage backend implementation

Base Classes
------------
StorageBackend : Abstract base class
    Interface for implementing custom storage backends
StorageReference : class
    Reference to stored helper data (type + location)
StorageError : Exception
    Base exception for storage operations

Examples
--------
>>> from decentralized_did.storage import InlineStorage, FileStorage, IPFSStorage
>>>
>>> # Inline storage (embed in metadata)
>>> inline = InlineStorage()
>>> ref = await inline.store(helper_data)
>>> print(ref)
StorageReference(type='inline', location='base64:...')
>>>
>>> # File storage (local persistence)
>>> file_storage = FileStorage(base_dir="./helpers")
>>> ref = await file_storage.store(helper_data)
>>> print(ref)
StorageReference(type='file', location='./helpers/abc123.helper')
>>>
>>> # IPFS storage (decentralized)
>>> ipfs = IPFSStorage(api_url="http://localhost:5001")
>>> ref = await ipfs.store(helper_data)
>>> print(ref)
StorageReference(type='ipfs', location='Qm...')
>>>
>>> # Factory pattern
>>> backend = create_storage_backend("file", base_dir="./data")
>>> backends = get_available_backends()
>>> print(backends)
['inline', 'file', 'ipfs']

See Also
--------
- CIP-20: Transaction metadata format
- IPFS Documentation: https://docs.ipfs.tech/
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
    # Base classes and exceptions
    "StorageBackend",
    "StorageError",
    "StorageReference",

    # Concrete backends
    "InlineStorage",
    "FileStorage",
    "IPFSStorage",

    # Factory functions
    "create_storage_backend",
    "get_available_backends",
    "get_backend_info",
    "register_backend",
]
