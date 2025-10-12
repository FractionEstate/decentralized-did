"""
Tests for storage backends.

Tests all storage backend implementations including:
- Inline storage
- File system storage
- IPFS storage
- Factory functions
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from decentralized_did.storage import (
    StorageBackend,
    StorageError,
    StorageReference,
    InlineStorage,
    FileStorage,
    IPFSStorage,
    create_storage_backend,
    get_available_backends,
    get_backend_info,
    register_backend,
)


# Test fixtures

@pytest.fixture
def sample_helper_data():
    """Sample helper data for testing."""
    return {
        "scheme": "FuzzyCommitment",
        "algorithm": "AES-256-CTR",
        "parameters": {
            "thresholdT": 10,
            "errorCorrection": "BCH"
        },
        "helperData": "0123456789abcdef" * 16,
        "salt": "abc123"
    }


@pytest.fixture
def temp_dir():
    """Temporary directory for file storage tests."""
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath, ignore_errors=True)


# Base class tests

def test_storage_reference_creation():
    """Test StorageReference creation."""
    ref = StorageReference(
        backend="file",
        uri="/path/to/file.json",
        metadata={"size": 1024}
    )

    assert ref.backend == "file"
    assert ref.uri == "/path/to/file.json"
    assert ref.metadata["size"] == 1024


def test_storage_reference_serialization():
    """Test StorageReference to/from dict."""
    ref = StorageReference(
        backend="ipfs",
        uri="ipfs://QmHash123",
        metadata={"pinned": True}
    )

    # To dict
    data = ref.to_dict()
    assert data["backend"] == "ipfs"
    assert data["uri"] == "ipfs://QmHash123"
    assert data["metadata"]["pinned"] is True

    # From dict
    ref2 = StorageReference.from_dict(data)
    assert ref2.backend == ref.backend
    assert ref2.uri == ref.uri
    assert ref2.metadata == ref.metadata


def test_storage_error():
    """Test StorageError exception."""
    cause = ValueError("Invalid data")
    error = StorageError(
        "Storage operation failed",
        backend="file",
        cause=cause
    )

    assert "Storage operation failed" in str(error)
    assert error.backend == "file"
    assert error.cause is cause


# InlineStorage tests

def test_inline_storage_store(sample_helper_data):
    """Test inline storage store operation."""
    backend = InlineStorage({})

    ref = backend.store(sample_helper_data)

    assert ref.backend == "inline"
    assert ref.uri.startswith("data:")
    assert "json" in ref.uri.lower()

    # Should be able to decode the data
    data_part = ref.uri.split(",", 1)[1]
    decoded = json.loads(data_part)
    assert decoded == sample_helper_data


def test_inline_storage_retrieve(sample_helper_data):
    """Test inline storage retrieve operation."""
    backend = InlineStorage({})

    ref = backend.store(sample_helper_data)
    retrieved = backend.retrieve(ref)

    assert retrieved == sample_helper_data


def test_inline_storage_size_limit(sample_helper_data):
    """Test inline storage size limit enforcement."""
    # Create large data
    large_data = sample_helper_data.copy()
    large_data["helperData"] = "x" * 10000

    # Set small size limit
    backend = InlineStorage({"max_size": 1000})

    with pytest.raises(StorageError) as exc_info:
        backend.store(large_data)

    assert "max_size" in str(exc_info.value).lower()


def test_inline_storage_delete(sample_helper_data):
    """Test inline storage delete operation."""
    backend = InlineStorage({})

    ref = backend.store(sample_helper_data)
    result = backend.delete(ref)

    # Inline storage always returns True (no-op)
    assert result is True


def test_inline_storage_health_check():
    """Test inline storage health check."""
    backend = InlineStorage({})

    # Should always be healthy (no dependencies)
    assert backend.health_check() is True


def test_inline_storage_supports_deletion():
    """Test inline storage deletion support."""
    backend = InlineStorage({})

    # Inline storage doesn't support deletion
    assert backend.supports_deletion() is False


# FileStorage tests

def test_file_storage_store(sample_helper_data, temp_dir):
    """Test file storage store operation."""
    backend = FileStorage({"base_path": temp_dir})

    ref = backend.store(sample_helper_data)

    assert ref.backend == "file"
    assert ref.uri.startswith(temp_dir)
    assert ref.uri.endswith(".json")
    assert Path(ref.uri).exists()

    # Verify file content
    with open(ref.uri) as f:
        stored = json.load(f)
    assert stored == sample_helper_data


def test_file_storage_retrieve(sample_helper_data, temp_dir):
    """Test file storage retrieve operation."""
    backend = FileStorage({"base_path": temp_dir})

    ref = backend.store(sample_helper_data)
    retrieved = backend.retrieve(ref)

    assert retrieved == sample_helper_data


def test_file_storage_delete(sample_helper_data, temp_dir):
    """Test file storage delete operation."""
    backend = FileStorage({"base_path": temp_dir})

    ref = backend.store(sample_helper_data)
    assert Path(ref.uri).exists()

    result = backend.delete(ref)

    assert result is True
    assert not Path(ref.uri).exists()


def test_file_storage_backup(sample_helper_data, temp_dir):
    """Test file storage backup functionality."""
    backup_dir = os.path.join(temp_dir, "backups")
    backend = FileStorage({
        "base_path": temp_dir,
        "backup": True,
        "backup_dir": backup_dir
    })

    # Store initial data
    ref1 = backend.store(sample_helper_data)

    # Modify and store again (should trigger backup)
    modified_data = sample_helper_data.copy()
    modified_data["salt"] = "xyz789"

    # Manually store with same filename to trigger backup
    # (In practice, hash would differ, but we'll test backup directly)
    backend._backup_file(Path(ref1.uri))

    ref2 = backend.store(modified_data)

    # Check backup exists
    backup_files = list(Path(backup_dir).glob("*.json"))
    assert len(backup_files) >= 1


def test_file_storage_pretty_format(sample_helper_data, temp_dir):
    """Test file storage pretty formatting."""
    backend = FileStorage({
        "base_path": temp_dir,
        "pretty": True
    })

    ref = backend.store(sample_helper_data)

    # Check that file is pretty-printed
    with open(ref.uri) as f:
        content = f.read()

    # Pretty-printed JSON has newlines and indentation
    assert "\n" in content
    assert "  " in content


def test_file_storage_health_check(temp_dir):
    """Test file storage health check."""
    backend = FileStorage({"base_path": temp_dir})

    # Should be healthy if directory is writable
    assert backend.health_check() is True

    # Make directory read-only
    os.chmod(temp_dir, 0o444)

    try:
        # Should fail health check
        assert backend.health_check() is False
    finally:
        # Restore permissions for cleanup
        os.chmod(temp_dir, 0o755)


def test_file_storage_auto_create_dirs(sample_helper_data):
    """Test file storage auto-creates directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_path = os.path.join(temp_dir, "nested", "path")

        backend = FileStorage({
            "base_path": nested_path,
            "create_dirs": True
        })

        ref = backend.store(sample_helper_data)

        # Directory should be created
        assert Path(nested_path).exists()
        assert Path(ref.uri).exists()


