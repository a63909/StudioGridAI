"""Create the StudioGrid Production Orchestrator on Vertex AI Agent Engine."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import agentplatform

from agents.google_adk.cloud_agent import build_cloud_adk_app
from agents.google_adk.runtime import AGENT_ENGINE_LOCATION, MODEL_LOCATION, MODEL_NAME

PROJECT_ID = "studiogrid-ai"
STAGING_BUCKET = "gs://studiogrid-ai-agent-staging"
RUNTIME_SERVICE_ACCOUNT = (
    "studiogrid-agent-runtime@studiogrid-ai.iam.gserviceaccount.com"
)
TOOL_SERVER_URL = "https://studiogrid-tool-server-udlec7cupa-ey.a.run.app"
DISPLAY_NAME = "studiogrid-production-orchestrator-3b"
MILESTONE = "STUDIOGRID_AI_AGENT_ENGINE_CLOUD_3B"


def _resource_name(agent: object) -> str:
    api_resource = getattr(agent, "api_resource", None)
    return str(
        getattr(api_resource, "name", None)
        or getattr(agent, "name", None)
        or ""
    )


def _requirements(project_root: Path) -> list[str]:
    path = project_root / "agents" / "google_adk" / "requirements.agent_engine.txt"
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _classify_deploy_error(exc: Exception) -> str | None:
    message = str(exc).lower()
    if any(
        token in message
        for token in (
            "storage.objects",
            "storage.buckets",
            "staging bucket",
            "does not have storage",
        )
    ):
        return "STORAGE_IAM_BLOCKER"
    if any(
        token in message
        for token in (
            "iam.serviceaccounts.actas",
            "act as service_account",
            "service account user",
            "permission denied",
            "aiplatform.reasoningengines.create",
            "aiplatform.reasoningengines.update",
        )
    ):
        return "IAM_BLOCKER"
    return None


def _existing(client: agentplatform.Client) -> object | None:
    for item in client.agent_engines.list():
        if getattr(item, "display_name", None) == DISPLAY_NAME:
            return item
    return None


def _deployment_config(project_root: Path) -> dict:
    return {
        "staging_bucket": STAGING_BUCKET,
        "requirements": _requirements(project_root),
        "extra_packages": ["agents", "services"],
        "display_name": DISPLAY_NAME,
        "description": (
            "StudioGrid Production Orchestrator: ACTOR_DELAYED and "
            "SHOT_COMPLETED routes with private typed tools."
        ),
        "service_account": RUNTIME_SERVICE_ACCOUNT,
        "min_instances": 0,
        "max_instances": 1,
        "container_concurrency": 1,
        "python_version": "3.12",
        "agent_framework": "google-adk",
        "labels": {
            "application": "studiogrid-ai",
            "milestone": "agent-engine-cloud-3b",
        },
        "env_vars": {
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "GEMINI_MODEL": MODEL_NAME,
            "STUDIOGRID_MODEL_LOCATION": MODEL_LOCATION,
            "STUDIOGRID_AI_ENABLED": "true",
            "STUDIOGRID_TOOL_SERVER_URL": TOOL_SERVER_URL,
            "STUDIOGRID_TOOL_SERVER_AUTHENTICATED": "true",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-only", action="store_true")
    parser.add_argument(
        "--update-resource",
        help="Update this exact existing Agent Engine resource in place.",
    )
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Return the matching resource instead of creating another instance.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    if Path.cwd().resolve() != project_root:
        raise RuntimeError(f"Run deployment from repository root: {project_root}")
    client = agentplatform.Client(project=PROJECT_ID, location=AGENT_ENGINE_LOCATION)
    existing = _existing(client)
    if args.list_only:
        print(
            json.dumps(
                {
                    "displayName": DISPLAY_NAME,
                    "existingResource": _resource_name(existing) if existing else None,
                },
                sort_keys=True,
            )
        )
        return 0
    if existing is not None and args.reuse_existing:
        print(
            json.dumps(
                {
                    "status": "REUSED",
                    "resourceName": _resource_name(existing),
                    "displayName": DISPLAY_NAME,
                },
                sort_keys=True,
            )
        )
        return 0
    if existing is not None and not args.update_resource:
        raise RuntimeError(
            f"Agent Engine already exists; use --reuse-existing or --update-resource "
            f"{_resource_name(existing)}"
        )

    app = build_cloud_adk_app()
    try:
        if args.update_resource:
            remote = client.agent_engines.update(
                name=args.update_resource,
                agent=app,
                config=_deployment_config(project_root),
            )
            operation_status = "UPDATED"
        else:
            remote = client.agent_engines.create(
                agent=app,
                config=_deployment_config(project_root),
            )
            operation_status = "CREATED"
    except Exception as exc:
        blocker = _classify_deploy_error(exc)
        if blocker:
            print(f"{blocker}: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        raise

    print(
        json.dumps(
            {
                "status": operation_status,
                "milestone": MILESTONE,
                "resourceName": _resource_name(remote),
                "displayName": DISPLAY_NAME,
                "region": AGENT_ENGINE_LOCATION,
                "model": MODEL_NAME,
                "modelLocation": MODEL_LOCATION,
                "serviceAccount": RUNTIME_SERVICE_ACCOUNT,
                "stagingBucket": STAGING_BUCKET,
                "toolServerUrl": TOOL_SERVER_URL,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
