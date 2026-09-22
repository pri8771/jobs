"""Assisted application execution engine with policy enforcement and human-in-the-loop review.

V1.5 boundary (F145-08..10): the engine inspects the actual destination form, classifies
every field, revalidates one canonical semantic snapshot immediately before writing,
writes only through the exact inspected locators, records what was really filled and
attached, and always stops at candidate review. It never submits and never promotes an
application to a submitted state from URL text, page text, caller flags or arbitrary
evidence dictionaries.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import uuid
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.browser.base import (
    BrowserRunner,
    BrowserSessionResult,
    FieldClassification,
    FieldFillProvenance,
    FormField,
    FormInspectionResult,
    PostFillEvidence,
    PreSubmitReviewManifest,
)
from jobs_automation.core.candidate_profile import CandidateProfileConfig
from jobs_automation.core.policy_registry import PolicyDecision
from jobs_automation.db.base import utc_now
from jobs_automation.db.canary_provenance import require_job_without_durable_canary_provenance
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    ApplicationPacketModel,
    ArtifactModel,
    AuditLogModel,
    JobModel,
    ResumeVariantModel,
    TaskModel,
)
from jobs_automation.policy.evaluator import PolicyEvaluationResult, PolicyEvaluator

logger = logging.getLogger(__name__)

# Native controls the runner can write and read back exactly. Everything else stays
# manual: the engine never guesses how to operate a custom widget.
_TEXT_LIKE_TYPES = frozenset({"text", "email", "tel", "url", "number", "search", "textarea"})

# External confirmation evidence must come from a trusted observer and carry a
# correlatable reference. URL keywords and arbitrary dictionaries never qualify.
ACCEPTED_CONFIRMATION_TYPES = frozenset({"confirmation_page", "confirmation_email"})
ACCEPTED_CONFIRMATION_OBSERVERS = frozenset({"browser_runner", "mailbox_ingestion"})


def resolve_artifact_path(storage_uri: str) -> Path:
    """Resolves an artifact storage URI to a filesystem Path."""
    if storage_uri.startswith("file://"):
        return Path(storage_uri[7:])
    return Path(storage_uri)


def verify_artifact_file(storage_uri: str, expected_sha: str) -> tuple[bool, str]:
    """Verifies that an artifact file exists on disk and matches its expected SHA-256 hash."""
    path = resolve_artifact_path(storage_uri)
    if not path.exists():
        return False, f"Artifact file does not exist at '{path}'"
    try:
        data = path.read_bytes()
        computed = hashlib.sha256(data).hexdigest()
        if computed != expected_sha:
            return (
                False,
                f"Artifact SHA-256 mismatch for '{path}': read {computed} != expected {expected_sha}",
            )
        return True, computed
    except Exception as err:
        return False, f"Failed to read artifact file at '{path}': {err}"


def compute_form_fingerprint(fields: list[FormField], url: str) -> str:
    """Computes a stable structural hash of the form (name/type/selector/required)."""
    fingerprint_raw = "|".join(
        f"{f.name}:{f.field_type}:{f.selector}:{f.required}"
        for f in sorted(fields, key=lambda x: x.name)
    )
    return hashlib.sha256(f"{url}|{fingerprint_raw}".encode()).hexdigest()[:16]


def normalize_destination(url: str) -> str:
    """Scheme, host and path of the actual destination; query and fragment are not identity."""
    parsed = urlparse(url)
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path or '/'}"


def compute_form_snapshot(
    fields: list[FormField],
    destination_url: str,
    *,
    form_action: str | None = None,
    security_warnings: list[str] | None = None,
    page_text_injection_detected: bool = False,
) -> str:
    """One canonical semantic snapshot of the form as it will be written to (F145-08).

    Binds the actual destination, the form action, every field's stable identity,
    name/type/required, label/help/placeholder, option identities and classification,
    plus the page-level security state. Any change to any of these between the first
    inspection and the pre-write recheck invalidates the prefill plan.
    """
    payload = {
        "destination": normalize_destination(destination_url),
        "form_action": form_action or "",
        "page_text_injection_detected": bool(page_text_injection_detected),
        "security_warnings": sorted(set(security_warnings or [])),
        "fields": sorted(
            (
                {
                    "selector": f.selector,
                    "name": f.name,
                    "field_type": f.field_type,
                    "required": bool(f.required),
                    "label": f.label or "",
                    "placeholder": f.placeholder or "",
                    "help_text": f.help_text or "",
                    "options": list(f.options),
                    "option_values": list(f.option_values),
                    "form_action": f.form_action or "",
                    "form_id": f.form_id or "",
                    "classification": str(f.classification),
                }
                for f in fields
            ),
            key=lambda item: (str(item["selector"]), str(item["name"])),
        ),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def describe_snapshot_changes(
    before: list[FormField],
    after: list[FormField],
    *,
    before_destination: str,
    after_destination: str,
    before_action: str | None,
    after_action: str | None,
    before_warnings: list[str],
    after_warnings: list[str],
) -> list[str]:
    """Human-readable, value-free summary of what changed between two inspections."""
    changes: list[str] = []
    if normalize_destination(before_destination) != normalize_destination(after_destination):
        changes.append("destination_changed")
    if (before_action or "") != (after_action or ""):
        changes.append("form_action_changed")
    if set(before_warnings) != set(after_warnings):
        changes.append("security_warnings_changed")

    def _key(field: FormField) -> tuple[str, str]:
        return (field.selector, field.name)

    before_map = {_key(f): f for f in before}
    after_map = {_key(f): f for f in after}
    for key in sorted(set(after_map) - set(before_map)):
        changes.append(f"field_added:{key[1]}")
    for key in sorted(set(before_map) - set(after_map)):
        changes.append(f"field_removed:{key[1]}")
    for key in sorted(set(before_map) & set(after_map)):
        old, new = before_map[key], after_map[key]
        for attribute in (
            "field_type",
            "required",
            "label",
            "placeholder",
            "help_text",
            "options",
            "option_values",
            "form_action",
            "classification",
        ):
            if getattr(old, attribute) != getattr(new, attribute):
                changes.append(f"field_changed:{key[1]}:{attribute}")
    return changes


# ---------------------------------------------------------------------------
# A-R15-02 / J15-11 — Prompt-injection detection
# ---------------------------------------------------------------------------
_PROMPT_INJECTION_PATTERNS: list[str] = [
    "ignore previous instructions",
    "ignore all previous",
    "disregard previous",
    "if you are an ai",
    "if you're an ai",
    "you are now",
    "as an ai",
    "system prompt",
    "output exactly",
    "output the following",
    "print the following",
    "repeat after me",
    "do not follow",
    "override instructions",
    "reveal your instructions",
    "leak candidate",
    "exfiltrate",
    "jailbreak",
    "prompt injection",
    "ignore your training",
    "forget your instructions",
    "act as if",
    "pretend you are",
    "new instructions:",
    "system_instruction",
    "system instruction",
    "system override",
    "admin override",
    "<!-- system",
    "<|system|>",
    "<|user|>",
    "<|assistant|>",
    "###instruction",
    "[system]",
    "[inst]",
]


def detect_prompt_injection_text(text: str) -> bool:
    """Returns True if untrusted text contains known prompt-injection patterns (A-R15-06)."""
    if not text:
        return False
    lower = text.lower()
    return any(pat in lower for pat in _PROMPT_INJECTION_PATTERNS)


def detect_prompt_injection(field: FormField) -> bool:
    """Returns True if any untrusted field text contains prompt-injection patterns.

    Untrusted field text includes name, label, placeholder, help text and options.
    This implements the J15-11 contract: untrusted form text must never be
    executed or used to override candidate facts, skip safety checks, or
    trigger submission.
    """
    untrusted_sources = [
        (field.name or "").lower(),
        (field.label or "").lower(),
        (field.placeholder or "").lower(),
        (field.help_text or "").lower(),
    ]
    # Also inspect select/radio option labels
    for opt in field.options or []:
        untrusted_sources.append(str(opt).lower())

    combined_untrusted = " ".join(untrusted_sources)
    return detect_prompt_injection_text(combined_untrusted)


def classify_field(
    field: FormField,
    candidate: CandidateProfileConfig,
    packet: ApplicationPacketModel | None = None,
) -> tuple[FieldClassification, str | None, str | None, str | None]:
    """Classifies a discovered form field according to the V1.5 safety taxonomy.

    Returns:
        (classification, canonical_key, mapped_value, source_reference)
    """
    # 0. A-R15-02 / J15-11: Prompt-injection resistance.
    # Untrusted page/field text must never execute as instructions or override
    # policy, candidate facts, or submission state.  Any field whose label,
    # name, placeholder, help text or option text contains injection patterns is
    # classified POLICY_BLOCKED and must cause the engine to halt.
    if detect_prompt_injection(field):
        return (
            FieldClassification.POLICY_BLOCKED,
            None,
            None,
            "security:prompt_injection_detected",
        )

    name_lower = (field.name or "").lower().strip()

    label_lower = (field.label or "").lower().strip()
    placeholder_lower = (field.placeholder or "").lower().strip()
    help_lower = (field.help_text or "").lower().strip()
    selector_lower = field.selector.lower()
    combined = f"{name_lower} {label_lower} {placeholder_lower} {help_lower} {selector_lower}"

    # 1. Authentication barriers (login, password, CAPTCHA, MFA, 2FA, OTP)
    if field.field_type == "password":
        return FieldClassification.AUTH_BARRIER, None, None, "auth_barrier:password"
    auth_keywords = [
        "captcha",
        "recaptcha",
        "hcaptcha",
        "turnstile",
        "mfa",
        "2fa",
        "otp",
        "verification_code",
        "verification code",
        "one-time",
        "passcode",
        "login",
        "sign in",
        "sign-in",
        "sso",
        "security code",
    ]
    if any(kw in combined for kw in auth_keywords):
        return FieldClassification.AUTH_BARRIER, None, None, "auth_barrier:challenge_detected"

    # 2. Demographic / EEO self-identification (MUST remain manual only)
    eeo_keywords = [
        "race",
        "ethnicity",
        "gender",
        "sex",
        "sexual orientation",
        "veteran",
        "disability",
        "handicap",
        "pronoun",
        "hispanic",
        "latino",
        "demographic",
        "equal opportunity",
        "eeo",
        "self-identify",
        "self_identify",
        "voluntary self-identification",
    ]
    if any(kw in combined for kw in eeo_keywords):
        return FieldClassification.EEO_MANUAL, None, None, "eeo_demographic_manual_only"

    # 3. Legal consent / Terms / Attestation (manual review required)
    consent_keywords = [
        "terms",
        "privacy policy",
        "consent",
        "attest",
        "certify",
        "acknowledge",
        "declaration",
        "signature",
        "sign here",
        "i agree",
        "agreement",
        "i accept",
    ]
    if any(kw in combined for kw in consent_keywords):
        return FieldClassification.CONSENT_MANUAL, None, None, "legal_consent_manual_only"

    # 4. File uploads (Resume / Cover letter / Unknown)
    # A-R15-09: Only positively identified resume/CV and cover-letter fields are FILE_ARTIFACT.
    # Unknown file inputs must fail to UNKNOWN_REQUIRED (if required) or UNKNOWN_OPTIONAL (if optional).
    # They must NEVER default to resume.
    if field.field_type == "file":
        resume_keywords = ["resume", "cv", "curriculum vitae", "curriculum_vitae", "lebenslauf"]
        cover_keywords = [
            "cover letter",
            "cover_letter",
            "coverletter",
            "cover note",
            "cover_note",
            "letter of intent",
            "motivation letter",
            "motivational letter",
        ]
        if any(kw in combined for kw in cover_keywords):
            return (
                FieldClassification.FILE_ARTIFACT,
                "cover_letter",
                None,
                "packet.cover_letter_artifact",
            )
        elif any(kw in combined for kw in resume_keywords):
            return (
                FieldClassification.FILE_ARTIFACT,
                "resume",
                None,
                "packet.resume_artifact",
            )
        else:
            if field.required:
                return (
                    FieldClassification.UNKNOWN_REQUIRED,
                    None,
                    None,
                    "unmapped_required_file_field",
                )
            return (
                FieldClassification.UNKNOWN_OPTIONAL,
                None,
                None,
                "unmapped_optional_file_field",
            )

    # 5. Packet screening question answers
    if packet and packet.answers_json:
        for ans_key, ans_val in packet.answers_json.items():
            norm_key = ans_key.lower().replace("_", " ")
            if ans_key.lower() == name_lower or norm_key in combined:
                return (
                    FieldClassification.PACKET_ANSWER,
                    ans_key,
                    str(ans_val),
                    f"packet.answers_json.{ans_key}",
                )

    # 6. Canonical candidate profile fields
    if any(
        k in combined for k in ["first_name", "firstname", "first name", "given name", "given_name"]
    ):
        parts = candidate.identity.full_name.split(maxsplit=1)
        val = parts[0] if parts else ""
        return (
            FieldClassification.SAFE_CANONICAL,
            "first_name",
            val,
            "candidate_profile.identity.full_name[0]",
        )

    if any(k in combined for k in ["last_name", "lastname", "last name", "family name", "surname"]):
        parts = candidate.identity.full_name.split(maxsplit=1)
        val = parts[1] if len(parts) > 1 else ""
        return (
            FieldClassification.SAFE_CANONICAL,
            "last_name",
            val,
            "candidate_profile.identity.full_name[1]",
        )

    if (
        any(k in combined for k in ["full_name", "fullname", "candidate name", "your name"])
        or name_lower == "name"
    ):
        return (
            FieldClassification.SAFE_CANONICAL,
            "full_name",
            candidate.identity.full_name,
            "candidate_profile.identity.full_name",
        )

    if field.field_type == "email" or any(k in combined for k in ["email", "e-mail"]):
        return (
            FieldClassification.SAFE_CANONICAL,
            "email",
            candidate.identity.email,
            "candidate_profile.identity.email",
        )

    if field.field_type == "tel" or any(
        k in combined for k in ["phone", "mobile", "telephone", "phone number"]
    ):
        return (
            FieldClassification.SAFE_CANONICAL,
            "phone",
            candidate.identity.phone,
            "candidate_profile.identity.phone",
        )

    if any(k in combined for k in ["location", "city", "address"]):
        loc_str = f"{candidate.identity.city}, {candidate.identity.state}".strip(", ")
        return (
            FieldClassification.SAFE_CANONICAL,
            "location",
            loc_str,
            "candidate_profile.identity.location",
        )

    if "linkedin" in combined:
        return (
            FieldClassification.SAFE_CANONICAL,
            "linkedin",
            candidate.links.linkedin or "",
            "candidate_profile.links.linkedin",
        )

    if "github" in combined:
        return (
            FieldClassification.SAFE_CANONICAL,
            "github",
            candidate.links.github or "",
            "candidate_profile.links.github",
        )

    if any(
        k in combined for k in ["portfolio", "website", "personal site", "personal_site", "blog"]
    ):
        val = candidate.links.portfolio or candidate.links.personal_site or ""
        return (
            FieldClassification.SAFE_CANONICAL,
            "portfolio",
            val,
            "candidate_profile.links.portfolio",
        )

    # 7. Unmapped fields
    if field.required:
        return FieldClassification.UNKNOWN_REQUIRED, None, None, "unmapped_required_field"
    return FieldClassification.UNKNOWN_OPTIONAL, None, None, "unmapped_optional_field"


def compute_barriers(
    classified_fields: list[FormField],
    unresolved_questions: list[str],
    policy_decision: PolicyDecision,
) -> list[str]:
    """Evaluates manual barriers and stop conditions."""
    barriers: list[str] = []
    if policy_decision in (PolicyDecision.BLOCKED, PolicyDecision.MANUAL_ONLY):
        barriers.append(f"policy_{policy_decision.value}")
    if unresolved_questions:
        barriers.append(f"unresolved_questions_count_{len(unresolved_questions)}")
    for f in classified_fields:
        if f.classification == FieldClassification.AUTH_BARRIER:
            barriers.append(f"auth_barrier:{f.name}")
        elif f.classification == FieldClassification.UNKNOWN_REQUIRED:
            barriers.append(f"unknown_required_field:{f.name}")
        elif f.classification == FieldClassification.CONSENT_MANUAL:
            barriers.append(f"consent_manual:{f.name}")
        elif f.classification == FieldClassification.POLICY_BLOCKED:
            barriers.append(f"policy_blocked:{f.name}")
    return barriers


_BLOCKING_BARRIER_PREFIXES = (
    "auth_barrier:",
    "unknown_required_field:",
    "unresolved_questions_",
    "consent_manual:",
    "policy_blocked:",
    "missing_required_cover_letter:",
    "ambiguous_required_field:",
    "ambiguous_required_file_field:",
    "manual_required_control:",
    "manual_required_select_no_exact_option:",
)


def _parse_utc(value: Any) -> datetime.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def is_valid_external_confirmation(
    session_res: BrowserSessionResult,
    auto_confirm: bool,  # noqa: ARG001  # present for call-site compatibility; is NOT evidence
    receipt_text: str | None,
    allow_simulation: bool = False,
    expected_domain: str | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    """Strictly evaluates whether independently correlated external confirmation exists.

    Contract (A-R15-01, F145-10):
    - ``auto_confirm=True`` means only "the candidate says they attempted"; it is NOT
      evidence and can never produce SUBMITTED alone.
    - ``receipt_text`` supplied by a caller is NOT evidence; it may annotate an already
      confirmed event.
    - A ``confirmation_url`` observed by the runner is NOT evidence on its own: URL
      keywords (``confirmation``, ``thank_you``, ``?next=confirmation``) prove nothing.
    - The only accepted evidence is a structured record captured by a trusted observer
      (``captured_by`` in browser_runner / mailbox_ingestion) of an accepted type
      (``confirmation_page`` / ``confirmation_email``) carrying an employer/ATS
      ``reference_id`` and an ``observed_at_utc`` timestamp; a confirmation page must
      also be on the application destination host when that host is known. Simulated
      or mock-marked evidence is rejected in live mode.
    - Everything else yields SUBMISSION_UNCONFIRMED so the record can be upgraded later
      when real correlated evidence arrives (e.g. mailbox ingestion).
    """
    if session_res.is_mock and not allow_simulation:
        return (
            False,
            "Simulated mock runner evidence cannot satisfy live submission confirmation.",
            {},
        )

    evidence = session_res.external_confirmation_evidence
    if not isinstance(evidence, dict) or not evidence:
        return (
            False,
            "No verifiable external receipt, confirmation URL, or confirmation email captured.",
            {},
        )
    if evidence.get("simulated") and not allow_simulation:
        return False, "Simulated confirmation rejected in live mode.", {}

    evidence_type = str(evidence.get("type") or "")
    if evidence_type not in ACCEPTED_CONFIRMATION_TYPES:
        return (
            False,
            f"External confirmation evidence type {evidence_type!r} is not an accepted "
            "correlated evidence type; arbitrary evidence dictionaries do not confirm.",
            {},
        )
    observer = str(evidence.get("captured_by") or "")
    if observer not in ACCEPTED_CONFIRMATION_OBSERVERS:
        return (
            False,
            "External confirmation evidence was not captured by a trusted observer "
            "(browser runner or mailbox ingestion).",
            {},
        )
    reference_id = str(evidence.get("reference_id") or "").strip()
    if not reference_id:
        return False, "External confirmation evidence carries no employer/ATS reference id.", {}
    if _parse_utc(evidence.get("observed_at_utc")) is None:
        return False, "External confirmation evidence has no valid observation timestamp.", {}
    if not allow_simulation:
        lowered = json.dumps(evidence, sort_keys=True, default=str).lower()
        if "mock" in lowered or "simulated" in lowered:
            return False, "Mock confirmation evidence rejected in live mode.", {}
    if evidence_type == "confirmation_page":
        page_url = str(evidence.get("url") or "")
        if not page_url.startswith(("https://", "http://")):
            return False, "Confirmation page evidence has no HTTP(S) URL.", {}
        if expected_domain and urlparse(page_url).netloc.lower() != expected_domain.lower():
            return (
                False,
                "Confirmation page host does not match the application destination.",
                {},
            )

    annotation = receipt_text or f"{evidence_type}:{reference_id}"
    return True, annotation, evidence


class AssistedApplicationPlan(BaseModel):
    """Execution plan for an assisted application."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    packet_id: str | None = None
    company_name: str
    job_title: str
    apply_url: str
    destination_domain: str
    policy: PolicyEvaluationResult
    prefill_data: dict[str, str] = Field(default_factory=dict)
    file_uploads: dict[str, str] = Field(default_factory=dict)
    unresolved_questions: list[str] = Field(default_factory=list)
    can_prefill: bool = False
    instructions: str = ""
    discovered_fields: list[FormField] = Field(default_factory=list)
    field_provenance: dict[str, FieldFillProvenance] = Field(default_factory=dict)
    barriers: list[str] = Field(default_factory=list)
    form_fingerprint: str | None = None


