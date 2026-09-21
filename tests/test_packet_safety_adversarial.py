"""Adversarial and safety tests for V1.4 packet preparation.

Covers all required acceptance scenarios from docs/V1_4_REPAIR_GUIDE.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.base import ModelGateway
from jobs_automation.adapters.models import LiteLLMModelGateway, MockModelGateway
from jobs_automation.automation.auto_engine import ControlledAutoApplicationEngine
from jobs_automation.core import (
    CandidateProfileConfig,
    ConfigLoader,
    ModelRoutingConfig,
    PolicyRegistryConfig,
)
from jobs_automation.core.candidate_profile import ResumeVersion
from jobs_automation.core.policy_registry import (
    DefaultPolicyConfig,
    PolicyDecision,
    PolicyEntryConfig,
)
from jobs_automation.db.models import (
    CompanyModel,
    JobModel,
    JobSourceModel,
)
from jobs_automation.db.session import init_db
from jobs_automation.policy.evaluator import PolicyEvaluator
from jobs_automation.preparation.packet_builder import ApplicationPacketBuilder
from jobs_automation.preparation.tailoring import (
    ResumeVariantSelector,
    ScreeningQuestionAnsweringService,
)
from jobs_automation.storage.artifact_store import ArtifactStore


class HallucinatingModelGateway(ModelGateway):
    """Adversarial model gateway that falsely claims resolved=true for unverified facts."""

    def complete(
        self,
        task: str,
        prompt: str,
        system_prompt: str | None = None,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "resolved": True,
            "answer": "Yes, candidate has Top Secret clearance and 15 years experience.",
            "evidence_found": "Hallucinated clearance",
            "origin": "adversarial_mock",
        }


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    return session


@pytest.fixture
def profile(tmp_path: Path) -> CandidateProfileConfig:
    loader = ConfigLoader("config")
    p, _ = loader.load_candidate_profile("config/candidate_profile.example.yaml")
    # Clear sensitive/unconfirmed facts
    p.work_authorization.requires_sponsorship_now = None
    p.work_authorization.requires_sponsorship_future = None
    p.work_authorization.authorized_to_work_in_us = None
    p.target.relocation = None
    p.application_answers.willing_to_relocate = None
    p.skills.certifications = []
    return p


def test_unsupported_model_answer_is_rejected(profile: CandidateProfileConfig) -> None:
    """Verify J14-08: Hallucinated model claim about security clearance is rejected."""
    gateway = HallucinatingModelGateway()
    service = ScreeningQuestionAnsweringService(gateway)

    questions = ["Do you hold an active security clearance?"]
    answers, provenance, unresolved = service.resolve_questions(questions, profile)

    assert len(answers) == 0
    assert len(unresolved) == 1
    assert "Model assertion rejected: security clearance not present" in unresolved[0]


def test_missing_work_auth_and_sponsorship_fails_closed(profile: CandidateProfileConfig) -> None:
    """Verify J14-08: Null work authorization and sponsorship route strictly to unresolved."""
    gateway = MockModelGateway()
    service = ScreeningQuestionAnsweringService(gateway)

    questions = [
        "Are you legally authorized to work in the United States?",
        "Will you now or in the future require visa sponsorship?",
    ]
    answers, provenance, unresolved = service.resolve_questions(questions, profile)

    assert len(answers) == 0
    assert len(unresolved) == 2
    assert any("Work authorization" in u for u in unresolved)
    assert any("Visa sponsorship" in u for u in unresolved)


def test_deterministic_work_auth_provenance(profile: CandidateProfileConfig) -> None:
    """Verify J14-08: Confirmed authorization records exact canonical field provenance."""
    profile.work_authorization.authorized_to_work_in_us = True
    profile.work_authorization.requires_sponsorship_now = False
    profile.work_authorization.requires_sponsorship_future = False

    gateway = MockModelGateway()
    service = ScreeningQuestionAnsweringService(gateway)

    questions = [
        "Are you legally authorized to work in the United States?",
        "Will you now or in the future require visa sponsorship?",
    ]
    answers, provenance, unresolved = service.resolve_questions(questions, profile)

    assert len(unresolved) == 0
    assert answers["Are you legally authorized to work in the United States?"] == "Yes"
    assert provenance["Are you legally authorized to work in the United States?"]["sources"] == [
        "work_authorization.authorized_to_work_in_us"
    ]
    assert answers["Will you now or in the future require visa sponsorship?"] == "No"
    assert "work_authorization.requires_sponsorship_now" in provenance[
        "Will you now or in the future require visa sponsorship?"
    ]["sources"]


def test_selected_family_cannot_silently_load_unmapped_source(
    db_session: Session, profile: CandidateProfileConfig, tmp_path: Path
) -> None:
    """Verify J14-01, J14-02: Selected variant A cannot load unmapped variant B source."""
    # Create source only for sap variant
    sap_resume = tmp_path / "resume_sap_btp.md"
    sap_resume.write_text("# SAP BTP Resume\n", encoding="utf-8")

    profile.resume.base_resume_paths = [str(sap_resume)]
    profile.resume.resume_sources = {"resume_sap_btp": str(sap_resume)}

    co = CompanyModel(normalized_name="MobileCo")
    db_session.add(co)
    db_session.flush()

    # Job will select mobile_ios variant
    job_ios = JobModel(
        company_id=co.id,
        normalized_title="Senior iOS Mobile Lead",
        status="shortlisted",
    )
    db_session.add(job_ios)
    db_session.commit()

    store = ArtifactStore(base_dir=tmp_path / "artifacts")
    gateway = MockModelGateway()
    builder = ApplicationPacketBuilder(db_session, profile, gateway, artifact_store=store)

    # Must fail closed with FileNotFoundError instead of silently using SAP resume
    with pytest.raises(FileNotFoundError, match="Selected resume variant 'resume_mobile_ios' cannot be resolved"):
        builder.build_packet(job_ios)


def test_litellm_gateway_fails_closed_when_fallback_disabled() -> None:
    """Verify J14-07: LiteLLMModelGateway fails closed on missing config when fallback_mock=False."""
    routing = ModelRoutingConfig(version=1)
    gateway = LiteLLMModelGateway(routing, fallback_mock=False)

    with pytest.raises(ValueError, match="No model routing configured for task 'unknown_task'"):
        gateway.complete(task="unknown_task", prompt="Test")


def test_two_packet_builds_preserve_historical_artifacts(
    db_session: Session, profile: CandidateProfileConfig, tmp_path: Path
) -> None:
    """Verify R14-01: Two packet builds for same job do not overwrite historical artifact bytes."""
    resume_file = tmp_path / "resume_ai_software_engineer.md"
    resume_file.write_text("# Candidate AI Engineer Resume\n", encoding="utf-8")
    profile.resume.base_resume_paths = [str(resume_file)]
    profile.resume.resume_sources = {"resume_ai_software_engineer": str(resume_file)}

    co = CompanyModel(normalized_name="Anthropic", domain="anthropic.com")
    db_session.add(co)
    db_session.flush()

    job = JobModel(
        company_id=co.id,
        normalized_title="AI Automation Engineer",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.commit()

    store = ArtifactStore(base_dir=tmp_path / "artifacts")
    gateway = MockModelGateway()
    builder = ApplicationPacketBuilder(db_session, profile, gateway, artifact_store=store)

    # Build 1
    packet_1, result_1 = builder.build_packet(job)

    # Build 2 (e.g. rebuild after profile change or revision)
    # Modify profile slightly so cover letter changes
    profile.identity.full_name = "Priyansh Chordia PE"
    packet_2, result_2 = builder.build_packet(job)

    # Packets and results must have distinct hashes and manifest URIs
    assert packet_1.id != packet_2.id
    assert result_1.manifest_artifact_uri != result_2.manifest_artifact_uri
    assert result_1.cover_letter_artifact_uri != result_2.cover_letter_artifact_uri

    # Historical bytes from Build 1 must still exist on disk and be fully verifiable
    assert store.verify(result_1.manifest_artifact_uri, hashlib.sha256(store.read(result_1.manifest_artifact_uri)).hexdigest()) is True
    assert store.verify(result_2.manifest_artifact_uri, hashlib.sha256(store.read(result_2.manifest_artifact_uri)).hexdigest()) is True
    assert store.verify(result_1.cover_letter_artifact_uri, result_1.cover_letter_artifact_sha256) is True
    assert store.verify(result_2.cover_letter_artifact_uri, result_2.cover_letter_artifact_sha256) is True

    # Bytes must be different and intact
    assert store.read(result_1.cover_letter_artifact_uri) != store.read(result_2.cover_letter_artifact_uri)


def test_resume_variant_family_attribution_all_variants(profile: CandidateProfileConfig) -> None:
    """Verify R14-02: Each variant maps to exact family, not generic primary headline."""
    # Canonical variant -> expected family mappings
    expected_families = {
        "resume_enterprise_automation": "Enterprise Automation & Solutions Architect",
        "resume_ai_software_engineer": "Senior Software Engineer / AI Automation Engineer",
        "resume_mobile_ios": "Senior iOS Engineer / Mobile Engineering Lead",
        "resume_technical_product": "Technical Product / Platform Product",
        "resume_sap_btp": "SAP BTP / Enterprise Automation",
    }

    for variant, expected_family in expected_families.items():
        family = ResumeVariantSelector.get_resume_family(variant, profile)
        assert family == expected_family
        # Variants other than enterprise automation must NOT match the primary headline
        if variant != "resume_enterprise_automation":
            assert family != profile.target.primary_headline

    # Verify custom family configured directly on profile version takes precedence
    profile.resume.recommended_versions.append(
        ResumeVersion(
            id="resume_mobile_ios",
            priority=1,
            family="Executive Mobile Systems Architect",
            source_path="/path/to/ios.md",
        )
    )
    custom_family = ResumeVariantSelector.get_resume_family("resume_mobile_ios", profile)
    assert custom_family == "Executive Mobile Systems Architect"


def test_mock_generation_origin_cannot_be_live_ready(
    db_session: Session, profile: CandidateProfileConfig, tmp_path: Path
) -> None:
    """Verify R14-03: Packets generated with MockModelGateway are never marked live-ready."""
    resume_file = tmp_path / "resume_ai_software_engineer.md"
    resume_file.write_text("# Candidate AI Engineer Resume\n", encoding="utf-8")
    profile.resume.base_resume_paths = [str(resume_file)]
    profile.resume.resume_sources = {"resume_ai_software_engineer": str(resume_file)}

    co = CompanyModel(normalized_name="TestOrg", domain="testorg.com")
    db_session.add(co)
    db_session.flush()

    job = JobModel(
        company_id=co.id,
        normalized_title="AI Automation Engineer",
        status="shortlisted",
    )
    db_session.add(job)
    db_session.commit()

    store = ArtifactStore(base_dir=tmp_path / "artifacts")
    gateway = MockModelGateway()
    builder = ApplicationPacketBuilder(db_session, profile, gateway, artifact_store=store)

    packet, result = builder.build_packet(job)

    # Must be marked non-live-ready
    assert packet.is_live_ready is False
    assert result.is_live_ready is False
    assert result.generation_origin == "mock"
    assert packet.generation_metadata_json["generation_origin"] == "mock"

    # Manifest must declare is_live_ready=False and generation_origin=mock
    manifest = json.loads(store.read(result.manifest_artifact_uri).decode("utf-8"))
    assert manifest["is_live_ready"] is False
    assert manifest["generation_origin"] == "mock"

    source = JobSourceModel(
        job_id=job.id,
        provider="greenhouse",
        canonical_apply_url="https://boards.greenhouse.io/testorg/jobs/123",
    )
    db_session.add(source)
    db_session.flush()

    # ControlledAutoApplicationEngine must reject live submission of mock-generated packet
    policy_cfg = PolicyRegistryConfig(
        version=1,
        default=DefaultPolicyConfig(decision=PolicyDecision.BLOCKED, reason="deny_by_default"),
        entries=[
            PolicyEntryConfig(
                platform="greenhouse",
                domain_pattern="*.greenhouse.io",
                capability="submit_application",
                decision=PolicyDecision.AUTO_ALLOWED,
                reviewed_at="2026-09-20",
                review_due_at="2027-01-01",
            )
        ],
    )
    evaluator = PolicyEvaluator(policy_cfg)
    auto_engine = ControlledAutoApplicationEngine(
        session=db_session,
        policy_evaluator=evaluator,
        candidate_profile=profile,
    )

    live_res = auto_engine.execute_auto_apply(
        job_id=job.id,
        packet_id=packet.id,
        mock_mode=False,
    )
    assert live_res.status == "FAILED_NOT_LIVE_READY"
    assert "not eligible for live submission" in live_res.message


def test_quantitative_experience_claims_require_exact_canonical_evidence(
    profile: CandidateProfileConfig,
) -> None:
    """Verify R14-04: Quantitative duration/count claims fail closed without exact canonical evidence."""
    profile.skills.primary = ["Python", "Docker", "FastAPI"]

    # Adversarial gateway asserting quantitative claims
    gateway = HallucinatingModelGateway()
    service = ScreeningQuestionAnsweringService(gateway)

    questions = [
        "How many years of Python experience do you have?",
        "Years of experience with Docker?",
        "How many engineers have you managed?",
    ]
    answers, provenance, unresolved = service.resolve_questions(questions, profile)

    # All 3 quantitative questions must remain unresolved
    assert len(answers) == 0
    assert len(unresolved) == 3
    for u in unresolved:
        assert "Quantitative claim in question" in u or "requires exact canonical evidence" in u

    # When exact canonical evidence is provided in custom_answers, it resolves deterministically
    profile.application_answers.custom_answers[
        "How many years of Python experience do you have?"
    ] = "8 years"

    answers2, provenance2, unresolved2 = service.resolve_questions(
        ["How many years of Python experience do you have?"], profile
    )
    assert len(unresolved2) == 0
    assert answers2["How many years of Python experience do you have?"] == "8 years"
    assert provenance2["How many years of Python experience do you have?"]["method"] == "deterministic"
    assert "application_answers.custom_answers" in provenance2["How many years of Python experience do you have?"]["sources"][0]

