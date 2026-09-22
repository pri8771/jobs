"""Compatibility shim: the proof database identity helper now lives in the package.

Import from ``jobs_automation.proof.database_identity`` instead. This module stays so
the capsule review references and any local automation keep resolving.
"""

from __future__ import annotations

from jobs_automation.proof.database_identity import (
    SUPPORTED_PROOF_DRIVERS,
    ProofDatabaseIdentityError,
    database_identity,
    resolve_runtime_database,
)

__all__ = [
    "SUPPORTED_PROOF_DRIVERS",
    "ProofDatabaseIdentityError",
    "database_identity",
    "resolve_runtime_database",
]
