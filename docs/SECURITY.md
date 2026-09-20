# Security and Privacy

## Secrets

Never commit:
- passwords
- session cookies
- browser profiles
- API keys
- OAuth client secrets intended to stay private
- OAuth refresh/access tokens
- MFA recovery codes
- government identifiers
- private demographic answers

Use:
- environment variables
- local ignored files
- OS keychain/credential manager
- secret manager for always-on deployment

## Git privacy

The repository is private, but private Git is not a secret manager.

Candidate facts that the user is comfortable versioning may be stored in private config. Highly sensitive facts should be injected at runtime.

## Gmail

Request the narrowest scopes that satisfy ingestion.

MVP should be read-only where possible.
Do not auto-delete, archive, or mark messages unless that feature is explicitly added and reviewed.

Persist provider IDs so the raw email can be located again.

## Browser sessions

Keep browser session/profile data local to the browser runner.
Do not serialize cookies into source control.
Do not add stealth or anti-detection plugins.

## External applications

Before submit:
- validate destination domain
- validate policy
- validate candidate facts
- validate packet version
- check idempotency key
- log intent

After submit:
- capture confirmation
- log outcome
- store external reference when available

## LLM privacy

Minimize what is sent to external models.
Prefer task-specific structured inputs.
Do not send unrelated email history.
Allow local-model routing for sensitive extraction if desired.

## Logs

Structured logs must redact:
- authorization headers
- tokens
- cookies
- passwords
- private keys
- full sensitive questionnaire answers when unnecessary

## Backups

Runtime database and artifacts should have encrypted backups before V1.0.
