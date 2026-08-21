# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path


WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "eshm20-site-model-oq314-ingestion.yml"
)


def _text():
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_is_owner_only_issue_comment_and_trusted_main_fenced():
    text = _text()
    assert "issue_comment:" in text
    assert "types: [created]" in text
    assert "pull_request:" not in text
    assert "workflow_dispatch:" not in text
    assert "github.event.issue.number == 281" in text
    assert "github.event.comment.user.login == github.event.repository.owner.login" in text
    assert "github.event.comment.author_association == 'OWNER'" in text
    assert "ref: ${{ github.event.repository.default_branch }}" in text
    assert "EXECUTION_SHA=\"$(git rev-parse HEAD)\"" in text
    assert "ref: ${{ needs.validate-request.outputs.execution_sha }}" in text


def test_workflow_pins_exact_oq314_source_and_observes_container_identity():
    text = _text()
    assert "refs/tags/v3.14.0:refs/tags/v3.14.0" in text
    assert "9f044c93d72846421a8faa90ebf0a6afacdf3c20" in text
    assert "openquake/engine:3.14.0" in text
    assert "BASE_REPO_DIGEST" in text
    assert "grep -Eq '^openquake/engine@sha256:[0-9a-f]{64}$'" in text
    assert "grep -Eq '^sha256:[0-9a-f]{64}$'" in text
    assert "-e OPENBLAS_NUM_THREADS=1" in text
    assert "PYTHONPATH=/oq-engine:/workspace" in text


def test_workflow_runs_fixed_action_and_never_publishes_provider_rows():
    text = _text()
    assert "run_eshm20_site_model_oq314_ingestion_action.py" in text
    assert "oc-eq1-eshm20-site-model-oq314-ingestion-request-v1" in text
    assert "oc-eq1-eshm20-site-model-oq314-ingestion-result-v1" in text
    assert ".external_bytes_persisted == false" in text
    assert ".raw_rows_returned == false" in text
    assert ".publication_authorized == false" in text
    assert ".model_use_authorized == false" in text
    assert "Provider/raw publication authority: false; model-use authority: false." in text
    assert "bounded-derived-oq314-site-ingestion-action-evidence-only" in text


def test_provider_activity_is_after_dedup_and_publisher_has_no_checkout():
    text = _text()
    assert text.index("Prove complete issue-local dedup before external activity") < text.index(
        "Fetch exact OpenQuake v3.14.0 source"
    )
    publish = text.split("publish-ingestion-evidence:", 1)[1]
    assert "actions/checkout@" not in publish
    assert "contents: write" not in text
