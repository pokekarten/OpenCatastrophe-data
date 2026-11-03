# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-source full XY/ring/PRJ profile for Luxembourg AGE HQ10/HQext.

The publisher-specific SHA-1 and previously witnessed SHA-256 are both
required before any coordinates are decoded. All per-ring coordinates and
geometries are ephemeral and never persisted or printed. This is a research
diagnostic, not a scientific flood-mask or insurer-CAT admission.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile

from research_runners.luxembourg_age_hq2021_sibling_source_receipts_v0 import (
    SOURCES, audit as source_audit,
)
from research_runners.luxembourg_age_hq100_2021_original_preflight_v0 import (
    HQ100OriginalError, MAX_PRJ_BYTES, _safe_member,
)
from research_runners.luxembourg_age_hq100_2021_prj_crs_screen_v0 import (
    parse_wkt, HQ100CRSError,
)
from research_runners.luxembourg_age_hq100_2021_ring_coordinate_quality_v0 import (
    axis_envelope_screen, check_shp, HQ100GeometryError,
)
from research_runners.luxembourg_age_hq100_2021_ring_topology_v0 import RingTopologyCounter

# Separate independent real-source receipts from the first verified download:
# https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41435808291
EXPECTED_SHA256 = {
    "hq10": "f5bf50e49f8e47207782e9030c6644594121c661cf31f4acb1bf292e5837b8fa",
    "hqext": "c26e81026bad0cad19e41086a905d7709bcf4cfd11341db2259aaa9d4d529888",
}


def _one_member(archive: zipfile.ZipFile, suffix: str):
    found = [i for i in archive.infolist()
             if not i.is_dir() and i.filename.lower().endswith(suffix)]
    if len(found) != 1:
        raise HQ100GeometryError("Expected one exact-original source member")
    _safe_member(found[0])
    return found[0]


