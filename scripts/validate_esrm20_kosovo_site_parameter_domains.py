# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded static-domain evidence for the exact ESRM20 Kosovo site model.

This module deliberately does not execute OpenQuake. It reuses the reviewed
Kosovo XML profiler's exact-byte and parser-safety boundary, then classifies
only the five site-parameter names already derived from the pinned
OpenQuake-3.14 GSIM set. Results contain counts and public contract constants,
never provider rows, coordinates, or raw attribute values.

Static-domain classification is weaker than OpenQuake runtime acceptance and
much weaker than scientific site-model sufficiency. Those higher gates remain
explicitly false.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from typing import Any

from scripts import profile_efehr_kosovo_site_model as _profile

SCHEMA_VERSION = "oc-esrm20-kosovo-site-parameter-domain-profile-v0"
SOURCE_ISSUE = 291
SITE_PROFILE_ISSUE = 459
SITE_STRUCTURE_RESULT_COMMENT_ID = 5310018006
REQUIRED_PARAMETER_HANDOFF_COMMENT_ID = 5310209812
XVF_SEMANTICS_COMMENT_ID = 5310202888
OPENQUAKE_TAG = "v3.14.0"
OPENQUAKE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
EXPECTED_SITE_COUNT = 37
REQUIRED_PARAMETERS = ("geology", "region", "slope", "vs30", "xvf")
SLOPE_CLAMP_FLOOR = Decimal("0.0005")
SLOPE_CLAMP_CEILING = Decimal("0.3")
REGION_MIN = 0
REGION_MAX = 5
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


class KosovoSiteDomainError(RuntimeError):
    """Raised when verified XML cannot support bounded domain classification."""


