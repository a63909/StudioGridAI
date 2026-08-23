#!/usr/bin/env bash
set -euo pipefail

PROJECT="studiogrid-ai"
REGION="europe-west3"
WEB_SERVICE="studiogrid-web"

for command in gcloud git curl cmp; do
  if ! command -v "${command}" >/dev/null 2>&1; then
    echo "${command} is required" >&2
    exit 1
  fi
done

if [[ ! -f apps/web/Dockerfile ]]; then
  echo "Run this script from the StudioGridAI repository root." >&2
  exit 1
fi

GIT_SHA="$(git rev-parse --short=12 HEAD)"
echo "Deploying contextual StudioGrid dashboard from ${GIT_SHA}"
gcloud config set project "${PROJECT}" >/dev/null

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TEMP_DIR}"' EXIT

# Capture the protected parts of the existing public web service. This deploy
# is allowed to change only the web container image/revision and traffic.
BEFORE_SERVICE_ACCOUNT="$(gcloud run services describe "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format='value(spec.template.spec.serviceAccountName)')"
BEFORE_INGRESS="$(gcloud run services describe "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format="value(metadata.annotations.'run.googleapis.com/ingress')")"
gcloud run services describe "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format='json(spec.template.spec.containers[0].env)' \
  >"${TEMP_DIR}/before-env.json"
gcloud run services get-iam-policy "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format=json \
  >"${TEMP_DIR}/before-iam.json"

CURRENT_IMAGE="$(gcloud run services describe "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format='value(spec.template.spec.containers[0].image)')"
EXPECTED_PREFIX="${REGION}-docker.pkg.dev/${PROJECT}/"

if [[ "${CURRENT_IMAGE}" != "${EXPECTED_PREFIX}"* ]]; then
  echo "BLOCKER: current web image is not in expected Artifact Registry region: ${CURRENT_IMAGE}" >&2
  exit 1
fi

IMAGE_REMAINDER="${CURRENT_IMAGE#${EXPECTED_PREFIX}}"
ARTIFACT_REPOSITORY="${IMAGE_REMAINDER%%/*}"
if [[ -z "${ARTIFACT_REPOSITORY}" ]]; then
  echo "BLOCKER: could not derive Artifact Registry repository from current web image" >&2
  exit 1
fi

gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
  --project="${PROJECT}" \
  --location="${REGION}" >/dev/null

WEB_IMAGE="${EXPECTED_PREFIX}${ARTIFACT_REPOSITORY}/web:contextual-dashboard-${GIT_SHA}"
echo "Artifact Registry repository: ${ARTIFACT_REPOSITORY}"
echo "Building web image: ${WEB_IMAGE}"

gcloud builds submit \
  --project="${PROJECT}" \
  --tag="${WEB_IMAGE}" \
  apps/web

# Update only the image. Omitting IAM, service-account, ingress and env flags
# preserves the verified Cloud Run service boundary.
gcloud run deploy "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --platform=managed \
  --image="${WEB_IMAGE}" \
  --quiet

REVISION="$(gcloud run services describe "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format='value(status.latestCreatedRevisionName)')"
if [[ -z "${REVISION}" ]]; then
  echo "BLOCKER: ${WEB_SERVICE} has no latest created revision" >&2
  exit 1
fi

READY_STATUS="$(gcloud run revisions describe "${REVISION}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format='value(status.conditions[0].status)')"
if [[ "${READY_STATUS}" != "True" ]]; then
  echo "BLOCKER: revision ${REVISION} is not Ready (${READY_STATUS:-UNKNOWN})" >&2
  exit 1
fi

gcloud run services update-traffic "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --to-revisions="${REVISION}=100" \
  --quiet

AFTER_SERVICE_ACCOUNT="$(gcloud run services describe "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format='value(spec.template.spec.serviceAccountName)')"
AFTER_INGRESS="$(gcloud run services describe "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format="value(metadata.annotations.'run.googleapis.com/ingress')")"
gcloud run services describe "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format='json(spec.template.spec.containers[0].env)' \
  >"${TEMP_DIR}/after-env.json"
gcloud run services get-iam-policy "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format=json \
  >"${TEMP_DIR}/after-iam.json"

if [[ "${BEFORE_SERVICE_ACCOUNT}" != "${AFTER_SERVICE_ACCOUNT}" ]]; then
  echo "BLOCKER: web runtime service account changed" >&2
  exit 1
fi
if [[ "${BEFORE_INGRESS}" != "${AFTER_INGRESS}" ]]; then
  echo "BLOCKER: web ingress changed" >&2
  exit 1
fi
if ! cmp -s "${TEMP_DIR}/before-env.json" "${TEMP_DIR}/after-env.json"; then
  echo "BLOCKER: web environment variables changed" >&2
  exit 1
fi
if ! cmp -s "${TEMP_DIR}/before-iam.json" "${TEMP_DIR}/after-iam.json"; then
  echo "BLOCKER: web IAM policy changed" >&2
  exit 1
fi

WEB_URL="$(gcloud run services describe "${WEB_SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --format='value(status.url)')"

curl -fsSL "${WEB_URL}/ru/dashboard" >/dev/null
curl -fsSL "${WEB_URL}/api/demo" >/dev/null

echo "Serving revision: ${WEB_SERVICE} -> ${REVISION} (100%)"
echo "Protected web configuration: PASS"
echo "Public dashboard: ${WEB_URL}/ru/dashboard"
echo "STUDIOGRID_CONTEXTUAL_DASHBOARD_WEB_OK"
