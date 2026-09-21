"""Assisted application execution engine with policy enforcement and human-in-the-loop review."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
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
    PreSubmitReviewManifest,
)
from jobs_automation.core.candidate_profile import CandidateProfileConfig
from jobs_automation.core.policy_registry import PolicyDecision
from jobs_automation.db.base import utc_now
from jobs_automation.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    ApplicationPacketModel,
    ArtifactModel,
    AuditLogModel,
    JobModel,
    TaskModel,
)
from jobs_automation.policy.evaluator import PolicyEvaluationResult, PolicyEvaluator

logger = logging.getLogger(__name__)


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
    """Computes a stable hash of the form structure to detect in-session changes."""
    fingerprint_raw = "|".join(
        f"{f.name}:{f.field_type}:{f.selector}:{f.required}"
        for f in sorted(fields, key=lambda x: x.name)
    )
    return hashlib.sha256(f"{url}|{fingerprint_raw}".encode()).hexdigest()[:16]


def classify_field(
    field: FormField,
    candidate: CandidateProfileConfig,
    packet: ApplicationPacketModel | None = None,
) -> tuple[FieldClassification, str | None, str | None, str | None]:
    """Classifies a discovered form field according to the V1.5 safety taxonomy.

    Returns:
        (classification, canonical_key, mapped_value, source_reference)
    """
    name_lower = (field.name or "").lower().strip()
    label_lower = (field.label or "").lower().strip()
    placeholder_lower = (field.placeholder or "").lower().strip()
    selector_lower = field.selector.lower()
    combined = f"{name_lower} {label_lower} {placeholder_lower} {selector_lower}"

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

    # 4. File uploads (Resume / Cover letter)
    file_keywords = ["resume", "cv", "curriculum vitae", "cover letter", "cover_letter"]
    if field.field_type == "file" or any(kw in combined for kw in file_keywords):
        if "cover" in combined:
            return (
                FieldClassification.FILE_ARTIFACT,
                "cover_letter",
                None,
                "packet.cover_letter_artifact",
            )
        return FieldClassification.FILE_ARTIFACT, "resume", None, "packet.resume_artifact"

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
    if any(k in combined for k in ["first_name", "firstname", "first name", "given name", "given_name"]):
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

    if field.field_type == "tel" or any(k in combined for k in ["phone", "mobile", "telephone", "phone number"]):
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

    if any(k in combined for k in ["portfolio", "website", "personal site", "personal_site", "blog"]):
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
    return barriers


def is_valid_external_confirmation(
    session_res: BrowserSessionResult,
    auto_confirm: bool,
    receipt_text: str | None,
    allow_simulation: bool = False,
) -> tuple[bool, str, dict[str, Any]]:
    """Strictly evaluates whether external confirmation evidence exists.

    Generic local receipt strings and simulated receipts cannot satisfy live confirmation.
    """
    if session_res.is_mock and not allow_simulation:
        return (
            False,
            "Simulated mock runner evidence cannot satisfy live submission confirmation.",
            {},
        )

    # Reject generic local placeholder strings
    generic_disallowed = {
        "application submitted via assisted browser",
        "confirmed manual submission via native portal",
        "manual native submission confirmed",
        "application prefilled",
        "prefilled successfully",
    }
    cleaned_receipt = (receipt_text or "").strip().lower()
    if cleaned_receipt in generic_disallowed:
        receipt_text = None

    # 1. Structured external confirmation evidence
    if session_res.external_confirmation_evidence:
        ev = session_res.external_confirmation_evidence
        if not allow_simulation and ev.get("simulated"):
            return False, "Simulated confirmation rejected in live mode.", {}
        receipt = receipt_text or str(ev.get("receipt_id") or "external_confirmed")
        return True, receipt, ev

    # 2. Confirmed external URL
    if session_res.confirmation_url:
        conf_url = session_res.confirmation_url
        if not allow_simulation and ("mock" in conf_url.lower() or "test" in conf_url.lower()):
            return False, "Mock confirmation URL rejected in live mode.", {}
        ev = {"type": "confirmation_page", "url": conf_url}
        receipt = receipt_text or f"Confirmed via external page: {conf_url}"
        return True, receipt, ev

    # 3. External verifiable receipt text
    if receipt_text:
        rec_lower = receipt_text.lower()
        if not allow_simulation and "mock" in rec_lower:
            return False, "Mock receipt text rejected in live mode.", {}
        if any(token in rec_lower for token in ["confirmation", "received", "application id", "ref", "receipt"]):
            ev = {"type": "external_receipt", "text": receipt_text}
            return True, receipt_text, ev

    return (
        False,
        "No verifiable external receipt, confirmation URL, or confirmation email captured.",
        {},
    )


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
    prefilled_count: int = 0
    receipt_text: str | None = None
    confirmation_url: str | None = None
    external_confirmation_evidence: dict[str, Any] | None = None
    form_fingerprint: str | None = None
    barriers: list[str] = Field(default_factory=list)
    review_manifest: PreSubmitReviewManifest | None = None
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

    def build_plan(
        self,
        job_id: uuid.UUID,
        packet_id: uuid.UUID | None = None,
    ) -> AssistedApplicationPlan:
        """Inspects job and application packet to construct a prefill and policy execution plan."""
        job = self.session.scalar(select(JobModel).where(JobModel.id == job_id))
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")

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
                # Must check for valid external confirmation evidence
                mock_res = BrowserSessionResult(
                    url=plan.apply_url,
                    submitted=True,
                    receipt_text=receipt_text,
                    is_mock=False,
                )
                valid_conf, conf_receipt, conf_ev = is_valid_external_confirmation(
                    session_res=mock_res,
                    auto_confirm=auto_confirm,
                    receipt_text=receipt_text,
                    allow_simulation=sim_allowed,
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
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                message="Explicit accepted packet_id is required for assisted execution. Latest-packet fallback is disabled.",
            )

        packet = self.session.scalar(
            select(ApplicationPacketModel).where(ApplicationPacketModel.id == packet_id)
        )
        if not packet:
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                message=f"ApplicationPacketModel {packet_id} not found in database.",
            )

        if packet.job_id != job_id:
            self._log_audit(
                action_type="assisted_prefill_rejected",
                entity_type="application_packet",
                entity_id=packet.id,
                result="blocked",
                metadata={"reason": "packet_job_id_mismatch", "target_job_id": str(job_id)},
            )
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                message=f"Packet {packet_id} belongs to job {packet.job_id}, not target job {job_id}.",
            )

        if live_ready_required and not packet.is_live_ready:
            self._log_audit(
                action_type="assisted_prefill_rejected",
                entity_type="application_packet",
                entity_id=packet.id,
                result="blocked",
                metadata={"reason": "packet_not_live_ready"},
            )
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                message="Packet is not marked live-ready. Review and accept packet before live execution.",
            )

        if packet.unresolved_questions_json:
            self._log_audit(
                action_type="assisted_prefill_rejected",
                entity_type="application_packet",
                entity_id=packet.id,
                result="blocked",
                metadata={"unresolved_questions": packet.unresolved_questions_json},
            )
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                message=f"Packet has unresolved consequential questions: {packet.unresolved_questions_json}",
            )

        if not packet.resume_artifact_id:
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                message="Packet has no resume artifact attached.",
            )

        # Verify resume artifact on disk & SHA-256 integrity (J15-04)
        resume_art = self.session.scalar(
            select(ArtifactModel).where(ArtifactModel.id == packet.resume_artifact_id)
        )
        if not resume_art:
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                message=f"Resume artifact {packet.resume_artifact_id} not found in database.",
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
                self.session.commit()
                return AssistedApplicationResult(
                    job_id=str(job_id),
                    status="BLOCKED",
                    policy_decision=plan.policy.decision.value,
                    destination_domain=plan.destination_domain,
                    message=f"Resume artifact integrity verification failed: {resume_sha}",
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
                    self.session.commit()
                    return AssistedApplicationResult(
                        job_id=str(job_id),
                        status="BLOCKED",
                        policy_decision=plan.policy.decision.value,
                        destination_domain=plan.destination_domain,
                        message=f"Cover letter artifact integrity verification failed: {cl_sha}",
                    )
                cover_letter_sha = cl_sha if valid_cl else cl_art.sha256

        # 5. Form Inspection Gate (Inspect Before Write - J15-01)
        inspection_res = self.browser_runner.inspect_form(plan.apply_url)
        if not inspection_res.form_found or len(inspection_res.fields) == 0:
            self._log_audit(
                action_type="assisted_inspection_failed",
                entity_type="job",
                entity_id=job_id,
                result="blocked",
                metadata={"url": plan.apply_url},
            )
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="BLOCKED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                message=f"Form inspection failed: no form found at destination URL {plan.apply_url}.",
            )

        # 6. Field Classification and Manual Barrier Classifier (J15-01 & J15-02)
        classified_fields: list[FormField] = []
        prefill_candidates: dict[str, str] = {}
        prov_dict: dict[str, FieldFillProvenance] = {}
        unfilled_field_names: list[str] = []

        for field in inspection_res.fields:
            classification, canonical_key, mapped_val, source_ref = classify_field(
                field=field,
                candidate=self.candidate,
                packet=packet,
            )
            updated_field = FormField(
                name=field.name,
                field_type=field.field_type,
                label=field.label,
                placeholder=field.placeholder,
                selector=field.selector,
                required=field.required,
                options=field.options,
                current_value=field.current_value,
                classification=classification,
            )
            classified_fields.append(updated_field)

            # Only SAFE_CANONICAL, PACKET_ANSWER, and FILE_ARTIFACT may be prefilled
            if classification in (
                FieldClassification.SAFE_CANONICAL,
                FieldClassification.PACKET_ANSWER,
            ):
                if mapped_val is not None:
                    prefill_candidates[field.name] = mapped_val
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
                prov_dict[field.name] = FieldFillProvenance(
                    field_name=field.name,
                    target_selector=field.selector,
                    classification=classification,
                    canonical_key=canonical_key,
                    source_reference=source_ref or "artifact",
                    value_hash=resume_sha,
                    confidence=1.0,
                    mapping_method="file_artifact_match",
                )
            else:
                unfilled_field_names.append(field.name)

        form_fingerprint = compute_form_fingerprint(classified_fields, plan.apply_url)
        barriers = compute_barriers(
            classified_fields=classified_fields,
            unresolved_questions=packet.unresolved_questions_json,
            policy_decision=plan.policy.decision,
        )

        # 7. Stop Conditions Before Prefill (J15-08)
        blocking_barriers = [
            b
            for b in barriers
            if b.startswith("auth_barrier:")
            or b.startswith("unknown_required_field:")
            or b.startswith("unresolved_questions_")
        ]
        if blocking_barriers:
            review_task = TaskModel(
                job_id=job_id,
                task_type="MANUAL_BARRIER_REVIEW",
                status="pending",
                payload_json={
                    "barriers": blocking_barriers,
                    "all_barriers": barriers,
                    "url": plan.apply_url,
                },
            )
            self.session.add(review_task)
            self._log_audit(
                action_type="assisted_prefill_halted_barriers",
                entity_type="job",
                entity_id=job_id,
                result="review_required",
                metadata={"blocking_barriers": blocking_barriers},
            )
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                status="REVIEW_REQUIRED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                barriers=barriers,
                form_fingerprint=form_fingerprint,
                message=f"Prefill halted due to manual barriers requiring candidate action: {blocking_barriers}",
            )

        # 8. Re-verify artifact bytes immediately before upload (J15-04)
        verified_uploads: dict[str, str] = {}
        if "resume" in plan.file_uploads:
            res_path = resolve_artifact_path(plan.file_uploads["resume"])
            if res_path.exists():
                computed_pre_upload = hashlib.sha256(res_path.read_bytes()).hexdigest()
                if computed_pre_upload != resume_sha:
                    self.session.commit()
                    return AssistedApplicationResult(
                        job_id=str(job_id),
                        status="BLOCKED",
                        policy_decision=plan.policy.decision.value,
                        destination_domain=plan.destination_domain,
                        message="Resume artifact bytes changed immediately before upload.",
                    )
            verified_uploads["resume"] = str(res_path)

        # 9. Pre-Submit Review Manifest (J15-03)
        run_id = str(uuid.uuid4())
        manifest = PreSubmitReviewManifest(
            run_id=run_id,
            timestamp=utc_now().isoformat(),
            job_id=str(job_id),
            company_name=plan.company_name,
            job_title=plan.job_title,
            destination_url=plan.apply_url,
            destination_domain=plan.destination_domain,
            detected_ats=inspection_res.detected_ats,
            policy_decision=plan.policy.decision.value,
            policy_version=1,
            packet_id=str(packet.id),
            packet_hash=packet.packet_hash,
            resume_variant_id=str(packet.resume_variant_id) if packet.resume_variant_id else None,
            resume_artifact_id=str(packet.resume_artifact_id) if packet.resume_artifact_id else None,
            resume_artifact_sha256=resume_sha,
            cover_letter_artifact_id=(
                str(packet.cover_letter_artifact_id) if packet.cover_letter_artifact_id else None
            ),
            cover_letter_artifact_sha256=cover_letter_sha,
            discovered_fields=classified_fields,
            prefilled_fields=prefill_candidates,
            provenance_records=prov_dict,
            unfilled_fields=unfilled_field_names,
            barriers=barriers,
            form_fingerprint=form_fingerprint,
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

        # 10. Execute Prefill on Browser Form
        prefill_res = self.browser_runner.prefill_form(
            url=plan.apply_url,
            field_values=prefill_candidates,
            file_uploads=verified_uploads,
        )

        # 11. Open Interactive Review Session (Halts before submission)
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

        # 12. Human Review Checkpoint & External Evidence Gate (J15-09 & J15-10)
        is_user_submit = auto_confirm or session_res.submitted
        if is_user_submit:
            valid_conf, conf_receipt, conf_evidence = is_valid_external_confirmation(
                session_res=session_res,
                auto_confirm=auto_confirm,
                receipt_text=receipt_text,
                allow_simulation=sim_allowed,
            )
            if valid_conf:
                now = utc_now()
                app.status = "SUBMITTED"
                app.applied_at = now
                app.last_activity_at = now

                self._record_submission_event(
                    application_id=app.id,
                    source="assisted_browser",
                    receipt=conf_receipt,
                    domain=plan.destination_domain,
                    packet_id=str(packet.id),
                    evidence=conf_evidence,
                )
                self._complete_review_task(job_id=job_id, app_id=app.id)
                self.session.commit()

                return AssistedApplicationResult(
                    job_id=str(job_id),
                    application_id=str(app.id),
                    status="SUBMITTED",
                    policy_decision=plan.policy.decision.value,
                    destination_domain=plan.destination_domain,
                    prefilled_count=len(prefill_res.prefilled_fields),
                    receipt_text=conf_receipt,
                    confirmation_url=session_res.confirmation_url,
                    external_confirmation_evidence=conf_evidence,
                    review_manifest=manifest,
                    form_fingerprint=form_fingerprint,
                    barriers=barriers,
                    message=f"Application for {plan.job_title} at {plan.company_name} confirmed submitted with external evidence.",
                )
            else:
                app.status = "SUBMISSION_UNCONFIRMED"
                self._record_submission_unconfirmed_event(
                    application_id=app.id,
                    source="assisted_browser",
                    domain=plan.destination_domain,
                    packet_id=str(packet.id),
                    reason=conf_receipt,
                )
                self.session.commit()

                return AssistedApplicationResult(
                    job_id=str(job_id),
                    application_id=str(app.id),
                    status="SUBMISSION_UNCONFIRMED",
                    policy_decision=plan.policy.decision.value,
                    destination_domain=plan.destination_domain,
                    prefilled_count=len(prefill_res.prefilled_fields),
                    review_manifest=manifest,
                    form_fingerprint=form_fingerprint,
                    barriers=barriers,
                    message=f"Interactive session ended or submit requested, but external confirmation evidence was missing: {conf_receipt}",
                )
        else:
            self.session.commit()
            return AssistedApplicationResult(
                job_id=str(job_id),
                application_id=str(app.id),
                status="REVIEW_REQUIRED",
                policy_decision=plan.policy.decision.value,
                destination_domain=plan.destination_domain,
                prefilled_count=len(prefill_res.prefilled_fields),
                review_manifest=manifest,
                form_fingerprint=form_fingerprint,
                barriers=barriers,
                message="Form inspected and prefilled with safe fields. Persistent visible browser session open for candidate review.",
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
