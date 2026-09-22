"""Base classes and types for browser automation and form interaction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FieldClassification(StrEnum):
    """Classification taxonomy for application form fields."""

    SAFE_CANONICAL = "SAFE_CANONICAL"  # Direct mapping to verified canonical candidate data
    PACKET_ANSWER = "PACKET_ANSWER"  # Exact accepted packet answer with provenance
    FILE_ARTIFACT = "FILE_ARTIFACT"  # Immutable accepted artifact upload
    EEO_MANUAL = "EEO_MANUAL"  # Demographic/self-identification; never auto-filled
    AUTH_BARRIER = "AUTH_BARRIER"  # Login, MFA, verification, CAPTCHA
    CONSENT_MANUAL = "CONSENT_MANUAL"  # Legal consent/attestation requiring user action
    UNKNOWN_REQUIRED = "UNKNOWN_REQUIRED"  # Required field with no safe mapping
    UNKNOWN_OPTIONAL = "UNKNOWN_OPTIONAL"  # Optional field with no safe mapping
    POLICY_BLOCKED = "POLICY_BLOCKED"  # Filling/action not permitted by current policy


class FieldFillProvenance(BaseModel):
    """Audit provenance for an individual form field fill action."""

    model_config = ConfigDict(extra="forbid")

    field_name: str
    target_selector: str
    classification: FieldClassification
    canonical_key: str | None = None
    source_reference: (
        str  # e.g. "candidate_profile.identity.email", "packet.answers_json.years_exp"
    )
    value_hash: str  # SHA-256 hash of the value for audit
    confidence: float = 1.0
    mapping_method: str = "exact_canonical_match"
    requires_human_review: bool = False


class FormField(BaseModel):
    """Represents a discovered interactive form field.

    ``selector`` is the exact locator captured at inspection time; writers must use it
    verbatim and never re-search the page with broad substrings. ``label``,
    ``placeholder``, ``help_text``, ``options`` and ``form_action`` are part of the
    semantic snapshot (F145-08): a change to any of them between inspection and the
    pre-write recheck invalidates the prefill plan.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    field_type: str = "text"  # text, email, tel, file, textarea, select, radio, checkbox, password
    label: str | None = None
    placeholder: str | None = None
    help_text: str | None = None
    selector: str
    required: bool = False
    options: list[str] = Field(default_factory=list)
    option_values: list[str] = Field(default_factory=list)
    form_action: str | None = None
    form_id: str | None = None
    dom_index: int | None = None
    current_value: str | None = None
    classification: FieldClassification = FieldClassification.UNKNOWN_OPTIONAL
    page_fingerprint: str | None = None


class FormInspectionResult(BaseModel):
    """Result of inspecting an application form on a webpage."""

    model_config = ConfigDict(extra="forbid")

    url: str
    title: str
    fields: list[FormField] = Field(default_factory=list)
    has_file_upload: bool = False
    detected_ats: str | None = None  # greenhouse, lever, workday, ashby, etc.
    form_found: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    form_fingerprint: str = ""
    barriers: list[str] = Field(default_factory=list)
    page_security_warnings: list[str] = Field(default_factory=list)
    page_text_injection_detected: bool = False
    is_mock: bool = False
    # Actual navigated destination after redirects; empty means "same as url".
    final_url: str = ""
    # Action attribute of the form that holds the inspected fields, when present.
    form_action: str | None = None
    form_count: int = 0
    # Set when the runner could not complete inspection; never a clean safety result.
    inspection_error: str | None = None
    semantic_snapshot: str = ""

    def destination_url(self) -> str:
        return self.final_url or self.url


class FormPrefillResult(BaseModel):
    """Result of prefilling fields in a browser form.

    ``prefilled_fields`` holds only values that were written *and read back* from the
    live control; ``failed_fields`` and ``unmatched_fields`` record every requested
    write that did not happen. ``success`` is true only when nothing failed.
    """

    model_config = ConfigDict(extra="forbid")

    url: str
    final_url: str = ""
    prefilled_fields: dict[str, str] = Field(default_factory=dict)
    provenance: dict[str, FieldFillProvenance] = Field(default_factory=dict)
    unmatched_fields: list[str] = Field(default_factory=list)
    failed_fields: dict[str, str] = Field(default_factory=dict)
    readback: dict[str, str] = Field(default_factory=dict)
    attached_files: dict[str, str] = Field(default_factory=dict)
    attached_file_digests: dict[str, str] = Field(default_factory=dict)
    verified_file_hashes: dict[str, str] = Field(default_factory=dict)
    success: bool = True
    message: str = "Prefilled successfully"
    is_mock: bool = False


