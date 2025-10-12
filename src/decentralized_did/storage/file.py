"""
File-based storage backend.

Stores helper data in local file system with atomic writes and backup support.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import hashlib

from .base import StorageBackend, StorageReference, StorageError


class FileStorage(StorageBackend):
    """
    File-based storage backend for helper data.

    Stores helper data as JSON files in a local directory with:
    - Atomic writes (write to temp, then rename)
    - Optional backup of replaced files
    - Path normalization and validation
    - Directory auto-creation

    Advantages:
    - Simple, no external dependencies
    - Fast local access
    - Full control over data
    - Supports backup/versioning

    Disadvantages:
    - Not decentralized
    - Requires file system access
    - No automatic replication
    - Subject to disk failure
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        """
        Initialize file storage.

        Config options:
            base_path (str): Base directory for storage (default: ~/.dec-did/storage)
            create_dirs (bool): Auto-create directories (default: True)
            backup (bool): Backup replaced files (default: False)
            backup_dir (str): Backup directory (default: {base_path}/backups)
            pretty (bool): Pretty-print JSON (default: False)
        """
        super().__init__(config)

        # Base storage path
        base_path = self.config.get("base_path", "~/.dec-did/storage")
        self.base_path = Path(base_path).expanduser().resolve()

        # Backup configuration
        self.backup_enabled = self.config.get("backup", False)
        backup_dir = self.config.get(
            "backup_dir", str(self.base_path / "backups"))
        self.backup_dir = Path(backup_dir).expanduser().resolve()

        # Other options
        self.create_dirs = self.config.get("create_dirs", True)
        self.pretty = self.config.get("pretty", False)

        # Create base directory if needed
        if self.create_dirs and not self.base_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, helper_data: Dict[str, Any]) -> str:
        """
        Generate filename from helper data hash.

        Args:
            helper_data: Helper data to hash

        Returns:
            Filename like "helper_abc123.json"
        """
        # Create deterministic hash of helper data
        json_str = json.dumps(helper_data, sort_keys=True)
        hash_obj = hashlib.sha256(json_str.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()[:16]

        return f"helper_{hash_hex}.json"

    def store(self, helper_data: Dict[str, Any]) -> StorageReference:
        """
        Store helper data to file system.

        Args:
            helper_data: Helper data dictionary

        Returns:
            StorageReference with file path

        Raises:
            StorageError: If write fails
        """
        try:
            # Generate filename
            filename = self._generate_filename(helper_data)
            file_path = self.base_path / filename

            # Backup existing file if it exists
            if self.backup_enabled and file_path.exists():
                self._backup_file(file_path)

            # Write to temporary file first (atomic write)
            temp_path = file_path.with_suffix('.tmp')
            indent = 2 if self.pretty else None

            with temp_path.open('w', encoding='utf-8') as f:
                json.dump(helper_data, f, indent=indent, sort_keys=True)

            # Atomic rename
            temp_path.replace(file_path)

            # Return reference
            return StorageReference(
                backend="file",
                uri=str(file_path),
                metadata={
                    "filename": filename,
                    "size": file_path.stat().st_size,
                    "created": datetime.now().isoformat(),
                }
            )

        except (OSError, IOError) as e:
            raise StorageError(
                f"File storage failed: {e}", backend="file", cause=e)
        except Exception as e:
            raise StorageError(
                f"Unexpected file storage error: {e}", backend="file", cause=e)

    def _backup_file(self, file_path: Path) -> None:
        """
        Backup existing file before replacement.

        Args:
            file_path: File to backup
        """
        if not file_path.exists():
            return

        # Create backup directory
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name

        # Copy file to backup
        shutil.copy2(file_path, backup_path)

    def retrieve(self, reference: StorageReference) -> Dict[str, Any]:
        """
        Retrieve helper data from file system.

        Args:
            reference: Storage reference with file path

        Returns:
            Helper data dictionary

        Raises:
            StorageError: If file not found or read fails
        """
        if reference.backend != "file":
            raise StorageError(
                f"Invalid backend type: expected 'file', got '{reference.backend}'",
                backend="file"
            )

        try:
            file_path = Path(reference.uri)

            if not file_path.exists():
                raise StorageError(
                    f"File not found: {file_path}", backend="file")

            with file_path.open('r', encoding='utf-8') as f:
                return json.load(f)

        except FileNotFoundError as e:
            raise StorageError(
                f"File not found: {reference.uri}", backend="file", cause=e)
        except json.JSONDecodeError as e:
            raise StorageError(
                f"Invalid JSON in file: {e}", backend="file", cause=e)
        except (OSError, IOError) as e:
            raise StorageError(
                f"File read failed: {e}", backend="file", cause=e)
        except Exception as e:
            raise StorageError(
                f"Unexpected file retrieval error: {e}", backend="file", cause=e)

    def delete(self, reference: StorageReference) -> bool:
        """
        Delete helper data file.

        Args:
            reference: Storage reference with file path

        Returns:
            True if deleted, False if not found

        Raises:
            StorageError: If deletion fails
        """
        if reference.backend != "file":
            raise StorageError(
                f"Invalid backend type: expected 'file', got '{reference.backend}'",
                backend="file"
            )

        try:
            file_path = Path(reference.uri)

            if not file_path.exists():
                return False

            # Backup before delete if enabled
            if self.backup_enabled:
                self._backup_file(file_path)

            file_path.unlink()
            return True

        except (OSError, IOError) as e:
            raise StorageError(
                f"File deletion failed: {e}", backend="file", cause=e)
        except Exception as e:
            raise StorageError(
                f"Unexpected file deletion error: {e}", backend="file", cause=e)

    def health_check(self) -> bool:
        """
        Check if file storage is operational.

        Returns:
            True if base directory is writable
        """
        try:
            # Check if base directory exists and is writable
            if not self.base_path.exists():
                if self.create_dirs:
                    self.base_path.mkdir(parents=True, exist_ok=True)
                else:
                    return False

            # Try to create and delete a test file
            test_file = self.base_path / ".health_check"
            test_file.write_text("health_check")
            test_file.unlink()

            return True

        except Exception:
            return False
