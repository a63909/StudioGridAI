# StudioGrid AI — 3:42 demo script

Target runtime: **3:42**. Hard stop: **3:50**. The official maximum is approximately four minutes, and only the first four minutes may be evaluated.

Record each command execution continuously and unedited. Use English narration or accurate English subtitles. Never expose browser profiles, credentials, tokens, raw commands in cloud logs, private prompts, or unrelated cloud resources.

## 0:00–0:20 — Open on the problem

**Visual:** Public `.run.app` URL, StudioGrid workspace, and LAST LIGHT title.

**Narration:**

> A film production day is a live constraint system. Actor delays, missing shots, locations, dependencies, completed work, and daylight can invalidate a plan in minutes. Traditional tools record the schedule. StudioGrid performs the operational work when reality changes.

## 0:20–0:40 — Agentic premise and safe routing

**Visual:** Architecture diagram. Trace browser → public web → private Control API → tool-less Gemini Command Router → typed validation. Then point to Agent Engine and the separate human boundary.

**Narration:**

> Give StudioGrid the production problem, not the steps. Raw language reaches only a Gemini classifier with no tools and no mutation authority. A strict typed allowlist then starts the deployed Google ADK workflow on Vertex AI Agent Engine. Specialists never receive the raw command.

## 0:40–0:52 — Clean synthetic state

**Visual:** Return to the public dashboard. Click **Reset Demo**. Show the unified command workspace.

**Narration:**

> This is the public Cloud Run application using fictional LAST LIGHT data. There is no localhost and no customer information.

## 0:52–1:42 — Primary Taskmaster proof: Coverage

**Visual:** Enter `Check SC_05 and make sure all required coverage is complete.` Click **Run** once. Keep the real loading state visible without cuts or speed-up. Show the contextual result.

**Narration:**

> I am giving StudioGrid one goal, not a workflow. The tool-less Gemini router classifies it as CHECK_COVERAGE. The private Control API invokes the remote Agent Engine, the ADK Production Orchestrator delegates to the Coverage Agent, and the specialist compares actual planned and completed shot state.

**Visual:** Show `SC_05`, `1/3`, `33.3%`, `SH_12`, `SH_13`, and `OPEN`. Expand **Technical details** briefly.

**Narration:**

> SC_05 has one of three required shots. SH_12 and SH_13 are missing, so the agent called the private typed tool and persisted an open alert. Here is the real model, agent, execution ID, and connected cloud path. No second user action was required.

## 1:42–2:33 — Secondary proof: Schedule

**Visual:** Reset. Enter `Maya Reed is 45 minutes late. Keep today's shoot on schedule.` Click **Run** once and retain the loading state.

**Narration:**

> Now the same input receives an exact supported actor-delay fact. Gemini routes the typed ACTOR_DELAY operation to the Schedule Agent. The specialist reasons over actors, scenes, locations, dependencies, completed work, schedule order, and daylight constraints.

**Visual:** Show FACT, PENDING, proposed order, evidence, benefit, risks, confidence, affected scenes, and unchanged current schedule.

**Narration:**

> The autonomous work is complete. Firestore now holds a PENDING recommendation with a concrete order and evidence. I did not choose a replacement scene or guide any intermediate step.

## 2:33–2:58 — Authority is not orchestration

**Visual:** Point to **Approve as human**, **Reject as human**, “the agent cannot make this decision,” and the unchanged schedule. Optionally expand Technical details.

**Narration:**

> Human approval is not manual orchestration. Routing, analysis, tool execution, and persistence are finished. A real schedule change affects an entire crew, so the model cannot authorize it. Autonomy where the agent has authority; deterministic human approval where a high-impact mutation crosses the authority boundary.

## 2:58–3:22 — Visible Google Cloud proof

**Visual:** Prepared sanitized views: Agent Engine resource, Cloud Run services, then Firestore or safe execution evidence.

**Narration:**

> The backend runs on Google Cloud. This is the deployed Agent Engine resource. Cloud Run exposes only the web publicly; the Control API and Tool Server require service identities. Firestore stores alerts, proposals, events, and execution evidence.

## 3:22–3:42 — Architecture and close

**Visual:** Full architecture diagram. Trace language to the isolated router, typed operation to ADK specialists, private tools to Firestore, and the separate human path.

**Narration:**

> StudioGrid separates untrusted language, agent reasoning, typed tools, durable state, and real-world authority. It does not just generate a production plan. It safely carries out the operational workflow when production reality changes.

**End card:**

```text
StudioGrid AI
AI Production Control Room
The Taskmaster
```

## Recording checks

- Public `.run.app` URL visible.
- Coverage command and result captured continuously and unedited.
- Schedule command and PENDING result captured continuously and unedited.
- No removed Maya/Daniel/Coverage direct-action controls are mentioned.
- Actual cloud latency retained.
- Backend Google Cloud proof readable.
- English narration/subtitles accurate.
- Export runtime ≤ 4:00; target 3:42.
- Publish publicly on YouTube or Vimeo only when the user explicitly authorizes it.
