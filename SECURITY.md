# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | ✅        |

## Reporting a Vulnerability

Please do **NOT** open a public GitHub issue for security vulnerabilities.

Contact: [Create a private security advisory on GitHub]

Provide:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)

We aim to respond within 72 hours.

## Security Model

### Trust Boundaries

```
[ Browser ]
      │  HTTPS only
      ▼
[ Cloud Run — FastAPI Tool Server ]
      │
      ├── Pydantic schema validation (all inputs)
      ├── Tool Registry (per-tool authorization check)
      ├── Approval Gates (blocking gates for destructive mutations)
      ├── Audit Logger → Cloud Logging
      └── State Layer → Firestore (via ADC, no key files)

[ Google ADK / Vertex Gemini ]
      │  authenticated tool calls → FastAPI Tool Server only
      └── Agents NEVER access Firestore directly
```

### Rules

- All state mutations pass through the FastAPI Tool Server
- Agents (Gemini / Google ADK) never access Firestore directly
- All mutations: schema validation → authorization → approval gate → audit log
- Human Approval Gates block destructive mutations
- No secrets in code, environment files, or Git history

### Secrets Policy

| Secret | Storage |
|--------|---------|
| Partner API keys | Google Secret Manager only |
| Gemini API key (if explicit) | Google Secret Manager only |
| Firestore credentials | Application Default Credentials (ADC) — no key files |
| Google ADK / Agent Engine credentials | ADC — no key files |
| Any credential | Never in Git, never in .env committed |

### Human Approval Required For

1. Schedule changes (`approve_schedule_proposal`)
2. Continuity alert overrides (`resolve_continuity_alert` override)
3. CRITICAL / HIGH risk resolution (`resolve_risk`)
4. Marking scenes COMPLETE with open coverage alerts
5. Deleting production data
6. Wrapping a shoot day

### Partner Integration

Partner integration status is `NOT_CONFIGURED` until official contest partner
runtime requirements are confirmed. No fake connections claimed.

### Rate Limiting

Rate limiting is architecturally planned via Cloud Armor / FastAPI middleware.
Implementation in Phase 2 (Cloud Run deployment).
