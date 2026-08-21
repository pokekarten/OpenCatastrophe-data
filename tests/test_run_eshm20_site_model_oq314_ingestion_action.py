# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json

import numpy
import pytest

from scripts import run_eshm20_site_model_oq314_ingestion_action as subject


SHA = "4e7294587979d9ca78ed79d23361aa8595276352"


def _request(**updates):
    value = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "requester": "test-agent",
    }
    value.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(
        value, sort_keys=True, separators=(",", ":")
    )


def _array():
    dtype = [
        ("lat", numpy.float64),
        ("lon", numpy.float64),
        ("region", numpy.uint32),
        ("vs30", numpy.float64),
        ("vs30measured", bool),
        ("xvf", numpy.float64),
        ("z1pt0", numpy.float64),
        ("z2pt5", numpy.float64),
    ]
    arr = numpy.zeros(94_493, dtype=dtype)
    arr["lat"] = 42.0
    arr["lon"] = numpy.linspace(-170.0, 170.0, len(arr))
    arr["region"] = numpy.arange(len(arr), dtype=numpy.uint32) % 6
    arr["vs30"] = 800.0
    arr["vs30measured"] = False
    arr["xvf"] = numpy.linspace(-500.0, 500.0, len(arr))
    arr["z1pt0"] = 100.0
    arr["z2pt5"] = 1.0
    return arr


def test_request_is_exactly_fenced():
    parsed = subject.validate_request(
        _request(), expected_issue=281, execution_sha=SHA
    )
    assert parsed["target_sha"] == SHA

    with pytest.raises(subject.SiteModelOq314IngestionError):
        subject.validate_request(
            _request(target_sha="0" * 40), expected_issue=281, execution_sha=SHA
        )
    with pytest.raises(subject.SiteModelOq314IngestionError):
        subject.validate_request(
            _request() + "\nextra", expected_issue=281, execution_sha=SHA
        )


def test_exact_oq314_value_domain_gate_accepts_bounded_synthetic_array():
    gate = subject._evaluate_site_array(_array())
    assert gate == {
        "record_count": 94_493,
        "parsed_header": list(subject.EXPECTED_HEADER),
        "required_mode_a_fields": list(subject.REQUIRED_MODE_A_FIELDS),
        "oq314_site_dtype_parse_verified": True,
        "lon_lat_finite_and_in_bounds": True,
        "coordinate_rounding_decimals": 5,
        "duplicate_coordinate_count_after_rounding": 0,
        "region_uint32_parse_verified": True,
        "region_supported_domain_verified": True,
        "region_distinct_count": 6,
        "vs30_positive_finite_verified": True,
        "vs30measured_bool_parse_verified": True,
        "vs30measured_distinct_count": 1,
        "xvf_finite_verified": True,
    }


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("lat", 91.0, "latitude outside"),
        ("lon", 181.0, "longitude outside"),
        ("region", 6, "region values"),
        ("vs30", 0.0, "vs30 must be positive"),
        ("vs30", numpy.inf, "vs30 must be positive"),
        ("xvf", numpy.inf, "xvf must be finite"),
    ],
)
def test_value_domain_gate_fails_closed(field, value, message):
    arr = _array()
    arr[field][0] = value
    with pytest.raises(subject.SiteModelOq314IngestionError, match=message):
        subject._evaluate_site_array(arr)


def test_duplicate_after_exact_five_decimal_rounding_is_rejected():
    arr = _array()
    arr["lon"][1] = arr["lon"][0] + 0.000001
    arr["lat"][1] = arr["lat"][0]
    with pytest.raises(
        subject.SiteModelOq314IngestionError,
        match="duplicate coordinates after OQ3.14 five-decimal rounding",
    ):
        subject._evaluate_site_array(arr)


def test_vs30measured_must_be_exact_oq_bool_dtype():
    arr = _array()
    dtype = [
        (name, numpy.uint8 if name == "vs30measured" else arr.dtype[name])
        for name in arr.dtype.names
    ]
    drifted = numpy.zeros(len(arr), dtype=dtype)
    for name in arr.dtype.names:
        drifted[name] = arr[name]
    with pytest.raises(
        subject.SiteModelOq314IngestionError, match="vs30measured bool dtype drifted"
    ):
        subject._evaluate_site_array(drifted)


def test_blocked_result_preserves_all_authority_ceilings():
    result = subject._blocked_result(execution_sha=SHA)
    assert result["status"] == "blocked"
    assert result["gate"] is None
    for field in subject._FALSE_CEILINGS:
        assert result[field] is False
    assert result["full_site_compatibility_verified"] is False
    assert result["historical_environment_verified"] is False
