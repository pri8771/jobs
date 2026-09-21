# A-V17-CRM-EVIDENCE

- Type: implementation / evidence
- Phase: V1.7
- Status: READY
- Owner: Antigravity Lane B
- Reviewer: ChatGPT
- Dependencies: none for code audit/repair
- Downstream: A-V17-MILESTONE-GATE, A-V20-INTEGRATED-OS

## Purpose

Make recruiter/contact/thread/application history reconstructable from source evidence across multiple roles and repeated recruiter relationships.

## Existing assets

- src/jobs_automation/lifecycle/crm.py
- src/jobs_automation/lifecycle/engine.py
- message/link/contact models
- lifecycle tests

## Acceptance criteria

- inbound and outbound recruiter messages link to contacts/applications with evidence
- one contact may span multiple roles/applications
- new role in an existing thread does not mutate the wrong application
- ambiguous message/application relationships route to review
- company/contact/application timeline is reconstructable
- manual correction/merge API or service exists for bad contact/link matches
- no generated summary replaces raw provider message evidence
- tests cover multi-role recruiter, reused thread, duplicate contact, and ambiguity cases
- CI green

## Worker tasks

- J17-01 SP2 — audit current CRM/linking behavior against this contract
- J17-02 SP3 — add multi-role contact/thread relationship support or repair gaps
- J17-03 SP2 — add manual correction/merge service for contact/message links
- J17-04 SP3 — expand lifecycle evidence/timeline tests
