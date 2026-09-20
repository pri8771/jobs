"""Tests for policy registry and default-deny evaluator."""

import datetime

from jobs_automation.core.config import ConfigLoader
from jobs_automation.core.policy_registry import (
    DefaultPolicyConfig,
    PolicyDecision,
    PolicyEntryConfig,
    PolicyRegistryConfig,
)
from jobs_automation.policy.evaluator import PolicyEvaluator


def test_evaluator_deny_by_default_on_unknown_domain() -> None:
    loader = ConfigLoader("config")
    policy_cfg, _ = loader.load_policy_registry()
    evaluator = PolicyEvaluator(policy_cfg)

    # Any unknown employer or ATS site defaults to BLOCKED
    res = evaluator.evaluate("unknown-company.com")
    assert res.decision == PolicyDecision.BLOCKED
    assert res.allowed_to_auto_submit is False
    assert "deny_by_default" in res.reason


def test_evaluator_linkedin_and_indeed_are_manual_only() -> None:
    loader = ConfigLoader("config")
    policy_cfg, _ = loader.load_policy_registry()
    evaluator = PolicyEvaluator(policy_cfg)

    res_linkedin = evaluator.evaluate("www.linkedin.com")
    assert res_linkedin.decision == PolicyDecision.MANUAL_ONLY
    assert res_linkedin.allowed_to_auto_submit is False

    res_indeed = evaluator.evaluate("indeed.com")
    assert res_indeed.decision == PolicyDecision.MANUAL_ONLY
    assert res_indeed.allowed_to_auto_submit is False


def test_evaluator_ziprecruiter_and_dice_are_assisted() -> None:
    loader = ConfigLoader("config")
    policy_cfg, _ = loader.load_policy_registry()
    evaluator = PolicyEvaluator(policy_cfg)

    res_zip = evaluator.evaluate("www.ziprecruiter.com")
    assert res_zip.decision == PolicyDecision.ASSISTED
    assert res_zip.allowed_to_auto_submit is False

    res_dice = evaluator.evaluate("dice.com")
    assert res_dice.decision == PolicyDecision.ASSISTED
    assert res_dice.allowed_to_auto_submit is False


def test_evaluator_blocks_expired_policy_review() -> None:
    config = PolicyRegistryConfig(
        version=1,
        default=DefaultPolicyConfig(),
        entries=[
            PolicyEntryConfig(
                platform="greenhouse",
                domain_pattern="*.greenhouse.io",
                capability="submit_application",
                decision=PolicyDecision.AUTO_ALLOWED,
                reviewed_at="2026-01-01",
                review_due_at="2026-03-01",
            )
        ],
    )
    evaluator = PolicyEvaluator(config)

    # Test as of today (which is after March 2026)
    as_of = datetime.date(2026, 9, 20)
    res = evaluator.evaluate("boards.greenhouse.io", as_of_date=as_of)
    assert res.decision == PolicyDecision.BLOCKED
    assert res.allowed_to_auto_submit is False
    assert "policy_review_expired" in res.reason


def test_evaluator_allows_auto_only_when_explicitly_configured_and_unexpired() -> None:
    config = PolicyRegistryConfig(
        version=1,
        default=DefaultPolicyConfig(),
        entries=[
            PolicyEntryConfig(
                platform="greenhouse",
                domain_pattern="*.greenhouse.io",
                capability="submit_application",
                decision=PolicyDecision.AUTO_ALLOWED,
                reviewed_at="2026-09-01",
                review_due_at="2026-12-01",
            )
        ],
    )
    evaluator = PolicyEvaluator(config)
    as_of = datetime.date(2026, 9, 20)
    res = evaluator.evaluate("boards.greenhouse.io", as_of_date=as_of)
    assert res.decision == PolicyDecision.AUTO_ALLOWED
    assert res.allowed_to_auto_submit is True