# IPFSStorage tests

@pytest.fixture
def mock_ipfs_client():
    """Mock IPFS client for testing."""
    client = MagicMock()
    client.id.return_value = {"ID": "QmTestNode"}
    client.add_bytes.return_value = "QmTestHash123"
    client.cat.return_value = b'{"test": "data"}'
    client.pin.add.return_value = None
    client.pin.rm.return_value = None
    return client


def test_ipfs_storage_available():
    """Test IPFS storage availability."""
    # This test checks if ipfshttpclient is available
    try:
        import ipfshttpclient  # noqa
        # If available, can create backend
        backend = IPFSStorage({})
        assert backend is not None
    except ImportError:
        pytest.skip("ipfshttpclient not available")


@pytest.mark.skipif(
    not hasattr(IPFSStorage, '_connect'),
    reason="IPFS client not available"
)
@patch('decentralized_did.storage.ipfs.IPFS_AVAILABLE', True)
@patch('decentralized_did.storage.ipfs.ipfshttpclient')
def test_ipfs_storage_store(mock_ipfs_module, sample_helper_data, mock_ipfs_client):
    """Test IPFS storage store operation."""
    mock_ipfs_module.connect.return_value = mock_ipfs_client

    backend = IPFSStorage({"api_url": "/ip4/127.0.0.1/tcp/5001"})

    ref = backend.store(sample_helper_data)

    assert ref.backend == "ipfs"
    assert ref.uri.startswith("ipfs://")
    assert "QmTestHash123" in ref.uri

    # Verify client was called
    mock_ipfs_client.add_bytes.assert_called_once()


