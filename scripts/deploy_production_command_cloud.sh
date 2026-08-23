#!/usr/bin/env bash
set -euo pipefail

PROJECT="studiogrid-ai"
REGION="europe-west3"
DEFAULT_ARTIFACT_REPOSITORY="studiogrid"
CONTROL_SERVICE="studiogrid-control-api"
WEB_SERVICE="studiogrid-web"
TOOL_SERVICE="studiogrid-tool-server"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud is required" >&2
  exit 1
fi
if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi
if ! command -v python >/dev/null 2>&1; then
  echo "python is required" >&2
  exit 1
fi
if [[ ! -f Dockerfile || ! -f apps/web/Dockerfile ]]; then
  echo "Run this script from the StudioGridAI repository root." >&2
  exit 1
fi

GIT_SHA="$(git rev-parse --short=12 HEAD)"
echo "Deploying StudioGrid Production Command from ${GIT_SHA}"
gcloud config set project "${PROJECT}" >/dev/null

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TEMP_DIR}"' EXIT

snapshot_runtime() {
  local phase="$1"
  local service
  for service in "${CONTROL_SERVICE}" "${WEB_SERVICE}" "${TOOL_SERVICE}"; do
    gcloud run services describe "${service}" \
      --project="${PROJECT}" \
      --region="${REGION}" \
      --format=json >"${TEMP_DIR}/${phase}-${service}.json"
    gcloud run services get-iam-policy "${service}" \
      --project="${PROJECT}" \
      --region="${REGION}" \
      --format=json >"${TEMP_DIR}/${phase}-${service}-iam.json"
  done
}

snapshot_runtime before

# Reuse the Artifact Registry Docker repository already backing the deployed
# Control API when possible. This avoids assuming a repository name that may
# differ between projects/deployment methods.
CURRENT_CONTROL_IMAGE="$(gcloud run services describe "${CONTROL_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format='value(spec.template.spec.containers[0].image)' 2>/dev/null || true)"

ARTIFACT_REPOSITORY=""
EXPECTED_PREFIX="${REGION}-docker.pkg.dev/${PROJECT}/"
if [[ "${CURRENT_CONTROL_IMAGE}" == "${EXPECTED_PREFIX}"* ]]; then
  IMAGE_REMAINDER="${CURRENT_CONTROL_IMAGE#${EXPECTED_PREFIX}}"
  ARTIFACT_REPOSITORY="${IMAGE_REMAINDER%%/*}"
fi

if [[ -z "${ARTIFACT_REPOSITORY}" ]]; then
  ARTIFACT_REPOSITORY="$(gcloud artifacts repositories list \
    --project="${PROJECT}" \
    --location="${REGION}" \
    --filter='format=DOCKER' \
    --format='value(name)' 2>/dev/null \
    | head -n 1 \
    | sed 's#.*/##' || true)"
fi

if [[ -z "${ARTIFACT_REPOSITORY}" ]]; then
  ARTIFACT_REPOSITORY="${DEFAULT_ARTIFACT_REPOSITORY}"
  echo "No Docker Artifact Registry repository found in ${REGION}; creating ${ARTIFACT_REPOSITORY}."
  gcloud artifacts repositories create "${ARTIFACT_REPOSITORY}" \
    --project="${PROJECT}" \
    --location="${REGION}" \
    --repository-format=docker \
    --description="StudioGrid deployment images" \
    --quiet
fi

# Fail early if the detected/created repository is not usable.
gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
  --project="${PROJECT}" \
  --location="${REGION}" >/dev/null

echo "Artifact Registry repository: ${ARTIFACT_REPOSITORY}"

REGISTRY="${REGION}-docker.pkg.dev/${PROJECT}/${ARTIFACT_REPOSITORY}"
CONTROL_IMAGE="${REGISTRY}/control-api:production-command-${GIT_SHA}"
WEB_IMAGE="${REGISTRY}/web:production-command-${GIT_SHA}"

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

