import pytest
from pydantic import ValidationError
from jobs_automation.intelligence.strategy import StrategyGuardrails
from jobs_automation.core.job_search import JobSearchConfig
import yaml

from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from jobs_automation.db.models import Base

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_strategy_guardrails_defaults():
    g = StrategyGuardrails()
    assert g.min_n_descriptive == 5
    assert g.min_n_comparison == 10
    assert g.min_n_per_arm == 5
    assert g.default_window_days == 90
    assert g.stale_after_days == 180

def test_strategy_guardrails_negative_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        StrategyGuardrails(min_n_descriptive=-1)

def test_job_search_config_with_strategy_guardrails():
    yaml_doc = """
version: 1
global:
  enabled: true
  freshness_days: 7
strategy_guardrails:
  min_n_descriptive: 20
    """
    data = yaml.safe_load(yaml_doc)
    config = JobSearchConfig(**data)
    assert config.strategy_guardrails.min_n_descriptive == 20
    assert config.strategy_guardrails.min_n_comparison == 10 # default

def test_job_search_config_without_strategy_guardrails():
    yaml_doc = """
version: 1
global:
  enabled: true
  freshness_days: 7
    """
    data = yaml.safe_load(yaml_doc)
    config = JobSearchConfig(**data)
    assert config.strategy_guardrails.min_n_descriptive == 5


def test_resume_strategy(db_session):
    from jobs_automation.intelligence.strategy import StrategyLearningService, StrategyGuardrails
    from jobs_automation.db.models import ResumeVariantModel, ApplicationPacketModel, ApplicationModel, JobModel, CompanyModel
    import datetime
    
    now = datetime.datetime.now(datetime.UTC)
    g = StrategyGuardrails(min_n_descriptive=2)
    svc = StrategyLearningService(db_session, g)
    
    comp = CompanyModel(normalized_name="ACME")
    db_session.add(comp)
    db_session.flush()
    job = JobModel(normalized_title="engineer", company_id=comp.id)
    db_session.add(job)
    db_session.flush()
    
    # 2 families, 3 variants total
    v1 = ResumeVariantModel(resume_family="backend", name="b1", version=1, content_hash="1")
    v2 = ResumeVariantModel(resume_family="backend", name="b2", version=2, content_hash="2")
    v3 = ResumeVariantModel(resume_family="frontend", name="f1", version=1, content_hash="3")
    db_session.add_all([v1, v2, v3])
    db_session.flush()
    
    p1 = ApplicationPacketModel(resume_variant_id=v1.id, job_id=job.id, candidate_profile_version=1, packet_hash="1")
    p2 = ApplicationPacketModel(resume_variant_id=v2.id, job_id=job.id, candidate_profile_version=1, packet_hash="2")
    p3 = ApplicationPacketModel(resume_variant_id=v3.id, job_id=job.id, candidate_profile_version=1, packet_hash="3")
    p_old = ApplicationPacketModel(resume_variant_id=v1.id, job_id=job.id, candidate_profile_version=1, packet_hash="4")
    db_session.add_all([p1, p2, p3, p_old])
    db_session.flush()
    
    # apps
    a1 = ApplicationModel(job_id=job.id, packet_id=p1.id, status="SUBMITTED", application_mode="auto", applied_at=now)
    a2 = ApplicationModel(job_id=job.id, packet_id=p2.id, status="SUBMITTED", application_mode="auto", applied_at=now)
    a3 = ApplicationModel(job_id=job.id, packet_id=p3.id, status="SUBMITTED", application_mode="auto", applied_at=now)
    
    # old app (outside 90 day window)
    old_date = now - datetime.timedelta(days=100)
    a_old = ApplicationModel(job_id=job.id, packet_id=p_old.id, status="SUBMITTED", application_mode="auto", applied_at=old_date)
    
    db_session.add_all([a1, a2, a3, a_old])
    db_session.commit()
    
    res = svc.resume_strategy(window_days=90)
    assert len(res) == 3
    
    # verify window excludes old
    for row in res:
        if row.resume_variant_id == str(v1.id):
            assert row.response.n == 1 # a1 only, not a_old
            
        assert not row.rollup
        assert row.response.n == row.response.denominator
