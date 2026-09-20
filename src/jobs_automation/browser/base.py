"""Base classes and types for browser automation and form interaction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FormField(BaseModel):
    """Represents a discovered interactive form field."""

    model_config = ConfigDict(extra="forbid")

    name: str
    field_type: str = "text"  # text, email, tel, file, textarea, select, radio, checkbox
    label: str | None = None
    placeholder: str | None = None
    selector: str
    required: bool = False
    options: list[str] = Field(default_factory=list)
    current_value: str | None = None


class FormInspectionResult(BaseModel):
    """Result of inspecting an application form on a webpage."""

    model_config = ConfigDict(extra="forbid")

    url: str
    title: str
    fields: list[FormField] = Field(default_factory=list)
    has_file_upload: bool = False
    detected_ats: str | None = None  # greenhouse, lever, workday, ashby, etc.
    form_found: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class FormPrefillResult(BaseModel):
    """Result of prefilling fields in a browser form."""

    model_config = ConfigDict(extra="forbid")

    url: str
    prefilled_fields: dict[str, str] = Field(default_factory=dict)
    unmatched_fields: list[str] = Field(default_factory=list)
    attached_files: dict[str, str] = Field(default_factory=dict)
    success: bool = True
    message: str = "Prefilled successfully"


class BrowserSessionResult(BaseModel):
    """Outcome of an interactive assisted application session."""

    model_config = ConfigDict(extra="forbid")

    url: str
    submitted: bool
    confirmation_url: str | None = None
    receipt_text: str | None = None
    screenshot_path: str | None = None
    notes: str | None = None


class BrowserRunner(ABC):
    """Abstract interface for browser automation runners."""

    @abstractmethod
    def inspect_form(self, url: str) -> FormInspectionResult:
        """Inspect the destination URL and return detected form fields."""
        pass

    @abstractmethod
    def prefill_form(
        self,
        url: str,
        field_values: dict[str, str],
        file_uploads: dict[str, str] | None = None,
    ) -> FormPrefillResult:
        """Prefill detected form fields with candidate values without submitting."""
        pass

    @abstractmethod
    def open_interactive_session(
        self,
        url: str,
        prefilled_fields: dict[str, str],
        file_uploads: dict[str, str] | None = None,
    ) -> BrowserSessionResult:
        """Launch visible browser for candidate review and manual submission confirmation."""
        pass