def _finalize(scenario: str, metadata: dict, coordinates: dict,
              ring_topology: dict, crs: dict) -> dict:
    """Fail closed on population, unvalidated source or mismatched declared CRS."""
    if scenario not in EXPECTED_SHA256 or scenario not in SOURCES:
        raise HQ100GeometryError("Unknown original flood scenario")
    if metadata.get("observed_sha256") != EXPECTED_SHA256[scenario] or (
            metadata.get("publisher_sha1_match") is not True):
        raise HQ100GeometryError("Publisher original checksum identity not established")
    if (coordinates["original_polygon_records"] != metadata["source_polygon_records"]
            or coordinates["source_polygon_ring_parts"] != metadata["original_source_ring_parts"]
            or coordinates["original_coordinate_pairs_read_and_aggregated"]
            != metadata["source_coordinates_skipped_without_reading"]
            or ring_topology["source_rings_examined_total"]
            != coordinates["source_polygon_ring_parts"]):
        raise HQ100GeometryError("Original coordinate and topology population mismatch")
    if (coordinates["positive_signed_orientation_ring_parts"] +
            coordinates["negative_signed_orientation_ring_parts"] +
            coordinates["zero_or_near_zero_signed_area_ring_parts"] !=
            coordinates["source_polygon_ring_parts"]):
        raise HQ100GeometryError("Original source ring winding population not conserved")
    if (ring_topology["individually_valid_nonzero_area_rings"] +
            ring_topology["individually_invalid_rings"] +
            ring_topology["complex_ring_geometry_test_skipped"] +
            ring_topology["geos_ring_test_errors"] !=
            coordinates["source_polygon_ring_parts"]):
        raise HQ100GeometryError("Original GEOS valid/invalid ring population not conserved")
    if (ring_topology["complex_ring_geometry_test_skipped"] != 0
            or ring_topology["geos_ring_test_errors"] != 0):
        raise HQ100GeometryError("Unexamined original polygon ring blocked")
    if coordinates["all_original_coordinates_finite"] is not True:
        raise HQ100GeometryError("Nonfinite original polygon source position")
    if (crs["crs_epsg_match_at_min90_confidence"] != 2169 or
            crs["original_crs_is_projected"] is not True or
            "metre" not in crs["original_crs_axis_unit_names"]):
        raise HQ100GeometryError("Original source CRS differs from expected projected EPSG:2169")
    if (not coordinates["file_bbox_matches_all_original_vertices"]
            or not coordinates["record_bbox_matches_all_original_vertices"]
            or coordinates["open_ring_parts"] != 0
            or coordinates["zero_or_near_zero_signed_area_ring_parts"] != 0
            or coordinates["closed_ring_parts"] != coordinates["source_polygon_ring_parts"]):
        raise HQ100GeometryError("Original polygon structural envelope/ring integrity fails")
    axis = axis_envelope_screen(coordinates["aggregate_original_projected_bbox_rounded_m"])
    return {
        "profile": "lu-age-2021-sibling-full-original-ring-quality-v0",
        "scenario": scenario,
        "publisher_url": SOURCES[scenario]["catalogue"],
        "source_original_sha256": EXPECTED_SHA256[scenario],
        "publisher_original_sha1_verified": True,
        "original_polygon_record_count": coordinates["original_polygon_records"],
        "original_ring_parts": coordinates["source_polygon_ring_parts"],
        "original_coordinate_pairs_tested": coordinates[
            "original_coordinate_pairs_read_and_aggregated"],
        "closed_rings": coordinates["closed_ring_parts"],
        "open_rings": coordinates["open_ring_parts"],
        "positive_winding_ring_parts": coordinates["positive_signed_orientation_ring_parts"],
        "negative_winding_ring_parts": coordinates["negative_signed_orientation_ring_parts"],
        "near_zero_signed_area_rings": coordinates["zero_or_near_zero_signed_area_ring_parts"],
        "all_coordinates_finite": coordinates["all_original_coordinates_finite"],
        "aggregate_source_bbox_projected_rounded_m": coordinates[
            "aggregate_original_projected_bbox_rounded_m"],
        "source_bbox_matches_original_header": True,
        "source_crs_epsg_90_confidence": crs["crs_epsg_match_at_min90_confidence"],
        "source_prj_axis_units": crs["original_crs_axis_unit_names"],
        "source_axis_envelope_screen": axis,
        "individual_ring_topology": ring_topology,
        "original_hq10_hq100_hqext_flood_areas_ordered_and_proven": False,
        "full_multipart_record_validated": False,
        "original_source_shell_hole_semantics_verified": False,
        "original_hazard_position_survey_accurate": False,
        "numeric_water_depth_observed": False,
        "source_geometries_or_identifiers_exported": False,
        "CAT_model_input_admitted": False,
        "real_insurer_portfolio_or_neon_updated": False,
    }


def audit(original_zip: Path, scenario: str) -> dict:
    if scenario not in EXPECTED_SHA256:
        raise HQ100GeometryError("Unknown HQ scenario")
    metadata = source_audit(original_zip, scenario=scenario)
    if metadata["observed_sha256"] != EXPECTED_SHA256[scenario]:
        raise HQ100GeometryError("Changed original archive SHA256 versus prior official source receipt")
    with zipfile.ZipFile(original_zip) as archive:
        shape = _one_member(archive, ".shp")
        prj = _one_member(archive, ".prj")
        with archive.open(prj) as stream:
            wkt = stream.read(MAX_PRJ_BYTES + 1)
        crs = parse_wkt(wkt)
        collector = RingTopologyCounter()
        with archive.open(shape) as stream:
            coords = check_shp(stream, ring_diagnostic=collector.observe)
    return _finalize(scenario, metadata, coords,
                     collector.summary(coords["source_polygon_ring_parts"]), crs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=tuple(EXPECTED_SHA256), required=True)
    parser.add_argument("--source-zip", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.source_zip, args.scenario), sort_keys=True,
                         indent=2, allow_nan=False))
    except (HQ100OriginalError, HQ100GeometryError, HQ100CRSError,
            OSError, zipfile.BadZipFile, ValueError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
