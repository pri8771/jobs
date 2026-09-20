"""Base alert email parser and URL / compensation normalization utilities."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from jobs_automation.ingestion.models import ExtractedJobPosting, RawEmailMessage

TRACKING_PARAMS_TO_REMOVE = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "trackingid",
    "refid",
    "midtoken",
    "midsig",
    "trk",
    "trkid",
    "eid",
    "trkemail",
    "otpcode",
    "alertid",
    "from",
    "vjk",
    "fccid",
    "cmp",
}


def clean_url(url: str) -> str:
    """Strip marketing and tracking query parameters to obtain a canonical URL."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        cleaned_pairs = [
            (k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS_TO_REMOVE
        ]
        new_query = urlencode(cleaned_pairs)
        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path.rstrip("/"),
                parsed.params,
                new_query,
                "",  # strip fragment
            )
        )
    except Exception:
        return url.strip()


def parse_salary_range(text: str) -> tuple[float | None, float | None, str]:
    """Parse salary/compensation text into min, max, and currency."""
    if not text:
        return None, None, "USD"

    # Match $150K - $180K or $150,000 - $180,000 or $150,000+
    # Check for /hr or /hour
    is_hourly = bool(re.search(r"/(?:hr|hour)", text, re.IGNORECASE))

    # Find dollar amounts
    matches = re.findall(r"\$\s*(\d+(?:[.,]\d+)?)\s*([kK])?", text)
    if not matches:
        return None, None, "USD"

    amounts: list[float] = []
    for num_str, k_suffix in matches:
        clean_num = float(num_str.replace(",", ""))
        if k_suffix.lower() == "k":
            clean_num *= 1000.0
        elif clean_num < 1000.0 and not is_hourly:
            # Often e.g. "$150 - $180k" where the first number implicitly has K
            if len(matches) > 1 and matches[1][1].lower() == "k":
                clean_num *= 1000.0

        if is_hourly:
            # Normalize hourly to standard full-time annual (~2080 hours)
            clean_num *= 2080.0

        amounts.append(clean_num)

    if len(amounts) == 1:
        return amounts[0], None, "USD"
    if len(amounts) >= 2:
        return min(amounts[0], amounts[1]), max(amounts[0], amounts[1]), "USD"

    return None, None, "USD"


def detect_remote_type(text: str) -> str | None:
    """Classify location text into remote, hybrid, or on_site."""
    if not text:
        return None
    lower = text.lower()
    if "remote" in lower:
        return "remote"
    if "hybrid" in lower:
        return "hybrid"
    if "on-site" in lower or "onsite" in lower or "in-office" in lower:
        return "on_site"
    return None


class BaseAlertParser(ABC):
    """Abstract base class for job alert email parsers."""

    @abstractmethod
    def can_parse(self, email: RawEmailMessage) -> bool:
        """Return True if this parser handles the given email."""
        pass

    @abstractmethod
    def parse(self, email: RawEmailMessage) -> list[ExtractedJobPosting]:
        """Extract job postings from the email."""
        pass
