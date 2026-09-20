# A-V12-CANDIDATE-PROVENANCE

- Type: data / evidence
- Phase: V1.2
- Status: PROPOSED
- Owner: Antigravity
- Reviewer: ChatGPT
- Dependencies: private candidate sources
- Downstream: safe screening answers, packet generation

## Purpose

Make every application-relevant candidate fact traceable without committing sensitive raw values to Git.

## Contract

Per field record:
- field_path
- presence
- provenance_class: user_confirmed | source_document | inferred | unknown
- source_reference
- verified_at
- reviewer
- allowed_for_application

## Acceptance

- inferred/unknown facts cannot become application truth
- private raw values need not be stored in Git
- provenance is machine-readable
- application services can request provenance for consequential answers
