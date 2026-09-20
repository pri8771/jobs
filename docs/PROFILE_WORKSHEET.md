# Candidate Profile Setup & Verification Worksheet

> **Purpose**: Single authoritative guide for configuring and verifying candidate profiles
> across LinkedIn, Indeed, ZipRecruiter, and Dice without improvising inconsistent facts.

## 1. Candidate Core Positioning

- **Candidate Name**: Priyansh Chordia (Priyansh)
- **Location**: Pittsburgh, PA (Target: Pittsburgh + US Remote)
- **Primary Headline**: `Enterprise Automation & Solutions Architect`
- **Target Compensation**: $150,000+ USD (confirm_base_vs_total_comp)
- **Resume Strategy**: `maintain_targeted_versions` (Default: `enterprise_automation_solutions_architect`)

### Positioning Guardrails
- **Summary**: Senior technical operator who can build software, automate business processes, manage enterprise systems, and lead vendors/projects.
- **Differentiators**:
  - Software engineering + enterprise systems
  - SAP exposure + automation
  - AI/OCR/LLM workflow automation
  - Infrastructure + business applications
  - Vendor/project leadership
  - Manufacturing/pharma experience
- **Avoid Positioning As**:
  - ⛔ generic IT generalist
  - ⛔ helpdesk/basic support
  - ⛔ only a developer

### Targeted Resume Tracks

| Priority | Resume Track ID | Core Focus & Keywords |
|---|---|---|
| 1 | `enterprise_automation_solutions_architect` | SAP BTP, AI/OCR automation, ERP workflows, integrations, vendors, infrastructure |
| 2 | `senior_software_ai_automation` | Python, FastAPI, React / Next.js, Firebase, Docker, Swift / iOS, OCR/LLM workflows |
| 3 | `senior_ios_mobile_lead` | Veeva CRM, HCP app, Swift / Objective-C, regulated apps, founder experience |
| 4 | `it_apps_infrastructure_manager` | Microsoft 365, VMware / Meraki, endpoint management, vendors, business systems, automation |

### ⚠️ Unresolved Facts (DO NOT FABRICATE)
The following items must remain `null` or `TODO` until confirmed by the user:
- **Identity**: email, phone
- **Work_authorization**: authorized_to_work_in_us, requires_sponsorship_now, requires_sponsorship_future
- **Target**: compensation_basis_unconfirmed, remote_preference, relocation, travel_percent_max
- **Experience_dates**: Veeva (iOS Developer): dates unresolved

## 2. Standardized Work & Education Record

### Experience
- **Viatris** — Contractor - SAP BTP / Enterprise Automation (2024-10 – Present)
- **Thar Process** — Head of IT / Business Operations (2019 – 2024)
- **Nootry** — Co-founder (2017 – 2019)
- **Veeva** — iOS Developer (Unknown – Unknown)

### Education
- **Carnegie Mellon University**: B.S. Chemical Engineering
- **Flatiron School**: Software Development / iOS Certificate

### Primary Skills (Tag Exactly)
SAP BTP, SAP integrations / ERP workflows, AI/OCR/LLM extraction, document automation, Python, FastAPI, React / Next.js, Docker, Swift / iOS, enterprise infrastructure, vendor management, project delivery

### Secondary Skills
Java, Objective-C, TypeScript, Firebase, Azure, AWS, GCP, VMware, Meraki, Microsoft 365

## 3. Platform Setup: LinkedIn

- **Policy Mode**: `MANUAL_ONLY` (Automating submission via bot is strictly prohibited).
- **Primary Purpose**: Discovery, recruiter visibility, daily email alerts, native Easy Apply manually.

### Profile Fields
- **Headline**: `Enterprise Automation & Solutions Architect | SAP BTP • AI Workflows • Enterprise Systems`
- **About Summary**:
  > Senior technical operator who can build software, automate business processes, manage enterprise systems, and lead vendors/projects.
  > Key areas: SAP BTP & ERP workflows, AI/OCR document automation, full-stack software engineering, and vendor/team delivery.
