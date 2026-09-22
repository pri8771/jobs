"""Tests for configuration models, validation, and loader."""

import pytest
from pydantic import ValidationError

from jobs_automation.core.candidate_profile import (
    DemographicAnswersConfig,
)
from jobs_automation.core.config import ConfigLoader
from jobs_automation.core.job_search import (
    ScoringWeightsConfig,
)
from jobs_automation.core.platforms import (
    EmailPollingConfig,
)
from jobs_automation.core.policy_registry import (
    DefaultPolicyConfig,
    PolicyDecision,
)


def test_load_all_example_configs() -> None:
    loader = ConfigLoader("config")
    report = loader.validate_all()
    assert report.success is True, f"Validation failed with errors: {report.errors}"
    assert len(report.loaded_files) == 5
    assert "candidate_profile" in report.loaded_files
    assert "job_search" in report.loaded_files
    assert "platforms" in report.loaded_files
    assert "model_routing" in report.loaded_files
    assert "policy_registry" in report.loaded_files


def test_candidate_profile_unresolved_facts_detected() -> None:
    loader = ConfigLoader("config")
    profile, _ = loader.load_candidate_profile("config/candidate_profile.example.yaml")
    unresolved = profile.check_unresolved_facts()

    # Verify that unconfirmed facts are tracked and not silently guessed
    assert "email" in unresolved["identity"]
    assert "phone" in unresolved["identity"]
    assert "authorized_to_work_in_us" in unresolved["work_authorization"]
    assert "compensation_basis_unconfirmed" in unresolved["target"]


def test_demographic_guessing_is_strictly_prohibited() -> None:
    with pytest.raises(ValidationError, match="Demographic policy must be 'do_not_guess'"):
        DemographicAnswersConfig(policy="infer_demographics")


def test_job_search_scoring_weights_sum_to_100() -> None:
    with pytest.raises(ValidationError, match="Scoring weights must sum to 100"):
        ScoringWeightsConfig(title_match=10, must_have_skills=10)


def test_job_search_threshold_validation() -> None:
    loader = ConfigLoader("config")
    search, _ = loader.load_job_search()
    assert search.scoring.threshold_shortlist >= search.scoring.threshold_review


def test_email_polling_default_is_four_hours() -> None:
    loader = ConfigLoader("config")
    platforms, _ = loader.load_platforms()
    assert platforms.email.polling_minutes == 240
    assert platforms.email.intended_interval_hours_min == 3
    assert platforms.email.intended_interval_hours_max == 4
    assert platforms.email.realtime_push_required is False


def test_minute_level_email_polling_is_prohibited() -> None:
    with pytest.raises(ValidationError, match="Minute-level polling.*is prohibited"):
        EmailPollingConfig(polling_minutes=15)


def test_realtime_email_push_is_prohibited() -> None:
    with pytest.raises(ValidationError, match="Realtime push.*is prohibited"):
        EmailPollingConfig(realtime_push_required=True)


def test_policy_registry_must_deny_by_default() -> None:
    with pytest.raises(ValidationError, match="Default policy decision must be 'blocked'"):
        DefaultPolicyConfig(decision=PolicyDecision.AUTO_ALLOWED)


@pytest.mark.parametrize("invalid", ["", "not-an-address", "a@b.com;c@d.com", "a@b.com, c@d.com"])
def test_invalid_canary_identity_rejects_whole_policy(invalid: str) -> None:
    with pytest.raises(ValidationError, match="exactly one email address"):
        EmailPollingConfig(canary_identities=["owner+canary@example.com", invalid])


def test_display_name_canary_identity_remains_valid() -> None:
    identity = "Owner Canary <OWNER+CANARY@example.com>"
    assert EmailPollingConfig(canary_identities=[identity]).canary_identities == [identity]


def test_plain_canary_alias_and_empty_default() -> None:
    assert EmailPollingConfig().canary_identities == []
    assert EmailPollingConfig(canary_identities=["owner+canary@example.com"]).canary_identities == [
        "owner+canary@example.com"
    ]


def test_canary_policy_does_not_allow_unknown_config_keys() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        EmailPollingConfig.model_validate({"canary_identities": [], "unknown_policy": True})
