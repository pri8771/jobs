# V2.0 User-Boundary Checklist

Purpose: make the remaining user-interactive steps small, explicit, and ready when engineering reaches them.

Do not perform these early just to make a status green.

## 1. Candidate provenance confirmation

Before consequential live application use, resolve only facts that are still needed by actual target jobs.

Likely confirmation categories:
- compensation basis: base salary vs total compensation target
- remote/hybrid preference
- relocation willingness
- travel tolerance
- exact Veeva employment dates if needed
- canonical email/phone
- work authorization/sponsorship facts if not already privately confirmed
- LinkedIn/GitHub/portfolio links where intended for applications

Do not require demographic/self-ID values; those remain manual per application.

## 2. Gmail OAuth

When A-V20-GMAIL-RUNTIME-READINESS is accepted:

User actions:
1. create/select Google Cloud project,
2. enable Gmail API,
3. configure OAuth consent,
4. create desktop/local OAuth client,
5. place client ID/secret in local runtime config/secret mechanism,
6. run the project's explicit interactive OAuth command,
7. approve Gmail read-only scope,
8. verify token is stored in the ignored runtime path.

Then engineering performs:
- real diagnostic
- bounded dry-run canary
- bounded persisted idempotency canary

## 3. Proof job selection

Before assisted/live application:
- review 2-5 strong real candidate jobs,
- choose one the user genuinely wants,
- confirm location/work arrangement,
- confirm compensation if known,
- approve exact job.

Do not pick a role only because the form is easy to automate.

## 4. Packet review

For the selected job, user sees:
- company/title/URL
- exact resume variant/artifact
- cover letter
- every screening answer + provenance
- unresolved/manual fields
- submission method/policy

User approves or rejects the exact packet.

## 5. Live browser / login boundary

User handles when required:
- login
- MFA
- CAPTCHA
- email/phone verification
- consent
- EEO/self-ID

Automation may resume after the barrier only if policy permits.

## 6. First real submission authorization

Authorization is specific to:
- one job
- one packet hash
- one submission method

No blanket permission.

## V2.0 acceptance

Full V2.0 requires real Gmail/live-data evidence, but it does not require unsafe or prohibited automatic application methods.

Manual/assisted application destinations remain legitimate V2.0 paths when policy requires them.
