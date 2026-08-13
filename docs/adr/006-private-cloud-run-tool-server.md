# ADR 006: Private Cloud Run Tool Server

**Status:** ACCEPTED FOR CLOUD TOOL-SERVER MILESTONE
**Verification date:** 2026-08-13

## Context

StudioGrid AI needs a private HTTP receiver for the existing typed FastAPI tools before the
Google Agent Engine runtime is deployed. The receiver must persist validated state in Firestore
without exposing human approval endpoints to the agent identity.

Target configuration:

- Google Cloud project: `studiogrid-ai`
- Cloud Run service: `studiogrid-tool-server`
- Cloud Run and future Agent Engine region: `europe-west3`
- Cloud Run service identity:
  `studiogrid-tool-server@studiogrid-ai.iam.gserviceaccount.com`
- allowed caller identity:
  `studiogrid-agent-runtime@studiogrid-ai.iam.gserviceaccount.com`
- Firestore: `(default)`, namespace `productions/last-light-demo`

## Official Google Cloud guidance verified

1. [Cloud Run access control](https://cloud.google.com/run/docs/securing/managing-access)
   documents private-by-default services and the `roles/run.invoker` permission boundary.
2. [Cloud Run service-to-service authentication](https://cloud.google.com/run/docs/authenticating/service-to-service)
   requires a Google-signed OIDC ID token and an audience equal to the receiving service URL
   (unless a supported custom audience is configured). The token is sent as a Bearer token.
3. [Cloud Run service identity](https://cloud.google.com/run/docs/configuring/services/service-identity)
   recommends a per-service user-managed service account and Application Default Credentials;
   the deployer needs `roles/iam.serviceAccountUser` on that service account.
4. [Cloud Run container contract](https://cloud.google.com/run/docs/container-contract)
   requires the ingress container to listen on `0.0.0.0` at the injected `PORT` value.
5. [Deploying services from source](https://cloud.google.com/run/docs/deploying-source-code)
   supports a repository Dockerfile and a Cloud Build-backed source deployment.

## Decision

### Container and runtime

Use the repository-root `Dockerfile` with build context `D:\StudioGridAI`:

- base image `python:3.12.11-slim-bookworm` (Python 3.12, satisfying Python 3.11+);
- pinned direct Cloud Run dependencies in `services/api/requirements.cloudrun.txt`;
- non-root `studiogrid` container user;
- entry point `uvicorn services.api.main:app --host 0.0.0.0 --port ${PORT}`;
- `.dockerignore` excludes Git data, local environments, credentials, frontend, tests, and docs.

The container includes only the existing API, the LAST LIGHT demo package, and the minimal
agent runtime metadata needed by the typed router. No service-account key is copied or mounted.

### Private receiving surface

Cloud Run IAM remains enabled. Deployment never uses `--allow-unauthenticated`, and no
`allUsers` binding is permitted.

`STUDIOGRID_AGENT_TOOL_SERVER_ONLY=true` makes the deployed process fail closed at the HTTP
surface: only `/health` and `/tools/agent/*` are reachable. Human schedule approval and rejection
routes return 404 in this mode. Local/full application mode keeps its existing routes.

The only new IAM binding is resource-level on `studiogrid-tool-server`:

```text
serviceAccount:studiogrid-agent-runtime@studiogrid-ai.iam.gserviceaccount.com
roles/run.invoker
```

No project-level invoker grant, `allUsers`, Owner, or Editor grant is part of this milestone.

### Authenticated caller

`FastAPIToolGateway` has two explicit modes:

- local: authentication disabled; existing `http://127.0.0.1` development flow is unchanged;
- cloud: authentication enabled; `google.oauth2.id_token.fetch_id_token` obtains an ephemeral
  Google-signed token from ADC/runtime service identity for the canonical Cloud Run URL audience.

Tokens exist only long enough to populate the outbound request header. They are neither logged
nor persisted. Agent Engine must later set the canonical service URL and enable authenticated
mode. No `GOOGLE_APPLICATION_CREDENTIALS` or service-account JSON is used.

### Deployment shape

The private service is deployed with the dedicated Tool Server service identity, zero minimum
instances, one maximum instance, one CPU, 512 MiB memory, and no Agent Engine resource.

## Verification requirements

- unauthenticated `/health` receives Cloud Run 401/403;
- an authorized Google identity reaches `/health` and sees Firestore `CONNECTED`;
- an authorized typed proposal request creates a PENDING proposal and audit events in
  `productions/last-light-demo`;
- malformed typed input receives Pydantic 422;
- approval/rejection paths are unavailable in cloud tool-server mode;
- service IAM contains the Agent runtime service-level invoker and no public principal.

## Consequences

The future Agent Engine deployment can call a verified private endpoint through service identity.
It still cannot approve or reject proposals. Human control remains outside this private agent-only
receiver. Agent Engine deployment is explicitly deferred to milestone 3B.

## Deployment verification (2026-08-13)

- canonical `status.url`:
  `https://studiogrid-tool-server-udlec7cupa-ey.a.run.app`
- supported regional URL:
  `https://studiogrid-tool-server-729921508335.europe-west3.run.app`
- active revision: `studiogrid-tool-server-00002-bpz`, 100% traffic
- Cloud Build confirmed base image `python:3.12.11-slim-bookworm`
- runtime identity:
  `studiogrid-tool-server@studiogrid-ai.iam.gserviceaccount.com`
- scaling: minimum zero (default), maximum one; one CPU; 512 MiB
- service IAM: exactly one resource-level binding, Agent runtime SA as `roles/run.invoker`
- public principals: none; unauthenticated health returned HTTP 403 on both service URLs
- authenticated canonical health: HTTP 200, Firestore `CONNECTED`
- malformed authenticated tool body: HTTP 422
- authenticated human approval route in agent-only mode: HTTP 404
- authenticated typed proposal: HTTP 200, status `PENDING`
- revision-2 Firestore evidence: proposal
  `b36dbdbc-6755-4912-99fe-1b23ad619b38`, correlation
  `cloud-smoke-3a-rev2-20260813-1625`, plus `SCHEDULE_PROPOSAL_CREATED` and `TOOL_CALLED`
  audit events
- cold-start durability: revision 2 hydrated the existing `state/current`; its prior `savedAt`
  value was preserved instead of re-seeding state

The authenticated smoke used the already-authorized deployer identity. Local impersonation of the
Agent runtime identity was intentionally not enabled because it would require the additional
`roles/iam.serviceAccountTokenCreator` role, which is outside this milestone. The future Agent
Engine runtime does not need impersonation: its own service identity obtains the ID token through
ADC/metadata, and its exact resource-level Cloud Run invoker binding is verified above.
