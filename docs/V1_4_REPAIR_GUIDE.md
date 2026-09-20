# V1.4 Repair Guide — File-Level Lead Notes

Status: URGENT / authoritative supplement to coordination/WORK_QUEUE.md

Purpose: remove ambiguity and shorten the path to V1.4 acceptance. This is not a new feature plan.

## 1. packet_builder.py — resume selection and artifact truth

File:
- src/jobs_automation/preparation/packet_builder.py

Current defects:
- build_packet() selects a variant name, then loops profile.resume.base_resume_paths and uses the first existing file.
- if no file exists, it synthesizes a stub resume.
- ArtifactModel rows are created with file:// URIs, but the bytes are never written.

Required changes:
- replace first-existing-file behavior with exact variant -> source resolution.
- remove synthetic resume fallback entirely from operational packet building.
- if selected source cannot be resolved/read, fail closed and create NEEDS_REVIEW or raise a dedicated preparation error.
- introduce a small local ArtifactStore abstraction/service for V1.4 rather than hard-coding fake file:// URIs.
- ArtifactStore should:
  - accept bytes/text,
  - atomically write to configured artifact root,
  - return canonical URI/path,
  - compute SHA-256 from the stored bytes,
  - support read-back verification.
- packet creation must only persist ArtifactModel after successful write + hash verification.
- packet hash should include resume variant identity plus final stored artifact hashes.

Suggested tests:
- selected family A cannot load family B source.
- missing selected resume -> no packet marked ready.
- artifact URI exists after build.
- read-back SHA-256 equals ArtifactModel.sha256.
- packet hash changes when final resume bytes change.

## 2. candidate_profile.py — explicit resume source mapping

File:
- src/jobs_automation/core/candidate_profile.py

Current defect:
- ResumeVersion has id/priority/emphasize but no exact source path.
- ResumeConfig has an unkeyed list of base_resume_paths.

Preferred minimal repair:
- add source_path (or equivalent) to ResumeVersion OR add an explicit resume_sources: dict[resume_id, path].
- maintain backward compatibility only if it remains fail-closed and unambiguous.
- default_resume_id must resolve to a configured exact source.
- validation should reject duplicate IDs and configured IDs without a resolvable source when operational preparation is requested.

Do not guess path by order.

## 3. db/models.py + Alembic — immutable resume attribution

Files:
- src/jobs_automation/db/models.py
- new migration under migrations/versions/

Implement ResumeVariantModel with durable identity required by docs/RESUME_OUTCOME_TRACKING.md.

Minimum fields:
- id UUID
- resume_family
- name / variant_id
- version
- parent_variant_id nullable
- source_reference / template version as appropriate
- target_job_id nullable
- target_role_family nullable
- tailoring_method
- model_provider nullable
- model_name nullable
- prompt_version nullable
- content_hash
- created_at
- superseded_at nullable

ApplicationPacketModel:
- add resume_variant_id FK, non-null for real/live-ready packets.

Migration:
- create resume_variant table,
- add application_packet.resume_variant_id,
- preserve compatibility with existing test/dev rows without fabricating live provenance.

Add relationships where helpful.

## 4. tailoring.py — remove hard-coded candidate truth

File:
- src/jobs_automation/preparation/tailoring.py

Current defects:
- CoverLetterDrafter prompt hard-codes Priyansh/Viatris/Thar/CMU/skills.
- fallback cover letter hard-codes candidate history.
- location logic hard-codes Pittsburgh.
- EEO logic auto-uses stored demographic values.
- model-based screening sends only the question and trusts resolved=true.

Required changes:
- CoverLetterDrafter must build evidence input only from canonical profile/evidence provided at runtime.
- no candidate name/employer/school/tenure/skill claim literals in operational implementation.
- no hard-coded city logic; derive from profile or leave unresolved.
- EEO/self-ID questions always unresolved/manual, even when demographic values exist.
- screening resolution must return provenance for each resolved answer.
- deterministic answers should cite canonical field paths, e.g.:
  work_authorization.authorized_to_work_in_us
- model-assisted answers must be given canonical evidence and cannot resolve a fact that evidence does not support.
- unsupported model resolved=true output must be rejected.

Recommended output structure:
- preserve answer text for downstream forms,
- add answer_provenance_json on ApplicationPacketModel OR equivalent durable packet metadata.

Each resolved answer should record:
- method: deterministic | model_assisted
- source field(s) / evidence ID(s)
- optional model/provider metadata
- confidence if useful

## 5. adapters/models.py — remove operational mock fallback

File:
- src/jobs_automation/adapters/models.py

Current defects:
- LiteLLMModelGateway defaults fallback_mock=True.
- if task config/model is missing, it returns MockModelGateway unconditionally, even before checking fallback_mock.
- exception path can silently fall back to MockModelGateway.
- MockModelGateway itself contains Priyansh-specific claims such as 8+ years Python and named employers.

Required changes:
- default real gateway behavior must fail closed.
- if task routing/model is missing in real mode -> explicit configuration error.
- provider failure in real mode -> explicit model failure, not mock content.
- MockModelGateway must be explicitly instantiated for tests/dev only.
- remove real-candidate-specific claims from MockModelGateway; use synthetic test content.
- expose origin metadata for model output:
  - provider/model,
  - deterministic,
  - explicit test/mock.

Real/live-ready packet must reject consequential content with origin=test/mock.

## 6. application packet provenance

Recommended minimal DB/model extension:
- application_packet.answer_provenance_json
- optional generation_metadata_json

Packet manifest should expose:
- candidate profile version
- resume family
- resume variant ID/version
- exact source reference
- exact artifact URI/hash
- cover-letter artifact URI/hash
- answers
- answer provenance
- unresolved questions
- model/provider origin
- packet hash

Do not claim independent verifiability if manifest only exists in terminal output.

## 7. EEO/manual regression cases

Always unresolved/manual:
- race
- ethnicity
- Hispanic/Latino identity
- gender/sex self-identification
- disability
- veteran status
- sexual orientation
- similar voluntary self-ID questions

Even if demographic_answers.values has data.

## 8. Adversarial screening tests

Add cases where fake/model output says:
- "Yes, 10 years Python" with no evidence.
- "No sponsorship needed" when canonical sponsorship is null.
- "Yes, willing to relocate" when relocation is null.
- "Yes, active clearance" with no evidence.

All must remain unresolved or be rejected.

Also test positive deterministic provenance:
- authorized_to_work_in_us=true -> answer Yes + field-path provenance.
- sponsorship fields explicitly false -> No + provenance.

## 9. V1.4 acceptance command/evidence bundle

Before READY FOR CHATGPT V1.4 RE-AUDIT, provide:
- migration filename
- changed file list
- pytest result/count
- ruff result
- mypy result
- GitHub Actions run/commit
- one packet manifest produced from real available resume bytes OR a clearly labeled non-live test fixture if private real source is not available to CI
- read-back artifact SHA verification evidence
- proof missing resume fails closed
- proof mock gateway cannot contaminate real packet
- proof EEO remains unresolved
- proof unsupported resolved=true model answer is rejected

## 10. Do not solve the wrong problem

Do not:
- chase zero unresolved questions,
- build new ATS adapters,
- connect Gmail,
- open live forms,
- add UI polish,
- add V2/V3 infra.

The only objective is to make V1.4 truthful, immutable, and independently auditable.
