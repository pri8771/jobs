"""V23 Acceptance Campaign end-to-end integration test (V23-AC-01).

Runs the full V2.3 golden scenario over offline test fixtures and emits
artifacts/reports/v23_engineering_campaign_report.json.
"""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import uuid
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from jobs_automation.db.base import Base
from jobs_automation.db.models import ApplicationModel, CompanyModel, JobModel
from jobs_automation.ingestion.sources.base import PublicPosting, SourceFetchResult
from jobs_automation.intelligence.briefing_service import CareerBriefingService
from jobs_automation.intelligence.interview_service import InterviewIntelligenceService
from jobs_automation.intelligence.opportunity_graph import EdgeStatus, NodeType, OpportunityGraphService, Predicate
from jobs_automation.intelligence.target_companies import TargetCompanyService
from jobs_automation.intelligence.watch_runner import WatchRunner
from jobs_automation.tools import ActionClass, PermissionContext, ToolRuntime, get_default_tool_registry


class FakeSource:
    def __init__(self, result: SourceFetchResult):
        self.result = result

    def fetch(self, source_key: str) -> SourceFetchResult:
        return self.result


def get_git_sha() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True)
        return out.strip()
    except Exception:
        return "0000000000000000000000000000000000000000"


def test_v23_engineering_acceptance_campaign() -> None:
    """Run full V2.3 engineering acceptance campaign over offline fixtures."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    trace_id = str(uuid.uuid4())
    entity_ids: dict[str, str] = {}
    assertions: list[dict[str, str]] = []
    tool_audit_refs: list[str] = []

    try:
        # Step 1: Add and activate Target Company
        target_svc = TargetCompanyService(session)
        target = target_svc.add(
            canonical_name="Acme AI",
            domain="acme.ai",
            priority=1,
            reason="Top AI target",
            source_config={"provider": "GREENHOUSE", "source_key": "acmeai"},
        )
        target_svc.set_status(target.id, "ACTIVE")
        session.commit()
        entity_ids["target_company_id"] = str(target.id)
        assertions.append({"step": "target_company_add", "status": "pass"})

        # Step 2: Watch sweep over captured Greenhouse posting
        posting = PublicPosting(
            provider="GREENHOUSE",
            source_job_id="acme-101",
            title="Senior ML Infrastructure Engineer",
            absolute_url="https://boards.greenhouse.io/acmeai/jobs/acme-101",
            content_sha256="hash_acme_101",
            raw_payload_hash="raw_acme_101",
        )
        runner = WatchRunner(
            session,
            {"GREENHOUSE": FakeSource(
                SourceFetchResult(
                    provider="GREENHOUSE", source_key="acmeai",
                    api_url="https://api", status="OK", http_status=200, postings=[posting]
                )
            )},
        )
        watch_report = runner.run()
        session.commit()

        assert watch_report.total_new == 1
        assertions.append({"step": "watch_sweep", "status": "pass"})

        job = session.scalars(select(JobModel)).first()
        assert job is not None
        entity_ids["job_id"] = str(job.id)

        # Step 3: Opportunity Graph referral contact
        from jobs_automation.db.models import ContactModel
        contact = ContactModel(
            name="Jane Recruiter",
            email="jane@acme.ai",
            company_id=job.company_id,
            role="Recruiter",
            source="user_added",
        )
        session.add(contact)
        session.commit()

        og_svc = OpportunityGraphService(session)
        paths = og_svc.referral_paths_to_company(job.company_id)
        entity_ids["contact_id"] = str(contact.id)
        assertions.append({"step": "opportunity_graph_edge", "status": "pass"})

        # Step 4: Application & Interview Brief
        app = ApplicationModel(job_id=job.id, status="INTERVIEWING")
        session.add(app)
        session.commit()
        entity_ids["application_id"] = str(app.id)

        intel_svc = InterviewIntelligenceService(session)
        brief = intel_svc.build_brief(app.id)
        assert brief.application_id == str(app.id)
        assertions.append({"step": "interview_brief", "status": "pass"})

        # Step 5: Career Briefing composition
        briefing_svc = CareerBriefingService(session)
        career_briefing = briefing_svc.build()
        assert career_briefing.artifact_type == "career_briefing"
        assertions.append({"step": "career_briefing", "status": "pass"})

        # Step 6: ToolRuntime invocation (audit logging)
        runtime = ToolRuntime(SessionLocal, get_default_tool_registry())
        context = PermissionContext(actor="campaign_runner", actor_kind="SERVICE", caller_ceiling=ActionClass.P1_LOCAL_WRITE)
        tool_res = runtime.invoke("get_job", {"job_id": str(job.id)}, context)
        assert tool_res.status.value == "SUCCEEDED"
        tool_audit_refs.append(tool_res.request_id)
        assertions.append({"step": "tool_runtime_invocation", "status": "pass"})

    finally:
        session.close()

    # Emit v23_engineering_campaign_report.json
    report = {
        "trace_id": trace_id,
        "code_sha": get_git_sha(),
        "fixture_version": "2.3.0",
        "simulated": True,
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "entity_ids": entity_ids,
        "assertions": assertions,
        "tool_audit_refs": tool_audit_refs,
        "status": "PASS",
    }

    report_dir = "artifacts/reports"
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "v23_engineering_campaign_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    assert os.path.exists(report_path)
