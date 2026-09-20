"""Registry for ATS adapters."""

from __future__ import annotations

from jobs_automation.automation.adapters.greenhouse import GreenhouseATSAdapter
from jobs_automation.automation.adapters.lever import LeverATSAdapter
from jobs_automation.automation.base import ATSAdapter


class ATSAdapterRegistry:
    """Registry maintaining active ATS submission adapters."""

    def __init__(self, adapters: list[ATSAdapter] | None = None) -> None:
        if adapters is None:
            self._adapters: list[ATSAdapter] = [
                GreenhouseATSAdapter(),
                LeverATSAdapter(),
            ]
        else:
            self._adapters = list(adapters)

    def register(self, adapter: ATSAdapter) -> None:
        self._adapters.append(adapter)

    def find_adapter(self, destination_domain: str) -> ATSAdapter | None:
        """Finds the first adapter capable of submitting to the destination domain."""
        for adp in self._adapters:
            if adp.can_handle(destination_domain):
                return adp
        return None

    @property
    def registered_platforms(self) -> list[str]:
        return [adp.platform_name for adp in self._adapters]
