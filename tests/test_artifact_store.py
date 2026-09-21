"""Tests for ArtifactStore."""

import hashlib
from pathlib import Path

import pytest

from jobs_automation.storage.artifact_store import ArtifactStore


def test_artifact_store_atomic_write_and_verify(tmp_path: Path) -> None:
    store = ArtifactStore(base_dir=tmp_path)
    content = "Hello, world! This is a test artifact."
    expected_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    uri, sha, size = store.store(content, "resumes", "test_resume.md")
    assert sha == expected_sha
    assert size == len(content.encode("utf-8"))
    assert uri.startswith("file://")
    assert Path(uri.replace("file://", "")).exists()

    # Read back
    read_bytes = store.read(uri)
    assert read_bytes.decode("utf-8") == content

    # Verify
    assert store.verify(uri, expected_sha) is True
    assert store.verify(uri, "wrong_hash") is False


def test_artifact_store_read_missing_fails(tmp_path: Path) -> None:
    store = ArtifactStore(base_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        store.read("file:///nonexistent/path/artifact.md")


def test_artifact_store_two_build_immutability(tmp_path: Path) -> None:
    """Verify R14-01: Two builds with different contents do not overwrite historical artifact bytes."""
    store = ArtifactStore(base_dir=tmp_path)

    # Build 1
    content_v1 = "Cover Letter Version 1 for Job X"
    uri_v1, sha_v1, _ = store.store(content_v1, "cover_letters", "job_x.txt")

    # Build 2 with different content but same nominal filename
    content_v2 = "Cover Letter Version 2 for Job X (revised)"
    uri_v2, sha_v2, _ = store.store(content_v2, "cover_letters", "job_x.txt")

    # URIs must be distinct
    assert uri_v1 != uri_v2

    # Both files must exist independently and preserve exact historical bytes
    assert store.read(uri_v1).decode("utf-8") == content_v1
    assert store.read(uri_v2).decode("utf-8") == content_v2
    assert store.verify(uri_v1, sha_v1) is True
    assert store.verify(uri_v2, sha_v2) is True


def test_artifact_store_overwrite_different_bytes_fails_closed(tmp_path: Path) -> None:
    """Verify R14-01: Direct overwrite of different bytes to same target path raises FileExistsError."""
    store = ArtifactStore(base_dir=tmp_path)

    content_v1 = "Historical immutable document content"
    uri_v1, sha_v1, _ = store.store(
        content_v1, "packets", "exact_doc.json", content_addressed=False
    )

    # Calling again with exact same content succeeds idempotently
    uri_v1_repeat, _, _ = store.store(
        content_v1, "packets", "exact_doc.json", content_addressed=False
    )
    assert uri_v1_repeat == uri_v1

    # Calling with different content to exact same target path raises FileExistsError
    content_v2 = "Conflicting new document content"
    with pytest.raises(FileExistsError, match="Historical artifact bytes cannot be overwritten"):
        store.store(content_v2, "packets", "exact_doc.json", content_addressed=False)

    # Original bytes remain completely unchanged
    assert store.read(uri_v1).decode("utf-8") == content_v1
