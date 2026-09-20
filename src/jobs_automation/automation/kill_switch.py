"""Kill switch manager for emergency cessation of automatic submissions."""

from __future__ import annotations

import datetime
import os

from jobs_automation.core.policy_registry import PolicyRegistryConfig


class KillSwitchManager:
    """Manages global and platform-specific emergency shutdown controls."""

    def __init__(
        self,
        global_override: bool | None = None,
        platform_overrides: dict[str, bool] | None = None,
        policy_config: PolicyRegistryConfig | None = None,
    ) -> None:
        self.global_override = global_override
        self.platform_overrides = dict(platform_overrides or {})
        self.policy_config = policy_config

    def is_global_active(self) -> tuple[bool, str]:
        """Checks if the global kill switch is active."""
        if self.global_override is True:
            return True, "Global kill switch enabled via manual override"

        env_val = os.getenv("JOBS_AUTOMATION_KILL_SWITCH", "").strip().lower()
        if env_val in ("true", "1", "yes", "on"):
            return (
                True,
                "Global kill switch enabled via JOBS_AUTOMATION_KILL_SWITCH environment variable",
            )

        return False, ""

    def is_platform_active(
        self, platform: str, as_of_date: datetime.date | None = None
    ) -> tuple[bool, str]:
        """Checks if a platform-specific kill switch or policy expiration is active."""
        # Check global first
        is_global, reason = self.is_global_active()
        if is_global:
            return True, reason

        norm_platform = platform.strip().lower()
        if self.platform_overrides.get(norm_platform) is True:
            return True, f"Kill switch active for platform '{norm_platform}' via explicit override"

        env_key = f"JOBS_AUTOMATION_KILL_SWITCH_{norm_platform.upper()}"
        env_val = os.getenv(env_key, "").strip().lower()
        if env_val in ("true", "1", "yes", "on"):
            return True, f"Kill switch active for platform '{norm_platform}' via {env_key}"

        # Check policy review date expiration
        if self.policy_config:
            if as_of_date is None:
                as_of_date = datetime.date.today()

            for entry in self.policy_config.entries:
                if entry.platform.lower() == norm_platform and entry.review_due_at:
                    try:
                        due_date = datetime.date.fromisoformat(entry.review_due_at)
                        if as_of_date > due_date:
                            return True, (
                                f"Automatic submission kill switch triggered: policy review for "
                                f"'{norm_platform}' expired on {entry.review_due_at} (current: {as_of_date})"
                            )
                    except ValueError:
                        pass

        return False, ""

    def activate_global(self) -> None:
        self.global_override = True

    def deactivate_global(self) -> None:
        self.global_override = False

    def activate_platform(self, platform: str) -> None:
        self.platform_overrides[platform.strip().lower()] = True

    def deactivate_platform(self, platform: str) -> None:
        self.platform_overrides[platform.strip().lower()] = False
