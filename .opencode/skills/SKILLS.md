# Skills used in this project

Pinned excerpts vendored under `.opencode/skills/` on 2026-09-15. Full sources linked; nothing auto-installed globally.

## Security vetting (done before vendoring)

- Fetched each `SKILL.md` as text via WebFetch and read it fully. All 12 are **guidance-only markdown** — no shell commands to run, no `curl|bash`, no base64 blobs, no credential/env exfiltration, no "ignore previous instructions" or other prompt-injection markers.
- `install.ps1` / `install.py` (jshsakura repo) were read but **NOT executed**. `install.ps1` bulk-downloads the repo zip and copies all 175+ skills into global config — legitimate but broad. Decision: **selective vendoring only** (12/175), project-local under `.opencode/skills/`, so a future upstream edit can't silently change global agent behavior.
- `ui-animation` references local `scripts/` (ffmpeg/opencv video analysis) — intentionally **not vendored, not run**. Only the CSS/motion rules were kept.
- `pbakaus/impeccable frontend-design` path 404'd — skipped; `anti-ui-slop-reviewer` covers the same ground.

## From jshsakura/awesome-opencode-skills

| Skill | Used for |
|---|---|
| `fastapi-developer` | Backend API contracts, async correctness, stable error schema |
| `frontend-developer` | Scoped dashboard changes, loading/empty/error consistency |
| `ui-designer` | Interaction/state guidance for dashboard |
| `anti-ui-slop-reviewer` | Finish-gate review of dashboard |
| `accessibility-tester` | A11y audit of dashboard |
| `websocket-engineer` | Real-time transport reasoning (polling lifecycle, stale-data guard) |
| `security-auditor` | Backend security review |
| `python-pro` | Python change discipline |
| `machine-learning-engineer` | Training→serving parity, fallback behavior |
| `test-automator` | `tests/` regression coverage |

## From finfin/awesome-frontend-skills

| Skill | Source | Used for |
|---|---|---|
| `frontend-ui-engineering` | addyosmani/agent-skills | No-AI-slop tokens, a11y, responsive, state rules |
| `ui-animation` | mblode/agent-skills | transform/opacity-only motion, easing tokens, reduced-motion |

## Re-verify

Re-fetch any skill and diff before updating: guidance files can change upstream like any dependency.
