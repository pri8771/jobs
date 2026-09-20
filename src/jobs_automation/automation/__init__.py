"""Controlled automatic application system with rate limiting, kill switch, and allowlisted ATS adapters."""

from jobs_automation.automation.auto_engine import (
    ControlledAutoApplicationEngine,
    ControlledAutoApplicationResult,
)
from jobs_automation.automation.base import ATSAdapter, SubmissionResult, ValidationResult
from jobs_automation.automation.kill_switch import KillSwitchManager
from jobs_automation.automation.rate_limiter import DomainRateLimiter

__all__ = [
    "ATSAdapter",
    "ControlledAutoApplicationEngine",
    "ControlledAutoApplicationResult",
    "DomainRateLimiter",
    "KillSwitchManager",
    "SubmissionResult",
    "ValidationResult",
]
