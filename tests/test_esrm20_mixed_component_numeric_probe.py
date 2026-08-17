# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import math

import pytest

from scripts import run_esrm20_mixed_component_numeric_probe as subject

SHA = "a" * 40


def _request(**overrides: object) -> str:
    payload: dict[str, object] = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": SHA,
        "requester": "test",
    }
    payload.update(overrides)
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def test_request_is_exact_sha_fenced() -> None:
    parsed = subject.validate_request(
        _request(), expected_issue=subject.SOURCE_ISSUE, execution_sha=SHA
    )
    assert parsed["target_sha"] == SHA


@pytest.mark.parametrize(
    "body",
    [
        "",
        subject.REQUEST_MARKER + "\n{}",
        _request(target_sha="b" * 40),
        subject.REQUEST_MARKER + "\n" + json.dumps({
            "schema_version": subject.REQUEST_SCHEMA_VERSION,
            "issue": subject.SOURCE_ISSUE,
            "target_sha": SHA,
            "requester": "test",
            "extra": True,
        }),
        subject.REQUEST_MARKER + '\n{"schema_version":"x","schema_version":"y"}',
    ],
)
def test_request_drift_fails_closed(body: str) -> None:
    with pytest.raises(subject.MixedComponentNumericProbeError):
        subject.validate_request(
            body, expected_issue=subject.SOURCE_ISSUE, execution_sha=SHA
        )


def test_probe_branch_selection_is_exact_and_zero_argument() -> None:
    assert subject.SELECTED_BRANCHES == (
        {
            "branch_set_id": "CratonModel",
            "branch_id": "CRParamMidMidSite",
            "requested_gsim_token": "ESHM20Craton",
            "native_component": "RotD50",
            "distance_field": "rrup",
        },
        {
            "branch_set_id": "Volcanic",
            "branch_id": "b61",
            "requested_gsim_token": "LanzanoLuzi2019shallow",
            "native_component": "GEOMETRIC_MEAN",
            "distance_field": "rhypo",
        },
    )
    assert subject.SYNTHETIC_CONTEXT == {
        "mag": 4.5,
        "vs30": 760.0,
        "rrup_km": 20.0,
        "rhypo_km": 20.0,
    }


def test_non_finite_numeric_output_fails_closed() -> None:
    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(subject.MixedComponentNumericProbeError):
            subject._finite(value, field="test")
    assert subject._finite(0.0, field="test") == 0.0
