#!/usr/bin/env bash
set -euo pipefail

PROJECT="studiogrid-ai"
REGION="europe-west3"
ARTIFACT_REPOSITORY="studiogrid"
CONTROL_SERVICE="studiogrid-control-api"
WEB_SERVICE="studiogrid-web"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud is required" >&2
  exit 1
fi
if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi
if [[ ! -f Dockerfile || ! -f apps/web/Dockerfile ]]; then
  echo "Run this script from the StudioGridAI repository root." >&2
  exit 1
fi

GIT_SHA="$(git rev-parse --short=12 HEAD)"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT}/${ARTIFACT_REPOSITORY}"
CONTROL_IMAGE="${REGISTRY}/control-api:production-command-${GIT_SHA}"
WEB_IMAGE="${REGISTRY}/web:production-command-${GIT_SHA}"

echo "Deploying StudioGrid Production Command from ${GIT_SHA}"
gcloud config set project "${PROJECT}" >/dev/null
gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
  --project="${PROJECT}" \
  --location="${REGION}" >/dev/null

# Build from the existing canonical Dockerfiles.
gcloud builds submit \
  --project="${PROJECT}" \
  --tag="${CONTROL_IMAGE}" \
  .

gcloud builds submit \
  --project="${PROJECT}" \
  --tag="${WEB_IMAGE}" \
  apps/web

# IMPORTANT: only update the image. Omitting IAM, service-account, ingress and
# env-var flags preserves the verified service configuration already deployed.
gcloud run deploy "${CONTROL_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --platform=managed \
  --image="${CONTROL_IMAGE}" \
  --quiet

gcloud run deploy "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --platform=managed \
  --image="${WEB_IMAGE}" \
  --quiet

CONTROL_URL="$(gcloud run services describe "${CONTROL_SERVICE}" --project="${PROJECT}" --region="${REGION}" --format='value(status.url)')"
WEB_URL="$(gcloud run services describe "${WEB_SERVICE}" --project="${PROJECT}" --region="${REGION}" --format='value(status.url)')"

echo "Control API: ${CONTROL_URL}"
echo "Public web:  ${WEB_URL}"

# Preserve the private boundary: an unauthenticated request must not succeed.
PRIVATE_STATUS="$(curl -sS -o /dev/null -w '%{http_code}' "${CONTROL_URL}/control/health" || true)"
if [[ "${PRIVATE_STATUS}" != "401" && "${PRIVATE_STATUS}" != "403" ]]; then
  echo "BLOCKER: private Control API returned HTTP ${PRIVATE_STATUS} without authentication" >&2
  exit 1
fi

echo "Private Control API boundary: PASS (${PRIVATE_STATUS})"

# Public app and BFF must be reachable.
curl -fsSL "${WEB_URL}" >/dev/null
COOKIE_JAR="$(mktemp)"
trap 'rm -f "${COOKIE_JAR}"' EXIT
curl -fsSL -c "${COOKIE_JAR}" "${WEB_URL}/api/demo" >/dev/null

# Reset the synthetic session, then prove the Taskmaster-style Coverage command:
# one natural-language goal -> Gemini routing -> existing ADK Coverage Agent ->
# typed private tool -> durable OPEN coverage alert.
curl -fsSL \
  -b "${COOKIE_JAR}" -c "${COOKIE_JAR}" \
  -H 'Content-Type: application/json' \
  -X POST \
  --data '{"operation":"RESET"}' \
  "${WEB_URL}/api/demo" >/dev/null

COMMAND_RESPONSE="$(curl -fsSL \
  -b "${COOKIE_JAR}" -c "${COOKIE_JAR}" \
  -H 'Content-Type: application/json' \
  -X POST \
  --data '{"operation":"COMMAND","command":"Check SC_05 and make sure all required coverage is complete."}' \
  "${WEB_URL}/api/demo")"

COMMAND_RESPONSE="${COMMAND_RESPONSE}" python - <<'PY'
import json
import os

payload = json.loads(os.environ["COMMAND_RESPONSE"])
routing = payload.get("commandRouting") or {}
coverage = payload.get("coverage") or {}
alert = coverage.get("alert") or {}
runtime = payload.get("runtime") or {}

assert routing.get("intent") == "CHECK_COVERAGE", routing
assert routing.get("target") == "COVERAGE_AGENT", routing
assert alert.get("status") == "OPEN", alert
assert runtime.get("agentEngine") == "CONNECTED", runtime
assert runtime.get("gemini") == "CONNECTED", runtime
assert runtime.get("privateToolServer") == "CONNECTED", runtime
assert runtime.get("firestore") == "CONNECTED", runtime

print("Production Command Coverage smoke: PASS")
print("Missing shots:", ", ".join((coverage.get("fact") or {}).get("missingShotIds", [])))
print("Execution ID:", (payload.get("technicalEvidence") or {}).get("executionId"))
PY

echo "STUDIOGRID_AI_PRODUCTION_COMMAND_CLOUD_OK"
