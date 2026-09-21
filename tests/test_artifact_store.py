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
