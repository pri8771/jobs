"""Gmail API adapter and MockEmailAdapter for testing.

V1.7 ingestion prerequisites implemented here:

* V17-M01 — bounded pagination with per-message fetch accounting. ``poll_messages`` pages
  through ``users.messages.list`` up to the caller's cap, fetches every listed message
  and records a :class:`PollReport`; a listed message that could not be fetched or a
  result truncated by the cap marks the poll incomplete.
* V17-M02 — direction is derived from the Gmail ``SENT`` label or a verified identity,
  never hard-coded; the provider-observed ``internalDate`` is the message time and the
  sender-claimed ``Date`` header is kept separately; addresses are parsed structurally.
"""

from __future__ import annotations

import base64
import datetime
import logging
from email.utils import getaddresses, parseaddr, parsedate_to_datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from jobs_automation.adapters.base import EmailAdapter
from jobs_automation.core.config import AppSettings
from jobs_automation.ingestion.models import PollReport, RawEmailMessage

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
READONLY_SCOPE = SCOPES[0]
MAX_PAGE_SIZE = 500


def normalize_address(value: str | None) -> str:
    """Lower-cased bare address from a header value; empty when none can be parsed."""
    _, address = parseaddr(value or "")
    return address.strip().lower()


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
    """Production Gmail API adapter (read-only)."""

    def __init__(
        self,
        credentials: Credentials | None = None,
        verified_identities: list[str] | None = None,
        page_size: int = 100,
        service: Any | None = None,
    ) -> None:
        if service is None:
            if credentials is None:
                oauth = GmailOAuthClient()
                credentials = oauth.get_credentials()
                if credentials is None:
                    raise RuntimeError(
                        "Gmail credentials not found. Complete OAuth setup or provide credentials."
                    )
            service = build("gmail", "v1", credentials=credentials)
        self.service: Resource = service
        self.verified_identities = {
            normalize_address(identity) for identity in (verified_identities or []) if identity
        }
        self.verified_identities.discard("")
        self.page_size = max(1, min(int(page_size), MAX_PAGE_SIZE))
        self._last_poll_report: PollReport | None = None

    def last_poll_report(self) -> PollReport | None:
        return self._last_poll_report

    def mailbox_address(self) -> str:
        """The authorized mailbox address (one profile metadata call, no message access)."""
        profile = self.service.users().getProfile(userId="me").execute()
        return normalize_address(str(profile.get("emailAddress") or ""))

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

        cap = max(0, int(max_results))
        report = PollReport(
            query=full_query or None,
            since_timestamp=since_timestamp,
            max_results=cap,
            adapter="gmail",
        )

        stubs: list[dict[str, Any]] = []
        page_token: str | None = None
        more_available = False
        while len(stubs) < cap:
            request_kwargs: dict[str, Any] = {
                "userId": "me",
                "q": full_query,
                "maxResults": min(self.page_size, cap - len(stubs)),
            }
            if page_token:
                request_kwargs["pageToken"] = page_token
            results = self.service.users().messages().list(**request_kwargs).execute()
            report.pages_fetched += 1
            if not isinstance(results, dict):
                report.missing_message_ids.append("<malformed-listing>")
                break

            raw_page = results.get("messages", [])
            if raw_page is None:
                raw_page = []
            if not isinstance(raw_page, list):
                report.missing_message_ids.append("<malformed-listing>")
                break

            page: list[dict[str, Any]] = []
            for item in raw_page:
                if not isinstance(item, dict):
                    report.missing_message_ids.append("<malformed-listing>")
                    continue
                page.append(item)

            remaining = cap - len(stubs)
            if len(page) > remaining:
                # Treat a provider response that exceeds the requested cap as a
                # truncation too.  We must not ingest an arbitrary prefix as though
                # it were a complete evidence set.
                stubs.extend(page[:remaining])
                report.truncated_by_cap = True
                break
            stubs.extend(page)

            token_value = results.get("nextPageToken")
            if token_value is not None and not isinstance(token_value, str):
                report.missing_message_ids.append("<malformed-listing>")
                break
            page_token = token_value or None
            if not page_token:
                more_available = False
                break
            if not page:
                # A continuation token without any listed records cannot be safely
                # interpreted and would otherwise risk an endless loop.
                report.missing_message_ids.append("<malformed-listing>")
                break
            more_available = True
        if more_available and len(stubs) >= cap:
            report.truncated_by_cap = True

        report.listed_count = len(stubs)
        messages: list[RawEmailMessage] = []
        for stub in stubs:
            msg_id = str(stub.get("id") or "")
            if not msg_id:
                report.missing_message_ids.append("<listed-without-id>")
                continue
            raw_msg = self.get_message(msg_id)
            if raw_msg is None:
                report.missing_message_ids.append(msg_id)
                continue
            if raw_msg.provider_message_id != msg_id:
                # The payload belongs to a different provider record than the one
                # admitted by the listing.  Do not let it substitute for the listed
                # evidence or enter the database under the wrong identifier.
                report.missing_message_ids.append("<payload-id-mismatch>")
                continue
            messages.append(raw_msg)
        report.fetched_count = len(messages)
        report.complete = not report.truncated_by_cap and not report.missing_message_ids
        self._last_poll_report = report
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
        except Exception as exc:
            logger.warning(
                "Gmail message %s could not be fetched (%s); poll will be marked incomplete.",
                message_id,
                type(exc).__name__,
            )
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
        msg_id = str(data.get("id", ""))
        thread_id = str(data.get("threadId", ""))
        try:
            internal_date_ms = int(data.get("internalDate", "0"))
        except (TypeError, ValueError):
            internal_date_ms = 0
        # Provider-observed time is the message time (V17-M02).
        received_at = datetime.datetime.fromtimestamp(internal_date_ms / 1000.0, tz=datetime.UTC)

        payload = data.get("payload", {}) or {}
        headers_list = payload.get("headers", []) or []
        headers: dict[str, Any] = {}
        for header in headers_list:
            if isinstance(header, dict):
                name = str(header.get("name", ""))
                if name:
                    headers[name] = str(header.get("value", ""))

        sender_header = str(headers.get("From", "") or "unknown")
        sender_address = normalize_address(sender_header)
        recipient_headers = [str(headers.get(key, "")) for key in ("To", "Cc") if headers.get(key)]
        recipients = [
            address.strip().lower()
            for _, address in getaddresses(recipient_headers)
            if address and address.strip()
        ]
        subject = str(headers.get("Subject", "(No Subject)") or "(No Subject)")

        # The sender-claimed Date header is recorded separately; it never replaces the
        # provider time, so a forged future Date cannot move a checkpoint.
        claimed_date: datetime.datetime | None = None
        if headers.get("Date"):
            try:
                parsed_dt = parsedate_to_datetime(str(headers["Date"]))
                if parsed_dt.tzinfo is None:
                    parsed_dt = parsed_dt.replace(tzinfo=datetime.UTC)
                claimed_date = parsed_dt.astimezone(datetime.UTC)
            except Exception:
                claimed_date = None

        label_ids = [str(label) for label in (data.get("labelIds") or [])]
        sent_label = "SENT" in label_ids
        identity_match = bool(sender_address) and sender_address in self.verified_identities
        if sent_label:
            direction, basis = "outbound", "gmail_sent_label"
        elif identity_match:
            direction, basis = "outbound", "verified_identity"
        else:
            direction, basis = "inbound", "inbound_default"

        body_text, body_html = self._extract_parts(payload)

        provider_metadata: dict[str, Any] = {
            "provider": "gmail",
            "label_ids": label_ids,
            "internal_date_utc": received_at.isoformat(),
            "claimed_date_utc": claimed_date.isoformat() if claimed_date else None,
            "claimed_date_skew_seconds": (
                (claimed_date - received_at).total_seconds() if claimed_date else None
            ),
            "direction_basis": basis,
            "sender_address": sender_address,
            "identity_verified": identity_match,
        }

        return RawEmailMessage(
            provider_message_id=msg_id,
            provider_thread_id=thread_id,
            received_at=received_at,
            sender=sender_header,
            recipients=recipients,
            direction=direction,
            subject=subject,
            headers=headers,
            body_text=body_text,
            body_html=body_html,
            raw_reference=None,
            provider_metadata=provider_metadata,
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


def _mock_query_epoch(value: str) -> datetime.datetime | None:
    """Interpret a Gmail ``before:``/``after:`` value (epoch seconds or YYYY/MM/DD)."""
    try:
        if value.isdigit():
            return datetime.datetime.fromtimestamp(int(value), tz=datetime.UTC)
        return datetime.datetime.strptime(value, "%Y/%m/%d").replace(tzinfo=datetime.UTC)
    except (ValueError, OverflowError, OSError):
        return None


def _mock_query_matches(query: str, message: RawEmailMessage) -> bool:
    """Approximate Gmail search semantics for the synthetic adapter.

    ``before:``/``after:``/``older:``/``newer:`` bound ``received_at``; ``from:`` and
    ``subject:`` match their field; other operators (``label:``, ``in:``, ``is:``,
    ``newer_than:`` ...) cannot be emulated on fixtures and are ignored; bare terms must
    each appear in the subject, body or sender.
    """
    for token in query.split():
        operator, sep, value = token.partition(":")
        operator = operator.lower()
        value = value.strip('"').lower()
        if not sep:
            term = token.strip('"').lower()
            if not (
                term in message.subject.lower()
                or term in message.body_text.lower()
                or term in message.sender.lower()
            ):
                return False
        elif operator in {"before", "older"}:
            bound = _mock_query_epoch(value)
            if bound is not None and message.received_at >= bound:
                return False
        elif operator in {"after", "newer"}:
            bound = _mock_query_epoch(value)
            if bound is not None and message.received_at < bound:
                return False
        elif operator == "from":
            if value not in message.sender.lower():
                return False
        elif operator == "subject":
            if value not in message.subject.lower():
                return False
    return True


class MockEmailAdapter(EmailAdapter):
    """Fixture-driven mock adapter for testing (synthetic; never genuine recruiting evidence)."""

    def __init__(self, messages: list[RawEmailMessage] | None = None) -> None:
        self.messages: list[RawEmailMessage] = messages or []
        self._last_poll_report: PollReport | None = None

    def last_poll_report(self) -> PollReport | None:
        return self._last_poll_report

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
            filtered = [m for m in filtered if _mock_query_matches(query, m)]

        selected = filtered[:max_results]
        self._last_poll_report = PollReport(
            query=query,
            since_timestamp=since_timestamp,
            max_results=max_results,
            pages_fetched=1,
            listed_count=len(filtered),
            fetched_count=len(selected),
            truncated_by_cap=len(filtered) > max_results,
            complete=len(filtered) <= max_results,
            adapter="mock_fixtures",
            synthetic=True,
        )
        return selected

    def get_thread(self, thread_id: str) -> list[RawEmailMessage]:
        thread = [m for m in self.messages if m.provider_thread_id == thread_id]
        thread.sort(key=lambda m: m.received_at)
        return thread
