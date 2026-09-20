# V1.5 Fast-Start Acceptance Plan

Status: PREPARED IN ADVANCE / DO NOT EXECUTE UNTIL V1.4 IS ACCEPTED

Purpose: eliminate planning delay once V1.4 passes.

## V1.5 objective

Take one user-approved real job and an accepted V1.4 packet into a visible assisted browser session, fill only known/proven fields, stop at uncertainty or authentication barriers, and capture real external confirmation after the user submits.

## Preconditions

All must be true:
- V1.4 accepted by ChatGPT lead.
- exact proof job selected by user.
- job is still live.
- location/work arrangement is acceptable to user.
- exact packet reviewed.
- unresolved questions handled by user.
- policy says ASSISTED or otherwise permits this workflow.
- no live submission without user approval.

## Implementation checklist

1. Browser profile
- dedicated persistent Jobs Automation browser profile on trusted machine.
- cookies/browser state remain local, never Git.

2. Form inspection
- detect destination/ATS.
- enumerate fields.
- identify required/optional/file/self-ID fields.
- do not infer hidden candidate facts.

3. Safe field mapping
- map form field -> canonical packet/candidate field.
- attach provenance.
- ambiguous mappings stay unfilled.

4. File upload
- upload exact V1.4 resume artifact bytes/hash.
- cover letter only if exact accepted artifact is intended.

5. Manual barriers
Stop for:
- login,
- MFA,
- CAPTCHA,
- new consent,
- unknown question,
- EEO/self-ID,
- ambiguous field,
- policy conflict.

6. Pre-submit review
Before submission show:
- company/role,
- destination URL,
- resume variant/hash,
- cover letter hash if used,
- every filled field,
- every unanswered/manual field,
- policy decision.

7. Submission boundary
User performs final submit in V1.5 assisted mode unless separately authorized V1.6 auto path exists.

8. Confirmation
Capture at least one external signal:
- confirmation page text/reference,
- application status in employer/ATS account,
- confirmation email later.

Store confirmation as evidence; do not infer success from page navigation alone.

## V1.5 exit

One real application can be completed with automation assistance, exact packet integrity preserved, external confirmation captured, and application lifecycle correctly recorded.

Then prepare V1.6 controlled system-submit proof on an explicitly approved destination.
