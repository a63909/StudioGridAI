from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "deploy_production_command_cloud.sh"
).read_text(encoding="utf-8")


def test_deploy_updates_only_existing_control_and_web_images():
    assert SCRIPT.count("gcloud run deploy") == 2
    assert 'gcloud run deploy "${CONTROL_SERVICE}"' in SCRIPT
    assert 'gcloud run deploy "${WEB_SERVICE}"' in SCRIPT
    assert 'gcloud run deploy "${TOOL_SERVICE}"' not in SCRIPT

    forbidden = (
        "add-iam-policy-binding",
        "set-iam-policy",
        "iam service-accounts",
        "--service-account",
        "--set-env-vars",
        "--update-env-vars",
        "--remove-env-vars",
        "--ingress",
        "--allow-unauthenticated",
        "--no-allow-unauthenticated",
        "firestore databases",
        "reasoning-engines delete",
    )
    for value in forbidden:
        assert value not in SCRIPT


def test_deploy_promotes_only_ready_control_and_web_revisions():
    assert SCRIPT.count("gcloud run services update-traffic") == 1
    assert 'promote_deployed_revision "${CONTROL_SERVICE}"' in SCRIPT
    assert 'promote_deployed_revision "${WEB_SERVICE}"' in SCRIPT
    assert 'promote_deployed_revision "${TOOL_SERVICE}"' not in SCRIPT
    assert "status.latestCreatedRevisionName" in SCRIPT
    assert "status.conditions[0].status" in SCRIPT
    assert '--to-revisions="${revision}=100"' in SCRIPT


def test_artifact_repository_is_created_only_after_absence_check():
    absence_check = 'if [[ -z "${ARTIFACT_REPOSITORY}" ]]; then'
    create = 'gcloud artifacts repositories create "${ARTIFACT_REPOSITORY}"'

    assert SCRIPT.count(create) == 1
    assert SCRIPT.rindex(absence_check) < SCRIPT.index(create)


def test_live_smoke_requires_exact_coverage_and_real_execution_evidence():
    required_assertions = (
        'routing.get("intent") == "CHECK_COVERAGE"',
        'routing.get("target") == "COVERAGE_AGENT"',
        'alert.get("status") == "OPEN"',
        '["SH_12", "SH_13"]',
        'runtime.get("agentEngine") == "CONNECTED"',
        'runtime.get("gemini") == "CONNECTED"',
        'runtime.get("privateToolServer") == "CONNECTED"',
        'runtime.get("firestore") == "CONNECTED"',
        'evidence.get("executionId")',
    )
    for value in required_assertions:
        assert value in SCRIPT


def test_deploy_snapshots_protected_cloud_run_configuration():
    assert "snapshot_runtime before" in SCRIPT
    assert "snapshot_runtime after" in SCRIPT
    assert "get-iam-policy" in SCRIPT
    assert "Protected Cloud Run configuration: PASS" in SCRIPT
