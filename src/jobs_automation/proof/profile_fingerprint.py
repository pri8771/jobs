"""Normalized fingerprint of a parsed canonical candidate profile.

The fingerprint binds a packet to the *parsed* profile object rather than to raw file
bytes, so re-indenting or re-ordering YAML does not change identity while any change
to a profile fact does. It is computed identically by the production packet builder,
the real-proof runner and the real-proof verifier.

The digest is derived from private facts and therefore belongs only in private
evidence (database metadata, private bundle); it is never written into the redacted
candidate bundle or the committed receipt.
"""

from __future__ import annotations

import hashlib
import json

from jobs_automation.core.candidate_profile import CandidateProfileConfig

FINGERPRINT_VERSION = 1


def candidate_profile_fingerprint(profile: CandidateProfileConfig) -> str:
    """Return the SHA-256 of the canonical JSON form of the parsed profile."""
    payload = {
        "fingerprint_version": FINGERPRINT_VERSION,
        "profile": profile.model_dump(mode="json"),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
