# Small assignment, review and portfolio records

Use existing native record formats where present. These fields are an interoperability checklist, not a replacement schema or authority service. Namespace every ID as project/repo + native artifact/run/task; identical version numbers or task IDs across repos are not the same item.

## Assignment to a worker

- project/repository, canonical instruction ref and read SHA;
- actual implementation ref/worktree, assigned host/session and bounded write surface;
- native artifact ID, tiny task IDs and current scope ceiling;
- objective and why it is needed for the current live milestone;
- exact input contracts/source evidence and expected output;
- primary files/functions, non-goals and reuse opportunities;
- positive path, adverse tests, failure behavior and exact required validation;
- current dependency/lead/private/live grants with source references;
- evidence expected, reviewer, handoff path and next allowed independent work;
- cheapest capable available worker/model class, not an invented model name;
- native heartbeat rule and actual owner;
- dispatch status: PREPARED, ASSIGNED_WAITING_FOR_WORKER or RUNNING only after observed launch/ack.

An assignment cannot grant its own live authority. An unavailable field is null/UNKNOWN with a reason, not a fabricated value.

## Independent review recommendation

```
project/repository:
artifact and submission:
reviewer actual identity/role:
code SHA + relevant production tree/dependency/schema identity:
evidence SHA/run IDs and source refs:
contract read from ref/SHA:
reviewed paths:
checks actually executed + exact commands/exits/log refs:
worker-reported checks NOT independently repeated:
positive production-path coverage:
adversarial coverage:
real-proof evidence type and remaining gates:
findings with smallest reproducer/repair:
recommendation: RECOMMEND_ACCEPT | REWORK_FOUND | REVIEW_BLOCKED
formal acceptance authority and requested action:
next bounded independent task:
```

A recommendation is not ACCEPTED. Never sign a Codex review as ChatGPT or invent an independent second reviewer. A separate genuine reviewer may be used when available and authorized; a renamed self-review is not independent.

## Owner input / authorization request

One consolidated request per actual unresolved frontier:
project, gate, why required, exact account/host/destination/action, inputs/artifact hashes, bounded count/window/budget/expiry, effect/no-effect boundary, already available grants, missing fact/access, and what safe work continues. Keep secret values out of the request. Distinguish metadata permission from private-content access and prefill from submit.

## Portfolio rollup

One row per project:
repository | verified scope + source SHA | actual worker/branch/SHA | current artifact | engineering evidence | real gate status | review recommendation/authorized verdict ref | heartbeat interpretation | blocker | next action.

Use UNVERIFIED, ACCESS_BLOCKED or INTENTIONALLY_WAITING instead of guessed progress. Do not carry forward old passing counts as a fresh run. Record per-project last observation and changed-since-last-review. Rollup changes never advance a project artifact.

## End of management pass

What was read; what checks ran; which project-local records were written; actual dispatch acknowledgements; requests sent; still-blocked boundaries; owned processes/services that remain running; final management session state; next exact resume action. A stopped session does not promise background activity. Do not disable approved production operation merely because management ends; honor that service's own scope/expiry.
