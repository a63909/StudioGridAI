# StudioGrid AI — demo shot list

## Pre-recording state

- Use a clean browser profile or hide bookmarks/profile details.
- Use a readable 1440p or 1080p desktop capture; set browser zoom so proposal evidence fits.
- Close notifications and unrelated tabs.
- Pre-open only: public demo, sanitized Agent Engine console view, Cloud Run services view, Firestore/evidence view, architecture PNG.
- Run one rehearsal, then **Reset Demo** immediately before the recorded take.
- Do not expose Cloud Shell history, access tokens, environment values, private logs, billing, emails, or unrelated projects.

## Ordered shots

| # | Time | Screen | Required visible proof | Audio/action | Edit rule |
|---:|---:|---|---|---|---|
| 1 | 0:00–0:18 | Public dashboard | `.run.app` address, StudioGrid AI, LAST LIGHT | Problem statement | Clean open |
| 2 | 0:18–0:35 | Architecture PNG | Public/private path and human boundary | Agentic premise | Static cut allowed |
| 3 | 0:35–0:48 | Dashboard | Reset result; four CONNECTED runtime cards | Explain synthetic data | Do not hide URL |
| 4 | 0:48–1:18 | Dashboard | Maya Reed, 45m, FACT, live running state | Click once and narrate orchestration | **No cut, speed-up, or overlay hiding state** |
| 5 | 1:18–1:48 | PENDING proposal | WHY, evidence, benefit, risks, confidence, reorder | Explain autonomous action | Continue same capture |
| 6 | 1:35–1:48 | Technical Evidence detail | Agent Engine provider, agent/model, execution/correlation IDs, duration, tool | Explain safe metadata | Continue same capture |
| 7 | 1:48–2:05 | Approval area | Human-only label and APPROVE button | Explain authority boundary; click approve | Continue same capture |
| 8 | 2:05–2:18 | Schedule/timeline | BEFORE/AFTER and `HUMAN_DECISION`; refresh persists | Explain real mutation | Continue same capture through refresh |
| 9 | 2:18–2:42 | Coverage | Actual count, missing `SH_12`, `SH_13`, OPEN alert | Click Coverage Check | One action, keep result readable |
| 10 | 2:42–2:52 | Agent Engine console | Exact resource, region, deployed status | Cloud proof | Sanitize surroundings |
| 11 | 2:52–3:02 | Cloud Run console | Public web; private Control API and Tool Server | Explain IAM boundary | Show ingress/auth without IAM edits |
| 12 | 3:02–3:12 | Firestore/evidence | Persisted proposal/execution/event metadata | Explain durability | No customer/raw prompt data |
| 13 | 3:12–3:34 | Architecture PNG | Full path plus external human authority | Summarize design | Slow readable highlight |
| 14 | 3:34–3:37 | End card | Name, tagline, category | Final line | End before 3:40 |

## Backup proof if Cloud Console capture is unavailable

The official rules accept `.run.app` URL proof and Vertex AI logs/Cloud Run views as examples. If authenticated console capture cannot be sanitized safely, use a read-only terminal view with these exact, non-secret outputs:

- `gcloud run services describe` showing service name, region, URL, revision, min/max scaling, and runtime service account.
- `gcloud run services get-iam-policy` showing `allUsers` only for `studiogrid-web`.
- `gcloud ai reasoning-engines` or the existing safe Agent Engine evidence JSON showing the exact resource.
- Sanitized Firestore/execution metadata from `docs/evidence/agent-engine-cloud-3b.json`.

Do not show an access token or Application Default Credentials file.

## Final quality gate

- Watch the export at 1× speed.
- Measure duration independently; do not rely only on editor timeline rounding.
- Verify first four minutes contain every required proof.
- Confirm English audio/subtitles are synchronized.
- Confirm no third-party music/logo/content creates a rights issue.
- Publish as **public**, not unlisted, only after explicit user approval.
