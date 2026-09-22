"""Browser automation and assisted application modules."""

from jobs_automation.browser.assisted_engine import (
    AssistedApplicationEngine,
    AssistedApplicationPlan,
    AssistedApplicationResult,
)
from jobs_automation.browser.base import (
    BrowserRunner,
    BrowserSessionResult,
    FieldClassification,
    FieldFillProvenance,
    FormField,
    FormInspectionResult,
    FormPrefillResult,
    PreSubmitReviewManifest,
)
from jobs_automation.browser.mock_runner import MockBrowserRunner
from jobs_automation.browser.playwright_runner import PlaywrightBrowserRunner

__all__ = [
    "AssistedApplicationEngine",
    "AssistedApplicationPlan",
    "AssistedApplicationResult",
    "BrowserRunner",
    "BrowserSessionResult",
    "FieldClassification",
    "FieldFillProvenance",
    "FormField",
    "FormInspectionResult",
    "FormPrefillResult",
    "MockBrowserRunner",
    "PlaywrightBrowserRunner",
    "PreSubmitReviewManifest",
]
