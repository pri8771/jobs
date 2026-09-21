"""Adapter implementations and interfaces."""

from jobs_automation.adapters.base import ATSAdapter, EmailAdapter, ModelGateway
from jobs_automation.adapters.gmail import GmailAdapter, GmailOAuthClient, MockEmailAdapter
from jobs_automation.adapters.models import (
    DeterministicModelGateway,
    LiteLLMModelGateway,
    MockModelGateway,
)

__all__ = [
    "ATSAdapter",
    "DeterministicModelGateway",
    "EmailAdapter",
    "GmailAdapter",
    "GmailOAuthClient",
    "LiteLLMModelGateway",
    "MockEmailAdapter",
    "MockModelGateway",
    "ModelGateway",
]
