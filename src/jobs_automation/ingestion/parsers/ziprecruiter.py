"""ZipRecruiter job alert email parser."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from jobs_automation.ingestion.models import ExtractedJobPosting, RawEmailMessage
from jobs_automation.ingestion.parsers.base import (
    BaseAlertParser,
    clean_url,
    detect_remote_type,
    parse_salary_range,
)


class ZipRecruiterAlertParser(BaseAlertParser):
    def can_parse(self, email: RawEmailMessage) -> bool:
        sender = email.sender.lower()
        subject = email.subject.lower()
        return "ziprecruiter.com" in sender and (
            "job" in subject or "alert" in subject or "match" in subject
        )

    def parse(self, email: RawEmailMessage) -> list[ExtractedJobPosting]:
        postings: list[ExtractedJobPosting] = []

        if not email.body_html:
            return self._parse_text(email.body_text)

        soup = BeautifulSoup(email.body_html, "html.parser")
        job_links = soup.find_all("a", href=re.compile(r"/jobs/|/k/|/c/|ziprecruiter\.com/job/"))

        seen_urls: set[str] = set()
        for link in job_links:
            href = link.get("href", "")
            title = link.get_text(strip=True)
            if (
                not title
                or len(title) < 3
                or title.lower() in {"view job", "apply now", "1-click apply"}
            ):
                continue

            clean = clean_url(href)
            if clean in seen_urls:
                continue
            seen_urls.add(clean)

            # Extract job id if present
            job_id_match = re.search(r"/job/([a-zA-Z0-9_-]+)", href)
            job_id = job_id_match.group(1) if job_id_match else None

            container = link.find_parent("td") or link.find_parent("div")
            company = "Unknown"
            location = None
            salary_text = None

            if container:
                text_lines = [line.strip() for line in container.stripped_strings if line.strip()]
                try:
                    title_idx = text_lines.index(title)
                    if title_idx + 1 < len(text_lines):
                        company = text_lines[title_idx + 1]
                    if title_idx + 2 < len(text_lines):
                        location = text_lines[title_idx + 2]
                    for line in text_lines[title_idx + 1 : title_idx + 6]:
                        if "$" in line:
                            salary_text = line
                            break
                except ValueError:
                    pass

            min_sal, max_sal, curr = parse_salary_range(salary_text or "")

            postings.append(
                ExtractedJobPosting(
                    title=title,
                    company=company,
                    location=location,
                    remote_type=detect_remote_type(f"{location or ''} {title}"),
                    compensation_min=min_sal,
                    compensation_max=max_sal,
                    compensation_currency=curr,
                    job_url=clean,
                    source_url=href,
                    source_job_id=job_id,
                    source_provider="ziprecruiter",
                    description_snippet=None,
                )
            )

        return postings

    def _parse_text(self, text: str) -> list[ExtractedJobPosting]:
        postings: list[ExtractedJobPosting] = []
        matches = re.finditer(
            r"([^\n]+)\n([^\n]+)\n([^\n]+)\n(https?://[^\s]+ziprecruiter\.com[^\s]+)",
            text,
        )
        for m in matches:
            title, company, location, url = m.groups()
            canonical = clean_url(url)
            postings.append(
                ExtractedJobPosting(
                    title=title.strip(),
                    company=company.strip(),
                    location=location.strip(),
                    remote_type=detect_remote_type(f"{location} {title}"),
                    job_url=canonical,
                    source_url=url,
                    source_provider="ziprecruiter",
                )
            )
        return postings