class AssistedApplicationResult(BaseModel):
    """Outcome of assisted application execution."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    application_id: str | None = None
    status: str  # SUBMITTED, SUBMISSION_UNCONFIRMED, MANUAL_RECORDED, BLOCKED, REVIEW_REQUIRED, ALREADY_SUBMITTED
    policy_decision: str
    destination_domain: str
    destination_final_url: str | None = None
    prefilled_count: int = 0
    receipt_text: str | None = None
    confirmation_url: str | None = None
    external_confirmation_evidence: dict[str, Any] | None = None
    form_fingerprint: str | None = None
    semantic_snapshot: str | None = None
    barriers: list[str] = Field(default_factory=list)
    security_warnings: list[str] = Field(default_factory=list)
    review_manifest: PreSubmitReviewManifest | None = None
    postfill_evidence: PostFillEvidence | None = None
    message: str


class AssistedApplicationEngine:
    """Coordinates policy checks, safe field prefilling, and human review gates."""

    def __init__(
        self,
        session: Session,
        policy_evaluator: PolicyEvaluator,
        browser_runner: BrowserRunner,
        candidate_profile: CandidateProfileConfig,
        allow_simulation: bool = False,
        require_live_ready: bool = True,
    ) -> None:
        self.session = session
        self.policy_evaluator = policy_evaluator
        self.browser_runner = browser_runner
        self.candidate = candidate_profile
        self.allow_simulation = allow_simulation
        self.require_live_ready = require_live_ready

    def _extract_domain(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc.lower()

    def _verify_packet_integrity(
        self,
        packet: ApplicationPacketModel,
        resume_sha: str,
        cl_sha: str | None,
    ) -> tuple[bool, str]:
        """Revalidates packet hash, answers provenance, and variant linkage before browser use (A-R15-08)."""
        # 1. Check resume variant linkage
        if packet.resume_variant_id:
            variant = self.session.scalar(
                select(ResumeVariantModel).where(ResumeVariantModel.id == packet.resume_variant_id)
            )
            if not variant:
                return False, f"Resume variant {packet.resume_variant_id} not found."
            if variant.content_hash != resume_sha:
                return (
                    False,
                    f"PACKET_VARIANT_MISMATCH: Resume variant content hash ({variant.content_hash}) != resume artifact SHA ({resume_sha})",
                )

        # 2. Check answers and provenance consistency
        answers = packet.answers_json or {}
        provenance = packet.answer_provenance_json or {}
        for ans_key in answers:
            if ans_key not in provenance:
                return (
                    False,
                    f"PACKET_PROVENANCE_MISMATCH: Answer for '{ans_key}' has no provenance record.",
                )
        for prov_key in provenance:
            if prov_key not in answers:
                return (
                    False,
                    f"PACKET_PROVENANCE_MISMATCH: Provenance key '{prov_key}' has no matching answer.",
                )

        # 3. Recompute canonical packet hash and compare
        from jobs_automation.preparation.packet_builder import compute_canonical_packet_hash

        computed_hash = compute_canonical_packet_hash(
            job_id=packet.job_id,
            profile_version=packet.candidate_profile_version,
            resume_variant_id=packet.resume_variant_id,
            resume_sha=resume_sha,
            cover_letter_sha=cl_sha,
            answers=answers,
            answer_provenance=provenance,
        )
        if computed_hash != packet.packet_hash:
            return (
                False,
                f"PACKET_HASH_MISMATCH: Recomputed packet hash ({computed_hash}) does not match persisted packet hash ({packet.packet_hash}).",
            )

        return True, ""

    def build_plan(
        self,
        job_id: uuid.UUID,
        packet_id: uuid.UUID | None = None,
    ) -> AssistedApplicationPlan:
        """Inspects job and application packet to construct a prefill and policy execution plan."""
        job = self.session.scalar(select(JobModel).where(JobModel.id == job_id))
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")

        require_job_without_durable_canary_provenance(self.session, job.id)

        apply_url = job.apply_url
        if not apply_url:
            raise ValueError(f"Job {job.title} at {job.company_name} has no apply URL")

        domain = self._extract_domain(apply_url)
        policy_res = self.policy_evaluator.evaluate(domain, capability="submit_application")

        packet: ApplicationPacketModel | None = None
        if packet_id:
            packet = self.session.scalar(
                select(ApplicationPacketModel).where(ApplicationPacketModel.id == packet_id)
            )
            if not packet:
                raise ValueError(f"ApplicationPacketModel with ID {packet_id} not found")
            if packet.job_id != job_id:
                raise ValueError(
                    f"Packet {packet_id} belongs to job {packet.job_id}, not target job {job_id}"
                )

        prefill_data: dict[str, str] = {}
        file_uploads: dict[str, str] = {}
        unresolved: list[str] = []

        if packet:
            unresolved = list(packet.unresolved_questions_json)
            # Find resume artifact file storage path
            if packet.resume_artifact_id:
                resume_art = self.session.scalar(
                    select(ArtifactModel).where(ArtifactModel.id == packet.resume_artifact_id)
                )
                if resume_art:
                    file_uploads["resume"] = resume_art.storage_uri

            # A-R15-07: Resolve cover letter artifact file storage path
            if packet.cover_letter_artifact_id:
                cl_art = self.session.scalar(
                    select(ArtifactModel).where(ArtifactModel.id == packet.cover_letter_artifact_id)
                )
                if cl_art:
                    file_uploads["cover_letter"] = cl_art.storage_uri

            # Map pre-computed screening answers
            for q_key, answer_val in packet.answers_json.items():
                prefill_data[q_key] = str(answer_val)

        # Standard candidate profile fields
        parts = self.candidate.identity.full_name.split(maxsplit=1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""

        prefill_data.setdefault("first_name", first_name)
        prefill_data.setdefault("last_name", last_name)
        prefill_data.setdefault("full_name", self.candidate.identity.full_name)
        if self.candidate.identity.email:
            prefill_data.setdefault("email", self.candidate.identity.email)
        if self.candidate.identity.phone:
            prefill_data.setdefault("phone", self.candidate.identity.phone)
        prefill_data.setdefault(
            "location", f"{self.candidate.identity.city}, {self.candidate.identity.state}"
        )

        if self.candidate.links.linkedin:
            prefill_data.setdefault("linkedin", self.candidate.links.linkedin)
        if self.candidate.links.github:
            prefill_data.setdefault("github", self.candidate.links.github)
        if self.candidate.links.portfolio:
            prefill_data.setdefault("portfolio", self.candidate.links.portfolio)
        if self.candidate.links.personal_site:
            prefill_data.setdefault("personal_site", self.candidate.links.personal_site)

        can_prefill = (
            policy_res.decision in (PolicyDecision.ASSISTED, PolicyDecision.AUTO_ALLOWED)
            and packet is not None
            and len(unresolved) == 0
        )

        if policy_res.decision == PolicyDecision.BLOCKED:
            instructions = f"Automation BLOCKED for {domain}: {policy_res.reason}. Do not submit automated requests."
        elif policy_res.decision == PolicyDecision.MANUAL_ONLY:
            instructions = (
                f"Platform {domain} requires manual native submission per policy. "
                "Open url in candidate's standard browser and use candidate worksheet to submit manually."
            )
        elif packet is None:
            instructions = (
                f"Assisted mode permitted for {domain}, but no explicit application packet was provided. "
                "A verified accepted packet is required before form prefill."
            )
        else:
            instructions = (
                f"Assisted mode permitted for {domain}. Form will be inspected, prefilled with safe fields, "
                "and reviewed prior to final human confirmation."
            )

        return AssistedApplicationPlan(
            job_id=str(job.id),
            packet_id=str(packet.id) if packet else None,
            company_name=job.company_name,
            job_title=job.title,
            apply_url=apply_url,
            destination_domain=domain,
            policy=policy_res,
            prefill_data=prefill_data,
            file_uploads=file_uploads,
            unresolved_questions=unresolved,
            can_prefill=can_prefill,
            instructions=instructions,
        )

    # ------------------------------------------------------------------ helpers

    def _blocked(
        self,
        job_id: uuid.UUID,
        plan: AssistedApplicationPlan,
        message: str,
        *,
        security_warnings: list[str] | None = None,
        barriers: list[str] | None = None,
        form_fingerprint: str | None = None,
        semantic_snapshot: str | None = None,
        destination_final_url: str | None = None,
    ) -> AssistedApplicationResult:
        self.session.commit()
        return AssistedApplicationResult(
            job_id=str(job_id),
            status="BLOCKED",
            policy_decision=plan.policy.decision.value,
            destination_domain=plan.destination_domain,
            destination_final_url=destination_final_url,
            security_warnings=list(security_warnings or []),
            barriers=list(barriers or []),
            form_fingerprint=form_fingerprint,
            semantic_snapshot=semantic_snapshot,
            message=message,
        )

    def _inspect(self, url: str) -> FormInspectionResult:
        """Inspect through the runner; an exception is an inspection failure, never clean."""
        try:
            return self.browser_runner.inspect_form(url)
        except Exception as exc:
            logger.warning("Browser inspection raised %s for %s", type(exc).__name__, url)
            return FormInspectionResult(
                url=url,
                title="",
                fields=[],
                form_found=False,
                inspection_error=type(exc).__name__,
            )

    def _classify_all(
        self, fields: list[FormField], packet: ApplicationPacketModel
    ) -> list[tuple[FormField, str | None, str | None, str | None]]:
        """Classify inspected fields, returning the classified copy plus mapping details."""
        classified: list[tuple[FormField, str | None, str | None, str | None]] = []
        for field in fields:
            classification, canonical_key, mapped_val, source_ref = classify_field(
                field=field,
                candidate=self.candidate,
                packet=packet,
            )
            updated_field = field.model_copy(update={"classification": classification})
            classified.append((updated_field, canonical_key, mapped_val, source_ref))
        return classified

    # ------------------------------------------------------------------ execute

    def execute(
        self,
        job_id: uuid.UUID,
        packet_id: uuid.UUID | None = None,
        auto_confirm: bool = False,
        receipt_text: str | None = None,
        allow_simulation: bool | None = None,
        require_live_ready: bool | None = None,
    ) -> AssistedApplicationResult:
        """Executes assisted application runtime with inspect-before-write, field classification, and review gates."""
        sim_allowed = self.allow_simulation if allow_simulation is None else allow_simulation
        live_ready_required = (
            self.require_live_ready if require_live_ready is None else require_live_ready
        )
        if sim_allowed:
            live_ready_required = False

        try:
            plan = self.build_plan(job_id=job_id, packet_id=packet_id)
        except ValueError as err:
            self._log_audit(
                action_type="assisted_prefill_rejected",
                entity_type="job",
                entity_id=job_id,
                result="blocked",
                metadata={"reason": str(err)},
            )
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                policy_decision="blocked",
                destination_domain="",
                message=str(err),
            )

        # 1. Idempotency Check: see if application was already submitted
        existing_app = self.session.scalar(
            select(ApplicationModel).where(ApplicationModel.job_id == job_id)
        )
        if existing_app and existing_app.status == "SUBMITTED":
            return AssistedApplicationResult(
                job_id=str(job_id),
                application_id=str(existing_app.id),
                status="ALREADY_SUBMITTED",
                policy_decision=existing_app.policy_decision,
                destination_domain=plan.destination_domain,
                message=f"Application for {plan.job_title} at {plan.company_name} was already submitted on {existing_app.applied_at}.",
            )

        # 2. Policy Gate: BLOCKED destinations halt immediately
        if plan.policy.decision == PolicyDecision.BLOCKED:
            self._log_audit(
                action_type="policy_blocked_application_attempt",
                entity_type="job",
                entity_id=job_id,
                result="blocked",
                metadata={"reason": plan.policy.reason, "domain": plan.destination_domain},
            )
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                message=f"Application blocked by platform policy: {plan.policy.reason}",
            )

        # 3. Policy Gate: MANUAL_ONLY destinations (e.g., LinkedIn, Indeed)
        if plan.policy.decision == PolicyDecision.MANUAL_ONLY:
            app = existing_app or ApplicationModel(
                job_id=job_id,
                destination_domain=plan.destination_domain,
                policy_decision=plan.policy.decision.value,
                application_mode="manual",
                status="MANUAL_IN_PROGRESS",
                packet_id=uuid.UUID(plan.packet_id) if plan.packet_id else None,
            )
            if not existing_app:
                self.session.add(app)
                self.session.flush()

            if auto_confirm:
                # A candidate report of a native manual submission carries no external
                # evidence; it is recorded as SUBMISSION_UNCONFIRMED for later upgrade.
                manual_report = BrowserSessionResult(
                    url=plan.apply_url,
                    submitted=True,
                    receipt_text=receipt_text,
                    is_mock=False,
                )
                valid_conf, conf_receipt, conf_ev = is_valid_external_confirmation(
                    session_res=manual_report,
                    auto_confirm=auto_confirm,
                    receipt_text=receipt_text,
                    allow_simulation=sim_allowed,
                    expected_domain=plan.destination_domain,
                )
                if valid_conf:
                    now = utc_now()
                    app.status = "SUBMITTED"
                    app.applied_at = now
                    app.last_activity_at = now
                    self._record_submission_event(
                        application_id=app.id,
                        source="manual_native",
                        receipt=conf_receipt,
                        domain=plan.destination_domain,
                        packet_id=plan.packet_id,
                        evidence=conf_ev,
                    )
                    self._complete_review_task(job_id=job_id, app_id=app.id)
                    self.session.commit()
                    return AssistedApplicationResult(
                        job_id=str(job_id),
                        application_id=str(app.id),
                        status="MANUAL_RECORDED",
                        policy_decision=plan.policy.decision.value,
                        destination_domain=plan.destination_domain,
                        receipt_text=conf_receipt,
                        external_confirmation_evidence=conf_ev,
                        message="Manual native application recorded as submitted with external evidence.",
                    )
                else:
                    app.status = "SUBMISSION_UNCONFIRMED"
                    self._record_submission_unconfirmed_event(
                        application_id=app.id,
                        source="manual_native",
                        domain=plan.destination_domain,
                        packet_id=plan.packet_id,
                        reason=conf_receipt,
                    )
                    self.session.commit()
                    return AssistedApplicationResult(
                        job_id=str(job_id),
                        application_id=str(app.id),
                        status="SUBMISSION_UNCONFIRMED",
                        policy_decision=plan.policy.decision.value,
                        destination_domain=plan.destination_domain,
                        message=f"Manual submission unconfirmed awaiting external evidence: {conf_receipt}",
                    )
            else:
                self.session.commit()
                return AssistedApplicationResult(
                    job_id=str(job_id),
                    application_id=str(app.id),
                    status="REVIEW_REQUIRED",
                    policy_decision=plan.policy.decision.value,
                    destination_domain=plan.destination_domain,
                    message=(
                        f"Manual submission required for {plan.destination_domain}. "
                        f"Apply URL: {plan.apply_url}. Confirm after submitting in portal."
                    ),
                )

        # 4. ASSISTED Execution Pre-Browser Contract Guards (J15-00)
        if packet_id is None:
            self._log_audit(
                action_type="assisted_prefill_rejected",
                entity_type="job",
                entity_id=job_id,
                result="blocked",
                metadata={"reason": "missing_explicit_packet_id"},
            )
            return self._blocked(
                job_id,
                plan,
                "Explicit accepted packet_id is required for assisted execution. Latest-packet fallback is disabled.",
            )

        packet = self.session.scalar(
            select(ApplicationPacketModel).where(ApplicationPacketModel.id == packet_id)
        )
        if not packet:
            return self._blocked(
                job_id, plan, f"ApplicationPacketModel {packet_id} not found in database."
            )

        if packet.job_id != job_id:
            self._log_audit(
                action_type="assisted_prefill_rejected",
                entity_type="application_packet",
                entity_id=packet.id,
                result="blocked",
                metadata={"reason": "packet_job_id_mismatch", "target_job_id": str(job_id)},
            )
            return self._blocked(
                job_id,
                plan,
                f"Packet {packet_id} belongs to job {packet.job_id}, not target job {job_id}.",
            )

        if live_ready_required and not packet.is_live_ready:
            self._log_audit(
                action_type="assisted_prefill_rejected",
                entity_type="application_packet",
                entity_id=packet.id,
                result="blocked",
                metadata={"reason": "packet_not_live_ready"},
            )
            return self._blocked(
                job_id,
                plan,
                "Packet is not marked live-ready. Review and accept packet before live execution.",
            )

        if packet.unresolved_questions_json:
            self._log_audit(
                action_type="assisted_prefill_rejected",
                entity_type="application_packet",
                entity_id=packet.id,
                result="blocked",
                metadata={"unresolved_questions": packet.unresolved_questions_json},
            )
            return self._blocked(
                job_id,
                plan,
                f"Packet has unresolved consequential questions: {packet.unresolved_questions_json}",
            )

        if not packet.resume_artifact_id:
            return self._blocked(job_id, plan, "Packet has no resume artifact attached.")

        # Verify resume artifact on disk & SHA-256 integrity (J15-04)
        resume_art = self.session.scalar(
            select(ArtifactModel).where(ArtifactModel.id == packet.resume_artifact_id)
        )
        if not resume_art:
            return self._blocked(
                job_id,
                plan,
                f"Resume artifact {packet.resume_artifact_id} not found in database.",
            )

        valid_resume, resume_sha = verify_artifact_file(resume_art.storage_uri, resume_art.sha256)
        if not valid_resume:
            if not sim_allowed:
                self._log_audit(
                    action_type="assisted_prefill_rejected",
                    entity_type="artifact",
                    entity_id=resume_art.id,
                    result="blocked",
                    metadata={"reason": resume_sha},
                )
                return self._blocked(
                    job_id,
                    plan,
                    f"Resume artifact integrity verification failed: {resume_sha}",
                )
            resume_sha = resume_art.sha256

        cover_letter_sha: str | None = None
        if packet.cover_letter_artifact_id:
            cl_art = self.session.scalar(
                select(ArtifactModel).where(ArtifactModel.id == packet.cover_letter_artifact_id)
            )
            if cl_art:
                valid_cl, cl_sha = verify_artifact_file(cl_art.storage_uri, cl_art.sha256)
                if not valid_cl and not sim_allowed:
                    return self._blocked(
                        job_id,
                        plan,
                        f"Cover letter artifact integrity verification failed: {cl_sha}",
                    )
                cover_letter_sha = cl_sha if valid_cl else cl_art.sha256

        # Verify packet integrity, provenance bijection, and variant linkage (A-R15-08)
        valid_packet, packet_err = self._verify_packet_integrity(
            packet=packet,
            resume_sha=resume_sha,
            cl_sha=cover_letter_sha,
        )
        if not valid_packet and not sim_allowed:
            self._log_audit(
                action_type="assisted_prefill_rejected",
                entity_type="application_packet",
                entity_id=packet.id,
                result="blocked",
                metadata={"reason": packet_err},
            )
            return self._blocked(job_id, plan, f"Packet integrity check failed: {packet_err}")

        # 5. Form Inspection Gate (Inspect Before Write - J15-01)
        inspection_res = self._inspect(plan.apply_url)
        page_security_warnings: list[str] = list(inspection_res.page_security_warnings or [])
        if (
            inspection_res.inspection_error
            or not inspection_res.form_found
            or len(inspection_res.fields) == 0
        ):
            self._log_audit(
                action_type="assisted_inspection_failed",
                entity_type="job",
                entity_id=job_id,
                result="blocked",
                metadata={
                    "url": plan.apply_url,
                    "security_warnings": page_security_warnings,
                    "inspection_error": inspection_res.inspection_error,
                },
            )
            detail = (
                f"inspection error {inspection_res.inspection_error}"
                if inspection_res.inspection_error
                else f"no form found at destination URL {plan.apply_url}"
            )
            return self._blocked(
                job_id,
                plan,
                f"Form inspection failed: {detail}. An incomplete inspection is not a clean safety result.",
                security_warnings=page_security_warnings,
            )

        # 5b. Destination binding (F145-08): the page actually navigated to must be a
        # destination the policy permits for assisted prefill.
        destination_final_url = inspection_res.destination_url()
        actual_domain = self._extract_domain(destination_final_url)
        if actual_domain and actual_domain != plan.destination_domain:
            redirected_policy = self.policy_evaluator.evaluate(
                actual_domain, capability="submit_application"
            )
            page_security_warnings.append(
                f"security_warning:destination_redirected:{actual_domain}"
            )
            if redirected_policy.decision not in (
                PolicyDecision.ASSISTED,
                PolicyDecision.AUTO_ALLOWED,
            ):
                self._log_audit(
                    action_type="assisted_prefill_halted_destination_redirect",
                    entity_type="job",
                    entity_id=job_id,
                    result="blocked",
                    metadata={
                        "planned_domain": plan.destination_domain,
                        "actual_domain": actual_domain,
                        "policy_decision": redirected_policy.decision.value,
                    },
                )
                return self._blocked(
                    job_id,
                    plan,
                    f"DESTINATION_REDIRECT_BLOCKED: the application page navigated to {actual_domain}, "
                    f"which policy does not permit for assisted prefill "
                    f"({redirected_policy.decision.value}).",
                    security_warnings=page_security_warnings,
                    destination_final_url=destination_final_url,
                )

        # 6. Field Classification and Manual Barrier Classifier (J15-01 & J15-02)
        classified = self._classify_all(inspection_res.fields, packet)
        classified_fields: list[FormField] = [item[0] for item in classified]
        name_counts = Counter(f.name for f in classified_fields)
        prefill_candidates: dict[str, str] = {}
        targets: dict[str, str] = {}
        prov_dict: dict[str, FieldFillProvenance] = {}
        unfilled_field_names: list[str] = []
        ambiguous_fields: list[str] = []
        manual_fields: list[str] = []
        extra_barriers: list[str] = []
        file_fields: dict[str, list[FormField]] = {"resume": [], "cover_letter": []}

        for field, canonical_key, mapped_val, source_ref in classified:
            classification = field.classification
            if classification in (
                FieldClassification.SAFE_CANONICAL,
                FieldClassification.PACKET_ANSWER,
            ):
                if mapped_val is None:
                    unfilled_field_names.append(field.name)
                    continue
                if name_counts[field.name] > 1:
                    # F145-09: several controls share this name; never pick one.
                    ambiguous_fields.append(field.name)
                    unfilled_field_names.append(field.name)
                    if field.required:
                        extra_barriers.append(f"ambiguous_required_field:{field.name}")
                    continue
                if field.field_type in ("checkbox", "radio"):
                    # Custom/native toggles are never guessed; the candidate sets them.
                    manual_fields.append(field.name)
                    unfilled_field_names.append(field.name)
                    if field.required:
                        extra_barriers.append(f"manual_required_control:{field.name}")
                    continue
                if field.field_type == "select":
                    if mapped_val not in field.options and mapped_val not in field.option_values:
                        manual_fields.append(field.name)
                        unfilled_field_names.append(field.name)
                        if field.required:
                            extra_barriers.append(
                                f"manual_required_select_no_exact_option:{field.name}"
                            )
                        continue
                elif field.field_type not in _TEXT_LIKE_TYPES:
                    manual_fields.append(field.name)
                    unfilled_field_names.append(field.name)
                    if field.required:
                        extra_barriers.append(f"manual_required_control:{field.name}")
                    continue
                prefill_candidates[field.name] = mapped_val
                targets[field.name] = field.selector
                val_hash = hashlib.sha256(mapped_val.encode("utf-8")).hexdigest()
                prov_dict[field.name] = FieldFillProvenance(
                    field_name=field.name,
                    target_selector=field.selector,
                    classification=classification,
                    canonical_key=canonical_key,
                    source_reference=source_ref or "unknown",
                    value_hash=val_hash,
                    confidence=1.0,
                    mapping_method=(
                        "exact_canonical_match"
                        if classification == FieldClassification.SAFE_CANONICAL
                        else "packet_answer_match"
                    ),
                )
            elif classification == FieldClassification.FILE_ARTIFACT:
                file_fields.setdefault(canonical_key or "unknown", []).append(field)
            else:
                unfilled_field_names.append(field.name)

        # F145-09: bind each upload to exactly one positively identified inspected field.
        planned_uploads: dict[str, str] = {}  # field name -> artifact storage path
        planned_upload_keys: dict[str, str] = {}  # field name -> "resume" | "cover_letter"
        expected_upload_digests: dict[str, str] = {}
        for artifact_key, matched_fields in file_fields.items():
            if not matched_fields:
                continue
            if len(matched_fields) > 1 or any(name_counts[f.name] > 1 for f in matched_fields):
                for f in matched_fields:
                    ambiguous_fields.append(f.name)
                    unfilled_field_names.append(f.name)
                    if f.required:
                        extra_barriers.append(f"ambiguous_required_file_field:{f.name}")
                continue
            field = matched_fields[0]
            if artifact_key == "cover_letter":
                if cover_letter_sha is None or "cover_letter" not in plan.file_uploads:
                    # Required cover-letter field but no artifact in packet: barrier below.
                    unfilled_field_names.append(field.name)
                    continue
                digest = cover_letter_sha
                storage_uri = plan.file_uploads["cover_letter"]
                file_source_ref = "packet.cover_letter_artifact"
            elif artifact_key == "resume":
                if "resume" not in plan.file_uploads:
                    unfilled_field_names.append(field.name)
                    continue
                digest = resume_sha
                storage_uri = plan.file_uploads["resume"]
                file_source_ref = "packet.resume_artifact"
            else:
                unfilled_field_names.append(field.name)
                continue
            planned_uploads[field.name] = storage_uri
            planned_upload_keys[field.name] = artifact_key
            expected_upload_digests[field.name] = digest
            targets[field.name] = field.selector
            prov_dict[field.name] = FieldFillProvenance(
                field_name=field.name,
                target_selector=field.selector,
                classification=FieldClassification.FILE_ARTIFACT,
                canonical_key=artifact_key,
                source_reference=file_source_ref,
                value_hash=digest,
                confidence=1.0,
                mapping_method="file_artifact_match",
            )

        form_fingerprint = compute_form_fingerprint(classified_fields, plan.apply_url)
        semantic_snapshot = compute_form_snapshot(
            classified_fields,
            destination_final_url,
            form_action=inspection_res.form_action,
            security_warnings=page_security_warnings,
            page_text_injection_detected=inspection_res.page_text_injection_detected,
        )
        barriers = compute_barriers(
            classified_fields=classified_fields,
            unresolved_questions=packet.unresolved_questions_json,
            policy_decision=plan.policy.decision,
        )
        barriers.extend(extra_barriers)

        # Check for missing required cover letter barrier (A-R15-07)
        for f in classified_fields:
            if (
                f.classification == FieldClassification.FILE_ARTIFACT
                and f.required
                and ("cover" in (f.name or "").lower() or "cover" in (f.label or "").lower())
                and cover_letter_sha is None
            ):
                barriers.append(f"missing_required_cover_letter:{f.name}")

        # 7. Stop Conditions Before Prefill (J15-08, A-R15-03, A-R15-02, A-R15-07, F145-09)
        blocking_barriers = [b for b in barriers if b.startswith(_BLOCKING_BARRIER_PREFIXES)]
        if blocking_barriers:
            review_task = TaskModel(
                job_id=job_id,
                task_type="MANUAL_BARRIER_REVIEW",
                status="pending",
                payload_json={
                    "barriers": blocking_barriers,
                    "all_barriers": barriers,
                    "url": plan.apply_url,
                    "security_warnings": page_security_warnings,
                },
            )
            self.session.add(review_task)
            self._log_audit(
                action_type="assisted_prefill_halted_barriers",
                entity_type="job",
                entity_id=job_id,
                result="review_required",
                metadata={
                    "blocking_barriers": blocking_barriers,
                    "security_warnings": page_security_warnings,
                },
            )
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="REVIEW_REQUIRED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                destination_final_url=destination_final_url,
                barriers=barriers,
                security_warnings=page_security_warnings,
                form_fingerprint=form_fingerprint,
                semantic_snapshot=semantic_snapshot,
                message=f"Prefill halted due to manual barriers requiring candidate action: {blocking_barriers}",
            )

        # 8. Re-verify artifact bytes immediately before upload (J15-04 & A-R15-07)
        verified_uploads: dict[str, str] = {}
        for field_name, storage_uri in planned_uploads.items():
            artifact_path = resolve_artifact_path(storage_uri)
            expected = expected_upload_digests[field_name]
            if artifact_path.exists():
                computed_pre_upload = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                if computed_pre_upload != expected:
                    label = planned_upload_keys[field_name].replace("_", " ").capitalize()
                    self._log_audit(
                        action_type="assisted_prefill_rejected",
                        entity_type="job",
                        entity_id=job_id,
                        result="blocked",
                        metadata={
                            "reason": f"{planned_upload_keys[field_name]}_bytes_mismatch_pre_upload"
                        },
                    )
                    return self._blocked(
                        job_id,
                        plan,
                        f"{label} artifact bytes changed immediately before upload.",
                        security_warnings=page_security_warnings,
                        destination_final_url=destination_final_url,
                    )
            verified_uploads[field_name] = str(artifact_path)

        # 9. Pre-Submit Review Manifest (J15-03 & A-R15-06): the plan, before any write.
        run_id = str(uuid.uuid4())
        manifest = PreSubmitReviewManifest(
            run_id=run_id,
            timestamp=utc_now().isoformat(),
            job_id=str(job_id),
            company_name=plan.company_name,
            job_title=plan.job_title,
            destination_url=plan.apply_url,
            destination_domain=plan.destination_domain,
            destination_final_url=destination_final_url,
            form_action=inspection_res.form_action,
            detected_ats=inspection_res.detected_ats,
            policy_decision=plan.policy.decision.value,
            policy_version=1,
            packet_id=str(packet.id),
            packet_hash=packet.packet_hash,
            resume_variant_id=str(packet.resume_variant_id) if packet.resume_variant_id else None,
            resume_artifact_id=str(packet.resume_artifact_id)
            if packet.resume_artifact_id
            else None,
            resume_artifact_sha256=resume_sha,
            cover_letter_artifact_id=(
                str(packet.cover_letter_artifact_id) if packet.cover_letter_artifact_id else None
            ),
            cover_letter_artifact_sha256=cover_letter_sha,
            discovered_fields=classified_fields,
            prefilled_fields=prefill_candidates,
            provenance_records=prov_dict,
            planned_file_uploads=planned_upload_keys,
            unfilled_fields=unfilled_field_names,
            ambiguous_fields=sorted(set(ambiguous_fields)),
            manual_fields=sorted(set(manual_fields)),
            barriers=barriers,
            security_warnings=page_security_warnings,
            form_fingerprint=form_fingerprint,
            semantic_snapshot=semantic_snapshot,
            can_proceed_to_review=True,
            blocking_reasons=[],
        )

        manifest_artifact = ArtifactModel(
            type="assisted_review_manifest",
            storage_uri=f"manifest://review/{run_id}.json",
            sha256=hashlib.sha256(manifest.model_dump_json().encode("utf-8")).hexdigest(),
            metadata_json=json.loads(manifest.model_dump_json()),
        )
        self.session.add(manifest_artifact)
        self.session.flush()

        # 10. F145-08: Revalidate the canonical semantic snapshot immediately before write.
        # Re-inspect and re-classify: a changed label, option, action, destination or a
        # new security warning invalidates the plan even when name/type are unchanged.
        pre_write_inspection = self._inspect(plan.apply_url)
        if (
            pre_write_inspection.inspection_error
            or not pre_write_inspection.form_found
            or len(pre_write_inspection.fields) == 0
        ):
            self._log_audit(
                action_type="assisted_prefill_halted_fingerprint_mismatch",
                entity_type="job",
                entity_id=job_id,
                result="blocked",
                metadata={
                    "inspected_snapshot": semantic_snapshot,
                    "pre_write_error": pre_write_inspection.inspection_error or "no_form",
                    "url": plan.apply_url,
                },
            )
            return self._blocked(
                job_id,
                plan,
                "FORM_REVALIDATION_FAILED: the pre-write re-inspection did not complete; "
                "an incomplete inspection is not a clean safety result.",
                security_warnings=page_security_warnings,
                barriers=barriers,
                form_fingerprint=form_fingerprint,
                semantic_snapshot=semantic_snapshot,
                destination_final_url=destination_final_url,
            )
        pre_write_fields = [
            item[0] for item in self._classify_all(pre_write_inspection.fields, packet)
        ]
        pre_write_destination = pre_write_inspection.destination_url()
        pre_write_warnings = list(pre_write_inspection.page_security_warnings or [])
        pre_write_domain = self._extract_domain(pre_write_destination)
        if pre_write_domain and pre_write_domain != plan.destination_domain:
            pre_write_warnings.append(f"security_warning:destination_redirected:{pre_write_domain}")
        pre_write_snapshot = compute_form_snapshot(
            pre_write_fields,
            pre_write_destination,
            form_action=pre_write_inspection.form_action,
            security_warnings=pre_write_warnings,
            page_text_injection_detected=pre_write_inspection.page_text_injection_detected,
        )
        if pre_write_snapshot != semantic_snapshot:
            changes = describe_snapshot_changes(
                classified_fields,
                pre_write_fields,
                before_destination=destination_final_url,
                after_destination=pre_write_destination,
                before_action=inspection_res.form_action,
                after_action=pre_write_inspection.form_action,
                before_warnings=page_security_warnings,
                after_warnings=pre_write_warnings,
            )
            self._log_audit(
                action_type="assisted_prefill_halted_fingerprint_mismatch",
                entity_type="job",
                entity_id=job_id,
                result="blocked",
                metadata={
                    "inspected_snapshot": semantic_snapshot,
                    "pre_write_snapshot": pre_write_snapshot,
                    "changes": changes,
                    "url": plan.apply_url,
                },
            )
            return self._blocked(
                job_id,
                plan,
                "FORM_SNAPSHOT_MISMATCH (FORM_FINGERPRINT_MISMATCH): the form changed between "
                f"inspection and prefill ({', '.join(changes) or 'semantic change'}). "
                "Halting to prevent writing against a stale form.",
                security_warnings=sorted(set(page_security_warnings) | set(pre_write_warnings)),
                barriers=barriers,
                form_fingerprint=form_fingerprint,
                semantic_snapshot=semantic_snapshot,
                destination_final_url=destination_final_url,
            )

        # 11. Execute Prefill on Browser Form through the exact inspected locators.
        prefill_res = self.browser_runner.prefill_form(
            url=plan.apply_url,
            field_values=prefill_candidates,
            file_uploads=verified_uploads,
            targets=targets,
        )

        # 12. F145-09: post-fill evidence distinguishes intended from actually filled values.
        attached_digests = dict(prefill_res.attached_file_digests)
        upload_mismatches = sorted(
            name
            for name, expected in expected_upload_digests.items()
            if attached_digests.get(name) != expected
        )
        readback_verified = (
            bool(prefill_res.success)
            and set(prefill_res.prefilled_fields) == set(prefill_candidates)
            and not upload_mismatches
        )
        notes: list[str] = []
        if upload_mismatches:
            notes.append(f"upload_digest_mismatch:{','.join(upload_mismatches)}")
        if prefill_res.failed_fields:
            notes.append(f"failed_fields:{','.join(sorted(prefill_res.failed_fields))}")
        if prefill_res.unmatched_fields:
            notes.append(f"unmatched_fields:{','.join(sorted(prefill_res.unmatched_fields))}")
        postfill = PostFillEvidence(
            run_id=run_id,
            timestamp=utc_now().isoformat(),
            destination_url=plan.apply_url,
            destination_final_url=prefill_res.final_url or destination_final_url,
            semantic_snapshot=semantic_snapshot,
            intended_fields={
                name: hashlib.sha256(value.encode("utf-8")).hexdigest()
                for name, value in prefill_candidates.items()
            },
            filled_fields={
                name: hashlib.sha256(
                    prefill_res.readback.get(name, value).encode("utf-8")
                ).hexdigest()
                for name, value in prefill_res.prefilled_fields.items()
            },
            failed_fields=dict(prefill_res.failed_fields),
            unmatched_fields=list(prefill_res.unmatched_fields),
            intended_files=dict(expected_upload_digests),
            attached_files=attached_digests,
            attached_readback={
                name: prefill_res.readback[name]
                for name in prefill_res.attached_files
                if name in prefill_res.readback
            },
            readback_verified=readback_verified,
            submit_performed=False,
            notes=notes,
        )
        postfill_artifact = ArtifactModel(
            type="assisted_postfill_evidence",
            storage_uri=f"manifest://postfill/{run_id}.json",
            sha256=hashlib.sha256(postfill.model_dump_json().encode("utf-8")).hexdigest(),
            metadata_json=json.loads(postfill.model_dump_json()),
        )
        self.session.add(postfill_artifact)
        self.session.flush()

        # 13. Open Interactive Review Session (prefill-to-review only; never submits)
        session_res = self.browser_runner.open_interactive_session(
            url=plan.apply_url,
            prefilled_fields=prefill_res.prefilled_fields,
            file_uploads=verified_uploads,
        )

        app = existing_app or ApplicationModel(
            job_id=job_id,
            destination_domain=plan.destination_domain,
            policy_decision=plan.policy.decision.value,
            application_mode="assisted",
            status="ASSISTED_PREFILLED",
            packet_id=packet.id,
        )
        if not existing_app:
            self.session.add(app)
            self.session.flush()
        app.status = "ASSISTED_PREFILLED" if readback_verified else "ASSISTED_PREFILL_PARTIAL"

        # 14. F145-10: nothing in this path can promote the application to a submitted
        # state. A caller flag, a runner-reported "submitted" or a URL are recorded as
        # ignored claims, never as evidence.
        if auto_confirm:
            page_security_warnings.append("security_warning:auto_confirm_ignored_prefill_only")
            self._log_audit(
                action_type="assisted_submit_claim_ignored",
                entity_type="application",
                entity_id=app.id,
                result="ignored",
                metadata={"claim": "auto_confirm", "receipt_text_present": bool(receipt_text)},
            )
        if session_res.submitted or session_res.submit_performed or session_res.confirmation_url:
            page_security_warnings.append(
                "security_warning:runner_submission_claim_ignored_prefill_only"
            )
            self._log_audit(
                action_type="assisted_submit_claim_ignored",
                entity_type="application",
                entity_id=app.id,
                result="ignored",
                metadata={
                    "claim": "runner_session_result",
                    "submitted": bool(session_res.submitted),
                    "submit_performed": bool(session_res.submit_performed),
                    "confirmation_url_present": bool(session_res.confirmation_url),
                },
            )

        self._log_audit(
            action_type="assisted_prefill_completed",
            entity_type="application",
            entity_id=app.id,
            input_hash=packet.packet_hash,
            result="review_required",
            metadata={
                "run_id": run_id,
                "readback_verified": readback_verified,
                "filled_count": len(prefill_res.prefilled_fields),
                "failed_count": len(prefill_res.failed_fields),
                "unmatched_count": len(prefill_res.unmatched_fields),
                "attached_count": len(attached_digests),
            },
        )
        self.session.commit()
        outcome = (
            "Form inspected and prefilled with safe fields; every write and upload was read back."
            if readback_verified
            else "Form inspected and partially prefilled; see post-fill evidence for failed or "
            "unmatched fields."
        )
        return AssistedApplicationResult(
            job_id=str(job_id),
            application_id=str(app.id),
            status="REVIEW_REQUIRED",
            policy_decision=plan.policy.decision.value,
            destination_domain=plan.destination_domain,
            destination_final_url=postfill.destination_final_url,
            prefilled_count=len(prefill_res.prefilled_fields),
            review_manifest=manifest,
            postfill_evidence=postfill,
            form_fingerprint=form_fingerprint,
            semantic_snapshot=semantic_snapshot,
            barriers=barriers,
            security_warnings=page_security_warnings,
            message=(
                f"{outcome} Persistent visible browser session open for candidate review; "
                "no submission was performed."
            ),
        )

    def _record_submission_event(
        self,
        application_id: uuid.UUID,
        source: str,
        receipt: str,
        domain: str,
        packet_id: str | None,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        event = ApplicationEventModel(
            application_id=application_id,
            event_type="APPLICATION_SUBMITTED",
            source=source,
            actor="candidate",
            payload_json={
                "receipt": receipt,
                "domain": domain,
                "packet_id": packet_id,
                "external_confirmation": evidence or {},
            },
        )
        self.session.add(event)

        packet_hash: str | None = None
        if packet_id:
            packet = self.session.scalar(
                select(ApplicationPacketModel).where(
                    ApplicationPacketModel.id == uuid.UUID(packet_id)
                )
            )
            if packet:
                packet_hash = packet.packet_hash

        self._log_audit(
            action_type="assisted_application_submitted",
            entity_type="application",
            entity_id=application_id,
            input_hash=packet_hash,
            result="success",
            metadata={"domain": domain, "source": source, "receipt": receipt},
        )

    def _record_submission_unconfirmed_event(
        self,
        application_id: uuid.UUID,
        source: str,
        domain: str,
        packet_id: str | None,
        reason: str,
    ) -> None:
        event = ApplicationEventModel(
            application_id=application_id,
            event_type="APPLICATION_SUBMISSION_UNCONFIRMED",
            source=source,
            actor="candidate",
            payload_json={
                "domain": domain,
                "packet_id": packet_id,
                "reason": reason,
            },
        )
        self.session.add(event)

        self._log_audit(
            action_type="assisted_application_unconfirmed",
            entity_type="application",
            entity_id=application_id,
            result="unconfirmed",
            metadata={"domain": domain, "source": source, "reason": reason},
        )

    def _complete_review_task(self, job_id: uuid.UUID, app_id: uuid.UUID) -> None:
        """Completes application review tasks satisfied by submission while preserving unrelated tasks."""
        tasks = self.session.scalars(
            select(TaskModel).where(
                TaskModel.job_id == job_id,
                TaskModel.status == "pending",
                TaskModel.task_type.in_(
                    [
                        "NEEDS_REVIEW",
                        "APPLICATION_REVIEW",
                        "ASSISTED_REVIEW",
                        "MANUAL_BARRIER_REVIEW",
                    ]
                ),
            )
        ).all()
        for t in tasks:
            t.status = "completed"
            t.application_id = app_id

    def _log_audit(
        self,
        action_type: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
        result: str,
        input_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        audit = AuditLogModel(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor="assisted_engine",
            input_hash=input_hash,
            result=result,
            metadata_json=metadata or {},
        )
        self.session.add(audit)
