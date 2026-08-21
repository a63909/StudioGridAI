# StudioGrid AI — 3:37 demo script

Target runtime: **3:37**. Hard stop: **3:50**. The official maximum is 4:00, and only the first four minutes may be evaluated.

Record the ACT_02 section as one continuous, unedited screen capture. Use English narration or burn in accurate English subtitles. Never expose browser profiles, credentials, tokens, private prompts, or unrelated cloud resources.

## 0:00–0:18 — Open on the problem

**Visual:** Public `.run.app` URL in the browser address bar; StudioGrid dashboard and LAST LIGHT title visible.

**Narration:**

> A film production day is a live constraint system. An actor is delayed, daylight is disappearing, locations have narrow windows, and every change affects multiple departments. Traditional tools record the plan. StudioGrid performs the operational work when reality changes.

## 0:18–0:35 — Agentic premise

**Visual:** Architecture diagram, centered on the action path; briefly highlight the separate human boundary.

**Narration:**

> StudioGrid is a deployed Google ADK multi-agent workflow on Vertex AI Agent Engine and Gemini 3.6 Flash. The agent may analyze, route, call tools, and persist a recommendation. It may not approve its own consequential schedule change.

## 0:35–0:48 — Reset and establish factual state

**Visual:** Return to public dashboard. Click **Reset Demo**. Show connected Agent Engine, Gemini, private Tool Server, and Firestore indicators.

**Narration:**

> This is the public Cloud Run application, using the fictional LAST LIGHT production package. I am resetting its synthetic state. There is no localhost and no customer data.

## 0:48–1:18 — Live, unedited Maya execution

**Visual:** Select Maya Reed and click **Simulate delay — 45 min** exactly once. Keep recording while the running state is visible. Do not cut or accelerate.

**Narration:**

> Maya Reed is now 45 minutes late. I am reporting the fact—not choosing a replacement scene or telling the agent how to reorder the day. The private Control API invokes the remote Agent Engine. Its Production Orchestrator delegates to the Schedule Agent, which reasons over actors, scenes, locations, completed shots, dependencies, schedule order, and daylight constraints.

## 1:18–1:48 — Proof of autonomous action

**Visual:** PENDING proposal. Pan or scroll through WHY, evidence, reorder, expected benefit, risks, and confidence. Expand Technical Evidence and show provider, agent, model, execution/correlation IDs, duration, tool name, and evidence reference.

**Narration:**

> The workflow has completed its autonomous work. The Schedule Agent called the typed `create_schedule_proposal` tool, and Firestore now holds this PENDING recommendation. Here are its rationale, factual evidence, concrete reorder, risks, confidence, and safe remote-execution metadata. No prompt or chain-of-thought is exposed.

## 1:48–2:18 — Safety boundary and real mutation

**Visual:** Point to “human only.” Click **Approve as human**. Show APPROVED state, schedule BEFORE/AFTER, and the `HUMAN_DECISION` event. Refresh the page and show the state remains.

**Narration:**

> The AI cannot apply it. Approval and rejection are server-side human-only tools, so prompt injection cannot grant the model that authority. I approve as the production manager. The Control API applies the already-specified reorder, records a HUMAN_DECISION, and Firestore preserves it across refresh.

## 2:18–2:42 — Coverage Agent

**Visual:** Click **Coverage Check**. Show factual count, OPEN alert, and missing `SH_12`, `SH_13`.

**Narration:**

> A second specialist performs another operational workflow. The Coverage Agent compares actual planned and completed shots. It finds that SH_12 and SH_13 are still missing and persists an open alert. This is computed from production state, not generated from a chat prompt.

## 2:42–3:12 — Visible Google Cloud proof

**Visual:** Three prepared cloud views, with unrelated data hidden: (1) Agent Engine resource and region; (2) Cloud Run services showing public web and private Control/Tool services; (3) Firestore record or safe execution evidence. Keep identifiers readable.

**Narration:**

> The backend is running on Google Cloud. This is the deployed Vertex AI Agent Engine resource in europe-west3. Cloud Run exposes only the web service publicly; the Control API and Tool Server require authenticated service identities. Firestore stores the proposal, event timeline, schedule state, and execution evidence.

## 3:12–3:37 — Architecture and close

**Visual:** Full architecture diagram. Animate or point along browser → web → private control → Agent Engine → agents/Gemini → private tools → Firestore, then the separate human path.

**Narration:**

> StudioGrid separates reasoning, tools, durable state, and authority. Gemini and ADK do the complex operational work; deterministic services enforce what the agent may change. StudioGrid AI does not just generate a production plan. It helps production adapt when reality changes.

**End card:**

```text
StudioGrid AI
AI Production Control Room
The Taskmaster
```

## Recording checks

- One continuous unedited capture from the ACT_02 click through PENDING result.
- Public `.run.app` URL visible.
- Actual loading time retained.
- Backend Google Cloud proof readable.
- English narration/subtitles accurate.
- Final exported runtime ≤ 4:00; target 3:37.
- Video set publicly visible on YouTube or Vimeo only when the user explicitly publishes it.
