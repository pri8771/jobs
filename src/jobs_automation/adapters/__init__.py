"""Adapter implementations and interfaces."""

from jobs_automation.adapters.base import ATSAdapter, EmailAdapter, ModelGateway
from jobs_automation.adapters.gmail import GmailAdapter, GmailOAuthClient, MockEmailAdapter
from jobs_automation.adapters.models import LiteLLMModelGateway, MockModelGateway

__all__ = [
    "ATSAdapter",
    "EmailAdapter",
    "GmailAdapter",
    "GmailOAuthClient",
    "LiteLLMModelGateway",
    "MockEmailAdapter",
    "MockModelGateway",
    "ModelGateway",
]
