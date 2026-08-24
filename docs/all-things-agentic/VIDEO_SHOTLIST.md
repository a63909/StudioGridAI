# StudioGrid AI — demo shot list

## Pre-recording state

- Use a clean browser profile or hide bookmarks/profile details.
- Capture at readable 1440p or 1080p; set browser zoom so command results remain legible.
- Close notifications and unrelated tabs.
- Pre-open only: public demo, sanitized Agent Engine console, Cloud Run services, Firestore/evidence, and the current architecture PNG.
- Rehearse once, then click **Reset Demo** immediately before the take.
- Do not expose Cloud Shell history, tokens, environment values, private logs, billing, emails, or unrelated projects.

## Ordered shots

| # | Time | Screen | Required visible proof | Audio/action | Edit rule |
|---:|---:|---|---|---|---|
| 1 | 0:00–0:20 | Public dashboard | `.run.app`, StudioGrid AI, LAST LIGHT, unified input | Production problem | Clean open |
| 2 | 0:20–0:40 | Architecture PNG | Tool-less router, typed validation, Agent Engine, separate human path | Safe agentic premise | Static cut allowed |
| 3 | 0:40–0:52 | Dashboard | Reset result; empty workspace | Explain synthetic data | Keep URL visible |
| 4 | 0:52–1:12 | Command input | Exact SC_05 Coverage command and real running state | Click Run once | **No cut, speed-up, or overlay hiding state** |
| 5 | 1:12–1:32 | Coverage result | `SC_05`, `1/3`, `33.3%`, `SH_12`, `SH_13`, `OPEN` | Explain autonomous result | Continue same capture |
| 6 | 1:32–1:42 | Technical details | `CHECK_COVERAGE`, Coverage Agent, model, execution ID, connected runtime | Explain durable proof | Continue same capture |
| 7 | 1:42–2:02 | Command input | Reset, exact Maya command, real running state | Click Run once | No cut during execution |
| 8 | 2:02–2:33 | Schedule result | FACT, PENDING, proposed order, evidence, benefit, risks, confidence | Explain completed autonomous work | Keep current schedule visible as unchanged |
| 9 | 2:33–2:58 | Authority area | Human approve/reject, agent cannot decide, optional Schedule execution ID | Explain autonomy vs authority | Do not approve unless this take includes mutation proof |
| 10 | 2:58–3:06 | Agent Engine console | Exact resource and region | Cloud proof | Sanitize surroundings |
| 11 | 3:06–3:14 | Cloud Run console | Public web; private Control API and Tool Server | IAM boundary | No IAM edits |
| 12 | 3:14–3:22 | Firestore/evidence | Persisted alert/proposal/execution metadata | Durability | No raw commands/customer data |
| 13 | 3:22–3:39 | Architecture PNG | Full language → router → typed agent workflow plus human boundary | Summarize design | Slow readable highlight |
| 14 | 3:39–3:42 | End card | Name, tagline, category | Final line | End before 3:50 |

## Backup proof if Cloud Console capture is unavailable

Use a sanitized read-only terminal view with non-secret outputs:

- `gcloud run services describe` for service name, region, URL, revision, scaling, and runtime service account;
- `gcloud run services get-iam-policy` showing `allUsers` only for `studiogrid-web`;
- the existing safe Agent Engine evidence JSON with the exact resource;
- sanitized Firestore/execution metadata from `docs/evidence/agent-engine-cloud-3b.json`.

Never show access tokens, ADC files, raw command logs, or service-account credentials.

## Final quality gate

- Watch the export at 1×.
- Independently measure duration.
- Confirm the first four minutes contain the full Coverage result, Schedule boundary, and Google Cloud proof.
- Confirm no legacy direct-action instructions remain.
- Confirm English audio/subtitles are synchronized.
- Confirm no third-party music/logo/content creates a rights issue.
- Publish as **public**, not unlisted, only after explicit user approval.
