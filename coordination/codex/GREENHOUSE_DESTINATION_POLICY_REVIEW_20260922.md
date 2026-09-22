# Greenhouse Destination-Policy Review: Jobs Automation V1.7 hosted-form route

- **Date:** 2026-09-22
- **Status:** PROPOSED. **Requires native lead approval. Not a live grant.**
- **Scope:** Question 1 of the five frozen transport questions in `V17_ACTIVE_DISPOSITION_20260922.md` section 3, plus the destination-specific facts for questions 2 to 5.
- **Not legal advice.** This is an internal safety and eligibility record. It is not a legal determination, not ToS clearance, not employer authorization, and it grants no submit authority.
- **Method:** Read-only review of public pages only (HTTP GET of public posting, public docs, robots.txt, public terms and privacy pages). No application form was opened interactively, no field was filled, nothing was submitted, and no login was attempted. Anti-bot findings come from Greenhouse's public documentation, not from probing the live form.
- **Public repo file:** contains no personal data.

---

## 1. Exact candidate-facing form

| Item | Value |
|---|---|
| Candidate-facing form URL | `https://job-boards.greenhouse.io/flexport/jobs/8110413` |
| Legacy URL | `https://boards.greenhouse.io/flexport/jobs/8110413` returns 301 to the URL above |
| Employer / board token | Flexport / `flexport` |
| Requisition | Greenhouse job id `8110413`, "Forward Deployed Engineer - Supply Chain Solutions", San Francisco, CA |
| Form placement | Embedded on the same page under "Apply for this job", ending in a "Submit application" control, footer "Powered by Greenhouse" |
| Login required to apply | None observed on the public page (no MyGreenhouse account needed to view the form) |
| Page HTTP status at review | 200 (2026-09-22) |

---

## 2. Findings per source

### 2.1 Greenhouse: candidate-facing terms

| Source | Finding |
|---|---|
| https://www.greenhouse.com/legal | This is a legal **index**, not a terms text. It lists the Privacy policy, a candidate CCPA/CPRA notice (for people applying to Greenhouse itself), the Master Subscription Agreement (customers), the DPA and subprocessors. **No candidate or job-seeker terms of use for job boards are published there.** |
| https://my.greenhouse.com/ (footer) | The "Terms of service" and "Terms of Use" links both resolve to `greenhouse.com/legal` (the index above). The MyGreenhouse User Agreement governs MyGreenhouse account users only, and its text was not publicly retrievable. It does not govern an unauthenticated job-board application. |
| Posting page footer | Only "Powered by Greenhouse" and the employer's privacy link. No terms link is shown to candidates. |
| https://www.greenhouse.com/privacy-policy (last updated May 28, 2026) | For customer job boards Greenhouse acts as processor or service provider, handling applicant data "only according to our customers' instructions". So the employer controls the destination. |
| https://support.greenhouse.io/hc/en-us/articles/43418495049499-MyGreenhouse-FAQ-for-Candidates | Greenhouse's own first-party Quick Apply: "we'll autofill those fields when you apply to jobs". First-party autofill exists. This says nothing about third-party tools. |

**Result:** we found no published Greenhouse term that expressly **permits** or expressly **prohibits** third-party assisted prefill of a job-board application.

### 2.2 Greenhouse: posture toward automated applying

| Source | Finding |
|---|---|
| https://support.greenhouse.io/hc/en-us/articles/115005448066 (Invisible reCAPTCHA) | Greenhouse "uses Google's reCAPTCHA to help keep robots and spammers from easily applying to jobs". |
| same | It "analyzes activity on a job post, like mouse movements and typing patterns". |
| same | Escalation: "a user may be asked to submit a code from their email". |
| same | Per-employer setting: "You can customize the sensitivity of your spam protection for each of your job boards". |
| https://www.greenhouse.com/blog/introducing-greenhouse-real-talent (June 3, 2025) | "Sophisticated algorithms detect bots, fake job applicants, mass applications". Optional CLEAR identity verification is offered inside MyGreenhouse. |
| https://fortune.com/2026/07/27/greenhouse-ceo-daniel-chait-ai-doom-loop-job-seekers-spam-interview-applications-unemployment/ | The Greenhouse CEO criticizes "tools that advertise, use AI to automatically apply to every Greenhouse job". This is a public stance, not a term. |

**Result:** the destination operator's documented posture is adversarial to automated applying. It uses technical controls that score automation signals, and those controls are tuned by each employer.

### 2.3 robots.txt (crawling only; not a submission permission)

| Host | Content at review |
|---|---|
| https://job-boards.greenhouse.io/robots.txt | No active rules. The directives are commented out ("To ban all spiders ... uncomment the next two lines"). |
| https://boards.greenhouse.io/robots.txt | `User-agent: *` / `Disallow: /embed/` |

