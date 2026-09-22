"""Playwright-based browser runner for form inspection and assisted application.

V1.5 safety contract implemented here:

* inspection captures the *actual* navigated destination, the owning form's action,
  labels/help/placeholder/options and an exact locator per field (F145-08);
* prefill writes only through the locators captured at inspection time, reads every
  value back from the live control, binds each upload to its unique inspected field
  and records the digest of the bytes attached (F145-09);
* the interactive session never submits and never infers a submission from URL text
  or page content (F145-10).
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from jobs_automation.browser.base import (
    BrowserRunner,
    BrowserSessionResult,
    FormField,
    FormInspectionResult,
    FormPrefillResult,
)

logger = logging.getLogger(__name__)

# Text-like controls that Playwright's fill() handles and input_value() reads back.
_FILLABLE_INPUT_TYPES = frozenset({"", "text", "email", "tel", "url", "number", "search"})

# One DOM pass that captures every semantic attribute the snapshot binds. Labels are
# resolved through label[for], the enclosing label, aria-label and aria-labelledby;
# help text through aria-describedby.
_INSPECT_FIELDS_JS = """
() => {
  const textOf = (node) => (node && node.innerText ? node.innerText : "").trim();
  const byIds = (ids) => (ids || "")
    .split(/\\s+/)
    .filter(Boolean)
    .map((id) => document.getElementById(id))
    .filter(Boolean)
    .map(textOf)
    .filter(Boolean)
    .join(" ");
  const labelFor = (el) => {
    if (el.id) {
      const explicit = document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
      if (explicit) return textOf(explicit);
    }
    const wrapping = el.closest("label");
    if (wrapping) return textOf(wrapping);
    const aria = el.getAttribute("aria-label");
    if (aria && aria.trim()) return aria.trim();
    const labelled = byIds(el.getAttribute("aria-labelledby"));
    return labelled || null;
  };
  const helpFor = (el) => byIds(el.getAttribute("aria-describedby")) || null;
  const fields = [];
  const elements = Array.from(document.querySelectorAll("input, textarea, select"));
  elements.forEach((el, index) => {
    const tag = el.tagName.toLowerCase();
    let type = tag === "textarea" ? "textarea" : tag === "select" ? "select"
      : (el.getAttribute("type") || "text").toLowerCase();
    const options = [];
    const optionValues = [];
    if (tag === "select") {
      Array.from(el.options).forEach((option) => {
        options.push(option.text.trim());
        optionValues.push(option.value);
      });
    }
    fields.push({
      index: index,
      tag: tag,
      type: type,
      id: el.id || null,
      name: el.getAttribute("name") || null,
      required: !!el.required || el.getAttribute("aria-required") === "true",
      placeholder: el.getAttribute("placeholder") || null,
      label: labelFor(el),
      help: helpFor(el),
      options: options,
      optionValues: optionValues,
      formAction: el.form ? (el.form.getAttribute("action") || "") : null,
      formId: el.form ? (el.form.getAttribute("id") || null) : null,
    });
  });
  return { fields: fields, formCount: document.querySelectorAll("form").length };
}
"""

_CONTROL_KIND_JS = (
    "el => el.tagName.toLowerCase() + ':' + ((el.getAttribute('type') || '').toLowerCase())"
)
_SELECTED_LABEL_JS = (
    "el => el.options && el.selectedIndex >= 0 ? el.options[el.selectedIndex].text.trim() : ''"
)
_FILE_READBACK_JS = (
    "el => el.files && el.files.length"
    " ? { name: el.files[0].name, size: el.files[0].size, count: el.files.length }"
    " : null"
)


def css_attribute_value(value: str) -> str:
    """Escape a string for use inside a double-quoted CSS attribute selector."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def stable_selector(
    entry: dict[str, Any], totals: dict[tuple[str, str], int], seen: dict[tuple[str, str], int]
) -> str:
    """Build the exact locator for one inspected control.

    Prefers the element id, then tag+name (disambiguated with Playwright's ``nth``
    when several controls share the same name), and finally the DOM position.
    """
    tag = str(entry.get("tag") or "input")
    element_id = entry.get("id")
    if element_id:
        return f'[id="{css_attribute_value(str(element_id))}"]'
    name = entry.get("name")
    if name:
        base = f'{tag}[name="{css_attribute_value(str(name))}"]'
        key = (tag, str(name))
        ordinal = seen.get(key, 0)
        seen[key] = ordinal + 1
        if totals.get(key, 1) == 1:
            return base
        return f"{base} >> nth={ordinal}"
    return f"{tag} >> nth={int(entry.get('index', 0))}"


