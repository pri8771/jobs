"""Mock browser runner for deterministic testing and headless environments."""

from __future__ import annotations

from jobs_automation.browser.base import (
    BrowserRunner,
    BrowserSessionResult,
    FormField,
    FormInspectionResult,
    FormPrefillResult,
)


class MockBrowserRunner(BrowserRunner):
    """Deterministic browser runner for tests and offline usage."""

    def __init__(
        self,
        interactive_submitted: bool = True,
        receipt_text: str = "Thank you for your application! Application ID: MOCK-APP-9981",
        detected_ats: str | None = "greenhouse",
    ) -> None:
        self.interactive_submitted = interactive_submitted
        self.receipt_text = receipt_text
        self.detected_ats = detected_ats
        self.inspected_urls: list[str] = []
        self.prefilled_calls: list[tuple[str, dict[str, str]]] = []
        self.sessions_opened: list[tuple[str, dict[str, str]]] = []

    def inspect_form(self, url: str) -> FormInspectionResult:
        self.inspected_urls.append(url)
        return FormInspectionResult(
            url=url,
            title="Careers Application Form",
            detected_ats=self.detected_ats,
            has_file_upload=True,
            fields=[
                FormField(
                    name="first_name", selector="#first_name", required=True, label="First Name"
                ),
                FormField(
                    name="last_name", selector="#last_name", required=True, label="Last Name"
                ),
                FormField(
                    name="email",
                    selector="#email",
                    field_type="email",
                    required=True,
                    label="Email",
                ),
                FormField(
                    name="phone", selector="#phone", field_type="tel", required=True, label="Phone"
                ),
                FormField(
                    name="linkedin", selector="#linkedin", required=False, label="LinkedIn Profile"
                ),
                FormField(
                    name="github", selector="#github", required=False, label="GitHub Profile"
                ),
                FormField(
                    name="resume",
                    selector="#resume",
                    field_type="file",
                    required=True,
                    label="Resume/CV",
                ),
            ],
            form_found=True,
            metadata={"mock": True},
        )

    def prefill_form(
        self,
        url: str,
        field_values: dict[str, str],
        file_uploads: dict[str, str] | None = None,
    ) -> FormPrefillResult:
        self.prefilled_calls.append((url, field_values))
        return FormPrefillResult(
            url=url,
            prefilled_fields=dict(field_values),
            unmatched_fields=[],
            attached_files=dict(file_uploads or {}),
            success=True,
            message="Mock form prefilled successfully",
        )

    def open_interactive_session(
        self,
        url: str,
        prefilled_fields: dict[str, str],
        file_uploads: dict[str, str] | None = None,
    ) -> BrowserSessionResult:
        self.sessions_opened.append((url, prefilled_fields))
        return BrowserSessionResult(
            url=url,
            submitted=self.interactive_submitted,
            confirmation_url=f"{url}/confirmation" if self.interactive_submitted else None,
            receipt_text=self.receipt_text if self.interactive_submitted else None,
            notes="Mock interactive session completed",
        )
