# V3 Permission Model Contract

Artifact: A-V30-PERMISSION-MODEL

## Permission classes

### P0_READ
Read internal/public data.

### P1_LOCAL_WRITE
Create/update local derived artifacts, drafts, analysis, review tasks.

### P2_EXTERNAL_PREP
Open or prepare an external workflow without committing the consequential action, e.g. assisted form prefill under policy.

### P3_USER_APPROVED_EXTERNAL
Consequential external write requiring explicit scoped user approval:
- application submit where allowed
- send recruiter message
- send connection request
- calendar mutation when consequential
- external profile update

### P4_BLOCKED
Never allowed by system policy/current platform constraints.

## Approval token

A P3 approval record must bind:
- user/actor
- action type
- exact target/entity
- exact artifact/version/hash
- method/transport
- issued_at
- expires_at or one-time use
- policy version
- optional limits

Changing the target/artifact/method invalidates the approval.

## Agent inheritance

An agent never has more permission than:
min(agent role, task permission, tool permission, policy decision, user approval).

No prompt can elevate permission.

## Safety

- CAPTCHA/MFA bypass remains P4_BLOCKED.
- fabricated candidate facts remain P4_BLOCKED.
- LinkedIn/Indeed auto-submit remains blocked/manual according to current policy.
- mock evidence never upgrades permission or confirms external success.

## Acceptance

- P0/P1 work proceeds without repeated user prompts.
- P3 cannot execute without valid scoped approval.
- expired approval is rejected.
- different packet/job cannot reuse approval.
- agent handoff cannot expand permission.
- all permission decisions are audited.