# A service can have traffic pinned to a named/tagged older revision. In that
# state the deploy command creates a healthy revision but does not necessarily
# make it serve requests. Promote only the just-created, Ready revision of each
# allowed service; no IAM, identity, ingress, env, or other service setting is
# changed here.
promote_deployed_revision() {
  local service="$1"
  local revision
  local ready_status

  revision="$(gcloud run services describe "${service}" \
    --project="${PROJECT}" \
    --region="${REGION}" \
    --format='value(status.latestCreatedRevisionName)')"
  if [[ -z "${revision}" ]]; then
    echo "BLOCKER: ${service} has no latest created revision" >&2
    exit 1
  fi

  ready_status="$(gcloud run revisions describe "${revision}" \
    --project="${PROJECT}" \
    --region="${REGION}" \
    --format='value(status.conditions[0].status)')"
  if [[ "${ready_status}" != "True" ]]; then
    echo "BLOCKER: ${service} revision ${revision} is not Ready (${ready_status:-UNKNOWN})" >&2
    exit 1
  fi

  gcloud run services update-traffic "${service}" \
    --project="${PROJECT}" \
    --region="${REGION}" \
    --to-revisions="${revision}=100" \
    --quiet
  echo "Serving revision: ${service} -> ${revision} (100%)"
}

promote_deployed_revision "${CONTROL_SERVICE}"
promote_deployed_revision "${WEB_SERVICE}"

snapshot_runtime after

# A deploy is allowed to create revisions and change only the two container
# images. Fail closed if IAM, service identity, env vars, ingress, or the Tool
# Server changed. This script contains no IAM mutation commands.
SNAPSHOT_DIR="${TEMP_DIR}" \
CONTROL_SERVICE="${CONTROL_SERVICE}" \
WEB_SERVICE="${WEB_SERVICE}" \
TOOL_SERVICE="${TOOL_SERVICE}" \
python - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["SNAPSHOT_DIR"])


def load(phase: str, service: str, suffix: str = ""):
    return json.loads((root / f"{phase}-{service}{suffix}.json").read_text())


def normalized(value):
    if isinstance(value, dict):
        return {key: normalized(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        items = [normalized(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True))
    return value


def service_account(document):
    return document["spec"]["template"]["spec"].get("serviceAccountName")


def environment(document):
    containers = document["spec"]["template"]["spec"].get("containers") or []
    return normalized((containers[0] if containers else {}).get("env") or [])


def ingress(document):
    annotations = document.get("metadata", {}).get("annotations", {})
    return annotations.get("run.googleapis.com/ingress")


def require_equal(label, before, after):
    if normalized(before) != normalized(after):
        raise AssertionError(f"Protected Cloud Run configuration changed: {label}")


for service in (os.environ["CONTROL_SERVICE"], os.environ["WEB_SERVICE"]):
    before = load("before", service)
    after = load("after", service)
    require_equal(f"{service} service account", service_account(before), service_account(after))
    require_equal(f"{service} environment", environment(before), environment(after))
    require_equal(f"{service} ingress", ingress(before), ingress(after))
    require_equal(
        f"{service} IAM",
        load("before", service, "-iam"),
        load("after", service, "-iam"),
    )

tool = os.environ["TOOL_SERVICE"]
tool_before = load("before", tool)
tool_after = load("after", tool)
require_equal(f"{tool} spec", tool_before.get("spec"), tool_after.get("spec"))
require_equal(
    f"{tool} ready revision",
    tool_before.get("status", {}).get("latestReadyRevisionName"),
    tool_after.get("status", {}).get("latestReadyRevisionName"),
)
require_equal(
    f"{tool} IAM",
    load("before", tool, "-iam"),
    load("after", tool, "-iam"),
)

print("Protected Cloud Run configuration: PASS")
PY

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
COOKIE_JAR="${TEMP_DIR}/cookies.txt"
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
evidence = payload.get("technicalEvidence") or {}
fact = coverage.get("fact") or {}

assert routing.get("intent") == "CHECK_COVERAGE", routing
assert routing.get("target") == "COVERAGE_AGENT", routing
assert routing.get("modelName") == "gemini-3.6-flash", routing
assert alert.get("status") == "OPEN", alert
assert alert.get("sceneId") == "SC_05", alert
assert sorted(alert.get("missingShotIds") or []) == ["SH_12", "SH_13"], alert
assert sorted(fact.get("missingShotIds") or []) == ["SH_12", "SH_13"], fact
assert runtime.get("agentEngine") == "CONNECTED", runtime
assert runtime.get("gemini") == "CONNECTED", runtime
assert runtime.get("privateToolServer") == "CONNECTED", runtime
assert runtime.get("firestore") == "CONNECTED", runtime
assert evidence.get("agentName") == "COVERAGE_AGENT", evidence
assert evidence.get("modelName") == "gemini-3.6-flash", evidence
assert evidence.get("executionId"), evidence

print("Production Command Coverage smoke: PASS")
print("Missing shots:", ", ".join(fact.get("missingShotIds", [])))
print("Execution ID:", evidence.get("executionId"))
PY

echo "STUDIOGRID_AI_PRODUCTION_COMMAND_CLOUD_OK"