robots.txt governs crawling. It does not grant permission to submit an application. It matters here only because Flexport's terms (2.4) make automated access conditional on it.

### 2.4 Flexport: site terms and AI or automation language

| Source | Finding |
|---|---|
| https://www.flexport.com/terms-and-conditions/terms-of-use/ (Last Updated: January 8, 2026) | Prohibits use "through automated means (including bots, spiders, crawlers, scrapers, data mining tools" ... "except in full compliance with any robots.txt or other technical or usage restrictions". |
| same (scope) | Covers flexport.com and "any related subdomains or websites operated by Flexport". `job-boards.greenhouse.io` is operated by Greenhouse, so **whether this clause applies to the hosted form is unclear**. If it does apply, Greenhouse's reCAPTCHA is arguably a "technical ... restriction". The terms do not mention careers or job applications. |
| https://job-boards.greenhouse.io/flexport/jobs/8110413 | No language about applicant AI use, automated applications, or authenticity attestation. The "AI" mentions are job-content only. Data clause: "By submitting your application, you are agreeing to our use and processing of your data". |
| https://www.flexport.com/careers/ | No stated policy on AI-assisted or automated applications. |
| https://www.flexport.com/privacy (last updated September 1, 2026) | Mentions Flexport's own possible use of automated decision-making technology (ADMT) under California law. It sets no rule on applicant-side automation. |

### 2.5 Employer / ATS API

| Source | Finding |
|---|---|
| https://docs.greenhouse.io/job-board.html (redirect from developers.greenhouse.io) | "authentication is not required for any GET endpoints" (public, read-only). |
| same | Application POST requires HTTP Basic Auth: "the Basic Auth username is your API key". |
| same | "the HTTP Basic Auth API token is a secret key". Posts must be proxied through the employer's own servers. |
| same | The hosted form "has built-in spam protection measures". |

### 2.6 Confirmation behavior

| Source | Finding |
|---|---|
| https://support.greenhouse.io/hc/en-us/articles/115004681926-I-applied-to-a-job-post-but-I-didn-t-receive-confirmation | Confirmation email is optional per employer: "some organizations opt not to send these confirmation emails". |
| https://support.greenhouse.io/hc/en-us/articles/115005516483-Edit-application-confirmation-page | The post-submit confirmation page "is editable and is set per job board" (employer-authored text). |

---

## 3. Determination per the five frozen questions

