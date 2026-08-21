# StudioGrid AI evidence

This directory contains safe, reproducible evidence for the deployed StudioGrid cloud product. It is contest-neutral historical product evidence; the current All Things Agentic submission package is in [`../all-things-agentic/`](../all-things-agentic/).

Never add credentials, identity tokens, service-account JSON, ADC files, raw prompts, chain-of-thought, private customer data, or unrelated cloud-console information.

## Verified cloud artifacts

### Vertex AI Agent Engine

[`agent-engine-cloud-3b.json`](agent-engine-cloud-3b.json) records:

- deployed Agent Engine resource and region;
- `gemini-3.6-flash`;
- Google ADK remote Schedule and Coverage execution;
- authenticated private Tool Server;
- Firestore PENDING proposal and coverage alert;
- safe execution/tool metadata;
- failure probe with zero invalid mutation;
- sampled Cloud Trace identifier.

It intentionally excludes prompts, messages, credentials, and chain-of-thought.

### Public cloud demo control plane

[`cloud-demo-3c/deployment.json`](cloud-demo-3c/deployment.json) records the verified public/private Cloud Run boundary, revisions, bounded scaling, runtime identities, no-localhost browser assertions, and golden-flow results.

[`cloud-demo-3c/browser-verification.md`](cloud-demo-3c/browser-verification.md) records EN/RU/mobile, ACT_02 approval, refresh persistence, Coverage, and final reset behavior.

[`cloud-demo-3c/README.md`](cloud-demo-3c/README.md) is the capture checklist and explicitly marks any console image that was not produced. Missing images must never be fabricated.

## Development assistance history

[`../IBM_BOB_DEVELOPMENT_LOG.md`](../IBM_BOB_DEVELOPMENT_LOG.md) is a preserved Phase 1 development-assistance log. It is not runtime evidence. Generated `Date: 2025` metadata was corrected transparently to `August 2026`; Git history retains the original lines. See [`../all-things-agentic/PROJECT_CHRONOLOGY.md`](../all-things-agentic/PROJECT_CHRONOLOGY.md).

## Evidence rules

- Prefer direct resource/API results and durable product state.
- Distinguish Git evidence, generated document claims, and filesystem metadata.
- Use synthetic LAST LIGHT data only.
- Redact browser profile details, account email, billing, and unrelated resources.
- A screenshot is evidence only if captured from the deployed product/cloud state it claims to show.
- A generated Markdown statement is not automatically proof of the underlying event.