@patch('decentralized_did.storage.ipfs.IPFS_AVAILABLE', True)
@patch('decentralized_did.storage.ipfs.ipfshttpclient')
def test_ipfs_storage_retrieve(mock_ipfs_module, sample_helper_data, mock_ipfs_client):
    """Test IPFS storage retrieve operation."""
    # Mock client to return our sample data
    data_bytes = json.dumps(sample_helper_data).encode()
    mock_ipfs_client.cat.return_value = data_bytes
    mock_ipfs_module.connect.return_value = mock_ipfs_client

    backend = IPFSStorage({"api_url": "/ip4/127.0.0.1/tcp/5001"})

    ref = StorageReference(
        backend="ipfs",
        uri="ipfs://QmTestHash123"
    )

    retrieved = backend.retrieve(ref)

    assert retrieved == sample_helper_data
    mock_ipfs_client.cat.assert_called_once_with("QmTestHash123")


@patch('decentralized_did.storage.ipfs.IPFS_AVAILABLE', True)
@patch('decentralized_did.storage.ipfs.ipfshttpclient')
def test_ipfs_storage_pinning(mock_ipfs_module, sample_helper_data, mock_ipfs_client):
    """Test IPFS storage pinning."""
    mock_ipfs_module.connect.return_value = mock_ipfs_client

    backend = IPFSStorage({
        "api_url": "/ip4/127.0.0.1/tcp/5001",
        "pin": True
    })

    ref = backend.store(sample_helper_data)

    # Verify pinning was called
    mock_ipfs_client.pin.add.assert_called_once()


@patch('decentralized_did.storage.ipfs.IPFS_AVAILABLE', True)
@patch('decentralized_did.storage.ipfs.ipfshttpclient')
def test_ipfs_storage_delete(mock_ipfs_module, mock_ipfs_client):
    """Test IPFS storage delete operation."""
    mock_ipfs_module.connect.return_value = mock_ipfs_client

    backend = IPFSStorage({"api_url": "/ip4/127.0.0.1/tcp/5001"})

    ref = StorageReference(
        backend="ipfs",
        uri="ipfs://QmTestHash123"
    )

    result = backend.delete(ref)

    # Should attempt to unpin
    assert result is True
    mock_ipfs_client.pin.rm.assert_called_once_with("QmTestHash123")


@patch('decentralized_did.storage.ipfs.IPFS_AVAILABLE', True)
@patch('decentralized_did.storage.ipfs.ipfshttpclient')
def test_ipfs_storage_health_check(mock_ipfs_module, mock_ipfs_client):
    """Test IPFS storage health check."""
    mock_ipfs_module.connect.return_value = mock_ipfs_client

    backend = IPFSStorage({"api_url": "/ip4/127.0.0.1/tcp/5001"})

    # Should be healthy if node responds
    assert backend.health_check() is True
    mock_ipfs_client.id.assert_called_once()

    # Test unhealthy node
    mock_ipfs_client.id.side_effect = Exception("Connection failed")
    assert backend.health_check() is False


# Factory tests

def test_create_storage_backend_inline(sample_helper_data):
    """Test factory creates inline backend."""
    backend = create_storage_backend("inline", {})

    assert isinstance(backend, InlineStorage)
    assert backend.get_backend_type() == "inline"

    # Test it works
    ref = backend.store(sample_helper_data)
    retrieved = backend.retrieve(ref)
    assert retrieved == sample_helper_data


def test_create_storage_backend_file(sample_helper_data, temp_dir):
    """Test factory creates file backend."""
    backend = create_storage_backend("file", {"base_path": temp_dir})

    assert isinstance(backend, FileStorage)
    assert backend.get_backend_type() == "file"

    # Test it works
    ref = backend.store(sample_helper_data)
    retrieved = backend.retrieve(ref)
    assert retrieved == sample_helper_data


def test_create_storage_backend_case_insensitive():
    """Test factory backend type is case-insensitive."""
    backend1 = create_storage_backend("INLINE", {})
    backend2 = create_storage_backend("Inline", {})
    backend3 = create_storage_backend("inline", {})

    assert all(isinstance(b, InlineStorage)
               for b in [backend1, backend2, backend3])


