"""Adversarial and safety tests for V1.4 packet preparation.

Covers all required acceptance scenarios from docs/V1_4_REPAIR_GUIDE.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.adapters.base import ModelGateway
from jobs_automation.adapters.models import LiteLLMModelGateway, MockModelGateway
from jobs_automation.core import CandidateProfileConfig, ConfigLoader, ModelRoutingConfig
from jobs_automation.db.models import CompanyModel, JobModel
from jobs_automation.db.session import init_db
from jobs_automation.preparation.packet_builder import ApplicationPacketBuilder
from jobs_automation.preparation.tailoring import ScreeningQuestionAnsweringService
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
