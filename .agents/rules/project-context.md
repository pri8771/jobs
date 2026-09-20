# Jobs Automation Workspace Rule

This workspace is a portable job-search automation project.

Canonical contract:
- AGENTS.md

Canonical product/architecture:
- docs/PROJECT_SPEC.md
- docs/ARCHITECTURE.md
- docs/PLATFORM_CONSTRAINTS.md
- docs/DATA_MODEL.md
- docs/ROADMAP.md

Current execution state:
- state/CURRENT.md
- state/DECISIONS.md

Rules:
- Work only on the active checkpoint unless the user explicitly changes scope.
- Update state/CURRENT.md at the end of meaningful work.
- Do not invent personal application facts.
- Do not bypass platform rules or anti-bot controls.
- No auto-submit without an explicit current AUTO_ALLOWED policy decision.
- Keep implementation independent of Antigravity itself.
