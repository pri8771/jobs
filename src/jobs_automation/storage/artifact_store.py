"""Artifact storage service with atomic persistence and SHA-256 read-back verification."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path


class ArtifactStore:
    """Manages persistent immutable storage for resume, cover letter, and packet artifacts."""

    def __init__(self, base_dir: Path | str = "artifacts") -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        content: str | bytes,
        artifact_type: str,
        filename: str,
    ) -> tuple[str, str, int]:
        """Atomically stores content and performs read-back hash verification.

        Returns:
            tuple of (storage_uri, sha256_hash, byte_count)
        """
        raw_bytes = content.encode("utf-8") if isinstance(content, str) else content
        computed_sha = hashlib.sha256(raw_bytes).hexdigest()
        byte_count = len(raw_bytes)

        target_dir = self.base_dir / artifact_type
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename

        # Atomic write using tempfile in same directory
        temp_file = tempfile.NamedTemporaryFile(
            dir=target_dir, delete=False, mode="wb"
        )
        try:
            temp_file.write(raw_bytes)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_file.close()
            os.replace(temp_file.name, target_path)
        except Exception:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise

        # Mandatory read-back verification
        read_back_bytes = target_path.read_bytes()
        read_back_sha = hashlib.sha256(read_back_bytes).hexdigest()
        if read_back_sha != computed_sha:
            raise ValueError(
                f"Artifact read-back verification failed for '{target_path}'. "
                f"Expected SHA {computed_sha}, read {read_back_sha}."
            )

        storage_uri = f"file://{target_path.resolve()}"
        return storage_uri, computed_sha, byte_count

    def read(self, storage_uri: str) -> bytes:
        """Reads artifact content from storage URI."""
        path_str = storage_uri[len("file://") :] if storage_uri.startswith("file://") else storage_uri
        p = Path(path_str)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Artifact not found at '{storage_uri}'")
        return p.read_bytes()

    def verify(self, storage_uri: str, expected_sha256: str) -> bool:
        """Verifies artifact bytes on disk match the expected SHA-256."""
        try:
            content = self.read(storage_uri)
            actual_sha = hashlib.sha256(content).hexdigest()
            return actual_sha.lower() == expected_sha256.lower()
        except Exception:
            return False
