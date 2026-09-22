#!/usr/bin/env python3
"""Import the live V1.4 proof job from Greenhouse's public Job Board API.

This is a non-consequential read-only public-data import. It does not open or
submit an application. It writes the real Job/JobSource into the configured
Jobs database and writes the live screening-question labels to a gitignored
.local/proofs file for the V1.4 packet proof.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from sqlalchemy import select

from jobs_automation.db.models import CompanyModel, JobModel, JobSourceModel
from jobs_automation.db.session import get_sessionmaker
from jobs_automation.ingestion.parsers.base import detect_remote_type
from jobs_automation.preparation.packet_builder import compute_questions_sha256

DEFAULT_BOARD_TOKEN = "opensesame"
DEFAULT_JOB_ID = "7967740"
DEFAULT_JOB_URL = "https://job-boards.greenhouse.io/opensesame/jobs/7967740?gh_jid=7967740"
DEFAULT_EXPECTED_TITLE = "AI Automation Engineer"
DEFAULT_COMPANY_NAME = "OpenSesame"
DEFAULT_COMPANY_DOMAIN = "opensesame.com"

STANDARD_LABEL_PREFIXES = (
    "first name",
    "last name",
    "preferred first name",
    "email",
    "phone",
    "location",
    "country",
    "resume",
    "cv",
    "cover letter",
    "linkedin",
    "website",
)


class ProofJobImportError(Exception):
    """Raised when the live public proof job cannot be validated/imported."""


def _fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "jobs-automation-real-proof/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProofJobImportError(f"Greenhouse public API request failed: {exc}") from exc

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProofJobImportError("Greenhouse response was not valid UTF-8 JSON") from exc

    if not isinstance(data, dict):
        raise ProofJobImportError("Greenhouse response must be a JSON object")
    return data


def _html_to_text(value: Any) -> str:
    html = str(value or "")
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    return unescape(text)


def _normalize_label(value: Any) -> str:
    text = _html_to_text(value)
    return re.sub(r"\s+", " ", text).strip().rstrip("*").strip()


def _is_standard_question(label: str) -> bool:
    lowered = label.lower()
    return any(lowered.startswith(prefix) for prefix in STANDARD_LABEL_PREFIXES)


def _extract_screening_questions(payload: dict[str, Any]) -> list[str]:
    questions_raw = payload.get("questions", [])
    if not isinstance(questions_raw, list):
        raise ProofJobImportError("Greenhouse 'questions' field is not an array")

    labels: list[str] = []
    seen: set[str] = set()
    for question in questions_raw:
        if not isinstance(question, dict):
            continue
        label = _normalize_label(question.get("label"))
        if not label or _is_standard_question(label):
            continue
        normalized = label.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        labels.append(label)

    if not labels:
        raise ProofJobImportError(
            "No non-standard application questions were returned by Greenhouse"
        )
    return labels


def _source_payload(job_payload: dict[str, Any], api_url: str) -> dict[str, Any]:
    content_text = _html_to_text(job_payload.get("content"))
    questions = _extract_screening_questions(job_payload)
    return {
        "api_url": api_url,
        "fetched_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "content_sha256": hashlib.sha256(content_text.encode("utf-8")).hexdigest(),
        "screening_question_count": len(questions),
        "question_list_sha256": compute_questions_sha256(questions),
        "source_kind": "greenhouse_public_job_board_api",
        "provider": "GREENHOUSE",
        "public_job_id": str(job_payload.get("id", "")),
    }


def _validated_job_fields(
    payload: dict[str, Any], *, job_id: str, expected_title: str
) -> tuple[str, str, str]:
    """Return (title, location, content text) only for the exact expected public posting."""
    returned_id = str(payload.get("id", ""))
    if returned_id != str(job_id):
        raise ProofJobImportError(
            f"Greenhouse returned job ID {returned_id!r}, expected {job_id!r}"
        )

    title = str(payload.get("title") or "").strip()
    if not title:
        raise ProofJobImportError("Greenhouse job has no title")

    expected = expected_title.strip()
    if not expected:
        raise ProofJobImportError("An expected proof-job title is required")
    if title.casefold() != expected.casefold():
        raise ProofJobImportError(f"Unexpected proof-job title: {title!r}; expected {expected!r}")

    location_obj = payload.get("location")
    location = ""
    if isinstance(location_obj, dict):
        location = str(location_obj.get("name") or "").strip()

    content_text = _html_to_text(payload.get("content"))
    if len(content_text) < 500:
        raise ProofJobImportError("Greenhouse job content is unexpectedly short")
    return title, location, content_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board-token", default=DEFAULT_BOARD_TOKEN)
    parser.add_argument("--job-id", default=DEFAULT_JOB_ID)
    parser.add_argument("--job-url", default=DEFAULT_JOB_URL)
    parser.add_argument(
        "--expected-title",
        default=DEFAULT_EXPECTED_TITLE,
        help="Exact public posting title the operator selected (case-insensitive match).",
    )
    parser.add_argument("--company-name", default=DEFAULT_COMPANY_NAME)
    parser.add_argument("--company-domain", default=DEFAULT_COMPANY_DOMAIN)
    parser.add_argument(
        "--questions-output",
        type=Path,
        default=Path(".local/proofs/opensesame_7967740_questions.json"),
    )
    args = parser.parse_args()

    api_url = (
        f"https://boards-api.greenhouse.io/v1/boards/{args.board_token}/jobs/"
        f"{args.job_id}?questions=true"
    )

    try:
        payload = _fetch_json(api_url)

        title, location, content_text = _validated_job_fields(
            payload, job_id=str(args.job_id), expected_title=args.expected_title
        )

        questions = _extract_screening_questions(payload)
        description_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
        source_payload = _source_payload(payload, api_url)

        session_factory = get_sessionmaker()
        with session_factory() as session:
            company = session.scalar(
                select(CompanyModel).where(CompanyModel.normalized_name == args.company_name)
            )
            if company is None:
                company = CompanyModel(
                    normalized_name=args.company_name,
                    domain=args.company_domain,
                )
                session.add(company)
                session.flush()

            existing_source = session.scalar(
                select(JobSourceModel).where(
                    JobSourceModel.provider == "GREENHOUSE",
                    JobSourceModel.source_job_id == str(args.job_id),
                )
            )

            now = datetime.datetime.now(datetime.UTC)

            if existing_source is not None:
                job = existing_source.job
                if job is None:
                    raise ProofJobImportError("Existing Greenhouse source has no linked JobModel")
                job.company_id = company.id
                job.normalized_title = title
                job.location_text = location or job.location_text
                job.remote_type = "remote" if "remote" in location.casefold() else job.remote_type
                job.description_text = content_text
                job.description_hash = description_hash
                job.last_seen_at = now
                job.status = "active"

                existing_source.source_url = args.job_url
                existing_source.canonical_apply_url = args.job_url
                existing_source.source_payload_json = source_payload
                existing_source.last_seen_at = now
            else:
                job = JobModel(
                    company_id=company.id,
                    normalized_title=title,
                    location_text=location or "Remote, US",
                    # Unstated location keeps the historical remote default; otherwise
                    # classify the posted location instead of asserting remote.
                    remote_type=detect_remote_type(location) if location else "remote",
                    description_text=content_text,
                    description_hash=description_hash,
                    first_seen_at=now,
                    last_seen_at=now,
                    status="active",
                )
                session.add(job)
                session.flush()

                source = JobSourceModel(
                    job_id=job.id,
                    provider="GREENHOUSE",
                    source_job_id=str(args.job_id),
                    source_url=args.job_url,
                    canonical_apply_url=args.job_url,
                    requisition_id=str(args.job_id),
                    source_payload_json=source_payload,
                    first_seen_at=now,
                    last_seen_at=now,
                )
                session.add(source)

            session.commit()
            job_uuid = str(job.id)

        args.questions_output.parent.mkdir(parents=True, exist_ok=True)
        args.questions_output.write_text(
            json.dumps(questions, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        print("REAL_PROOF_JOB_IMPORT_PASS")
        print(f"job_id={job_uuid}")
        print(f"greenhouse_job_id={args.job_id}")
        print(f"job_url={args.job_url}")
        print(f"title={title}")
        print(f"location={location or 'Remote, US'}")
        print(f"description_sha256={description_hash}")
        print(f"questions_count={len(questions)}")
        print(f"questions_output={args.questions_output}")
        return 0
    except (OSError, ValueError, ProofJobImportError) as exc:
        print(f"REAL_PROOF_JOB_IMPORT_FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
