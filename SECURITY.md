# Security policy

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, personal data, or private cloud identifiers. Use the repository host's private security-advisory feature when the public repository is created.

Include a concise description, reproduction steps, likely impact, and a suggested mitigation if available.

## Current trust boundaries

```text
[ Public browser ]
      │ HTTPS, fixed demo actions
      ▼
[ Public Cloud Run: studiogrid-web ]
      │ server-side Google ID token
      ▼
[ Private Cloud Run: studiogrid-control-api ]
      │ remote Agent Engine invocation
      ▼
[ Vertex AI Agent Engine / Google ADK / Gemini ]
      │ authenticated typed tool calls
      ▼
[ Private Cloud Run: studiogrid-tool-server ]
      │ validated durable writes
      ▼
[ Firestore ]

[ Human APPROVE / REJECT ]
      │ fixed browser action → BFF → private Control API
      └─ server-side ApprovalGate → mutation + HUMAN_DECISION
```

Only `studiogrid-web` is public. Unauthenticated calls to the Control API and Tool Server are denied by Cloud Run IAM.

## Public input boundary

The public Next.js route:

- accepts only RESET, fixed ACTOR_DELAY, APPROVE, REJECT, and CHECK_COVERAGE operations;
- caps request bodies at 2048 bytes;
- validates identifiers and exact actor/delay pairs;
- applies a demo session/IP rate limiter;
- keeps the demo session in an HTTP-only, Secure, SameSite=Lax cookie;
- never exposes private backend URLs or identity tokens to the browser.

The rate limiter is an in-process demo control and is not presented as a general distributed abuse-prevention system. The verified Cloud Run web service is capped to one instance for demo stability/cost control.

## Prompt-injection defense

The cloud demo does not accept arbitrary user prompts. Extra fields are rejected by Pydantic (`extra = forbid`). Safety does not rely on prompt wording:

- agents can create only PENDING schedule proposals;
- approve/reject/wrap/delete tools are HUMAN-only;
- high-impact state transitions are checked server-side;
- an AGENT or SYSTEM caller is rejected even if model instructions are compromised.

Tests: `tests/unit/test_phase2_agents.py`, `tests/unit/test_approval_gates.py`, and `tests/unit/test_tool_authorization.py`.

## Tool and state rules

- Agents call narrow typed capabilities, not a generic database tool.
- Agents never access Firestore directly.
- Tool Registry checks caller identity/type, schema, referenced entities, and state transitions.
- Agent execution IDs and correlation IDs must match their tool envelope.
- Invalid mutations fail closed and do not create a proposal.
- Human decisions are stored as separate auditable events.

## Secrets policy

| Material | Policy |
|---|---|
| Cloud credentials | ADC/workload identity; never service-account JSON in Git |
| Cloud Run ID tokens | Created server-side in memory; never logged or committed |
| Gemini access | Vertex AI identity; no browser API key |
| Environment configuration | Local `.env*` ignored; no secret values in examples |
| Future external credentials | Secret Manager only after an integration is explicitly implemented |

Repository and submission evidence must exclude private keys, ADC files, refresh tokens, identity tokens, email credentials, raw prompts, chain-of-thought, and customer data.

## Safe evidence

Allowed evidence is limited to operational metadata such as resource name, service/revision, model, agent, execution/correlation/session IDs, duration, tool name, status, and evidence references. Screenshots must hide account/profile information and unrelated cloud resources.

## Human approval requirements

At minimum, a HUMAN caller is required for:

1. schedule proposal approval;
2. schedule proposal rejection;
3. wrapping a shoot day;
4. deleting production data;
5. high/critical risk or continuity resolution where configured.

The public cloud golden flow verifies the schedule approval/rejection boundary.

## Demo data

LAST LIGHT is fictional synthetic production data. The public demo is not approved for customer, personal, confidential studio, or regulated data.

## Known security scope

- This is a hackathon demo, not a claim of legal or industry compliance certification.
- No real production integration is configured.
- Cloud resource IAM must be rechecked before every public demonstration.
- Submitted screenshots/video must be reviewed frame-by-frame for incidental secrets.
