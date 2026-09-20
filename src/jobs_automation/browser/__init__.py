"""Browser automation and assisted application modules."""

from jobs_automation.browser.assisted_engine import (
    AssistedApplicationEngine,
    AssistedApplicationResult,
)
from jobs_automation.browser.base import (
    BrowserRunner,
    FormField,
    FormInspectionResult,
    FormPrefillResult,
)
from jobs_automation.browser.mock_runner import MockBrowserRunner

__all__ = [
    "AssistedApplicationEngine",
    "AssistedApplicationResult",
    "BrowserRunner",
    "FormField",
    "FormInspectionResult",
    "FormPrefillResult",
    "MockBrowserRunner",
]
