# All Things Agentic submission checklist

Official submission window: **August 3, 2026 9:00 AM PT–August 31, 2026 5:00 PM PT**. Primary category: **The Taskmaster**.

## Required submission fields and assets

| Item | Copy/source | Status |
|---|---|---|
| Category | The Taskmaster | READY; select in Devpost |
| Project title | StudioGrid AI | READY |
| Tagline | AI Production Control Room | READY |
| Hosted project URL | <https://studiogrid-web-729921508335.europe-west3.run.app> | READY; currently public |
| English description | `DEVPOST_SUBMISSION_EN.md` | READY |
| Features/functionality | Golden workflow, autonomous agent work, bounded human mutation authority | READY |
| Technology list | Gemini 3.6 Flash, Google ADK, Vertex AI Agent Engine, Cloud Run, Firestore, Cloud Trace | READY |
| Data-source disclosure | Original fictional synthetic LAST LIGHT package; no customer data | READY |
| Findings/learnings and challenges | `DEVPOST_SUBMISSION_EN.md` | READY |
| Repository URL | No Git remote configured | **USER ACTION** |
| Repository visibility/access | Public, or private with `testing@devpost.com` and `cloudhackathons@google.com` access | **USER ACTION** |
| README spin-up instructions | Root `README.md` | READY |
| Architecture source | `architecture.mmd` | READY |
| Architecture image | `assets/studiogrid-architecture.png`, 3000×2200 | READY |
| Demo video | English or accurate English subtitles; public YouTube/Vimeo; maximum 4:00 | **USER ACTION: record, review, upload** |
| Application in action | Continuous ACT_02 action plus Coverage | SCRIPT/SHOTLIST READY |
| Visible Google Cloud backend proof | Agent Engine, Cloud Run, Firestore/safe evidence | CAPTURE PLAN READY; two sanitized console stills remain manual |
| Testing access | Public web requires no login; private services remain protected | READY |
| Entrant eligibility, age, residence, sanctions, conflict, ownership declarations | Cannot be inferred from source code or workstation metadata | **USER MUST CONFIRM BEFORE SUBMISSION** |
| Terms/privacy consents and final representations | Devpost form | **USER ACTION** |

## Technical quality gate

| Check | Result |
|---|---|
| New-project Git chronology | PASS on available Git evidence; root commit 2026-08-11 and no pre-window commit found |
| Mandatory Gemini 3.5+ | PASS — `gemini-3.6-flash` |
| Google Agent Framework | PASS — Google ADK 2.6.3 |
| Google Cloud infrastructure | PASS — Cloud Run and Firestore; Agent Engine/Trace also used |
| Public-cloud golden smoke | PASS — see `FRESH_CLOUD_HEALTH.md` |
| Backend tests | PASS — 100 |
| Frontend tests | PASS — 12 |
| Lint | PASS |
| Typecheck | PASS |
| Production build | PASS |
| Production dependency audit | PASS — 0 vulnerabilities |
| Secret/public-repo audit | PASS for local checkpoint |

## Low-risk bonus drafts

- Technical article draft: `BONUS_ARTICLE_DRAFT_EN.md`; includes the required hackathon disclosure. **Do not publish without explicit approval.**
- Social draft: `BONUS_SOCIAL_POST_EN.md`; includes `#AllThingsAgenticHackathon`. **Do not publish without explicit approval.**
- No extra model was added merely for bonus points.

## Final user-only sequence

1. Confirm personal eligibility and legal/ownership representations against the official rules.
2. Choose the repository destination and visibility; review, authorize, and perform push.
3. Manually capture sanitized Agent Engine and Firestore stills if they will be used.
4. Record the scripted video, verify runtime at 1× is at most 4:00, and ensure the continuous live action and Google Cloud proof are readable.
5. Upload the video publicly to YouTube or Vimeo.
6. Optionally publish the article and social post, then add their URLs.
7. Paste the English copy and links into Devpost, select The Taskmaster, preview everything, and submit before the deadline.

No repository push, video upload, publication, or Devpost submission is authorized by this checklist.
