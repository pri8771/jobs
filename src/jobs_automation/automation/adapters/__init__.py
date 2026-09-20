"""Allowlisted ATS adapters and adapter registry."""

from jobs_automation.automation.adapters.greenhouse import GreenhouseATSAdapter
from jobs_automation.automation.adapters.lever import LeverATSAdapter
from jobs_automation.automation.adapters.registry import ATSAdapterRegistry

__all__ = [
    "ATSAdapterRegistry",
    "GreenhouseATSAdapter",
    "LeverATSAdapter",
]