def _finite_decimal(value: str) -> Decimal | None:
    if value == "" or value != value.strip():
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _site_attributes(element: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_name, value in element.attrib.items():
        namespace, local_name = _profile._split_qname(raw_name)
        if local_name not in REQUIRED_PARAMETERS:
            continue
        if namespace is not None:
            raise KosovoSiteDomainError(
                f"required site parameter {local_name!r} is unexpectedly namespaced"
            )
        if local_name in result:
            raise KosovoSiteDomainError(
                f"required site parameter {local_name!r} is duplicated"
            )
        result[local_name] = value

    missing = sorted(set(REQUIRED_PARAMETERS).difference(result))
    if missing:
        raise KosovoSiteDomainError(
            "verified site element is missing required parameter names: "
            + ", ".join(missing)
        )
    return result


def _new_numeric_counts(site_count: int) -> dict[str, int]:
    return {
        "occurrence_count": site_count,
        "finite_decimal_count": 0,
        "static_domain_match_count": 0,
        "static_domain_reject_count": 0,
    }


def profile_site_parameter_domains(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
    expected_site_count: int,
) -> dict[str, Any]:
    """Classify content-free static-domain counts after reviewed byte/XML gates."""

    if (
        type(expected_site_count) is not int
        or isinstance(expected_site_count, bool)
        or expected_site_count < 1
    ):
        raise KosovoSiteDomainError("expected site count must be a positive integer")

    try:
        structure = _profile.profile_verified_xml_bytes(
            raw,
            expected_byte_count=expected_byte_count,
            expected_sha256=expected_sha256,
        )
        text, _ = _profile._decode_literal_xml(raw)
    except _profile.KosovoSiteProfileError as exc:
        raise KosovoSiteDomainError("reviewed Kosovo site-profile gate rejected input") from exc
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:  # pragma: no cover - structure profiler already gates this
        raise KosovoSiteDomainError("verified site-model XML is malformed") from exc

    sites = [
        element
        for element in root.iter()
        if _profile._split_qname(element.tag)[1] == "site"
    ]
    if len(sites) != expected_site_count:
        raise KosovoSiteDomainError(
            "verified XML site count does not match the frozen expectation"
        )
    if structure.get("element_count", 0) < expected_site_count:
        raise KosovoSiteDomainError("reviewed structure profile is internally inconsistent")

    vs30 = _new_numeric_counts(expected_site_count)
    vs30["positive_finite_count"] = 0
    xvf = _new_numeric_counts(expected_site_count)
    region = _new_numeric_counts(expected_site_count)
    slope = _new_numeric_counts(expected_site_count)
    region["integral_numeric_count"] = 0
    slope["below_clamp_floor_count"] = 0
    slope["within_clamp_interval_count"] = 0
    slope["above_clamp_ceiling_count"] = 0
    geology = {
        "occurrence_count": expected_site_count,
        "nonempty_count": 0,
        "recognized_calibrated_label_count": 0,
        "fixed_effects_fallback_label_count": 0,
        "static_domain_match_count": 0,
        "static_domain_reject_count": 0,
    }

    for element in sites:
        attributes = _site_attributes(element)

        number = _finite_decimal(attributes["vs30"])
        if number is not None:
            vs30["finite_decimal_count"] += 1
            if number > 0:
                vs30["positive_finite_count"] += 1
                vs30["static_domain_match_count"] += 1

        number = _finite_decimal(attributes["xvf"])
        if number is not None:
            xvf["finite_decimal_count"] += 1
            xvf["static_domain_match_count"] += 1

        number = _finite_decimal(attributes["region"])
        if number is not None:
            region["finite_decimal_count"] += 1
            if number == number.to_integral_value():
                region["integral_numeric_count"] += 1
                integer = int(number)
                if REGION_MIN <= integer <= REGION_MAX:
                    region["static_domain_match_count"] += 1

        number = _finite_decimal(attributes["slope"])
        if number is not None:
            slope["finite_decimal_count"] += 1
            slope["static_domain_match_count"] += 1
            if number < SLOPE_CLAMP_FLOOR:
                slope["below_clamp_floor_count"] += 1
            elif number > SLOPE_CLAMP_CEILING:
                slope["above_clamp_ceiling_count"] += 1
            else:
                slope["within_clamp_interval_count"] += 1

        label = attributes["geology"]
        if label != "" and label == label.strip():
            geology["nonempty_count"] += 1
            geology["static_domain_match_count"] += 1
            if label in RECOGNIZED_GEOLOGY_LABELS:
                geology["recognized_calibrated_label_count"] += 1
            else:
                geology["fixed_effects_fallback_label_count"] += 1

    for counts in (vs30, xvf, region, slope, geology):
        counts["static_domain_reject_count"] = (
            expected_site_count - counts["static_domain_match_count"]
        )

    result = {
        "schema_version": SCHEMA_VERSION,
        "openquake_reference": {
            "tag": OPENQUAKE_TAG,
            "commit": OPENQUAKE_COMMIT,
        },
        "required_site_parameter_names": list(REQUIRED_PARAMETERS),
        "site_count": expected_site_count,
        "parameter_domains": {
            "vs30": {
                **vs30,
                "static_contract": "finite_decimal_and_gt_zero",
            },
            "xvf": {
                **xvf,
                "static_contract": "finite_decimal_only",
                "branch_specific_semantics_required": True,
            },
            "region": {
                **region,
                "static_contract": "integral_numeric_inclusive_0_to_5",
                "inclusive_min": REGION_MIN,
                "inclusive_max": REGION_MAX,
            },
            "slope": {
                **slope,
                "static_contract": "finite_decimal_with_model_clamping",
                "clamp_floor": str(SLOPE_CLAMP_FLOOR),
                "clamp_ceiling": str(SLOPE_CLAMP_CEILING),
            },
            "geology": {
                **geology,
                "static_contract": "nonempty_label_with_fixed_effects_fallback",
                "recognized_calibrated_labels": sorted(RECOGNIZED_GEOLOGY_LABELS),
            },
        },
        "static_domain_reject_total": sum(
            counts["static_domain_reject_count"]
            for counts in (vs30, xvf, region, slope, geology)
        ),
        "static_domain_classification_complete": True,
        "raw_xml_returned": False,
        "raw_attribute_values_returned": False,
        "raw_site_rows_returned": False,
        "openquake_runtime_value_acceptance_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "gsim_site_parameter_sufficiency_verified": False,
        "site_adjusted_reference_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    return result


def profile_verified_kosovo_site_parameter_domains(raw: bytes) -> dict[str, Any]:
    """Profile only the exact Kosovo bytes already bound by trusted #342/#459."""

    domain_profile = profile_site_parameter_domains(
        raw,
        expected_byte_count=_profile.EXPECTED_BYTE_COUNT,
        expected_sha256=_profile.EXPECTED_SHA256,
        expected_site_count=EXPECTED_SITE_COUNT,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "site_profile_issue": SITE_PROFILE_ISSUE,
        "site_structure_result_comment_id": SITE_STRUCTURE_RESULT_COMMENT_ID,
        "required_parameter_handoff_comment_id": REQUIRED_PARAMETER_HANDOFF_COMMENT_ID,
        "xvf_semantics_comment_id": XVF_SEMANTICS_COMMENT_ID,
        "site_identity": {
            "project_id": _profile.PROJECT_ID,
            "project_path": _profile.PROJECT_PATH,
            "commit_sha": _profile.COMMIT_SHA,
            "repository_path": _profile.REPOSITORY_PATH,
            "byte_count": _profile.EXPECTED_BYTE_COUNT,
            "sha256": _profile.EXPECTED_SHA256,
            "receipt_comment_id": _profile.RECEIPT_COMMENT_ID,
        },
        "domain_profile": domain_profile,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
