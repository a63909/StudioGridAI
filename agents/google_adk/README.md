# Google Cloud Agent Builder Integration

## Status: Phase 2 — NOT YET IMPLEMENTED

This directory will contain the real Google Cloud Agent Builder / Gemini integration.

The Phase 1 placeholder is in `adk_adapter.py`.

---

## Prerequisites Before Phase 2 Implementation

### 1. Verify Current SDK

**Do not use API method names from memory or training data.**
The Agent Builder / Vertex AI Agents API changes frequently.

Before writing any code:
- Check the current official documentation at cloud.google.com
- Verify the current Python SDK package name and version
- Create `docs/adr/005-agent-builder-integration.md` recording the verified integration approach

### 2. Google Cloud Project

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
```

### 3. Application Default Credentials

**No service account JSON key files.**

For local development:
```bash
gcloud auth application-default login
```

For Cloud Run: attach a service account with least-privilege IAM roles.

### 4. Enable APIs

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

Verify the current Agent Builder API identifier before enabling it.

### 5. IAM Roles for Cloud Run Service Account

```
roles/aiplatform.user      — Gemini inference
roles/datastore.user       — Firestore read/write
roles/logging.logWriter    — Cloud Logging
roles/storage.objectViewer — Cloud Storage
```

---

## Phase 2 Architecture

```
Agent Builder Runtime
  └── PRODUCTION_ORCHESTRATOR (Gemini model)
        ├── tool declarations → FastAPI Tool Server
        ├── SCHEDULE_AGENT (Gemini model)
        ├── COVERAGE_AGENT (Gemini model)
        ├── CONTINUITY_AGENT (Gemini model)
        ├── PRODUCTION_RISK_AGENT (Gemini model)
        └── WRAP_REPORT_AGENT (deterministic, no model needed)
```

FastAPI Tool Server receives authenticated calls from Agent Builder.
All tool calls pass through: schema validation → authorization → approval gate → audit.

---

## UI Mode Indicator

Phase 1: `DEV MODE — AI NOT CONNECTED`
Phase 2: `PRODUCTION — Gemini [model-version]`

The UI always shows current mode honestly.
