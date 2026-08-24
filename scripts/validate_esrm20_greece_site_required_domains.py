# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded static consumer-domain evidence for the exact ESRM20 Greece site model.

The exact Greece bytes are already trusted and structurally profiled. This
module reuses that exact-byte/parser boundary and classifies only the three site
parameters required by the frozen OpenQuake 3.13 Athens GSIM:
``region``, ``slope`` and ``geology``.

The result contains only aggregate counts and fingerprints. It never returns
provider rows, coordinates or raw attribute values, and it does not execute
OpenQuake or promote CRS, benchmark, publication or model-use authority.
"""

from __future__ import annotations

import hashlib
import math
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from typing import Any

from scripts import profile_efehr_greece_site_model as _greece
from scripts import profile_efehr_kosovo_site_model as _shared

SCHEMA_VERSION = "oc-esrm20-greece-site-required-domain-profile-v0"
SOURCE_ISSUE = 285
SITE_STRUCTURE_RESULT_COMMENT_ID = 5_389_106_408
SEMANTICS_HANDOFF_COMMENT_ID = 5_393_126_444
OPENQUAKE_VERSION = "3.13.0"
OPENQUAKE_COMMIT = "16dd69ecea0c6dcaf49c22ca12edc9da3f024889"
OPENQUAKE_GSIM = "KothaEtAl2020ESHM20SlopeGeology"
OPENQUAKE_GSIM_BLOB = "e5154d05851e81cf384bb84282c9742522c3a05d"
EXPECTED_SITE_COUNT = 1_491
REQUIRED_PARAMETERS = ("region", "slope", "geology")
SLOPE_CLAMP_FLOOR = Decimal("0.0005")
SLOPE_CLAMP_CEILING = Decimal("0.3")
REGION_DEFAULT = 0
REGION_CALIBRATED_MIN = 1
REGION_CALIBRATED_MAX = 5
REGION_UINT32_MAX = (1 << 32) - 1
EXPECTED_REGION_VALUE_SET_SHA256 = (
    "2100f74540b48d50e35963625f64f84081c74ca7512bc605dc7da10ddc0bffef"
)
EXPECTED_GEOLOGY_VALUE_SET_SHA256 = (
    "8d9e1a295e459ee88ede1140a5bd01478d3638993cdb79994a2bc2010818c583"
)
RECOGNIZED_GEOLOGY_LABELS = frozenset(
    {
        "CENOZOIC",
        "CRETACEOUS",
        "HOLOCENE",
        "JURASSIC-TRIASSIC",
        "PALEOZOIC",
        "PLEISTOCENE",
        "PRECAMBRIAN",
        "UNKNOWN",
    }
)


class GreeceSiteDomainError(RuntimeError):
    """Raised when exact Greece bytes fail bounded consumer-domain checks."""


def _finite_decimal(value: str) -> Decimal | None:
    if value == "" or value != value.strip():
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _value_set_sha256(values: set[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _site_attributes(element: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_name, value in element.attrib.items():
        namespace, local_name = _shared._split_qname(raw_name)
        if local_name not in REQUIRED_PARAMETERS:
            continue
        if namespace is not None:
            raise GreeceSiteDomainError(
                f"required site parameter {local_name!r} is unexpectedly namespaced"
            )
        if local_name in result:
            raise GreeceSiteDomainError(
                f"required site parameter {local_name!r} is duplicated"
            )
        result[local_name] = value

    missing = sorted(set(REQUIRED_PARAMETERS).difference(result))
    if missing:
        raise GreeceSiteDomainError(
            "verified site element is missing required parameter names: "
            + ", ".join(missing)
        )
    return result


def profile_required_site_domains(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
    expected_site_count: int,
) -> dict[str, Any]:
    """Classify bounded required-domain counts after reviewed byte/XML gates."""

    if (
        type(expected_site_count) is not int
        or isinstance(expected_site_count, bool)
        or expected_site_count < 1
    ):
        raise GreeceSiteDomainError("expected site count must be a positive integer")

    try:
        structure = _shared.profile_verified_xml_bytes(
            raw,
            expected_byte_count=expected_byte_count,
            expected_sha256=expected_sha256,
        )
        text, _ = _shared._decode_literal_xml(raw)
    except _shared.KosovoSiteProfileError as exc:
        raise GreeceSiteDomainError(
            "reviewed site-profile gate rejected input"
        ) from exc

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:  # pragma: no cover - reviewed parser gates first
        raise GreeceSiteDomainError("verified site-model XML is malformed") from exc

    sites = [
        element
        for element in root.iter()
        if _shared._split_qname(element.tag)[1] == "site"
    ]
    if len(sites) != expected_site_count:
        raise GreeceSiteDomainError(
            "verified XML site count does not match the frozen expectation"
        )
    if structure.get("leaf_element_count") != expected_site_count:
        raise GreeceSiteDomainError(
            "reviewed structure profile is internally inconsistent"
        )

    region = {
        "occurrence_count": expected_site_count,
        "finite_decimal_count": 0,
        "integral_numeric_count": 0,
        "runtime_default_region_count": 0,
        "calibrated_region_count": 0,
        "consumer_domain_reject_count": 0,
    }
    slope = {
        "occurrence_count": expected_site_count,
        "finite_decimal_count": 0,
        "finite_binary64_count": 0,
        "below_clamp_floor_count": 0,
        "within_clamp_interval_count": 0,
        "above_clamp_ceiling_count": 0,
        "consumer_domain_reject_count": 0,
    }
    geology = {
        "occurrence_count": expected_site_count,
        "nonempty_count": 0,
        "recognized_calibrated_label_count": 0,
        "fixed_effects_fallback_label_count": 0,
        "consumer_domain_reject_count": 0,
    }
    region_values: set[str] = set()
    geology_values: set[str] = set()

    for element in sites:
        attributes = _site_attributes(element)

        region_value = attributes["region"]
        region_values.add(region_value)
        number = _finite_decimal(region_value)
        if number is not None:
            region["finite_decimal_count"] += 1
            if number == number.to_integral_value():
                region["integral_numeric_count"] += 1
                integer = int(number)
                if REGION_CALIBRATED_MIN <= integer <= REGION_CALIBRATED_MAX:
                    region["calibrated_region_count"] += 1
                elif 0 <= integer <= REGION_UINT32_MAX:
                    region["runtime_default_region_count"] += 1
                else:
                    region["consumer_domain_reject_count"] += 1
            else:
                region["consumer_domain_reject_count"] += 1
        else:
            region["consumer_domain_reject_count"] += 1

        slope_value = attributes["slope"]
        number = _finite_decimal(slope_value)
        if number is None:
            slope["consumer_domain_reject_count"] += 1
        else:
            slope["finite_decimal_count"] += 1
            try:
                binary64 = float(slope_value)
            except (OverflowError, ValueError):
                binary64 = math.nan
            if math.isfinite(binary64):
                slope["finite_binary64_count"] += 1
                if number < SLOPE_CLAMP_FLOOR:
                    slope["below_clamp_floor_count"] += 1
                elif number > SLOPE_CLAMP_CEILING:
                    slope["above_clamp_ceiling_count"] += 1
                else:
                    slope["within_clamp_interval_count"] += 1
            else:
                slope["consumer_domain_reject_count"] += 1

        geology_value = attributes["geology"]
        geology_values.add(geology_value)
        if geology_value != "" and geology_value == geology_value.strip():
            geology["nonempty_count"] += 1
            if geology_value in RECOGNIZED_GEOLOGY_LABELS:
                geology["recognized_calibrated_label_count"] += 1
            else:
                geology["fixed_effects_fallback_label_count"] += 1
        else:
            geology["consumer_domain_reject_count"] += 1

    region_hash = _value_set_sha256(region_values)
    geology_hash = _value_set_sha256(geology_values)
    reject_total = sum(
        counts["consumer_domain_reject_count"]
        for counts in (region, slope, geology)
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "openquake_reference": {
            "version": OPENQUAKE_VERSION,
            "commit": OPENQUAKE_COMMIT,
            "gsim": OPENQUAKE_GSIM,
            "gsim_blob": OPENQUAKE_GSIM_BLOB,
        },
        "required_site_parameter_names": list(REQUIRED_PARAMETERS),
        "site_count": expected_site_count,
        "parameter_domains": {
            "region": {
                **region,
                "static_contract": (
                    "uint32_integral_calibrated_1_to_5_else_default_coefficients"
                ),
                "runtime_dtype": "uint32",
                "explicit_default_code": REGION_DEFAULT,
                "calibrated_inclusive_min": REGION_CALIBRATED_MIN,
                "calibrated_inclusive_max": REGION_CALIBRATED_MAX,
                "distinct_value_set_sha256": region_hash,
                "matches_expected_exact_value_set": (
                    region_hash == EXPECTED_REGION_VALUE_SET_SHA256
                ),
            },
            "slope": {
                **slope,
                "static_contract": "finite_binary64_with_kotha_runtime_clamping",
                "consumer_unit": "m/m",
                "clamp_floor": str(SLOPE_CLAMP_FLOOR),
                "clamp_ceiling": str(SLOPE_CLAMP_CEILING),
            },
            "geology": {
                **geology,
                "static_contract": "recognized_kotha_geology_label_or_fixed_effects_fallback",
                "distinct_value_set_sha256": geology_hash,
                "matches_expected_exact_value_set": (
                    geology_hash == EXPECTED_GEOLOGY_VALUE_SET_SHA256
                ),
            },
        },
        "required_consumer_domain_reject_total": reject_total,
        "required_static_compatibility_complete": (
            reject_total == 0
            and region_hash == EXPECTED_REGION_VALUE_SET_SHA256
            and geology_hash == EXPECTED_GEOLOGY_VALUE_SET_SHA256
        ),
        "raw_xml_returned": False,
        "raw_attribute_values_returned": False,
        "raw_site_rows_returned": False,
        "raw_coordinates_returned": False,
        "openquake_runtime_value_acceptance_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "gsim_site_parameter_sufficiency_verified": False,
        "site_adjusted_reference_authorized": False,
        "benchmark_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_verified_greece_site_required_domains(raw: bytes) -> dict[str, Any]:
    """Profile only the exact Greece bytes already bound by trusted #285/#661."""

    try:
        exact = _greece.profile_verified_greece_site_model(raw)
    except _greece.GreeceSiteProfileError as exc:
        raise GreeceSiteDomainError(
            "exact Greece site-profile gate rejected input"
        ) from exc

    if exact.get("byte_count") != _greece.EXPECTED_BYTE_COUNT:
        raise GreeceSiteDomainError("exact Greece site-profile byte identity drifted")
    if exact.get("sha256") != _greece.EXPECTED_SHA256:
        raise GreeceSiteDomainError("exact Greece site-profile hash identity drifted")

    domain_profile = profile_required_site_domains(
        raw,
        expected_byte_count=_greece.EXPECTED_BYTE_COUNT,
        expected_sha256=_greece.EXPECTED_SHA256,
        expected_site_count=EXPECTED_SITE_COUNT,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "site_structure_result_comment_id": SITE_STRUCTURE_RESULT_COMMENT_ID,
        "semantics_handoff_comment_id": SEMANTICS_HANDOFF_COMMENT_ID,
        "site_identity": {
            "project_id": _greece.PROJECT_ID,
            "project_path": _greece.PROJECT_PATH,
            "release": _greece.RELEASE,
            "commit_sha": _greece.COMMIT_SHA,
            "consumer_event": _greece.CONSUMER_EVENT,
            "repository_path": _greece.REPOSITORY_PATH,
            "byte_count": _greece.EXPECTED_BYTE_COUNT,
            "sha256": _greece.EXPECTED_SHA256,
            "receipt_comment_id": _greece.RECEIPT_COMMENT_ID,
        },
        "domain_profile": domain_profile,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