- **Location**: Pittsburgh, PA
- **Recommended Alerts to Create (Daily Email)**:
  1. `Enterprise Automation Architect` (Location: Pittsburgh, PA & Remote)
  2. `SAP BTP Architect` / `SAP Integration` (Location: Remote)
  3. `AI Automation Engineer` / `Applied AI Engineer` (Location: Remote)
  4. `Solutions Architect` ($150,000+)

### Verification Checklist
- [ ] Headline and About text updated.
- [ ] Experience entries aligned with canonical work history.
- [ ] Top 5 skills pinned: SAP BTP, Python, FastAPI, Enterprise Architecture, Docker.
- [ ] 4 daily email job alerts created and active.
- [ ] Account status marked `verified` in `config/platforms.yaml`.

## 4. Platform Setup: Indeed

- **Policy Mode**: `MANUAL_ONLY` (Third-party bot submission is prohibited by terms).
- **Primary Purpose**: Job search alerts, employer postings, native manual application.

### Profile Fields
- **Desired Job Title**: `Enterprise Automation & Solutions Architect`
- **Desired Salary**: `$150,000+ per year`
- **Relocation / Remote**: Pittsburgh, PA / Remote
- **Uploaded Resume Variant**: `enterprise_automation_solutions_architect`
- **Recommended Saved Search Alerts (Daily Email)**:
  1. `"Enterprise Automation" OR "Solutions Architect"` (Remote / Pittsburgh, $150K+)
  2. `"SAP BTP" OR "SAP Integration"` (Remote)
  3. `"AI Automation" OR "Applied AI"` (Remote)

### Verification Checklist
- [ ] Profile resume uploaded and set as default.
- [ ] Job alert emails enabled and verified delivering to inbox.
- [ ] Account status marked `verified` in `config/platforms.yaml`.

## 5. Platform Setup: ZipRecruiter

- **Policy Mode**: `ASSISTED_PENDING_POLICY_REVIEW` (Native 1-Click Apply manual, no automated bot).
- **Primary Purpose**: Profile matching, candidate alerts, 1-Click Apply queue.

### Profile Fields
- **Professional Headline**: `Enterprise Automation & Solutions Architect`
- **Target Compensation**: `$150,000+`
- **Skills Tagged**:
  - SAP BTP, SAP integrations / ERP workflows, AI/OCR/LLM extraction, document automation, Python, FastAPI, React / Next.js, Docker
- **Recommended Alerts (Daily Email)**:
  1. `Solutions Architect` (Remote / Pittsburgh, PA)
  2. `Enterprise Systems Architect` (Remote)
  3. `AI Platform Engineer` / `AI Automation` (Remote)

### Verification Checklist
- [ ] Candidate profile fully completed (100% profile score).
- [ ] Default resume uploaded.
- [ ] Daily job match emails activated.
- [ ] Account status marked `verified` in `config/platforms.yaml`.

## 6. Platform Setup: Dice

- **Policy Mode**: `ASSISTED_PENDING_POLICY_REVIEW` (Technologist profile, manual/assisted application).
- **Primary Purpose**: Tech-specific recruiter matching, high-signal alerts.

### Profile Fields
- **Job Title**: `Enterprise Automation & Solutions Architect`
- **Years of Experience**: 7+ years
- **Work Preference**: Full-Time, Remote / Hybrid
- **Key Technologies Listed**:
  - SAP BTP, Python, FastAPI, Docker, Next.js, Swift, AWS, Azure, VMware, Meraki
- **Recommended Alerts (Daily Email)**:
  1. `SAP BTP` / `Enterprise Integration`
  2. `Solutions Architect` AND `Automation`
  3. `Applied AI` / `LLM Automation`

### Verification Checklist
- [ ] Technologist profile completed and set to searchable by recruiters.
- [ ] Primary resume uploaded.
- [ ] Recurring alert notifications configured to deliver daily.
- [ ] Account status marked `verified` in `config/platforms.yaml`.

## 7. Email Polling & Ingestion Setup Checklist

- [ ] All 4 platforms configured to send alert emails to the primary Gmail address.
- [ ] Confirmed Gmail polling cadence: **Every 4 hours (240 minutes)**.
- [ ] Verified daily reconciliation pass enabled.
- [ ] Verified that realtime push/webhooks are disabled.
- [ ] Confirmed sender addresses / subjects recorded in Gmail filter rules.
