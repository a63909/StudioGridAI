# All Things Agentic — official requirements verification

Verified against the live official pages on **2026-08-21**. The Official Rules are binding; the overview, FAQ, Resources, and Updates clarify presentation and judging expectations.

## Official sources

- Overview: <https://allthingsagentichackathon.devpost.com/>
- Official Rules: <https://allthingsagentichackathon.devpost.com/rules>
- FAQ: <https://allthingsagentichackathon.devpost.com/details/faqs>
- Resources: <https://allthingsagentichackathon.devpost.com/resources>
- Updates: <https://allthingsagentichackathon.devpost.com/updates>

## Requirement map

| Requirement | Official source | StudioGrid evidence | Status |
|---|---|---|---|
| Submit during August 3, 2026 9:00 AM PT–August 31, 2026 5:00 PM PT | Rules §4 | Deadline recorded here and in `SUBMISSION_CHECKLIST.md` | PASS for preparation; submission is a user action |
| Entrant is above the age of majority, has Internet access, is not in an excluded location or sanctions category, and has no listed conflict | Rules §3; FAQ “Teams & Eligibility” | Cannot be established from repository or workstation metadata | **NEEDS USER CONFIRMATION** |
| Russia is among the explicitly excluded places of residence | Rules §§intro, 3; FAQ | A workstation path, locale, or timezone is not proof of legal residence. If the entrant is a resident of Russia, the official wording says the entrant is not eligible | **NEEDS USER CONFIRMATION BEFORE SUBMISSION** |
| New projects only: project created during the Submission Period | Rules §6; FAQ “Can I submit an existing project?” | `PROJECT_CHRONOLOGY.md`; earliest reachable commit `6d2adcc…`, author and commit date 2026-08-11; no commit before the contest cutoff found | PASS on available Git evidence |
| Standard frameworks, libraries, starter templates, and AI coding assistants are permitted; disclose other pre-existing work | Rules §6; FAQ “Using AI to help you Build” | Codex and historical IBM Bob assistance are disclosed in repository documentation; no pre-August-3 StudioGrid Git artifact was found | PASS |
| Choose one category | Rules §6; FAQ | Primary category: **The Taskmaster** | PASS |
| Taskmaster: complete workflow, action rather than text-only chat | Overview “What to Build”; Rules §6; Resources “Taskmaster — in depth” | ACTOR_DELAYED → Production Orchestrator → Schedule Agent → typed proposal tool → durable PENDING proposal; human approval at mutation boundary; Coverage Agent performs a second operational workflow | PASS |
| Gemini 3.5 or newer via Gemini API or Vertex AI | Rules §6 | `gemini-3.6-flash`; `agents/google_adk/runtime.py`; live Agent Engine evidence | PASS |
| At least one Google Agent Framework | Rules §6; FAQ | Google ADK 2.6.3; `agents/google_adk/agent_graph.py`, `cloud_agent.py`, deployment requirements | PASS |
| At least one Google Cloud infrastructure service | Rules §6; FAQ | Cloud Run, Firestore, Vertex AI Agent Engine, Cloud Trace | PASS |
| Project installs/runs consistently and matches submitted claims | Rules §6 “Functionality” | 100 backend tests; 12 frontend tests; lint/typecheck/build; fresh ACT_02, ACT_03, Coverage cloud smoke in `FRESH_CLOUD_HEALTH.md` | PASS |
| Authorized use of third-party SDKs/data and compliance with licenses | Rules §6 | Open-source dependencies; MIT repository license; synthetic LAST LIGHT data; no customer data | PASS for documented assets; entrant retains final ownership confirmation |
| English application/submission materials, or English translations/subtitles | Rules §6 | English UI and primary English copy/video script; Russian UI/copy is additional | PASS |
| Original work, ownership, and no third-party rights violation | Rules §6 | Original synthetic film package and source repository | **NEEDS USER CONFIRMATION** (legal representation) |
| Free working access for judging/testing if a live project is supplied | Rules §6 “Testing” | Public Cloud Run web URL requires no localhost or login | PASS while service remains available |
| Select category in submission form | Rules §6 submission list | The Taskmaster | USER ACTION |
| Hosted project URL, encouraged | Overview; Rules §6 | <https://studiogrid-web-729921508335.europe-west3.run.app> | PASS |
| Text description: features, technologies, other data sources, findings/learnings | Rules §6 | `DEVPOST_SUBMISSION_EN.md` | PASS |
| Public or private GitHub/GitLab/Bitbucket repository URL | Rules §6 | No Git remote is currently configured | **NEEDS ACTION: create/select repository and push only after approval** |
| If private, grant access to `testing@devpost.com` and `cloudhackathons@google.com` | Rules §6; FAQ | Not applicable until repository visibility is chosen | USER ACTION IF PRIVATE |
| README step-by-step local/cloud spin-up instructions | Rules §6; FAQ | Root `README.md`, “Reproducibility and spin-up” | PASS |
| Clear architecture diagram | Rules §6 | `architecture.mmd`; visually verified 3000×2200 `assets/studiogrid-architecture.png` | PASS |
| Demo video: problem, value proposition, app in action, Google Cloud backend proof | Rules §6 | `VIDEO_SCRIPT_EN.md`, `VIDEO_SHOTLIST.md`; planned live `.run.app`, Agent Engine, Cloud Run, and Firestore proof | MATERIALS PASS; recording is USER ACTION |
| Video no longer than 4 minutes; only first four may be evaluated | Rules §6; FAQ | Script target 3:37 | PASS by design; final export must be checked |
| Video publicly visible on YouTube or Vimeo | Rules §6; FAQ | Not uploaded by this milestone | USER ACTION |
| Video in English or with English subtitles | Rules §6; FAQ | English script | PASS by design |
| Proof of Action: live, unedited execution visible | Rules §8; Updates self-check | `LIVE_CAPTURE_SEQUENCE.md` and shot list preserve one continuous ACT_02 execution and visible UI/database changes | PASS by design; final recording is USER ACTION |
| Keep submitted video, repository, and live app unchanged through judging | FAQ “Submitting” | Recorded in `SUBMISSION_CHECKLIST.md` | USER OPERATIONAL ACTION |
| Optional public build article with required hackathon-purpose disclosure | Rules §§6, 8 | `BONUS_ARTICLE_DRAFT_EN.md` contains exact disclosure | OPTIONAL; publish manually for up to 0.2 point |
| Optional social post with `#AllThingsAgenticHackathon` | Rules §§6, 8; overview | `BONUS_SOCIAL_POST_EN.md` | OPTIONAL; publish manually for up to 0.2 point |
| Optional additional Google AI models such as Gemma, Veo, or Lyria | Rules §§6, 8 | Deliberately not added during code freeze | OPTIONAL / NOT APPLICABLE |

