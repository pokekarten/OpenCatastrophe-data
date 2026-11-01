# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, offline geographic-region × peril evidence matrix (research only).

An explicitly declared target grid is authoritative for the *questions*, NOT
for the real geography, scientific source quality, licence, or exposure. Empty
targets remain visible. Never infer worldwide coverage from a selected grid.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.region_peril_readiness_v0 import ROLES, RegionPerilError, assess, region_key

VERSION = "OC_REGION_PERIL_MATRIX_V0"
MAX_REGIONS = 200
MAX_PERILS = 24
MAX_CELLS = 512
MAX_EVIDENCE = 512
REGION_FIELDS = {"country_iso3", "admin_system", "admin_level",
                 "admin_id", "boundary_year"}


def _load_json(original: bytes):
    if type(original) is not bytes or not 0 < len(original) <= 1_000_000:
        raise RegionPerilError("matrix JSON byte budget exceeded")

    def no_duplicate_properties(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RegionPerilError("duplicate matrix JSON property")
            result[key] = value
        return result

    def no_nonfinite(value):
        raise RegionPerilError("non-finite matrix JSON number")

    try:
        return json.loads(original.decode("utf-8"),
                          object_pairs_hook=no_duplicate_properties,
                          parse_constant=no_nonfinite)
    except (UnicodeError, ValueError) as exc:
        if isinstance(exc, RegionPerilError):
            raise
        raise RegionPerilError("invalid UTF-8 / matrix JSON") from exc


def build_matrix(payload):
    if type(payload) is not dict or set(payload) != {
            "schema_version", "regions", "perils", "evidence"}:
        raise RegionPerilError("matrix root must declare exact fields")
    if payload["schema_version"] != VERSION:
        raise RegionPerilError("unsupported region-peril matrix version")
    regions, perils, evidence = (payload["regions"], payload["perils"],
                                 payload["evidence"])
    if (type(regions) is not list or not 1 <= len(regions) <= MAX_REGIONS
            or type(perils) is not list or not 1 <= len(perils) <= MAX_PERILS
            or type(evidence) is not list or len(evidence) > MAX_EVIDENCE
            or len(regions) * len(perils) > MAX_CELLS):
        raise RegionPerilError("matrix dimensions exceed explicit bounded scope")

    validated_perils = []
    for peril in perils:
        if type(peril) is not str or peril == "all":
            raise RegionPerilError("matrix requires individually named perils")
        # The v0 single-region validator is the shared identity authority.
        if peril in validated_perils:
            raise RegionPerilError("duplicate peril in target grid")
        validated_perils.append(peril)

    region_keys = {}
    for region in regions:
        if type(region) is not dict or set(region) != REGION_FIELDS:
            raise RegionPerilError("matrix regions must have exact geographic fields")
        key = region_key({**region, "peril": perils[0]})
        if key in region_keys:
            raise RegionPerilError("duplicate geographic target identity")
        region_keys[key] = region

    reports = {}
    for doc in evidence:
        report = assess(doc)
        target = (report["region_key"], report["peril"])
        if target[0] not in region_keys or target[1] not in validated_perils:
            raise RegionPerilError("evidence outside explicit region/peril target grid")
        if target in reports:
            raise RegionPerilError("duplicate evidence document for one target cell")
        reports[target] = report

    cells = []
    for key in sorted(region_keys):
        for peril in sorted(validated_perils):
            target = (key, peril)
            report = reports.get(target)
            if report is None:
                report = assess({
                    "schema_version": "OC_REGION_PERIL_EVIDENCE_V0",
                    "scope": {**region_keys[key], "peril": peril},
                    "evidence": [],
                })
            cells.append({
                "region_key": key,
                "peril": peril,
                "evidence_document_supplied": target in reports,
                "source_receipt_count": report["source_receipt_count"],
                "catalogued_roles": report["catalogued_roles"],
                "claimed_original_qc_roles": report["claimed_original_qc_roles"],
                "missing_catalogued_roles": report["missing_catalogued_roles"],
                "missing_original_qc_roles": report["missing_original_qc_roles"],
                "automatic_model_admission_allowed": False,
            })
    return {
        "schema_version": VERSION,
        "status": "RESEARCH_DECLARED_TARGET_GRID_ONLY_NOT_WORLDWIDE_COMPLETENESS",
        "target_region_count": len(region_keys),
        "target_peril_count": len(validated_perils),
        "target_cell_count": len(cells),
        "evidence_supplied_cell_count": len(reports),
        "no_evidence_cell_count": len(cells) - len(reports),
        "all_eight_roles_catalogued_cell_count": sum(
            not c["missing_catalogued_roles"] for c in cells),
        "all_eight_roles_claimed_original_qc_cell_count": sum(
            not c["missing_original_qc_roles"] for c in cells),
        "cells": cells,
        "independent_provider_bytes_or_licences_verified": False,
        "true_global_geography_or_peril_coverage_proven": False,
        "automatic_model_admission_allowed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix_json", type=Path)
    args = parser.parse_args(argv)
    result = build_matrix(_load_json(args.matrix_json.read_bytes()))
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
