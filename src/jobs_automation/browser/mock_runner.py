"""Mock browser runner for deterministic testing and headless environments."""

from __future__ import annotations

import hashlib
from pathlib import Path

from jobs_automation.browser.base import (
    BrowserRunner,
    BrowserSessionResult,
    FormField,
    FormInspectionResult,
    FormPrefillResult,
)


class MockBrowserRunner(BrowserRunner):
    """Deterministic browser runner for tests and offline usage.

    The mock never reports a submission by default (FR15-03): ``interactive_submitted``
    must be opted into explicitly, and even then the engine's prefill-only path ignores
    it.
    """

    def __init__(
        self,
        interactive_submitted: bool = False,
        receipt_text: str = "Thank you for your application! Application ID: MOCK-APP-9981",
        detected_ats: str | None = "greenhouse",
        custom_fields: list[FormField] | None = None,
        custom_inspection: FormInspectionResult | None = None,
        changed_inspection: FormInspectionResult | None = None,
        page_text: str | None = None,
        page_text_injection_detected: bool = False,
        page_security_warnings: list[str] | None = None,
        final_url: str | None = None,
        form_action: str | None = None,
        fail_fields: set[str] | None = None,
        inspection_error: str | None = None,
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
        self.final_url = final_url
        self.form_action = form_action
        self.fail_fields = set(fail_fields or set())
        self.inspection_error = inspection_error
        self.inspected_urls: list[str] = []
        self.prefilled_calls: list[tuple[str, dict[str, str]]] = []
        self.prefill_targets: list[dict[str, str]] = []
        self.sessions_opened: list[tuple[str, dict[str, str]]] = []
        self.open_sessions: list[tuple[str, dict[str, str], dict[str, str]]] = []

    def inspect_form(self, url: str) -> FormInspectionResult:
        self.inspected_urls.append(url)

        if self.inspection_error is not None:
            return FormInspectionResult(
                url=url,
                title="",
                fields=[],
                form_found=False,
                inspection_error=self.inspection_error,
                is_mock=True,
            )

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

        fields = (
            self.custom_fields
            if self.custom_fields is not None
            else [
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
        )
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
            final_url=self.final_url or url,
            form_action=self.form_action,
            form_count=1,
        )

    def prefill_form(
        self,
        url: str,
        field_values: dict[str, str],
        file_uploads: dict[str, str] | None = None,
        targets: dict[str, str] | None = None,
    ) -> FormPrefillResult:
        self.prefilled_calls.append((url, field_values))
        self.prefill_targets.append(dict(targets or {}))
        prefilled: dict[str, str] = {}
        failed: dict[str, str] = {}
        readback: dict[str, str] = {}
        for name, value in field_values.items():
            if name in self.fail_fields:
                failed[name] = "mock_write_failure"
                continue
            prefilled[name] = value
            readback[name] = value

        attached: dict[str, str] = {}
        digests: dict[str, str] = {}
        for name, path in (file_uploads or {}).items():
            if name in self.fail_fields:
                failed[name] = "mock_upload_failure"
                continue
            file_path = Path(path)
            attached[name] = path
            if file_path.is_file():
                data = file_path.read_bytes()
                digests[name] = hashlib.sha256(data).hexdigest()
                readback[name] = f"{file_path.name}:{len(data)}"
            else:
                digests[name] = hashlib.sha256(path.encode("utf-8")).hexdigest()
                readback[name] = f"{file_path.name}:0"

        return FormPrefillResult(
            url=url,
            final_url=self.final_url or url,
            prefilled_fields=prefilled,
            unmatched_fields=[],
            failed_fields=failed,
            readback=readback,
            attached_files=attached,
            attached_file_digests=digests,
            verified_file_hashes=dict(digests),
            success=not failed,
            message="Mock form prefilled successfully" if not failed else "Mock prefill partial",
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
            submit_performed=False,
        )
