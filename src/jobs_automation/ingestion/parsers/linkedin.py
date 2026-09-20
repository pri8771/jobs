"""LinkedIn job alert email parser."""

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


class LinkedInAlertParser(BaseAlertParser):
    def can_parse(self, email: RawEmailMessage) -> bool:
        sender = email.sender.lower()
        subject = email.subject.lower()
        return "linkedin.com" in sender and (
            "job" in subject or "alert" in subject or "opportunity" in subject
        )

    def parse(self, email: RawEmailMessage) -> list[ExtractedJobPosting]:
        postings: list[ExtractedJobPosting] = []

        if not email.body_html:
            return self._parse_text(email.body_text)

        soup = BeautifulSoup(email.body_html, "html.parser")

        # Find links pointing to job views
        job_links = soup.find_all("a", href=re.compile(r"/jobs/view/|/comm/jobs/view/"))

        seen_job_ids: set[str] = set()
        for link in job_links:
            href = link.get("href", "")
            match = re.search(r"/view/(\d+)", href)
            job_id = match.group(1) if match else None

            if job_id and job_id in seen_job_ids:
                continue
            if job_id:
                seen_job_ids.add(job_id)

            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            # Locate company and location from parent or sibling container
            container = link.find_parent("td") or link.find_parent("div")
            company = "Unknown"
            location = None
            salary_text = None

            if container:
                text_lines = [line.strip() for line in container.stripped_strings if line.strip()]
                # Typically format is [Title, Company, Location, Salary?]
                try:
                    title_idx = text_lines.index(title)
                    if title_idx + 1 < len(text_lines):
                        company = text_lines[title_idx + 1]
                    if title_idx + 2 < len(text_lines):
                        location = text_lines[title_idx + 2]
                    for line in text_lines[title_idx + 1 : title_idx + 5]:
                        if "$" in line:
                            salary_text = line
                            break
                except ValueError:
                    pass

            min_sal, max_sal, curr = parse_salary_range(salary_text or "")
            canonical_url = clean_url(href)
            if job_id:
                canonical_url = f"https://www.linkedin.com/jobs/view/{job_id}"

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
                    source_job_id=job_id,
                    requisition_id=None,
                    source_provider="linkedin",
                    description_snippet=None,
                )
            )

        return postings

    def _parse_text(self, text: str) -> list[ExtractedJobPosting]:
        postings: list[ExtractedJobPosting] = []
        matches = re.finditer(
            r"([^\n]+)\n([^\n]+)\n([^\n]+)\n(https?://[^\s]+linkedin\.com[^\s]+jobs/view/(\d+)[^\s]*)",
            text,
        )
        for m in matches:
            title, company, location, url, job_id = m.groups()
            canonical = f"https://www.linkedin.com/jobs/view/{job_id}"
            postings.append(
                ExtractedJobPosting(
                    title=title.strip(),
                    company=company.strip(),
                    location=location.strip(),
                    remote_type=detect_remote_type(f"{location} {title}"),
                    job_url=canonical,
                    source_url=url,
                    source_job_id=job_id,
                    source_provider="linkedin",
                )
            )
        return postings