| # | Question | Determination |
|---|---|---|
| 1 | **Destination policy / ToS eligibility** | **UNCLEAR.** We found no explicit prohibition and no explicit permission. Greenhouse publishes no candidate-facing job-board terms. Its documented controls (behavioral reCAPTCHA that scores "mouse movements and typing patterns", email-code escalation, Real Talent bot and mass-apply detection) and its public stance are adversarial to automated applying. Whether Flexport's automated-means clause reaches a Greenhouse-operated host is unclear. If it does, it conditions automation on compliance with "technical ... restrictions", which reCAPTCHA arguably is. A Playwright-driven prefill is exactly the kind of signal those controls score. Under section 3 rule 1 ("unclear ... stop"), **automated or assisted transport on this route = `BLOCKED_NO_ELIGIBLE_TRANSPORT`**. Owner approval cannot override this. |
| 2 | **Scoped authorization** | None exists. Any future grant needs all of: exact job (`flexport` / `8110413`); session alias (no Greenhouse or MyGreenhouse login is in scope, so the alias is the owner's local browser profile); exact packet hash; exact method (manual native submission, per the proposed decision below); policy reference (this file plus the registry entry version); and an unexpired approval not later than `review_due_at`. Consequential unresolved questions (sponsorship, work authorization, prior employment, travel/in-office) block. |
| 3 | **Bot challenge / verification** | **Expected and documented.** Invisible reCAPTCHA is present on Greenhouse hosted forms, with an email verification-code escalation. The sensitivity is set per employer, so its presence and strictness on Flexport's board cannot be known in advance without probing, and we did not probe. Any challenge, email code, CLEAR or identity check, or login prompt is a **terminal automation halt** that routes to manual owner review. No solver, stealth, fingerprint evasion, retry, or alternate endpoint. |
| 4 | **No employer API** | **Confirmed prohibited.** The Job Board API application POST needs Flexport's secret API key (Basic Auth). We do not have it and must not acquire it. The public GET endpoints (`boards-api.greenhouse.io`) are read-only and are **not** submission authority. The intended route is the visible hosted form only. |
| 5 | **Confirmation signal** | The thank-you page is employer-editable per board, and the confirmation email is optional per employer. So a thank-you page, a navigation, or an HTTP 200 is **insufficient**. `SUBMITTED` requires correlated external evidence: an application-confirmation email tied to this job and candidate if Flexport sends one, or an employer or recruiter confirmation. Otherwise the result is `SUBMISSION_UNCONFIRMED`, with no blind retry. |

**Overall:** eligibility is **not clear**, so decision `assisted` is **not** proposed. The owner may still apply by hand in their own browser. That is non-automated, and the unclear automation eligibility does not bar it.

---

## 4. Proposed registry entry (PROPOSED, not applied)

Target file (not edited by this review): `config/policy_registry.example.yaml` or the runtime registry. The schema is `PolicyEntryConfig` with `extra="forbid"`, so the reason goes in `notes` (entries have no `reason` field). The evaluator does a single-glob `fnmatch`, so there are two exact-host entries. A `*.greenhouse.io` glob would over-match (`app.`, `my.`, `boards-api.` and others).

```yaml
  # PROPOSED 2026-09-22. Requires native lead approval. Not a live grant.
  # Source: coordination/jobs/coordination/codex/GREENHOUSE_DESTINATION_POLICY_REVIEW_20260922.md
  - platform: "greenhouse"
    domain_pattern: "job-boards.greenhouse.io"
    capability: "submit_application"
    decision: "manual_only"
    reviewed_at: "2026-09-22"
    review_due_at: "2026-10-22"
    evidence:
      - "https://job-boards.greenhouse.io/flexport/jobs/8110413"
      - "https://www.greenhouse.com/legal"
      - "https://www.greenhouse.com/privacy-policy"
      - "https://support.greenhouse.io/hc/en-us/articles/115005448066"
      - "https://www.greenhouse.com/blog/introducing-greenhouse-real-talent"
      - "https://docs.greenhouse.io/job-board.html"
      - "https://support.greenhouse.io/hc/en-us/articles/115004681926-I-applied-to-a-job-post-but-I-didn-t-receive-confirmation"
      - "https://support.greenhouse.io/hc/en-us/articles/115005516483-Edit-application-confirmation-page"
      - "https://www.flexport.com/terms-and-conditions/terms-of-use/"
      - "https://job-boards.greenhouse.io/robots.txt"
    notes:
      - "reason: automation_eligibility_unclear. No published candidate terms; operator uses behavioral reCAPTCHA plus bot/mass-apply detection."
      - "V1.7 hosted-form automated/assisted transport state: BLOCKED_NO_ELIGIBLE_TRANSPORT."
      - "manual_only = owner submits natively in own browser via worksheet; no Playwright prefill, no automated submit."
      - "Any CAPTCHA, email code, identity/CLEAR check or login prompt: terminal halt, manual owner review, no bypass."
      - "Job Board API POST requires employer secret key: never used; public GET endpoints are not submission authority."
      - "SUBMITTED requires correlated confirmation email or employer confirmation; else SUBMISSION_UNCONFIRMED."

  - platform: "greenhouse"
    domain_pattern: "boards.greenhouse.io"
    capability: "submit_application"
    decision: "manual_only"
    reviewed_at: "2026-09-22"
    review_due_at: "2026-10-22"
    evidence:
      - "https://boards.greenhouse.io/robots.txt"
      - "https://support.greenhouse.io/hc/en-us/articles/115005448066"
      - "https://docs.greenhouse.io/job-board.html"
    notes:
      - "Legacy host; /flexport/jobs/8110413 301-redirects to job-boards.greenhouse.io. Same determination as job-boards.greenhouse.io entry."
      - "robots.txt disallows /embed/; embedded-iframe routes are out of scope."
```

**Stricter alternative for the lead:** set `decision: "blocked"` on both entries. Leaving the entries out has the same effect, because the registry default is blocked. That also stops the packet-guided manual worksheet flow (`MANUAL_IN_PROGRESS`) for Greenhouse. Choose it if the lead wants no system involvement at all while eligibility is unclear. Note that adding `manual_only` relaxes today's default `blocked`, but only for human, non-automated submission.

### What would change the determination to `assisted`

At least one of these would need to be recorded in a new review. None is present today.
- Greenhouse publishes candidate-facing terms that expressly allow third-party assistive prefill with a human submitting.
- Flexport gives written, requisition-scoped employer consent to assisted prefill on its Greenhouse board. This is destination-side authority, not owner approval.

Even then, question 3 still applies: a challenge is a terminal halt.

---

## 5. Approval block

- [ ] Lead approves determination Q1 = UNCLEAR, which means `BLOCKED_NO_ELIGIBLE_TRANSPORT` for automated or assisted transport
- [ ] Lead selects the registry decision: `manual_only` (proposed) or `blocked` (stricter)
- [ ] Lead authorizes a separate change to apply the entry to the registry (this review edits no registry file)

This record authorizes nothing. It does not authorize G15 or G16, any live submit, or any prefill session.
