"""Generic fallback job alert email parser."""

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


class GenericAlertParser(BaseAlertParser):
    def can_parse(self, email: RawEmailMessage) -> bool:
        # Fallback parser can parse any email that looks like an alert
        sub = email.subject.lower()
        return "job" in sub or "alert" in sub or "career" in sub or "opening" in sub

    def parse(self, email: RawEmailMessage) -> list[ExtractedJobPosting]:
        postings: list[ExtractedJobPosting] = []

        if not email.body_html:
            return self._parse_text(email.body_text)

        soup = BeautifulSoup(email.body_html, "html.parser")
        job_pattern = re.compile(
            r"greenhouse\.io|lever\.co|ashbyhq\.com|myworkdayjobs\.com|smartrecruiters\.com|/jobs/|/careers/|/position/",
            re.IGNORECASE,
        )
        links = soup.find_all("a", href=job_pattern)

        seen_urls: set[str] = set()
        for link in links:
            href = link.get("href", "")
            title = link.get_text(strip=True)
            if (
                not title
                or len(title) < 4
                or title.lower() in {"apply now", "view job", "read more"}
            ):
                continue

            cleaned = clean_url(href)
            if cleaned in seen_urls:
                continue
            seen_urls.add(cleaned)

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
                    job_url=cleaned,
                    source_url=href,
                    source_provider="generic",
                    description_snippet=None,
                )
            )

        return postings

    def _parse_text(self, text: str) -> list[ExtractedJobPosting]:
        postings: list[ExtractedJobPosting] = []
        matches = re.finditer(
            r"([^\n]+)\n([^\n]+)\n(https?://[^\s]+(?:greenhouse|lever|ashby|workday|careers|jobs)[^\s]*)",
            text,
            re.IGNORECASE,
        )
        for m in matches:
            title, company, url = m.groups()
            cleaned = clean_url(url)
            postings.append(
                ExtractedJobPosting(
                    title=title.strip(),
                    company=company.strip(),
                    job_url=cleaned,
                    source_url=url,
                    source_provider="generic",
                )
            )
        return postings
