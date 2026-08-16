# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json

import pytest

from scripts import run_eshm20_gsim_reference_runtime as subject


EXECUTION_SHA = "7" * 40
IMAGE_DIGEST = "sha256:" + "8" * 64


def _request(**updates):
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": EXECUTION_SHA,
        "requester": "test-owner",
    }
    payload.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def _gate_result():
    return {
        "gmm_identity": {
            "project_id": subject.gmm.PROJECT_ID,
            "project_path": subject.gmm.PROJECT_PATH,
            "commit_sha": subject.gmm.COMMIT_SHA,
            "repository_path": subject.gmm.REPOSITORY_PATH,
            "byte_count": subject.gmm.EXPECTED_BYTE_COUNT,
            "sha256": subject.gmm.EXPECTED_SHA256,
        },
        "openquake_reference": {
            "repository": subject.runtime.ENGINE_REPOSITORY,
            "tag": subject.runtime.ENGINE_TAG,
            "commit": subject.runtime.ENGINE_COMMIT,
            "version": subject.runtime.ENGINE_VERSION,
        },
        "reference_runtime_fingerprint": {
            "reference_recipe_match": True,
            "observation": {"container_image_digest": IMAGE_DIGEST},
        },
        "branch_count": 1,
        "branches": [
            {
                "branch_set_id": "bs1",
                "branch_id": "b1",
                "requested_gsim_token": "Example",
                "resolved_gsim_class": "Example",
                "constructor_accepted": True,
            }
        ],
        "unique_resolved_gsim_classes": ["Example"],
        "alias_requested_tokens": [],
        "engine_source_commit_verified": True,
        "reference_runtime_observation_validated": True,
        "alias_resolution_verified": True,
        "registry_resolution_verified": True,
        "constructor_compatibility_verified": True,
        "exact_source_constructor_compatibility_verified": True,
        "gsim_request_runtime_compatibility_verified": False,
        "full_hazard_compatibility_verified": False,
        "site_model_compatibility_verified": False,
        "vulnerability_compatibility_verified": False,
        "reference_run_verified": False,
        "scientific_validity_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
        "provider_secret": "must-not-copy",
    }


def test_request_is_bound_to_issue_and_exact_trusted_sha():
    parsed = subject.validate_request(
        _request(),
        expected_issue=subject.SOURCE_ISSUE,
        execution_sha=EXECUTION_SHA,
    )
    assert parsed["target_sha"] == EXECUTION_SHA


@pytest.mark.parametrize(
    "body, issue, sha",
    [
        (_request(extra="forbidden"), subject.SOURCE_ISSUE, EXECUTION_SHA),
        (_request(issue=431), subject.SOURCE_ISSUE, EXECUTION_SHA),
        (_request(target_sha="6" * 40), subject.SOURCE_ISSUE, EXECUTION_SHA),
        (_request(), 431, EXECUTION_SHA),
        (_request(), subject.SOURCE_ISSUE, "not-a-sha"),
        ("prefix\n" + _request(), subject.SOURCE_ISSUE, EXECUTION_SHA),
    ],
)
def test_request_fails_closed_on_scope_or_identity_drift(body, issue, sha):
    with pytest.raises(subject.ReferenceRuntimeExecutionError):
        subject.validate_request(body, expected_issue=issue, execution_sha=sha)


def test_request_rejects_duplicate_json_keys():
    body = (
        subject.REQUEST_MARKER
        + '\n{"schema_version":"'
        + subject.REQUEST_SCHEMA_VERSION
        + '","issue":432,"target_sha":"'
        + EXECUTION_SHA
        + '","requester":"a","requester":"b"}'
    )
    with pytest.raises(subject.ReferenceRuntimeExecutionError):
        subject.validate_request(
            body,
            expected_issue=subject.SOURCE_ISSUE,
            execution_sha=EXECUTION_SHA,
        )


def test_bounded_result_promotes_only_same_process_recipe_runtime_compatibility():
    result = subject._bounded_result(
        _gate_result(),
        execution_sha=EXECUTION_SHA,
        image_digest=IMAGE_DIGEST,
    )

    assert result["status"] == "pass"
    assert result["target_sha"] == EXECUTION_SHA
    assert result["execution_sha"] == EXECUTION_SHA
    assert result["same_process_runtime_observation_collected"] is True
    assert (
        result["executing_environment_matches_reconstructed_reference_recipe_fields"]
        is True
    )
    assert result["gsim_request_reference_recipe_runtime_compatibility_verified"] is True
    assert result["historical_environment_verified"] is False
    assert result["numerical_hazard_agreement_verified"] is False
    assert result["full_hazard_compatibility_verified"] is False
    assert result["reference_run_verified"] is False
    assert result["publication_authorized"] is False
    assert result["model_use_authorized"] is False
    assert "provider_secret" not in result


@pytest.mark.parametrize(
    "field",
    [
        "full_hazard_compatibility_verified",
        "site_model_compatibility_verified",
        "vulnerability_compatibility_verified",
        "reference_run_verified",
        "scientific_validity_verified",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    ],
)
def test_bounded_result_rejects_upstream_authority_widening(field):
    upstream = _gate_result()
    upstream[field] = True
    with pytest.raises(subject.ReferenceRuntimeExecutionError):
        subject._bounded_result(
            upstream,
            execution_sha=EXECUTION_SHA,
            image_digest=IMAGE_DIGEST,
        )


def test_acquisition_detects_authority_rebinding_before_network(monkeypatch):
    called = False

    def forbidden_network(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("network must not be reached")

    monkeypatch.setattr(subject.gmm, "EXPECTED_SHA256", "0" * 64)
    monkeypatch.setattr(subject, "_OPEN_FIXED", forbidden_network)

    with pytest.raises(
        subject.ReferenceRuntimeExecutionError,
        match="authority drifted",
    ):
        subject._acquire_exact_gmm()
    assert called is False