class PreSubmitReviewManifest(BaseModel):
    """Machine-readable pre-submit review manifest for human-in-the-loop audit.

    This manifest describes the *plan* built from the inspected form. Actual fill and
    upload outcomes are recorded separately in ``PostFillEvidence``.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: str
    job_id: str
    company_name: str
    job_title: str
    destination_url: str
    destination_domain: str
    destination_final_url: str = ""
    form_action: str | None = None
    detected_ats: str | None = None
    policy_decision: str
    policy_version: int | str = 1
    packet_id: str
    packet_hash: str
    resume_variant_id: str | None = None
    resume_artifact_id: str | None = None
    resume_artifact_sha256: str
    cover_letter_artifact_id: str | None = None
    cover_letter_artifact_sha256: str | None = None
    discovered_fields: list[FormField] = Field(default_factory=list)
    prefilled_fields: dict[str, str] = Field(default_factory=dict)
    provenance_records: dict[str, FieldFillProvenance] = Field(default_factory=dict)
    planned_file_uploads: dict[str, str] = Field(default_factory=dict)
    unfilled_fields: list[str] = Field(default_factory=list)
    ambiguous_fields: list[str] = Field(default_factory=list)
    manual_fields: list[str] = Field(default_factory=list)
    barriers: list[str] = Field(default_factory=list)
    security_warnings: list[str] = Field(default_factory=list)
    form_fingerprint: str
    semantic_snapshot: str = ""
    can_proceed_to_review: bool = True
    blocking_reasons: list[str] = Field(default_factory=list)


class PostFillEvidence(BaseModel):
    """What actually happened in the browser after the prefill writes (F145-09).

    Intended values are hashed so the evidence can be committed without field values;
    filled values are hashes of what was read back from the live control after the
    write. ``readback_verified`` is true only when every intended write and upload was
    observed exactly. ``submit_performed`` is always false in V1.5 prefill-to-review.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: str
    destination_url: str
    destination_final_url: str
    semantic_snapshot: str
    intended_fields: dict[str, str] = Field(default_factory=dict)
    filled_fields: dict[str, str] = Field(default_factory=dict)
    failed_fields: dict[str, str] = Field(default_factory=dict)
    unmatched_fields: list[str] = Field(default_factory=list)
    intended_files: dict[str, str] = Field(default_factory=dict)
    attached_files: dict[str, str] = Field(default_factory=dict)
    attached_readback: dict[str, str] = Field(default_factory=dict)
    readback_verified: bool = False
    submit_performed: bool = False
    notes: list[str] = Field(default_factory=list)


class BrowserSessionResult(BaseModel):
    """Outcome of an interactive assisted application session."""

    model_config = ConfigDict(extra="forbid")

    url: str
    submitted: bool
    confirmation_url: str | None = None
    receipt_text: str | None = None
    external_confirmation_evidence: dict[str, Any] | None = None
    screenshot_path: str | None = None
    notes: str | None = None
    is_mock: bool = False
    # True only if the runner itself performed a submit action; V1.5 runners never do.
    submit_performed: bool = False


class BrowserRunner(ABC):
    """Abstract interface for browser automation runners."""

    @abstractmethod
    def inspect_form(self, url: str) -> FormInspectionResult:
        """Inspect the destination URL and return detected form fields."""
        pass

    @abstractmethod
    def prefill_form(
        self,
        url: str,
        field_values: dict[str, str],
        file_uploads: dict[str, str] | None = None,
        targets: dict[str, str] | None = None,
    ) -> FormPrefillResult:
        """Write values/files into the exact inspected locators given by ``targets``.

        ``field_values`` and ``file_uploads`` are keyed by inspected field name and
        ``targets`` maps each name to the locator captured at inspection time. A name
        without a target is reported as unmatched; runners never search the page
        themselves. Nothing is submitted.
        """
        pass

    @abstractmethod
    def open_interactive_session(
        self,
        url: str,
        prefilled_fields: dict[str, str],
        file_uploads: dict[str, str] | None = None,
    ) -> BrowserSessionResult:
        """Leave the visible browser open for candidate review; never submits."""
        pass
