"""Google Cloud Agent Builder integration boundary — Phase 2.

This module is a placeholder in Phase 1.

Phase 2 implementation requirements:
1. Verify current official Agent Builder / Vertex AI Agent SDK version
   (API changes frequently — do not use method names from memory)
2. Set GOOGLE_CLOUD_PROJECT environment variable
3. Configure Application Default Credentials:
   gcloud auth application-default login
4. Enable APIs:
   - Vertex AI API (aiplatform.googleapis.com)
   - Agent Builder API (verify current product name)
5. IAM roles for Cloud Run service account:
   - roles/aiplatform.user
   - roles/datastore.user

Authentication: ADC only. No service account JSON key files.

See: docs/adr/002-agent-interfaces.md
"""
from __future__ import annotations

AGENT_BUILDER_STATUS = "NOT_CONNECTED"
GEMINI_STATUS = "NOT_CONNECTED"

PHASE_1_NOTICE = (
    "DEV MODE — AI NOT CONNECTED. "
    "Google Cloud Agent Builder integration is a Phase 2 component. "
    "All agent logic in Phase 1 uses deterministic implementations."
)


class AgentBuilderAdapter:
    """Phase 2: wraps real Google Cloud Agent Builder runtime.

    IMPORTANT: Before implementing this class in Phase 2, verify the
    current official Agent Builder SDK. Do not use API method names
    from memory or training data — the API changes frequently.

    Create docs/adr/005-agent-builder-integration.md before Phase 2 coding.
    """

    def __init__(self) -> None:
        raise NotImplementedError(
            "AgentBuilderAdapter is a Phase 2 component.\n"
            "See agents/google_adk/README.md for setup requirements."
        )
