# Fresh public-cloud health check

Verified on **2026-08-21** against the deployed public application. No localhost, redeploy, IAM mutation, resource creation, or product-code change was used.

Public URL: <https://studiogrid-web-729921508335.europe-west3.run.app>

## Golden flow result

| Check | Real result | Status |
|---|---|---|
| Public web | Root followed two expected locale redirects to `/en/dashboard`; final HTTP `200` | PASS |
| RESET baseline | Synthetic LAST LIGHT state returned `3` completed shots and no active proposal | PASS |
| ACT_02 | Maya Reed, 45 minutes; real remote result was a `PENDING` Schedule Agent proposal using `gemini-3.6-flash` | PASS |
| No mutation before approval | Current schedule matched the recorded BEFORE schedule | PASS |
| Human approval | Proposal became `APPROVED`; decision actor type was `HUMAN`; schedule order changed | PASS |
| Audit categories | `FACT`, `INFERENCE`, `RECOMMENDATION`, and `HUMAN_DECISION` persisted | PASS |
| Refresh persistence | The same proposal ID and `APPROVED` status remained after a fresh GET | PASS |
| ACT_03 | Daniel, 30 minutes; a second generic proposal became `PENDING`, then `REJECTED` | PASS |
| Coverage | Coverage Agent persisted an `OPEN` alert for missing `SH_12` and `SH_13` | PASS |
| Runtime dependencies | Agent Engine, Gemini, private Tool Server, and Firestore all reported `CONNECTED` | PASS |
| Final RESET | Returned to `3` completed shots and no active proposal | PASS |

Safe execution identifiers from this run:

- demo session: `e8fdac29-f8e4-4d19-83dc-3e867717e0f8`;
- ACT_02 proposal: `36844442-3434-472a-b7eb-1af17eda53ea`;
- ACT_02 execution: `552c8d3f-d24b-4e11-ae6b-e45ff8a5d5d9`;
- ACT_03 proposal: `181df099-15c2-4958-948d-14d8f2b46830`;
- Coverage alert: `ee1fbe29-e776-431b-a3be-58255b6cea50`.

These are evidence references, not credentials.

## Public/private boundary

Read-only Cloud Run service and IAM inspection confirmed:

| Service | Ready revision | `allUsers` Run Invoker | Unauthenticated GET |
|---|---|---:|---:|
| `studiogrid-web` | `studiogrid-web-00007-zdw` | yes | `307` at `/`, then final `200` at `/en/dashboard` |
| `studiogrid-control-api` | `studiogrid-control-api-00004-qjc` | no | `403` |
| `studiogrid-tool-server` | `studiogrid-tool-server-00002-bpz` | no | `403` |

No service had an explicit minimum-instance annotation, so no always-on minimum was enabled by this milestone.

## Browser checks

- English dashboard and full action path: PASS.
- Mobile viewport `390×844`: PASS; page client/scroll width remained `375/375`, with no horizontal overflow.
- Russian UI: PASS.
- Real screenshots and exact limitations: [`evidence/EVIDENCE_INDEX.md`](evidence/EVIDENCE_INDEX.md).

## Deployment decision

No submission-blocking production regression was found. **No redeploy was performed.**
