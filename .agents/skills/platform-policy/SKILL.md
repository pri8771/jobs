---
name: platform-policy
description: Evaluate whether a job source or application destination may be automated, assisted, manual-only, or blocked. Use before implementing or executing browser automation, job submission, scraping, or a new job-board/ATS adapter.
---

# Platform Policy

## Goal

Prevent the automation layer from assuming that discovering a job authorizes automated submission.

## Procedure

1. Read docs/PLATFORM_CONSTRAINTS.md.
2. Identify the exact source platform and destination domain.
3. Check the runtime/versioned policy registry.
4. If current evidence is missing or expired, default to BLOCKED for auto-submit.
5. Classify capability as:
   - MANUAL_ONLY
   - ASSISTED
   - AUTO_ALLOWED
   - BLOCKED
6. Persist the reason/evidence when implementation reaches runtime policy handling.

## Hard constraints

- No CAPTCHA bypass.
- No fingerprint spoofing.
- No stealth evasion.
- No rate-limit bypass.
- No LinkedIn Easy Apply bot.
- No Indeed Apply bot.
- Do not reinterpret employer/job-posting APIs as candidate-side apply permission.