class PlaywrightBrowserRunner(BrowserRunner):
    """Local visible or headless browser runner using Playwright with persistent session support."""

    def __init__(
        self,
        headless: bool = False,
        timeout_ms: int = 30000,
        user_data_dir: str | None = None,
        action_timeout_ms: int | None = None,
    ) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.user_data_dir = user_data_dir
        # Per-action timeout (fill/select/upload); None keeps Playwright's default.
        self.action_timeout_ms = action_timeout_ms
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None

    def _ensure_playwright(self) -> Any:
        try:
            import playwright.sync_api as p_sync  # type: ignore[import-not-found,unused-ignore]

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
            if self.action_timeout_ms is not None:
                self._page.set_default_timeout(self.action_timeout_ms)

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

    # ------------------------------------------------------------------ inspection

    def inspect_form(self, url: str) -> FormInspectionResult:
        """Inspect the live page; a failed inspection is reported, never treated as clean."""
        try:
            page = self._get_or_create_page(url)
            return self._inspect_loaded_page(page, url)
        except Exception as exc:
            logger.warning("Form inspection failed for %s: %s", url, type(exc).__name__)
            return FormInspectionResult(
                url=url,
                title="",
                fields=[],
                form_found=False,
                inspection_error=type(exc).__name__,
            )

    def _inspect_loaded_page(self, page: Any, url: str) -> FormInspectionResult:
        final_url = str(page.url or url)
        title = page.title()

        # Detect known ATS platforms by URL or page content
        content_lower = page.content().lower()
        url_lower = f"{url} {final_url}".lower()
        detected_ats: str | None = None
        if "greenhouse.io" in url_lower or "greenhouse" in content_lower:
            detected_ats = "greenhouse"
        elif "lever.co" in url_lower or "lever" in content_lower:
            detected_ats = "lever"
        elif "myworkdayjobs.com" in url_lower or "workday" in content_lower:
            detected_ats = "workday"
        elif "ashbyhq.com" in url_lower or "ashby" in content_lower:
            detected_ats = "ashby"

        raw = page.evaluate(_INSPECT_FIELDS_JS)
        entries: list[dict[str, Any]] = list(raw.get("fields", [])) if isinstance(raw, dict) else []
        form_count = int(raw.get("formCount", 0)) if isinstance(raw, dict) else 0

        # Count tag+name duplicates first so locators are disambiguated deterministically.
        totals: dict[tuple[str, str], int] = {}
        seen: dict[tuple[str, str], int] = {}
        for entry in entries:
            if entry.get("name") and not entry.get("id"):
                key = (str(entry.get("tag") or "input"), str(entry["name"]))
                totals[key] = totals.get(key, 0) + 1

        fields: list[FormField] = []
        has_file_upload = False
        form_action: str | None = None
        for entry in entries:
            field_type = str(entry.get("type") or "text")
            if field_type in ("hidden", "submit", "button", "reset", "image"):
                continue
            name = str(entry.get("name") or entry.get("id") or "").strip()
            if not name:
                continue
            if field_type == "file":
                has_file_upload = True
            entry_action = entry.get("formAction")
            if form_action is None and entry_action is not None:
                form_action = str(entry_action)
            fields.append(
                FormField(
                    name=name,
                    field_type=field_type,
                    label=(str(entry["label"]).strip() or None) if entry.get("label") else None,
                    placeholder=str(entry.get("placeholder") or "") or None,
                    help_text=(str(entry["help"]).strip() or None) if entry.get("help") else None,
                    selector=stable_selector(entry, totals, seen),
                    required=bool(entry.get("required")),
                    options=[str(option) for option in entry.get("options", [])],
                    option_values=[str(value) for value in entry.get("optionValues", [])],
                    form_action=str(entry_action) if entry_action is not None else None,
                    form_id=str(entry["formId"]) if entry.get("formId") else None,
                    dom_index=int(entry.get("index", 0)),
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
            final_url=final_url,
            form_action=form_action,
            form_count=form_count,
        )

    # --------------------------------------------------------------------- prefill

    def prefill_form(
        self,
        url: str,
        field_values: dict[str, str],
        file_uploads: dict[str, str] | None = None,
        targets: dict[str, str] | None = None,
    ) -> FormPrefillResult:
        page = self._get_or_create_page(url)
        locators = dict(targets or {})
        prefilled: dict[str, str] = {}
        unmatched: list[str] = []
        failed: dict[str, str] = {}
        readback: dict[str, str] = {}
        attached: dict[str, str] = {}
        digests: dict[str, str] = {}

        for name, value in field_values.items():
            selector = locators.get(name)
            if not selector:
                unmatched.append(name)
                continue
            locator = page.locator(selector)
            try:
                count = int(locator.count())
            except Exception as exc:
                failed[name] = f"locator_error:{type(exc).__name__}"
                continue
            if count != 1:
                failed[name] = f"locator_not_unique:{count}"
                continue
            try:
                kind = str(locator.evaluate(_CONTROL_KIND_JS))
                tag, _, input_type = kind.partition(":")
                if tag == "select":
                    try:
                        locator.select_option(label=value)
                    except Exception:
                        locator.select_option(value=value)
                    selected_label = str(locator.evaluate(_SELECTED_LABEL_JS))
                    observed = str(locator.input_value())
                    readback[name] = selected_label or observed
                    if selected_label == value or observed == value:
                        prefilled[name] = value
                    else:
                        failed[name] = "readback_mismatch"
                elif tag == "textarea" or (tag == "input" and input_type in _FILLABLE_INPUT_TYPES):
                    locator.fill(value)
                    observed = str(locator.input_value())
                    readback[name] = observed
                    if observed == value:
                        prefilled[name] = value
                    else:
                        failed[name] = "readback_mismatch"
                else:
                    failed[name] = f"unsupported_control:{kind}"
            except Exception as exc:
                failed[name] = f"write_failed:{type(exc).__name__}"

        for name, file_path in (file_uploads or {}).items():
            selector = locators.get(name)
            if not selector:
                unmatched.append(name)
                continue
            locator = page.locator(selector)
            try:
                count = int(locator.count())
            except Exception as exc:
                failed[name] = f"locator_error:{type(exc).__name__}"
                continue
            if count != 1:
                failed[name] = f"locator_not_unique:{count}"
                continue
            path = Path(file_path)
            if not path.is_file():
                failed[name] = "file_missing"
                continue
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            try:
                kind = str(locator.evaluate(_CONTROL_KIND_JS))
                if kind != "input:file":
                    failed[name] = f"unsupported_control:{kind}"
                    continue
                locator.set_input_files(str(path))
                observed = locator.evaluate(_FILE_READBACK_JS)
                if (
                    isinstance(observed, dict)
                    and int(observed.get("count", 0)) == 1
                    and int(observed.get("size", -1)) == len(data)
                    and str(observed.get("name")) == path.name
                ):
                    attached[name] = str(path)
                    digests[name] = digest
                    readback[name] = f"{path.name}:{len(data)}"
                else:
                    failed[name] = "upload_readback_mismatch"
            except Exception as exc:
                failed[name] = f"upload_failed:{type(exc).__name__}"

        success = not unmatched and not failed
        return FormPrefillResult(
            url=url,
            final_url=str(page.url or url),
            prefilled_fields=prefilled,
            unmatched_fields=unmatched,
            failed_fields=failed,
            readback=readback,
            attached_files=attached,
            attached_file_digests=digests,
            verified_file_hashes=dict(digests),
            success=success,
            message=(
                "Prefilled and read back successfully"
                if success
                else f"Prefill partial: failed={sorted(failed)} unmatched={sorted(unmatched)}"
            ),
        )

    # ------------------------------------------------------------------- session

    def open_interactive_session(
        self,
        url: str,
        prefilled_fields: dict[str, str],
        file_uploads: dict[str, str] | None = None,
    ) -> BrowserSessionResult:
        """Leave the persistent browser open for human review; never submit or infer submission."""
        page = self._get_or_create_page(url)
        logger.info(
            "Persistent visible browser session active. Awaiting candidate review/interaction."
        )
        return BrowserSessionResult(
            url=str(page.url or url),
            submitted=False,
            confirmation_url=None,
            notes=(
                "Prefill-to-review only: the runner performed no submit action and does not "
                "infer submission from page text or URL."
            ),
            submit_performed=False,
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