def test_other_strategies_empty(db_session):
    from jobs_automation.intelligence.strategy import StrategyLearningService, StrategyGuardrails
    g = StrategyGuardrails()
    svc = StrategyLearningService(db_session, g)
    assert svc.source_strategy() == []
    assert svc.role_strategy() == []
    assert svc.company_strategy() == []

def test_get_best_resume_variant(db_session):
    from jobs_automation.intelligence.strategy import StrategyLearningService, StrategyGuardrails
    from jobs_automation.db.models import ResumeVariantModel, ApplicationPacketModel, ApplicationModel, JobModel, CompanyModel, ApplicationEventModel
    import datetime
    
    now = datetime.datetime.now(datetime.UTC)
    g = StrategyGuardrails(min_n_descriptive=2)
    svc = StrategyLearningService(db_session, g)
    
    comp = CompanyModel(normalized_name="ACME2")
    db_session.add(comp)
    db_session.flush()
    job = JobModel(normalized_title="engineer2", company_id=comp.id)
    db_session.add(job)
    db_session.flush()
    
    # 2 variants in family 'data'
    v1 = ResumeVariantModel(resume_family="data", name="d1", version=1, content_hash="hash-d1")
    v2 = ResumeVariantModel(resume_family="data", name="d2", version=1, content_hash="hash-d2")
    db_session.add_all([v1, v2])
    db_session.flush()
    
    # Give v1 N=2 with 1 interview (50% rate)
    p1_a = ApplicationPacketModel(resume_variant_id=v1.id, job_id=job.id, candidate_profile_version=1, packet_hash="pkt-d1-a")
    p1_b = ApplicationPacketModel(resume_variant_id=v1.id, job_id=job.id, candidate_profile_version=1, packet_hash="pkt-d1-b")
    # Give v2 N=1 with 1 interview (100% rate, but N=1 < min_n=2)
    p2_a = ApplicationPacketModel(resume_variant_id=v2.id, job_id=job.id, candidate_profile_version=1, packet_hash="pkt-d2-a")
    db_session.add_all([p1_a, p1_b, p2_a])
    db_session.flush()
    
    app1 = ApplicationModel(job_id=job.id, packet_id=p1_a.id, status="REJECTED", applied_at=now)
    app2 = ApplicationModel(job_id=job.id, packet_id=p1_b.id, status="INTERVIEWING", applied_at=now)
    app3 = ApplicationModel(job_id=job.id, packet_id=p2_a.id, status="INTERVIEWING", applied_at=now)
    db_session.add_all([app1, app2, app3])
    db_session.flush()

    # Need events to trigger outcomes
    ev2 = ApplicationEventModel(application_id=app2.id, event_type="INTERVIEW_REQUESTED", occurred_at=now, source="email")
    ev3 = ApplicationEventModel(application_id=app3.id, event_type="INTERVIEW_REQUESTED", occurred_at=now, source="email")
    db_session.add_all([ev2, ev3])
    db_session.commit()
    
    # 'highest_conversion' should pick v1 because it has N=2 >= min_n=2
    rec = svc.get_best_resume_variant(job.id, "data", strategy="highest_conversion")
    assert rec.resume_variant_id == str(v1.id)
    assert rec.strategy_used == "highest_conversion"
    assert rec.confidence == "HIGH"
    
    # 'explore' should pick v2 because it has lowest N
    rec_exp = svc.get_best_resume_variant(job.id, "data", strategy="explore")
    assert rec_exp.resume_variant_id == str(v2.id)
    assert rec_exp.strategy_used == "explore"
    assert rec_exp.confidence == "LOW"
    
    # Add another variant with no applications
    v3 = ResumeVariantModel(resume_family="data", name="d3", version=1, content_hash="hash-d3")
    db_session.add(v3)
    db_session.commit()
    
    # Now 'explore' should pick v3
    rec_exp2 = svc.get_best_resume_variant(job.id, "data", strategy="explore")
    assert rec_exp2.resume_variant_id == str(v3.id)
    
