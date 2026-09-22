# Retained harness-assumption diagnostics

These failures occurred while constructing the synthetic integration fixture. They were corrected only where the harness contradicted existing product contracts. They are retained for auditability and are not presented as product defects or final evidence.

1. The first generic Indeed alert lacked enough matching skill evidence, so the evaluator correctly returned `CONSIDER` with score 60 rather than `SHORTLISTED`. The synthetic alert was made contract-complete; no evaluator threshold was bypassed.
2. Lifecycle messages initially predated the persisted poll checkpoint and were correctly excluded. Synthetic timestamps were made chronological relative to the alert/checkpoint; no checkpoint was overwritten.
3. A duplicate setup run used the 48-hour reconciliation window against a ten-day-old alert and correctly excluded it. Replay was changed to exercise normal checkpoint overlap and later to re-deliver the complete fixture through a fresh daemon object in the same database.
4. The initial fake interview URL did not match the production Google Meet parser. It was replaced with a syntactically valid synthetic `meet.google.com` URL; no network call occurred.
5. An early assertion expected one total contact. Product behavior correctly produced two because the separate confirmation sender and the recruiting-thread sender are distinct. The final assertion requires unique recruiter authority within the recruiting thread.
6. An early analytics expectation excluded the manual draft, but the mailbox confirmation legitimately advanced it to submitted. The final report preserves the observed funnel and resume analytics instead of forcing a counter.
7. An early review assertion expected a generic manual-review reason. The actual durable reasons are `Packet has 2 unresolved question(s)` and `Interview requested but no explicit schedule confirmed`; the final harness asserts these exact product-visible reasons.

The final independent root run supersedes intermediate local runs. Its raw logs and structured report are included unchanged under `root-result/`.