## Judging criteria

| Criterion | Weight | Official emphasis | StudioGrid proof |
|---|---:|---|---|
| Innovation & Operational Utility | 40% | High-value autonomous action over chat; Taskmaster multi-step workflow | Real schedule analysis/proposal, generic second actor, Coverage workflow, and approved state mutation |
| Architectural Discipline & Tech Stack | 30% | Decoupling, state, scoped tools/security, failure handling | ADK agent separation, Agent Engine, private services, typed tools, Firestore, server-side approval gate, error traces |
| Demo & Production Readiness | 30% | Live unedited action, reproducibility, architecture, visible Google Cloud proof | Public URL, continuous ACT_02 capture, before/after, persistence, cloud console/resource proof, tests/build |

## Important wording notes

- The overview and FAQ consistently spell the required social hashtag `#AllThingsAgenticHackathon`. One Rules line displays an accidental space; this package uses the consistent no-space form.
- The binding judging text asks whether a Taskmaster agent completes a multi-step workflow without human intervention. StudioGrid must show that the agent autonomously performs the entire analysis, routing, evidence collection, and proposal creation. The single human decision is a deliberate authorization boundary for a consequential schedule mutation—not step-by-step guidance to the agent.
- Eligibility is a legal/personal fact. This repository can prove chronology and technology, but it cannot prove the entrant's residence, age, employment conflicts, sanctions status, or ownership representations.
