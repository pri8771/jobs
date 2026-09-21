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
        custom_fields: list[FormField] | None = None,
        custom_inspection: FormInspectionResult | None = None,
        changed_inspection: FormInspectionResult | None = None,
        page_text: str | None = None,
        page_text_injection_detected: bool = False,
        page_security_warnings: list[str] | None = None,
    ) -> None:
        self.interactive_submitted = interactive_submitted
        self.receipt_text = receipt_text
        self.detected_ats = detected_ats
        self.custom_fields = custom_fields
        self.custom_inspection = custom_inspection
        self.changed_inspection = changed_inspection  # A-R15-05: returned on 2nd+ inspect call
        self.page_text = page_text
        self.page_text_injection_detected = page_text_injection_detected
        self.page_security_warnings = page_security_warnings or []
        self.inspected_urls: list[str] = []
        self.prefilled_calls: list[tuple[str, dict[str, str]]] = []
        self.sessions_opened: list[tuple[str, dict[str, str]]] = []
        self.open_sessions: list[tuple[str, dict[str, str], dict[str, str]]] = []

    def inspect_form(self, url: str) -> FormInspectionResult:
        self.inspected_urls.append(url)

        # A-R15-05: If changed_inspection is set, return it on the 2nd+ call to
        # simulate a form that changed between initial inspection and pre-write validation.
        if self.changed_inspection is not None and len(self.inspected_urls) >= 2:
            return self.changed_inspection

        if self.custom_inspection is not None:
            return self.custom_inspection

        # A-R15-06: Page-level injection detection
        page_injection = self.page_text_injection_detected
        warnings = list(self.page_security_warnings)
        if self.page_text:
            from jobs_automation.browser.assisted_engine import detect_prompt_injection_text

            if detect_prompt_injection_text(self.page_text):
                page_injection = True
                if "security_warning:page_level_prompt_injection_detected" not in warnings:
                    warnings.append("security_warning:page_level_prompt_injection_detected")

        fields = self.custom_fields if self.custom_fields is not None else [
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
        ]
        return FormInspectionResult(
            url=url,
            title="Careers Application Form",
            detected_ats=self.detected_ats,
            has_file_upload=True,
            fields=fields,
            form_found=True,
            form_fingerprint=f"mock_fingerprint_{len(fields)}",
            metadata={"mock": True},
            page_security_warnings=warnings,
            page_text_injection_detected=page_injection,
            is_mock=True,
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
            is_mock=True,
        )

    def open_interactive_session(
        self,
        url: str,
        prefilled_fields: dict[str, str],
        file_uploads: dict[str, str] | None = None,
    ) -> BrowserSessionResult:
        self.sessions_opened.append((url, prefilled_fields))
        self.open_sessions.append((url, prefilled_fields, dict(file_uploads or {})))
        return BrowserSessionResult(
            url=url,
            submitted=self.interactive_submitted,
            confirmation_url=f"{url}/confirmation" if self.interactive_submitted else None,
            receipt_text=self.receipt_text if self.interactive_submitted else None,
            external_confirmation_evidence=(
                {
                    "type": "mock_confirmation",
                    "receipt_id": "MOCK-APP-9981",
                    "simulated": True,
                }
                if self.interactive_submitted
                else None
            ),
            notes="Mock interactive session completed",
            is_mock=True,
        )
