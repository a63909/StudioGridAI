# Browser verification — cloud demo 3C

- Captured at: `2026-08-18T20:09:59.0216564Z`
- Public URL: `https://studiogrid-web-729921508335.europe-west3.run.app`
- Browser: Codex in-app browser, public network path, no localhost
- Responsive viewport: `390 × 844`

## Verified live behavior

- Bare URL resolved to `/en/dashboard`; English is deterministic default even with a Russian browser locale.
- EN showed `LAST LIGHT`, all cloud-status cards, fixed ACT_02/ACT_03 controls, schedule, coverage, timeline, and safe technical evidence.
- ACT_02 produced a real `PENDING` recommendation with `FACT`, `INFERENCE`, and `RECOMMENDATION` evidence.
- `Approve as human` produced `APPROVED_BY_HUMAN`, a changed before/after schedule, and a `HUMAN_DECISION` timeline event.
- Reload preserved the approved proposal and human decision.
- RU mobile flow independently ran RESET → ACT_02 → PENDING → `Одобрить как человек` → `Одобрено человеком` → before/after → refresh persistence.
- Expanded technical evidence showed only provider, agent/model, execution/session/correlation IDs, duration, verified tool name, evidence reference, and short rationale; no credentials, prompt, or chain-of-thought.
- The long mobile status has `clientWidth == scrollWidth` and `clientHeight == scrollHeight` after the wrap fix, so it does not overflow its metric card.
- A final clean RESET restored the deterministic synthetic seed while retaining historical proposal/execution evidence.
- After deployment, revision `studiogrid-web-00007-zdw` was rechecked in the public in-app browser: bare URL → `/en/dashboard`, EN and RU content rendered, and neither path used localhost.

## Capture note

The in-app browser screenshot command timed out after the final layout fix. No stale or fabricated screenshot was committed. The dedicated responsive pass ran at `390 × 844`; the post-deploy revision smoke ran at the browser's default `1280 × 720` because a second viewport override was not applied by the capability. The deployment metadata, live DOM assertions, real proposal/execution identifiers, and HTTP/IAM checks are recorded in `deployment.json`.
