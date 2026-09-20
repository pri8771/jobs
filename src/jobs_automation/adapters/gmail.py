"""Gmail API adapter and MockEmailAdapter for testing."""

from __future__ import annotations

import base64
import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from jobs_automation.adapters.base import EmailAdapter
from jobs_automation.core.config import AppSettings
from jobs_automation.ingestion.models import RawEmailMessage

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailOAuthClient:
    """Manages Google OAuth 2.0 credentials for read-only Gmail access."""

    def __init__(self, token_path: str | Path | None = None) -> None:
        settings = AppSettings()
        self.token_path = Path(token_path or settings.gmail_token_path)
        self.client_id = settings.gmail_client_id
        self.client_secret = settings.gmail_client_secret

    def get_credentials(self, allow_interactive: bool = False) -> Credentials | None:
        creds: Credentials | None = None

        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_path, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
            except Exception:
                creds = None

        if not creds and allow_interactive and self.client_id and self.client_secret:
            client_config = {
                "installed": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

        return creds


class GmailAdapter(EmailAdapter):
    """Production Gmail API adapter."""

    def __init__(self, credentials: Credentials | None = None) -> None:
        if credentials is None:
            oauth = GmailOAuthClient()
            credentials = oauth.get_credentials()
            if credentials is None:
                raise RuntimeError(
                    "Gmail credentials not found. Complete OAuth setup or provide credentials."
                )
        self.service: Resource = build("gmail", "v1", credentials=credentials)

    def poll_messages(
        self,
        query: str | None = None,
        since_timestamp: str | None = None,
        max_results: int = 100,
    ) -> list[RawEmailMessage]:
        full_query = query or ""
        if since_timestamp:
            try:
                dt = datetime.datetime.fromisoformat(since_timestamp)
                epoch = int(dt.timestamp())
                full_query = f"after:{epoch} {full_query}".strip()
            except ValueError:
                pass

        results = (
            self.service.users()
            .messages()
            .list(userId="me", q=full_query, maxResults=max_results)
            .execute()
        )
        msg_stubs = results.get("messages", [])

        messages: list[RawEmailMessage] = []
        for stub in msg_stubs:
            msg_id = stub.get("id")
            if msg_id:
                raw_msg = self.get_message(msg_id)
                if raw_msg:
                    messages.append(raw_msg)
        return messages

    def get_message(self, message_id: str) -> RawEmailMessage | None:
        try:
            data = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            return self._parse_gmail_message_payload(data)
        except Exception:
            return None

    def get_thread(self, thread_id: str) -> list[RawEmailMessage]:
        try:
            thread_data = (
                self.service.users()
                .threads()
                .get(userId="me", id=thread_id, format="full")
                .execute()
            )
            messages_data = thread_data.get("messages", [])
            messages: list[RawEmailMessage] = []
            for d in messages_data:
                parsed = self._parse_gmail_message_payload(d)
                if parsed:
                    messages.append(parsed)
            # Sort chronologically
            messages.sort(key=lambda m: m.received_at)
            return messages
        except Exception:
            return []

    def _parse_gmail_message_payload(self, data: dict[str, Any]) -> RawEmailMessage:
        msg_id = data.get("id", "")
        thread_id = data.get("threadId", "")
        internal_date_ms = int(data.get("internalDate", "0"))
        received_at = datetime.datetime.fromtimestamp(internal_date_ms / 1000.0, tz=datetime.UTC)

        payload = data.get("payload", {})
        headers_list = payload.get("headers", [])
        headers = {h.get("name", ""): h.get("value", "") for h in headers_list}

        sender = headers.get("From", "unknown")
        recipients_str = headers.get("To", "")
        recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]
        subject = headers.get("Subject", "(No Subject)")

        # Date header fallback if needed
        if "Date" in headers:
            try:
                parsed_dt = parsedate_to_datetime(headers["Date"])
                if parsed_dt.tzinfo is None:
                    parsed_dt = parsed_dt.replace(tzinfo=datetime.UTC)
                received_at = parsed_dt.astimezone(datetime.UTC)
            except Exception:
                pass

        body_text, body_html = self._extract_parts(payload)

        return RawEmailMessage(
            provider_message_id=msg_id,
            provider_thread_id=thread_id,
            received_at=received_at,
            sender=sender,
            recipients=recipients,
            direction="inbound",
            subject=subject,
            headers=headers,
            body_text=body_text,
            body_html=body_html,
            raw_reference=None,
        )

    def _extract_parts(self, payload: dict[str, Any]) -> tuple[str, str | None]:
        body_text = ""
        body_html: str | None = None

        def walk_parts(part: dict[str, Any]) -> None:
            nonlocal body_text, body_html
            mime = part.get("mimeType", "")
            data_str = part.get("body", {}).get("data")
            if data_str:
                decoded = base64.urlsafe_b64decode(data_str).decode("utf-8", errors="replace")
                if mime == "text/plain":
                    body_text += decoded
                elif mime == "text/html":
                    body_html = decoded

            for subpart in part.get("parts", []):
                walk_parts(subpart)

        walk_parts(payload)
        return body_text, body_html


class MockEmailAdapter(EmailAdapter):
    """Fixture-driven mock adapter for testing."""

    def __init__(self, messages: list[RawEmailMessage] | None = None) -> None:
        self.messages: list[RawEmailMessage] = messages or []

    def poll_messages(
        self,
        query: str | None = None,
        since_timestamp: str | None = None,
        max_results: int = 100,
    ) -> list[RawEmailMessage]:
        filtered = self.messages
        if since_timestamp:
            try:
                since_dt = datetime.datetime.fromisoformat(since_timestamp)
                filtered = [m for m in filtered if m.received_at >= since_dt]
            except ValueError:
                pass

        if query:
            q_lower = query.lower()
            filtered = [
                m
                for m in filtered
                if q_lower in m.subject.lower()
                or q_lower in m.body_text.lower()
                or q_lower in m.sender.lower()
            ]

        return filtered[:max_results]

    def get_thread(self, thread_id: str) -> list[RawEmailMessage]:
        thread = [m for m in self.messages if m.provider_thread_id == thread_id]
        thread.sort(key=lambda m: m.received_at)
        return thread
