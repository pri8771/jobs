"""Playwright-based browser runner for form inspection and assisted application."""

from __future__ import annotations

import logging
from typing import Any

from jobs_automation.browser.base import (
    BrowserRunner,
    BrowserSessionResult,
    FormField,
    FormInspectionResult,
    FormPrefillResult,
)

logger = logging.getLogger(__name__)


class PlaywrightBrowserRunner(BrowserRunner):
    """Local visible or headless browser runner using Playwright."""

    def __init__(self, headless: bool = False, timeout_ms: int = 30000) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms

    def _ensure_playwright(self) -> Any:
        try:
            # Playwright is an optional runtime dependency: the ignore must stay valid
            # both when it is absent (CI) and when it is installed (engineering hosts).
            import playwright.sync_api as p_sync  # type: ignore[import-not-found,unused-ignore]

            return p_sync
        except ImportError as e:
            raise RuntimeError(
                "Playwright is not installed. To use live browser automation, install with:\n"
                "pip install playwright && playwright install chromium\n"
                "Or run with --mock-browser for offline/test mode."
            ) from e

    def inspect_form(self, url: str) -> FormInspectionResult:
        p_sync = self._ensure_playwright()
        fields: list[FormField] = []
        detected_ats: str | None = None
        has_file_upload = False

        with p_sync.sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, timeout=self.timeout_ms)
                page.wait_for_load_state("domcontentloaded")
                title = page.title()

                # Detect known ATS platforms by URL or page content
                content_lower = page.content().lower()
                url_lower = url.lower()
                if "greenhouse.io" in url_lower or "greenhouse" in content_lower:
                    detected_ats = "greenhouse"
                elif "lever.co" in url_lower or "lever" in content_lower:
                    detected_ats = "lever"
                elif "myworkdayjobs.com" in url_lower or "workday" in content_lower:
                    detected_ats = "workday"
                elif "ashbyhq.com" in url_lower or "ashby" in content_lower:
                    detected_ats = "ashby"

                # Query standard input/select/textarea elements
                inputs = page.query_selector_all("input, textarea, select")
                for inp in inputs:
                    tag_name = inp.evaluate("el => el.tagName.toLowerCase()")
                    inp_type = inp.get_attribute("type") or (
                        "textarea" if tag_name == "textarea" else "text"
                    )
                    name = inp.get_attribute("name") or inp.get_attribute("id") or ""
                    if not name or inp_type in ("hidden", "submit", "button", "reset"):
                        continue

                    required = (
                        inp.get_attribute("required") is not None
                        or inp.get_attribute("aria-required") == "true"
                    )
                    placeholder = inp.get_attribute("placeholder") or ""

                    if inp_type == "file":
                        has_file_upload = True

                    # Try to extract associated label
                    inp_id = inp.get_attribute("id")
                    label_text = None
                    if inp_id:
                        label_el = page.query_selector(f"label[for='{inp_id}']")
                        if label_el:
                            label_text = label_el.inner_text().strip()

                    selector = f"#{inp_id}" if inp_id else f"{tag_name}[name='{name}']"
                    fields.append(
                        FormField(
                            name=name,
                            field_type=inp_type,
                            label=label_text,
                            placeholder=placeholder,
                            selector=selector,
                            required=required,
                        )
                    )

                return FormInspectionResult(
                    url=url,
                    title=title,
                    fields=fields,
                    has_file_upload=has_file_upload,
                    detected_ats=detected_ats,
                    form_found=len(fields) > 0,
                )
            finally:
                browser.close()

    def prefill_form(
        self,
        url: str,
        field_values: dict[str, str],
        file_uploads: dict[str, str] | None = None,
    ) -> FormPrefillResult:
        p_sync = self._ensure_playwright()
        prefilled: dict[str, str] = {}
        unmatched: list[str] = []
        attached: dict[str, str] = {}

        with p_sync.sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            try:
                page.goto(url, timeout=self.timeout_ms)
                page.wait_for_load_state("domcontentloaded")

                for key, val in field_values.items():
                    # Attempt selector match by id, name, or label
                    matched = False
                    for selector in [f"#{key}", f"input[name='{key}']", f"textarea[name='{key}']"]:
                        if page.query_selector(selector):
                            page.fill(selector, val)
                            prefilled[key] = val
                            matched = True
                            break
                    if not matched:
                        unmatched.append(key)

                if file_uploads:
                    for key, file_path in file_uploads.items():
                        for selector in [
                            f"#{key}",
                            f"input[name='{key}'][type='file']",
                            "input[type='file']",
                        ]:
                            if page.query_selector(selector):
                                page.set_input_files(selector, file_path)
                                attached[key] = file_path
                                break

                return FormPrefillResult(
                    url=url,
                    prefilled_fields=prefilled,
                    unmatched_fields=unmatched,
                    attached_files=attached,
                    success=True,
                )
            finally:
                browser.close()

    def open_interactive_session(
        self,
        url: str,
        prefilled_fields: dict[str, str],
        file_uploads: dict[str, str] | None = None,
    ) -> BrowserSessionResult:
        """Launches a visible browser window, prefills form fields, and leaves page open for user review."""
        p_sync = self._ensure_playwright()
        with p_sync.sync_playwright() as p:
            # Always launch visible browser for assisted interactive session
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            try:
                page.goto(url, timeout=self.timeout_ms)
                page.wait_for_load_state("domcontentloaded")

                for key, val in prefilled_fields.items():
                    for selector in [f"#{key}", f"input[name='{key}']", f"textarea[name='{key}']"]:
                        if page.query_selector(selector):
                            try:
                                page.fill(selector, val)
                            except Exception as fill_err:
                                logger.warning(f"Could not fill {selector}: {fill_err}")
                            break

                if file_uploads:
                    for key, file_path in file_uploads.items():
                        for selector in [
                            f"#{key}",
                            f"input[name='{key}'][type='file']",
                            "input[type='file']",
                        ]:
                            if page.query_selector(selector):
                                try:
                                    page.set_input_files(selector, file_path)
                                except Exception as upload_err:
                                    logger.warning(f"Could not upload {file_path}: {upload_err}")
                                break

                # Keep session open until closed or user confirmation in terminal
                logger.info(
                    "Form prefilled. Visible browser window is open for candidate inspection."
                )
                page.wait_for_timeout(5000)

                return BrowserSessionResult(
                    url=page.url,
                    submitted=False,
                    notes="Interactive browser session displayed to user.",
                )
            finally:
                browser.close()
