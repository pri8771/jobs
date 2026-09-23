import pytest
from sqlalchemy.exc import IntegrityError
from jobs_automation.db.base import Base
from jobs_automation.db.models import OpportunityEdgeModel, TargetCompanyModel, TargetCompanyObservationModel, StrategyExperimentModel, StrategyExperimentAssignmentModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jobs_automation.intelligence.envelope import utc_now

@pytest.fixture(scope="module")
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_opportunity_edge_unique_constraint(session):
    import uuid
    sid = uuid.uuid4()
    oid = uuid.uuid4()
    
    edge1 = OpportunityEdgeModel(
        subject_type="job", subject_id=sid, predicate="REQUIRES",
        object_type="skill", object_id=oid, source_type="MODEL_INFERENCE",
        source_reference="hash1", method="extract", confidence=0.9,
        observed_at=utc_now(), valid_from=utc_now(), created_by="system"
    )
    session.add(edge1)
    session.commit()
    
    edge2 = OpportunityEdgeModel(
        subject_type="job", subject_id=sid, predicate="REQUIRES",
        object_type="skill", object_id=oid, source_type="MODEL_INFERENCE",
        source_reference="hash1", method="extract", confidence=0.9,
        observed_at=utc_now(), valid_from=utc_now(), created_by="system"
    )
    session.add(edge2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

def test_target_company_unique_canonical_name(session):
    c1 = TargetCompanyModel(canonical_name="Acme Corp")
    session.add(c1)
    session.commit()
    
    c2 = TargetCompanyModel(canonical_name="Acme Corp")
    session.add(c2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
