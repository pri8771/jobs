"""Adapter implementations and interfaces."""

from jobs_automation.adapters.base import ATSAdapter, EmailAdapter, ModelGateway
from jobs_automation.adapters.gmail import GmailAdapter, GmailOAuthClient, MockEmailAdapter

__all__ = [
    "ATSAdapter",
    "EmailAdapter",
    "GmailAdapter",
    "GmailOAuthClient",
    "MockEmailAdapter",
    "ModelGateway",
]
