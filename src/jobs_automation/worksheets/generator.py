"""Profile setup worksheet and platform checklist generator."""

from __future__ import annotations

from pathlib import Path

from jobs_automation.core.candidate_profile import CandidateProfileConfig
from jobs_automation.core.job_search import JobSearchConfig


class ProfileWorksheetGenerator:
    """Generates structured Markdown setup checklists for LinkedIn, Indeed, ZipRecruiter, and Dice

    grounded in docs/CANDIDATE_POSITIONING.md and the candidate profile config.
    """

    def __init__(self, profile: CandidateProfileConfig, job_search: JobSearchConfig) -> None:
        self.profile = profile
        self.job_search = job_search

    def generate_markdown(self) -> str:
        lines: list[str] = [
            "# Candidate Profile Setup & Verification Worksheet",
            "",
            "> **Purpose**: Single authoritative guide for configuring and verifying candidate profiles",
            "> across LinkedIn, Indeed, ZipRecruiter, and Dice without improvising inconsistent facts.",
            "",
            "## 1. Candidate Core Positioning",
            "",
            f"- **Candidate Name**: {self.profile.identity.full_name} ({self.profile.identity.preferred_name or self.profile.identity.full_name})",
            f"- **Location**: {self.profile.identity.city}, {self.profile.identity.state} (Target: Pittsburgh + US Remote)",
            f"- **Primary Headline**: `{self.profile.target.primary_headline}`",
            f"- **Target Compensation**: ${self.profile.target.target_compensation_usd_min:,}+ USD ({self.profile.target.compensation_basis})",
            f"- **Resume Strategy**: `{self.profile.resume.strategy}` (Default: `{self.profile.resume.default_resume_id}`)",
            "",
            "### Positioning Guardrails",
            f"- **Summary**: {self.profile.positioning.summary}",
            "- **Differentiators**:",
        ]
        for diff in self.profile.positioning.differentiators:
            lines.append(f"  - {diff}")
        lines.append("- **Avoid Positioning As**:")
        for avoid in self.profile.positioning.avoid_positioning_as:
            lines.append(f"  - ⛔ {avoid}")

        lines.extend(
            [
                "",
                "### Targeted Resume Tracks",
                "",
                "| Priority | Resume Track ID | Core Focus & Keywords |",
                "|---|---|---|",
            ]
        )
        for rv in self.profile.resume.recommended_versions:
            focus = ", ".join(rv.emphasize)
            lines.append(f"| {rv.priority} | `{rv.id}` | {focus} |")

        # Unknown / Unresolved Facts
        unresolved = self.profile.check_unresolved_facts()
        has_unresolved = any(len(items) > 0 for items in unresolved.values())
        if has_unresolved:
            lines.extend(
                [
                    "",
                    "### ⚠️ Unresolved Facts (DO NOT FABRICATE)",
                    "The following items must remain `null` or `TODO` until confirmed by the user:",
                ]
            )
            for cat, items in unresolved.items():
                if items:
                    lines.append(f"- **{cat.capitalize()}**: {', '.join(items)}")

        # Education & Experience
        lines.extend(
            [
                "",
                "## 2. Standardized Work & Education Record",
                "",
                "### Experience",
            ]
        )
        if self.profile.experience.current_role:
            cr = self.profile.experience.current_role
            lines.append(f"- **{cr.company}** — {cr.role} ({cr.start or 'Unknown'} – Present)")
        for role in self.profile.experience.roles:
            dates = f"{role.start or 'Unknown'} – {role.end or 'Unknown'}"
            lines.append(f"- **{role.company}** — {role.role} ({dates})")

        lines.extend(
            [
                "",
                "### Education",
            ]
        )
        for edu in self.profile.education:
            lines.append(f"- **{edu.school}**: {edu.credential}")

        lines.extend(
            [
                "",
                "### Primary Skills (Tag Exactly)",
                ", ".join(self.profile.skills.primary),
                "",
                "### Secondary Skills",
                ", ".join(self.profile.skills.secondary),
            ]
        )

        # Platform sections
        lines.extend(self._generate_linkedin_section())
        lines.extend(self._generate_indeed_section())
        lines.extend(self._generate_ziprecruiter_section())
        lines.extend(self._generate_dice_section())

        lines.extend(
            [
                "",
                "## 7. Email Polling & Ingestion Setup Checklist",
                "",
                "- [ ] All 4 platforms configured to send alert emails to the primary Gmail address.",
                "- [ ] Confirmed Gmail polling cadence: **Every 4 hours (240 minutes)**.",
                "- [ ] Verified daily reconciliation pass enabled.",
                "- [ ] Verified that realtime push/webhooks are disabled.",
                "- [ ] Confirmed sender addresses / subjects recorded in Gmail filter rules.",
            ]
        )

        return "\n".join(lines) + "\n"

    def _generate_linkedin_section(self) -> list[str]:
        return [
            "",
            "## 3. Platform Setup: LinkedIn",
            "",
            "- **Policy Mode**: `MANUAL_ONLY` (Automating submission via bot is strictly prohibited).",
            "- **Primary Purpose**: Discovery, recruiter visibility, daily email alerts, native Easy Apply manually.",
            "",
            "### Profile Fields",
            f"- **Headline**: `{self.profile.target.primary_headline} | SAP BTP • AI Workflows • Enterprise Systems`",
            "- **About Summary**:",
            f"  > {self.profile.positioning.summary}",
            "  > Key areas: SAP BTP & ERP workflows, AI/OCR document automation, full-stack software engineering, and vendor/team delivery.",
            f"- **Location**: {self.profile.identity.city}, {self.profile.identity.state}",
            "- **Recommended Alerts to Create (Daily Email)**:",
            "  1. `Enterprise Automation Architect` (Location: Pittsburgh, PA & Remote)",
            "  2. `SAP BTP Architect` / `SAP Integration` (Location: Remote)",
            "  3. `AI Automation Engineer` / `Applied AI Engineer` (Location: Remote)",
            "  4. `Solutions Architect` ($150,000+)",
            "",
            "### Verification Checklist",
            "- [ ] Headline and About text updated.",
            "- [ ] Experience entries aligned with canonical work history.",
            "- [ ] Top 5 skills pinned: SAP BTP, Python, FastAPI, Enterprise Architecture, Docker.",
            "- [ ] 4 daily email job alerts created and active.",
            "- [ ] Account status marked `verified` in `config/platforms.yaml`.",
        ]

    def _generate_indeed_section(self) -> list[str]:
        return [
            "",
            "## 4. Platform Setup: Indeed",
            "",
            "- **Policy Mode**: `MANUAL_ONLY` (Third-party bot submission is prohibited by terms).",
            "- **Primary Purpose**: Job search alerts, employer postings, native manual application.",
            "",
            "### Profile Fields",
            f"- **Desired Job Title**: `{self.profile.target.primary_headline}`",
            f"- **Desired Salary**: `${self.profile.target.target_compensation_usd_min:,}+ per year`",
            "- **Relocation / Remote**: Pittsburgh, PA / Remote",
            "- **Uploaded Resume Variant**: `enterprise_automation_solutions_architect`",
            "- **Recommended Saved Search Alerts (Daily Email)**:",
            '  1. `"Enterprise Automation" OR "Solutions Architect"` (Remote / Pittsburgh, $150K+)',
            '  2. `"SAP BTP" OR "SAP Integration"` (Remote)',
            '  3. `"AI Automation" OR "Applied AI"` (Remote)',
            "",
            "### Verification Checklist",
            "- [ ] Profile resume uploaded and set as default.",
            "- [ ] Job alert emails enabled and verified delivering to inbox.",
            "- [ ] Account status marked `verified` in `config/platforms.yaml`.",
        ]

    def _generate_ziprecruiter_section(self) -> list[str]:
        return [
            "",
            "## 5. Platform Setup: ZipRecruiter",
            "",
            "- **Policy Mode**: `ASSISTED_PENDING_POLICY_REVIEW` (Native 1-Click Apply manual, no automated bot).",
            "- **Primary Purpose**: Profile matching, candidate alerts, 1-Click Apply queue.",
            "",
            "### Profile Fields",
            f"- **Professional Headline**: `{self.profile.target.primary_headline}`",
            f"- **Target Compensation**: `${self.profile.target.target_compensation_usd_min:,}+`",
            "- **Skills Tagged**:",
            f"  - {', '.join(self.profile.skills.primary[:8])}",
            "- **Recommended Alerts (Daily Email)**:",
            "  1. `Solutions Architect` (Remote / Pittsburgh, PA)",
            "  2. `Enterprise Systems Architect` (Remote)",
            "  3. `AI Platform Engineer` / `AI Automation` (Remote)",
            "",
            "### Verification Checklist",
            "- [ ] Candidate profile fully completed (100% profile score).",
            "- [ ] Default resume uploaded.",
            "- [ ] Daily job match emails activated.",
            "- [ ] Account status marked `verified` in `config/platforms.yaml`.",
        ]

    def _generate_dice_section(self) -> list[str]:
        return [
            "",
            "## 6. Platform Setup: Dice",
            "",
            "- **Policy Mode**: `ASSISTED_PENDING_POLICY_REVIEW` (Technologist profile, manual/assisted application).",
            "- **Primary Purpose**: Tech-specific recruiter matching, high-signal alerts.",
            "",
            "### Profile Fields",
            f"- **Job Title**: `{self.profile.target.primary_headline}`",
            "- **Years of Experience**: 7+ years",
            "- **Work Preference**: Full-Time, Remote / Hybrid",
            "- **Key Technologies Listed**:",
            "  - SAP BTP, Python, FastAPI, Docker, Next.js, Swift, AWS, Azure, VMware, Meraki",
            "- **Recommended Alerts (Daily Email)**:",
            "  1. `SAP BTP` / `Enterprise Integration`",
            "  2. `Solutions Architect` AND `Automation`",
            "  3. `Applied AI` / `LLM Automation`",
            "",
            "### Verification Checklist",
            "- [ ] Technologist profile completed and set to searchable by recruiters.",
            "- [ ] Primary resume uploaded.",
            "- [ ] Recurring alert notifications configured to deliver daily.",
            "- [ ] Account status marked `verified` in `config/platforms.yaml`.",
        ]

    def save_worksheet(self, destination_path: str | Path = "docs/PROFILE_WORKSHEET.md") -> Path:
        content = self.generate_markdown()
        path = Path(destination_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
