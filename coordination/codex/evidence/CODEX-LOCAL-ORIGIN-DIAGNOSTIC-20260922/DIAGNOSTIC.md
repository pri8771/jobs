# J20-01 mutation safety diagnostic — first gap

Engineering evidence only. Source, tests, and native coordination remain unchanged. No acceptance, browser execution, mailbox/model/application action, scheduler change, spend, deployment, or merge occurred.

## Source and authority

- Origin verified: `https://github.com/pri8771/jobs.git`
- Accepted source: `413a18ee13ee049f57651ddd7060fd98fafad5f9`
- Tree: `f40e443a084e4a2e5c6a4ac7cbc4f6dcf791cfa6`
- Checkout: `/Users/pchordia/Downloads/swarm_codex/review/jobs-config-status-source` (clean before and after)
- Python import path verified to the accepted checkout; shared venv editable checkout was not used.
- Coordination: `codex/portfolio-review-20260922` at `4fb94fa544476f7d10d99a6bc8b097c94450f1c2`, clean when inspected.
- Release: final section of `coordination/codex/GOAL_20260922.md`, against `coordination/artifacts/A-V20-CONTROL-CENTER.md`.

## Inventory and result

Source search found one HTTP handler with `do_GET` and `do_POST` and one mutation route: `POST /api/reviews/{id}/resolve` (`server.py:894`). It sets the selected task status and resolution notes then commits (`server.py:914-920`). Authorization executes before route parsing, body parsing, or DB session entry (`server.py:890`).

The source-bound reproducer exercised 20 cases against synthetic PostgreSQL. Each negative compared every column of every table before and after, and counted production handler DB session entries. Each positive proved only the selected task's `status` and `payload_json` changed; all other tables remained identical.

| Case group | Observed result | DB effect |
|---|---|---|
| Remote IPv4/IPv6 without token | 403 | No session entry; no mutation |
| Remote with spoofed local Host/Origin/forwarded-IP headers | 403 | No session entry; no mutation |
| Remote supplied token when token is unconfigured | 403 | No session entry; no mutation |
| Configured token missing/wrong, including loopback missing token | 401 | No session entry; no mutation |
| Default tokenless IPv4/IPv6 loopback | 200 | Selected task completed with synthetic notes |
| Local write disabled or invalid enable value | 403 | No session entry; no mutation |
| Remote exact operator token or Bearer token | 200 | Selected task completed with synthetic notes |
| Valid remote token while local write is disabled | 200 | Selected task completed with synthetic notes |
| PUT/PATCH/DELETE/OPTIONS/HEAD via actual inherited HTTP dispatcher | 501 | No session entry; no mutation |
| Foreign Origin, text/plain body, tokenless loopback | **200** | **Selected review task completion committed** |

## First gap and causal diagnosis

The tokenless-local branch trusts the TCP peer alone (`server.py:870-875`). It ignores explicit evidence that the request was initiated by a foreign origin. Reproduced input:

```text
POST /api/reviews/{synthetic-task-uuid}/resolve
client_address = 127.0.0.1
Host: 127.0.0.1:8765
Origin: https://foreign-origin.example
Content-Type: text/plain
No operator token configured or supplied
Body: {"resolution_notes": "Synthetic diagnostic: foreign_origin_tokenless_loopback"}
```

The handler returns 200 and durably changes the pending task to completed. Because JSON parsing does not require `application/json` (`server.py:904-906`), a foreign-origin simple-POST shape reaches the mutation directly. A loopback peer does not by itself establish that the initiating browser origin is the trusted local operator.

This is a local operator authorization-boundary gap. It is **not** evidence that a remote TCP client bypassed token checks; those checks passed. Browser delivery, CORS/private-network enforcement, DNS rebinding, and end-to-end exploitation were not exercised or claimed. The safety interpretation for lead review is that an explicitly foreign initiating origin must not acquire operator authority solely from a loopback TCP peer.

## Smallest repair proposal

At the existing tokenless-local authorization gate, reject an explicitly foreign Origin (including opaque/null or malformed origins) and cross-site browser metadata before accepting loopback; retain same-origin dashboard requests and local tools without browser Origin headers. An explicitly valid operator token remains the existing authorization path. Use canonical origin parsing rather than substring matching. This can remain confined to the existing authorization helper plus focused header-matrix regression coverage after a bounded repair release.

Stop-at-first-gap honored: no later read-completeness checks, task-type/status mutation probes, new UI, or source repairs were attempted.

## Reproduction and cleanup

Command (exit 0):

```sh
PYTHONPATH=/Users/pchordia/Downloads/swarm_codex/review/jobs-config-status-source/src:/Users/pchordia/Downloads/swarm_codex/review/jobs-config-status-source /Users/pchordia/Downloads/swarm_codex/review/jobs-source/.venv/bin/python /tmp/jobs-control-safety-diagnostic-20260922/reproduce.py > /tmp/jobs-control-safety-diagnostic-20260922/run.log 2>&1
```

The script connects only to the owned Unix socket `/var/folders/fg/lmdhrms177s93m879bkgvjzr0000gn/T/jobs-proof-pg-7_ashjwd`, verifies port 56422 and empty `listen_addresses`, creates a unique `j20_safety_<uuid>` DB, and drops precisely that DB in `finally`. Final database count for its exact name: **0**. It does not stop or alter the shared PostgreSQL service or any other database. No HTTP listener was opened.

Artifacts: `reproduce.py`, `run.log`, `result.json` (full synthetic row diffs and outcomes), `SHA256SUMS`. The first successful run already proved cleanup0; a repeat after correcting only source-line metadata also proves cleanup0. An unrelated output-summary one-liner had a Python quoting error after the first run; it performed no database/source action and did not affect the diagnostic.
