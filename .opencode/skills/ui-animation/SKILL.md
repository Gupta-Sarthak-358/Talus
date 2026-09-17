---
name: ui-animation
description: UI motion rules — springs, gestures, easing, and performance. Use when adding or reviewing animation in the dashboard.
---

# UI Animation (project-applicable rules)

Source: https://github.com/mblode/agent-skills (via finfin/awesome-frontend-skills). Vetted 2026-09-15: guidance-only, no executable payload. Reference `scripts/` (video motion reverse-engineering) intentionally NOT vendored or run.

## Core rules

- Animate for feedback, orientation, continuity, or deliberate delight. Frequent UI must stay invisible.
- Keep keyboard focus and repeated navigation immediate; never gate task completion on animation.
- Prefer CSS transitions for interruptible UI (keyframes restart on interruption; transitions retarget). Keyframes only for predetermined sequences.
- Implementation priority: CSS transitions > WAAPI > CSS keyframes > JS rAF.
- Tappable controls press on `:active` at 0ms; `touch-action: manipulation`.
- Never animate layout properties (`width`, `height`, `top`, `left`). Movement: `transform` and `opacity` only. State feedback may use `color`/`background-color`/`opacity`.
- Never `transition: all` — list properties explicitly.
- Disable transitions during theme switches.

## Easing defaults

| Element | Duration | Easing |
|---|---|---|
| Button press feedback | 100–160ms | `cubic-bezier(0.22, 1, 0.36, 1)` |
| Small popovers/tooltips | 125–200ms | `ease-out` |
| Dropdowns | 150–250ms | `cubic-bezier(0.22, 1, 0.36, 1)` |
| Modals/drawers | 200–350ms | `cubic-bezier(0.22, 1, 0.36, 1)` |
| Hover (colour/opacity) | 200ms | `ease` |
| Hover (transform/scale) | 100–150ms | enter curve |

Routine UI under 300ms. Avoid `ease-in` (lags user action).

## Accessibility

- Honor `prefers-reduced-motion`: replace spatial travel/looping with immediate state changes or restrained fades.
- Gate hover motion behind `@media (hover: hover) and (pointer: fine)`.

## Validation

- Grep diff for layout-property transitions and `transition: all`.
- Retoggle rapidly; confirm retarget (no restart-from-zero jumps).
- Confirm `will-change` only around animations, looping animations pause off-screen.
- Test touch on real device where possible.
