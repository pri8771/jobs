"""Per-domain rate limiting and polite submission pacing."""

from __future__ import annotations

import datetime
from collections import defaultdict


class DomainRateLimiter:
    """Enforces per-domain submission rate limits and polite pacing."""

    def __init__(
        self,
        min_interval_seconds: float = 5.0,
        max_per_hour: int = 15,
    ) -> None:
        self.min_interval_seconds = min_interval_seconds
        self.max_per_hour = max_per_hour
        self._history: dict[str, list[datetime.datetime]] = defaultdict(list)

    def check_rate_limit(
        self,
        domain: str,
        now: datetime.datetime | None = None,
    ) -> tuple[bool, str, float]:
        """Checks if a submission to the domain is permitted.

        Returns (allowed, reason, retry_after_seconds).
        """
        if now is None:
            now = datetime.datetime.now(datetime.UTC)

        norm_domain = domain.strip().lower()
        events = self._history[norm_domain]

        # Prune events older than 1 hour
        one_hour_ago = now - datetime.timedelta(hours=1)
        events = [t for t in events if t > one_hour_ago]
        self._history[norm_domain] = events

        if events:
            # Check min interval since last event
            last_event = events[-1]
            elapsed = (now - last_event).total_seconds()
            if elapsed < self.min_interval_seconds:
                wait_sec = self.min_interval_seconds - elapsed
                return (
                    False,
                    f"Pacing limit: must wait {wait_sec:.1f}s before next submission to {norm_domain}",
                    wait_sec,
                )

            # Check hourly cap
            if len(events) >= self.max_per_hour:
                oldest_event = events[0]
                wait_sec = (oldest_event + datetime.timedelta(hours=1) - now).total_seconds()
                return (
                    False,
                    f"Hourly limit reached ({self.max_per_hour}/hr) for {norm_domain}",
                    max(0.0, wait_sec),
                )

        return True, "Rate limit check passed", 0.0

    def record_submission(
        self,
        domain: str,
        now: datetime.datetime | None = None,
    ) -> None:
        """Records a successful or attempted submission for rate tracking."""
        if now is None:
            now = datetime.datetime.now(datetime.UTC)

        norm_domain = domain.strip().lower()
        self._history[norm_domain].append(now)

    def reset(self) -> None:
        self._history.clear()
