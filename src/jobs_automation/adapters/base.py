"""Abstract interfaces and protocols for replaceable integrations."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jobs_automation.ingestion.models import RawEmailMessage


class EmailMessagePayload(ABC):
    """Normalized payload from an email provider."""


class EmailAdapter(ABC):
    """Abstract interface for email ingestion providers (e.g. Gmail API)."""

    @abstractmethod
    def poll_messages(
        self,
        query: str | None = None,
        since_timestamp: str | None = None,
        max_results: int = 100,
    ) -> list[RawEmailMessage]:
        """Fetch messages matching query with checkpoint window."""

    @abstractmethod
    def get_thread(self, thread_id: str) -> list[RawEmailMessage]:
        """Fetch complete chronological thread history."""


class ModelGateway(ABC):
    """Abstract interface for LLM operations (LiteLLM-compatible)."""

    @abstractmethod
    def complete(
        self,
        task: str,
        prompt: str,
        system_prompt: str | None = None,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a completion task routed through configured models."""


class ATSAdapter(ABC):
    """Abstract interface for employer careers and ATS destinations."""

    @abstractmethod
    def inspect_destination(self, url: str) -> dict[str, Any]:
        """Inspect form fields, requirements, and policy compliance."""

    @abstractmethod
    def prepare_application(self, packet_id: uuid.UUID, destination_url: str) -> dict[str, Any]:
        """Prepare and validate form values without submitting."""
