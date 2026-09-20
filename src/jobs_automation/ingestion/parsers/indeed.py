"""Indeed job alert email parser."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from jobs_automation.ingestion.models import ExtractedJobPosting, RawEmailMessage
from jobs_automation.ingestion.parsers.base import (
    BaseAlertParser,
    clean_url,
    detect_remote_type,
    parse_salary_range,
)


class IndeedAlertParser(BaseAlertParser):
    def can_parse(self, email: RawEmailMessage) -> bool:
        sender = email.sender.lower()
        subject = email.subject.lower()
        return "indeed.com" in sender and (
            "job" in subject or "alert" in subject or "new" in subject
        )

    def parse(self, email: RawEmailMessage) -> list[ExtractedJobPosting]:
        postings: list[ExtractedJobPosting] = []

        if not email.body_html:
            return self._parse_text(email.body_text)

        soup = BeautifulSoup(email.body_html, "html.parser")

        # Find links pointing to job views (either /rc/clk or jk= parameter or /viewjob)
        job_links = soup.find_all("a", href=re.compile(r"jk=[a-f0-9]+|/viewjob|/rc/clk"))

        seen_job_keys: set[str] = set()
        for link in job_links:
            href = link.get("href", "")
            # Extract job key (jk)
            jk_match = re.search(r"jk=([a-f0-9]+)", href)
            job_key = jk_match.group(1) if jk_match else None

            if not job_key:
                # Check URL query param
                parsed = urlparse(href)
                params = parse_qs(parsed.query)
                if "jk" in params:
                    job_key = params["jk"][0]

            if job_key and job_key in seen_job_keys:
                continue
            if job_key:
                seen_job_keys.add(job_key)

            title = link.get_text(strip=True)
            if not title or len(title) < 3 or title.lower() in {"view job", "apply now", "indeed"}:
                continue

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
            canonical_url = clean_url(href)
            if job_key:
                canonical_url = f"https://www.indeed.com/viewjob?jk={job_key}"

            postings.append(
                ExtractedJobPosting(
                    title=title,
                    company=company,
                    location=location,
                    remote_type=detect_remote_type(f"{location or ''} {title}"),
                    compensation_min=min_sal,
                    compensation_max=max_sal,
                    compensation_currency=curr,
                    job_url=canonical_url,
                    source_url=href,
                    source_job_id=job_key,
                    source_provider="indeed",
                    description_snippet=None,
                )
            )

        return postings

    def _parse_text(self, text: str) -> list[ExtractedJobPosting]:
        postings: list[ExtractedJobPosting] = []
        matches = re.finditer(
            r"([^\n]+)\n([^\n]+)\n([^\n]+)\n(https?://[^\s]+indeed\.com[^\s]+jk=([a-f0-9]+)[^\s]*)",
            text,
        )
        for m in matches:
            title, company, location, url, job_key = m.groups()
            canonical = f"https://www.indeed.com/viewjob?jk={job_key}"
            postings.append(
                ExtractedJobPosting(
                    title=title.strip(),
                    company=company.strip(),
                    location=location.strip(),
                    remote_type=detect_remote_type(f"{location} {title}"),
                    job_url=canonical,
                    source_url=url,
                    source_job_id=job_key,
                    source_provider="indeed",
                )
            )
        return postings
