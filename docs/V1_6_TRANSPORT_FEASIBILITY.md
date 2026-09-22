# Candidate-Side Programmatic Application Transport — ATS Survey

Task: V17-T01 (`docs/FABLE_V17_LIVE.md` §6) · Artifact: `A-V16-TRANSPORT` · SP1
Worker state: `WORKER_REPORTED_DONE` (research only; no code, no live or mutating calls). Lead decides.
Produced 2026-09-22 by a bounded read-only research subagent; reviewed and committed by the Fable worker session.

**Access note:** Every vendor host tested (greenhouse.io, lever.co, ashbyhq.com, workday.com — including support/help/legal subdomains) returned `EGRESS_BLOCKED`/403 to direct WebFetch/curl from this sandbox. Only github.com (vendors' own doc-source repos) was directly fetchable. Citations marked "(indexed, not directly fetched)" are search-engine excerpts of the named primary page, not independently re-verified in this session — flagged per instructions rather than asserted as confirmed.

## 1. Greenhouse Job Board API
- **Eligibility:** NOT_ELIGIBLE_EMPLOYER_CREDENTIAL (API). Hosted form: ELIGIBLE.
- **Credential owner:** `POST /v1/boards/{board_token}/jobs/{id}` needs HTTP Basic Auth, API key as username, no password. Key is created inside the employer's Greenhouse account by a user with "Basic and above" job-board-credential permission — employer only. Docs warn the key is a secret and any client-exposed POST "would reveal your secret key to anybody that views source."
- **Destination identity:** `board_token` = employer's board slug; `{id}` = job id.
- **Confirmation:** Required fields documented (first/last name, email); success response body/status code not specified in the retrieved text — unclear.
- **Bot protection:** Docs recommend the hosted "Embedded Job Application" over custom POSTs because it has "built-in spam protection"; Greenhouse support separately documents "Invisible reCAPTCHA" analyzing behavior on job-board applications, sometimes falling back to email verification. `job-boards.greenhouse.io/{board}/jobs/{id}` is the documented candidate route.
- **Docs:** github.com/grnhse/greenhouse-api-docs/blob/master/source/includes/job-board/_applications.md (fetched directly); support.greenhouse.io/hc/en-us/articles/115005448066-Invisible-reCAPTCHA (indexed, not directly fetched); support.greenhouse.io/hc/en-us/articles/13446638483355 (key ownership, indexed).

## 2. Lever Postings API
- **Eligibility:** NOT_ELIGIBLE_EMPLOYER_CREDENTIAL (API). Hosted posting page: ELIGIBLE.
- **Credential owner:** "You need an API key, which a Super Admin of your account can generate from your integrations settings page" — employer's Lever account only, passed as `?key=`.
- **Destination identity:** `{site}` = employer site slug; `{posting_id}` = posting.
- **Confirmation:** Success = `200 OK`, `{ok:true, applicationId:'...'}`. Candidate confirmation email is an employer-configurable toggle, suppressed by `silent:true`.
- **Bot protection:** Lever's own docs tell integrators to add their own "captchas and session or IP based rate limits"; the API itself only rate-limits (429 above 2 req/s) — no built-in verification.
- **Docs:** github.com/lever/postings-api README (fetched directly); help.lever.co/hc/en-us/articles/20087307202333 (confirmation email, indexed, not directly fetched).

## 3. Ashby
- **Eligibility:** NOT_ELIGIBLE_EMPLOYER_CREDENTIAL (API). Hosted form: ELIGIBLE.
- **Credential owner:** `GET /posting-api/job-board/{clientname}` is public/unauthenticated but read-only (lists jobs, not an apply route). `POST api.ashbyhq.com/applicationForm.submit` does submit an application but needs an Ashby API key scoped `candidatesWrite`, created only by an admin under the employer's Ashby workspace (Admin > Integrations > API Keys).
- **Destination identity:** `{clientname}` = employer board slug; postings expose an `applyUrl` pointing to `jobs.ashbyhq.com/{org}/{postingId}`.
- **Confirmation:** Response has a `success` field the caller must check; Ashby documents an automatic candidate confirmation email from an ashbyhq.com address.
- **Bot protection:** No captcha specifics found in reachable sources — UNCLEAR, not confirmed absent.
- **Docs:** developers.ashbyhq.com/reference/applicationformsubmit; developers.ashbyhq.com/reference/authentication (both indexed only — every direct WebFetch to developers.ashbyhq.com was blocked).

## 4. Workday
- **Eligibility:** NOT_ELIGIBLE — no public candidate application API exists.
- **Credential owner:** Recruiting/Staffing REST and SOAP services sit behind a Workday Community customer login, using per-tenant OAuth/integration credentials issued to the employer (Workday customer) only.
- **Destination identity:** Candidates reach only a tenant's hosted career site, e.g. `{tenant}.wd{n}.myworkdayjobs.com/...`; no documented public apply endpoint exists.
- **Confirmation:** Hosted-UI confirmation page/email only; not independently verified this session.
- **Bot protection:** Workday's site terms reportedly bar bypassing/ignoring robots.txt instructions (indexed, not directly fetched).
- **Docs:** developer.workday.com/api-overview; community.workday.com/custom/developer/API/Recruiting/v26.0/Recruiting.html; workday.com/en-us/legal/site-terms.html (all indexed — every workday.com/developer.workday.com host was blocked to direct fetch).

## 5. Browser automation on the official hosted form
- **Eligibility:** UNCLEAR. No reachable vendor doc explicitly authorizes or forbids a candidate automating their own single submission on the vendor-hosted page; absence of a clause is not the same as permission.
- **Credential owner:** None — this route uses no API credential, only the public page.
- **Destination identity:** The employer's own posting URL on the vendor's hosted domain (same URLs as the "hosted form" rows above).
- **Confirmation:** Only what a human sees: on-page "submitted" confirmation and/or a confirmation email (Greenhouse and Lever: configurable; Ashby: automatic).
- **Bot protection:** Greenhouse and Ashby both document reCAPTCHA/verification on this exact surface (§1, §3); automation risks being challenged or blocked regardless of any ToS question.

## Recommendation
None of the three API routes is genuinely candidate-usable — each requires an employer-owned secret with no legitimate candidate path to obtain it, and Workday has no candidate API at all. The one narrowly-supportable transport is **Playwright browser automation driving the vendor's own hosted apply page at the employer's official posting URL, as the candidate, submitting only the candidate's own data**, treating any reCAPTCHA/verification challenge as a hard stop rather than something to solve.

## Open questions for a human lead
1. Does automating a form a human would otherwise fill by hand count as prohibited "automated access" under each vendor's ToS for a single, candidate-initiated submission — and does that risk matter enough to block this route?
2. Does any live attempt require explicit scoped authorization under `docs/AUTHORIZATION_GATES.md` before it touches a real employer posting, even once?
3. When a bot-protection challenge appears, must the agent halt and hand off to the human candidate — and who sets that threshold?
4. Should any ATS API be used at all here, given every documented apply/POST endpoint needs an employer-owned key?
5. What is the acceptable, minimal-PII "external confirmation signal" to record as submission proof — page text, email receipt, or both?

## Worker consequence for V1.6 engineering (not a decision)

Until the lead records a destination policy for the hosted-form route and the owner approves an exact job/packet/method, the truthful transport state for G16 is `BLOCKED_NO_ELIGIBLE_TRANSPORT`. V1.6 engineering (`V17-A01..X01`) can still be built against the existing browser runner as the transport candidate, with CAPTCHA/MFA/verification challenges modelled as terminal manual barriers, never as something to solve.
