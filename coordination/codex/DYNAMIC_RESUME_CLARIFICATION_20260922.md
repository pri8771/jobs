# Per-job resume requirement — owner clarification, 2026-09-22

Owner: “Our job profile should be dynamic. Basically, every job description is different, and each one may or may not use ai to filter resumes, so we want to craft each resume based on the requirements, and what ive done.”

Required behavior: maintain verified career facts and derive a tailored resume for each job description. The exact-resume proof requirement freezes the version approved for one application; it does not require one permanent generic resume. Unsupported experience, dates, qualifications and metrics must remain unknown/questions. We cannot assume whether a particular employer uses an AI screener.

Existing contracts agree: `docs/PROJECT_SPEC.md` maps evidence to requirements and allows tailored variants; `docs/CANDIDATE_POSITIONING.md` explicitly rejects one generic resume and permits truthful emphasis/reordering.

Read-only implementation audit at main `1a4efbb0ae68937c4e93e57e9e26fea883ed4ca0` and accepted canary `b2688eeabb5ca996767b27b78d0004678eeee756`:

- `evaluation/scorer.py` reads the JD and profile for deterministic evaluation.
- `preparation/tailoring.py` selects among resume families by title/family, not full JD.
- `preparation/packet_builder.py` copies the configured resume source bytes and records `tailoring_method=base`, target job and provenance hashes. No automated JD-to-resume generator is wired into this path.
- The packet and assisted-browser integrity paths freeze and recheck exact approved bytes/answers/profile identity. Hashes establish identity, not factual correctness.

Fastest genuine preparation proof: reuse the recovered private career and keyword banks, propose/confirm a current genuine proof job, prepare a truthful job-specific resume privately, bind it as the selected source, review only genuinely unresolved consequential answers, then use the accepted G14 production path under its separate exact scope. `DeterministicModelGateway` makes an external model grant unnecessary for this path. This would prove preparation/identity, not automatic tailoring.

The deterministic cover-letter fallback contains generic achievement language without claim-level matching; it still requires factual review. Do not describe model-free output as automatically fact-verified.

**Correction at 20:30 UTC:** the owner supplied past-chat examples and pointed out that the sources were already known. Local inspection recovered the canonical evidence-tiered career bank, keyword mappings, master application profile and audit notes. Career-source location is RESOLVED; do not ask the owner to reconstruct this material. Local-only source map: `/Users/pchordia/Downloads/swarm_codex/jobs_private/CAREER_SOURCES_20260922.md`. No personal contents were copied into this public repository. Existing dirty personal pipeline data was left untouched. The owner need only confirm the selected proof job and truly unresolved consequential answers when applicable; sourcing and runtime-schema mapping are Codex work. Automatic generation remains a separate implementation gap, not a missing-career-history blocker. Lead provenance disposition in `V17_ACTIVE_DISPOSITION_20260922.md` reuses accepted P0A/packet provenance and forbids a redundant parallel provenance implementation.

Historical audit corrections: correct Jobs PR26 is https://github.com/pri8771/jobs/pull/26; its earlier hosted `mypy src tests` failure was 22 typing errors, not billing. Those errors were subsequently repaired in accepted eec0ae3 and its hosted check passed. The pre-disposition queue listed `A-V16-SUBMISSION-ENGINE-REPAIR` BLOCKED, not IN_PROGRESS. The accepted policy permits the scoped Greenhouse candidate-form route and exact-SHA engineering acceptance before main merge; neither is a live grant or destination-specific clearance. G14-G17 remain UNPASSED.


The historical audit above is scoped to its recorded source SHAs. Jobs engine composition is now accepted at c719835; COMP-3A bounded.py is the released implementation scope. This source-recovery note does not alter that scope or establish live G14–G17 proof. New career claims since the bank audit require evidence review; pasted assistant summaries and planned publication experiments are not automatic factual upgrades.
