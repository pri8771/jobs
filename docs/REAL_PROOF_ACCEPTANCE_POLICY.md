# Real-Proof Milestone Acceptance Policy

Owner directive:
A version is **not complete** merely because code, tests, CI, fixtures, and adversarial tests pass.

## Required states

Every version/milestone may have two independent states:

- **ENGINEERING_ACCEPTED** — implementation, tests, CI, failure behavior, and adversarial cases are accepted.
- **REAL_PROVEN** — at least one real, non-mock example has run successfully through the milestone's actual production path.

A version is called **COMPLETE** only when both are true.

## What counts as REAL_PROVEN

The example must use real inputs appropriate to the milestone.

For V1.4 packet preparation this means:

1. a real currently-live job posting,
2. the user's actual private candidate profile source,
3. actual resume file bytes from the selected resume family,
4. the production packet-builder path,
5. no example YAML as candidate truth,
6. no temporary/synthetic resume fixture,
7. no MockModelGateway, HallucinatingModelGateway, or silent mock fallback,
8. non-mock generation metadata for any generated content,
9. actual packet/resume/cover-letter/manifest artifacts written and SHA-verified,
10. a redacted evidence bundle that another reviewer can inspect.

A truthful unresolved answer is acceptable.
The proof is about the real pipeline behaving correctly, not about forcing every question to resolve.

## What does NOT count

- unit/integration fixture data,
- candidate_profile.example.yaml,
- temp test resumes,
- fake companies/jobs,
- mock gateways,
- simulated browser/ATS receipts,
- hard-coded proof output,
- CI-only evidence,
- manually authored JSON pretending to be runtime output.

## Privacy

Real proof must not require committing private resume/profile contents.

Commit only redacted evidence such as:
- source type,
- public job URL,
- hashes,
- byte counts,
- variant/family/version IDs,
- provenance classes/field paths,
- model/provider origin,
- packet/artifact IDs/hashes,
- unresolved question names/categories when safe,
- verifier results.

Private local paths should be redacted or represented by a stable hash/basename when necessary.

## Acceptance ownership

Workers can report a real proof run.
Scout may independently validate the evidence bundle.
Only ChatGPT lead may mark REAL_PROVEN / COMPLETE.

## Version progression

Later-version engineering may continue in parallel, but the official completed-version number cannot advance past a milestone whose required real proof is missing.