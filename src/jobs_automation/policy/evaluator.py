"""Policy evaluation engine with strict deny-by-default behavior."""

from __future__ import annotations

import datetime
import fnmatch

from pydantic import BaseModel, ConfigDict, Field

from jobs_automation.core.policy_registry import (
    PolicyDecision,
    PolicyEntryConfig,
    PolicyRegistryConfig,
)


class PolicyEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destination: str
    capability: str
    decision: PolicyDecision
    reason: str
    matched_pattern: str | None = None
    platform: str | None = None
    reviewed_at: str | None = None
    review_due_at: str | None = None
    evidence: list[str] = Field(default_factory=list)
    allowed_to_auto_submit: bool = False


class PolicyEvaluator:
    """Evaluates automation permissions for application destinations and platforms.

    Enforces deny-by-default: if no explicit, unexpired rule allows automation,
    the decision is BLOCKED.
    """

    def __init__(self, config: PolicyRegistryConfig) -> None:
        self.config = config

    def evaluate(
        self,
        destination_domain: str,
        capability: str = "submit_application",
        platform_hint: str | None = None,
        as_of_date: datetime.date | None = None,
    ) -> PolicyEvaluationResult:
        if as_of_date is None:
            as_of_date = datetime.date.today()

        norm_domain = destination_domain.strip().lower()

        # Find best matching entry
        matched_entry: PolicyEntryConfig | None = None
        for entry in self.config.entries:
            if entry.capability != capability:
                continue

            # If platform_hint is specified, prefer matching platform
            if platform_hint and entry.platform.lower() != platform_hint.lower():
                continue

            pattern = entry.domain_pattern.lower()
            if fnmatch.fnmatch(norm_domain, pattern) or norm_domain == pattern.lstrip("*."):
                matched_entry = entry
                break

        # Fallback without platform_hint if not found
        if matched_entry is None and platform_hint is not None:
            for entry in self.config.entries:
                if entry.capability != capability:
                    continue
                pattern = entry.domain_pattern.lower()
                if fnmatch.fnmatch(norm_domain, pattern) or norm_domain == pattern.lstrip("*."):
                    matched_entry = entry
                    break

        if matched_entry is None:
            return PolicyEvaluationResult(
                destination=destination_domain,
                capability=capability,
                decision=self.config.default.decision,
                reason=f"{self.config.default.reason}: no matching policy for {norm_domain}",
                allowed_to_auto_submit=False,
            )

        # Check if review has expired
        if matched_entry.review_due_at:
            try:
                due_date = datetime.date.fromisoformat(matched_entry.review_due_at)
                if as_of_date > due_date:
                    return PolicyEvaluationResult(
                        destination=destination_domain,
                        capability=capability,
                        decision=PolicyDecision.BLOCKED,
                        reason=f"policy_review_expired: review was due on {matched_entry.review_due_at}",
                        matched_pattern=matched_entry.domain_pattern,
                        platform=matched_entry.platform,
                        reviewed_at=matched_entry.reviewed_at,
                        review_due_at=matched_entry.review_due_at,
                        evidence=matched_entry.evidence,
                        allowed_to_auto_submit=False,
                    )
            except ValueError:
                pass

        allowed_auto = matched_entry.decision == PolicyDecision.AUTO_ALLOWED
        return PolicyEvaluationResult(
            destination=destination_domain,
            capability=capability,
            decision=matched_entry.decision,
            reason=f"matched_policy_entry: platform={matched_entry.platform}",
            matched_pattern=matched_entry.domain_pattern,
            platform=matched_entry.platform,
            reviewed_at=matched_entry.reviewed_at,
            review_due_at=matched_entry.review_due_at,
            evidence=matched_entry.evidence,
            allowed_to_auto_submit=allowed_auto,
        )
