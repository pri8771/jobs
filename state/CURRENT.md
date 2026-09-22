# Current Jobs state — V1.7 live campaign

Owner scope: **get V1.7 live and stop**. One Fable implementation worker/session and one owned five-minute heartbeat. ChatGPT remains lead/acceptor. Old three-lane and V2/V3 execution prose is superseded; no live-action authority is implied by engineering scope.

Reviewed main before this lead write: `3c34f9161b5149dba882e5cc7cd910a7104f8834`.

## Active worker and review surface

- Active implementation branch: `claude/serene-brown-g6uij0`.
- Latest reviewed worker code head: `a6b5ba34eface2cb205e3d9e3809c339d38b06b7` (2026-09-22T00:42:05Z), one commit beyond the PR #11 capsule head `2615f6b5b2a7eab9b98ef3f4e3b50eeb55c8e298`.
- Draft review container: PR #12, **Fable — V1.7 live implementation**. It is not accepted or merge-authorized.
- PR #11 remains unaccepted source/support for the V1.4/V1.5 capsule. PR #10 is inactive future inventory.
- New phase-0 commit adds the consolidated readiness report, V1.6 transport research, runtime `jsonschema`, credential-safe SQLAlchemy `URL` handling, and small mypy/Playwright/schema-test hygiene changes.

## Lead review verdict for phase 0

- `coordination/reviews/V17_READINESS_20260922.md` is accepted as the current **operational readiness inventory** only. It is not engineering or live-gate acceptance.
- V17-T01 transport research is useful support evidence: employer-credentialed ATS submit APIs are not a candidate transport. The browser-hosted form remains only a **candidate transport under policy/owner gating**; `A-V16-TRANSPORT` is not live-ready and G16 remains blocked until an exact job/packet/method is approved and destination policy permits it.
- The code hygiene changes at `a6b5ba34...` are **not engineering-accepted yet**. There are no exact-head GitHub checks/workflow runs for this code head, and the worker has not returned a coherent `READY_FOR_LEAD_REVIEW` batch with exact-head full validation. Worker-reported 253 passing tests apply to capsule baseline `2615f6b...`, not this head.

## Formal evidence state

- **G14 / V1.4:** P0A remains REWORK/IN_PROGRESS; no accepted genuine packet proof or independently validated receipt. `coordination/proofs/` on main still contains only README + schema.
- **G15 / V1.5:** engineering not accepted; no scoped genuine visible-browser prefill/upload proof.
- **G16 / V1.6:** engineering incomplete; no exact approved real system submission or correlated external confirmation. Candidate-hosted browser transport remains policy/authorization gated.
- **G17 / V1.7:** merged PR #3 lifecycle/CRM code is preserved, but no accepted genuine bounded recruiting-ingestion/lifecycle/replay proof.

None of V1.4–V1.7 is COMPLETE on current reviewed evidence. V1.7 requires accepted engineering plus genuine G14, G15, G16 and G17.

## Runtime/readiness evidence from active worker

- Fable reports local PostgreSQL 16.13 engineering availability, `postgresql+psycopg://` app connectivity, and full migration upgrade → downgrade → re-upgrade on its sandbox; this is useful worker evidence and is not the owner's production DB.
- Fable reports Playwright headless and headed-under-Xvfb engineering availability; this is not G15 evidence on the owner's real application page.
- This worker host does **not** have the private candidate profile, exact selected `resume_ai_software_engineer` bytes, owner browser session, Gmail OAuth/token, or bounded genuine recruiting thread set. None was accessed.
- Public Greenhouse egress is blocked on the worker sandbox, so the current proof job must be revalidated from an eligible host when G14 opens.

## Heartbeat / CI

- Single owned worker watcher is active on `worker/v14-real-proof` solely as the heartbeat publication branch for this Fable session.
- Latest verified heartbeat at this lead sync: #27, `773da18a0a7aceb5d5d2c752c187cff2ffa15ebd`, `2026-09-22T00:50:27Z`, five minutes after #26. Task text points to the active V1.7 branch above.
- Heartbeat issue-posting and hosted CI are still infrastructure-blocked: the latest heartbeat progress job failed before any step (`steps: []`, `runner_id: 0`). Do not call this green CI or a code-test failure.

## Immediate next action

Fable continues one session only:
1. Complete F145-01..06 as one coherent P0A/integration batch on the active branch, preserving the consolidated PR #11 review criteria.
2. Run targeted proof tests, full pytest, Ruff and mypy on the exact code head plus real PostgreSQL production-path validation available on the worker host.
3. Return `READY_FOR_LEAD_REVIEW`; ChatGPT reviews the actual diff/evidence and either accepts P0A or issues one smallest bounded repair.
4. While a lead/live gate is blocked, Fable may continue specifically permitted independent V1.5 engineering F145-07..11; it must not self-open private/browser/mailbox/submission gates.
5. After accepted P0A, move immediately to genuine G14 input readiness/proof on an eligible host. G15/G16/G17 follow only with their actual scoped grants.

`worker-pc` is online infrastructure but no new task is warranted: the active Fable host already has PostgreSQL/test capability, and the prior clean-sync task failed because fetch/test permissions were denied. Do not repeat it unchanged.

At accepted G14/G15/G16/G17 and V1.7 engineering completion: **STOP** and await new owner scope. No V2/V3 assignment.
