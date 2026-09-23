import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from jobs_automation.intelligence.envelope import RateWithN, DerivedArtifactEnvelope, EvidenceRef, canonical_json_hash

def test_rate_with_n_valid():
    rate = RateWithN(numerator=1, denominator=2, min_n=5)
    assert rate.rate == 0.5000
    assert rate.n == 2
    assert rate.low_n is True

def test_rate_with_n_zero_denominator():
    rate = RateWithN(numerator=0, denominator=0, min_n=5)
    assert rate.rate is None
    assert rate.n == 0
    assert rate.low_n is True

def test_rate_with_n_invalid():
    with pytest.raises(ValidationError):
        RateWithN(numerator=3, denominator=2)

def test_canonical_json_hash():
    obj1 = {"b": 2, "a": 1}
    obj2 = {"a": 1, "b": 2}
    assert canonical_json_hash(obj1) == canonical_json_hash(obj2)
    
def test_envelope_round_trip():
    ref = EvidenceRef(ref_type="job", ref_id="123")
    env = DerivedArtifactEnvelope(
        artifact_type="test",
        generated_at=datetime.now(timezone.utc),
        generator="test.Class",
        generator_version="1.0.0",
        source_refs=[ref]
    )
    data = env.model_dump_json()
    env2 = DerivedArtifactEnvelope.model_validate_json(data)
    assert env.artifact_type == env2.artifact_type