def test_create_storage_backend_unknown():
    """Test factory raises error for unknown backend."""
    with pytest.raises(StorageError) as exc_info:
        create_storage_backend("unknown", {})

    assert "unknown storage backend" in str(exc_info.value).lower()
    assert "available backends" in str(exc_info.value).lower()


def test_get_available_backends():
    """Test get_available_backends returns valid list."""
    backends = get_available_backends()

    assert isinstance(backends, list)
    assert "inline" in backends  # Inline should always be available
    assert "file" in backends    # File should always be available


def test_get_backend_info_inline():
    """Test get_backend_info for inline backend."""
    info = get_backend_info("inline")

    assert info["name"] == "inline"
    assert info["available"] is True
    assert info["class"] == "InlineStorage"
    assert info["supports_deletion"] is False


def test_get_backend_info_file():
    """Test get_backend_info for file backend."""
    info = get_backend_info("file")

    assert info["name"] == "file"
    assert info["available"] is True
    assert info["class"] == "FileStorage"
    assert info["supports_deletion"] is True


def test_get_backend_info_unknown():
    """Test get_backend_info raises error for unknown backend."""
    with pytest.raises(StorageError):
        get_backend_info("unknown")


def test_register_backend():
    """Test registering custom backend."""
    class CustomStorage(StorageBackend):
        def store(self, helper_data):
            pass

        def retrieve(self, reference):
            pass

        def delete(self, reference):
            pass

        def health_check(self):
            return True

        def get_backend_type(self):
            return "custom"

    register_backend("custom", CustomStorage)

    # Should be able to create it
    backend = create_storage_backend("custom", {})
    assert isinstance(backend, CustomStorage)

    # Should appear in available backends
    info = get_backend_info("custom")
    assert info["name"] == "custom"


def test_register_backend_duplicate():
    """Test registering duplicate backend raises error."""
    class DummyStorage(StorageBackend):
        pass

    with pytest.raises(StorageError) as exc_info:
        register_backend("inline", DummyStorage)  # inline already registered

    assert "already registered" in str(exc_info.value).lower()


def test_register_backend_invalid_class():
    """Test registering non-StorageBackend raises error."""
    class NotABackend:
        pass

    with pytest.raises(StorageError) as exc_info:
        register_backend("invalid", NotABackend)  # type: ignore

    assert "storagebackend" in str(exc_info.value).lower()
# Integration tests


def test_backend_switching(sample_helper_data, temp_dir):
    """Test switching between backends."""
    # Store with inline
    inline = create_storage_backend("inline", {})
    ref1 = inline.store(sample_helper_data)
    data1 = inline.retrieve(ref1)

    # Store same data with file
    file_backend = create_storage_backend("file", {"base_path": temp_dir})
    ref2 = file_backend.store(sample_helper_data)
    data2 = file_backend.retrieve(ref2)

    # Both should have same data
    assert data1 == data2 == sample_helper_data

    # But different storage methods
    assert ref1.backend == "inline"
    assert ref2.backend == "file"


def test_error_handling_missing_file(temp_dir):
    """Test error handling for missing file."""
    backend = FileStorage({"base_path": temp_dir})

    ref = StorageReference(
        backend="file",
        uri=os.path.join(temp_dir, "nonexistent.json")
    )

    with pytest.raises(StorageError):
        backend.retrieve(ref)


def test_error_handling_invalid_json(temp_dir):
    """Test error handling for invalid JSON."""
    backend = FileStorage({"base_path": temp_dir})

    # Create file with invalid JSON
    invalid_file = os.path.join(temp_dir, "invalid.json")
    with open(invalid_file, "w") as f:
        f.write("{invalid json")

    ref = StorageReference(
        backend="file",
        uri=invalid_file
    )

    with pytest.raises(StorageError):
        backend.retrieve(ref)


def test_concurrent_storage_operations(sample_helper_data, temp_dir):
    """Test multiple concurrent storage operations."""
    backend = FileStorage({"base_path": temp_dir})

    # Store multiple items
    refs = []
    for i in range(10):
        data = sample_helper_data.copy()
        data["salt"] = f"salt_{i}"
        ref = backend.store(data)
        refs.append(ref)

    # Retrieve all items
    for i, ref in enumerate(refs):
        retrieved = backend.retrieve(ref)
        assert retrieved["salt"] == f"salt_{i}"

    # Delete all items
    for ref in refs:
        assert backend.delete(ref) is True
        assert not Path(ref.uri).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
