"""Playwright-based browser runner for form inspection and assisted application."""

from __future__ import annotations

import hashlib
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
    """Local visible or headless browser runner using Playwright with persistent session support."""

    def __init__(
        self,
        headless: bool = False,
        timeout_ms: int = 30000,
        user_data_dir: str | None = None,
    ) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.user_data_dir = user_data_dir
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None

    def _ensure_playwright(self) -> Any:
        try:
            import playwright.sync_api as p_sync  # type: ignore[import-not-found]

            return p_sync
        except ImportError as e:
            raise RuntimeError(
                "Playwright is not installed. To use live browser automation, install with:\n"
                "pip install playwright && playwright install chromium\n"
                "Or run with --mock-browser for offline/test mode."
            ) from e

    def _get_or_create_page(self, url: str) -> Any:
        """Obtains or creates the persistent Playwright page, ensuring single-session continuity."""
        if self._page is None or self._page.is_closed():
            p_sync = self._ensure_playwright()
            if self._playwright is None:
                self._playwright = p_sync.sync_playwright().start()

            if self.user_data_dir:
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=self.headless,
                )
                self._page = (
                    self._context.pages[0] if self._context.pages else self._context.new_page()
                )
            else:
                self._browser = self._playwright.chromium.launch(headless=self.headless)
                self._context = self._browser.new_context()
                self._page = self._context.new_page()

        if url:
            current_url = self._page.url or ""
            if (
                not current_url
                or current_url == "about:blank"
                or current_url.rstrip("/") != url.rstrip("/")
            ):
                self._page.goto(url, timeout=self.timeout_ms)
                self._page.wait_for_load_state("domcontentloaded")

        return self._page

    def inspect_form(self, url: str) -> FormInspectionResult:
        page = self._get_or_create_page(url)
        fields: list[FormField] = []
        detected_ats: str | None = None
        has_file_upload = False

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

        fingerprint_raw = "|".join(
            f"{f.name}:{f.field_type}:{f.selector}:{f.required}"
            for f in sorted(fields, key=lambda x: x.name)
        )
        form_fingerprint = hashlib.sha256(fingerprint_raw.encode("utf-8")).hexdigest()[:16]

        # A-R15-06: Page-level prompt injection inspection outside form fields
        page_security_warnings: list[str] = []
        page_text_injection = False
        try:
            body_text = page.inner_text("body")
            from jobs_automation.browser.assisted_engine import detect_prompt_injection_text

            if detect_prompt_injection_text(body_text):
                page_text_injection = True
                page_security_warnings.append(
                    "security_warning:page_level_prompt_injection_detected"
                )
        except Exception as exc:
            logger.debug(f"Could not inspect page text for prompt injection: {exc}")

        return FormInspectionResult(
            url=url,
            title=title,
            fields=fields,
            has_file_upload=has_file_upload,
            detected_ats=detected_ats,
            form_found=len(fields) > 0,
            form_fingerprint=form_fingerprint,
            page_security_warnings=page_security_warnings,
            page_text_injection_detected=page_text_injection,
        )

    def prefill_form(
        self,
        url: str,
        field_values: dict[str, str],
        file_uploads: dict[str, str] | None = None,
    ) -> FormPrefillResult:
        page = self._get_or_create_page(url)
        prefilled: dict[str, str] = {}
        unmatched: list[str] = []
        attached: dict[str, str] = {}

        for key, val in field_values.items():
            matched = False
            for selector in [f"#{key}", f"input[name='{key}']", f"textarea[name='{key}']"]:
                if page.query_selector(selector):
                    try:
                        page.fill(selector, val)
                        prefilled[key] = val
                        matched = True
                        break
                    except Exception as err:
                        logger.warning(f"Could not fill selector {selector}: {err}")
            if not matched:
                unmatched.append(key)

        # A-R15-07 / A-R15-09: Exact field-specific upload mapping; remove generic input[type='file'] fallback
        if file_uploads:
            for key, file_path in file_uploads.items():
                if key == "resume":
                    selectors = [
                        f"#{key}",
                        f"input[name='{key}'][type='file']",
                        "input[type='file'][name*='resume' i]",
                        "input[type='file'][id*='resume' i]",
                        "input[type='file'][aria-label*='resume' i]",
                    ]
                elif key == "cover_letter":
                    selectors = [
                        f"#{key}",
                        f"input[name='{key}'][type='file']",
                        "input[type='file'][name*='cover' i]",
                        "input[type='file'][id*='cover' i]",
                        "input[type='file'][aria-label*='cover' i]",
                    ]
                else:
                    selectors = [
                        f"#{key}",
                        f"input[name='{key}'][type='file']",
                    ]

                for selector in selectors:
                    if page.query_selector(selector):
                        try:
                            page.set_input_files(selector, file_path)
                            attached[key] = file_path
                            break
                        except Exception as upload_err:
                            logger.warning(f"Could not upload file {file_path}: {upload_err}")

        return FormPrefillResult(
            url=url,
            prefilled_fields=prefilled,
            unmatched_fields=unmatched,
            attached_files=attached,
            success=True,
        )

    def open_interactive_session(
        self,
        url: str,
        prefilled_fields: dict[str, str],
        file_uploads: dict[str, str] | None = None,
    ) -> BrowserSessionResult:
        """Leaves persistent browser open for human review without premature auto-close."""
        page = self._get_or_create_page(url)

        # Fields were already prefilled during prefill_form on this page;
        # ensure visible state and verify if user submitted or page navigated
        logger.info(
            "Persistent visible browser session active. Awaiting candidate review/interaction."
        )

        current_url = page.url
        is_submitted = False
        confirmation_url: str | None = None

        if "confirmation" in current_url.lower() or "thank_you" in current_url.lower():
            is_submitted = True
            confirmation_url = current_url

        return BrowserSessionResult(
            url=current_url,
            submitted=is_submitted,
            confirmation_url=confirmation_url,
            notes="Persistent interactive browser session open for candidate inspection.",
        )

    def close(self) -> None:
        """Cleanly close page, context, browser, and playwright instance."""
        if self._page is not None and not self._page.is_closed():
            try:
                self._page.close()
            except Exception:
                pass
        self._page = None

        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
        self._context = None

        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
        self._browser = None

        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
        self._playwright = None

    def __enter__(self) -> PlaywrightBrowserRunner:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
