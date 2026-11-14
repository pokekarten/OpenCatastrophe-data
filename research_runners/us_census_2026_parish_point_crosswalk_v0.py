# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only point→official parish→synthetic OpenCat region crosswalk.

A source-derived representative point from each verified official polygon
demonstrates the point/spatial-join mechanics. It is NOT an independently
observed building, a real insurer location, a vulnerability, or TIV.
Never write original SHP, coordinates or an admitted asset portfolio.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import re
import sys
import zipfile

from research_runners.us_census_2026_county_zip_audit_v0 import (
    CensusZipError, MAX_ZIP_BYTES, STEM,
)
from research_runners.us_census_2026_louisiana_64_parish_qc_v0 import (
    Louisiana64Error, _la_positions, inspect_all_louisiana,
)
from research_runners.us_census_2026_parish_spatial_pilot_v0 import (
    PINNED_ORIGINAL_SHA256, PilotGeometryError, _reconstruct_shape,
)

MAX_TEST_POINTS = 128
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,80}\Z")
CENSUS_2026_SOURCE_NAMESPACE = "US_CENSUS_TIGER_2026"
MODEL_TARGET_PARENT = "US-LA"


@dataclass(frozen=True)
class SyntheticPoint:
    asset_id: str
    longitude: float
    latitude: float
    origin: str = "synthetic_test_only"


class CrosswalkError(ValueError):
    pass


def _blocked(reason):
    raise CrosswalkError("synthetic parish crosswalk: "+reason)


def match_synthetic_points(polygons, sites):
    """Pure, fail-closed spatial matcher; output is ONLY synthetic labels.

    This does not independently authenticate the supplied shapes or sites.
    The real-source runner calls it only after exact source byte/topology QC.
    """
    try:
        from shapely.geometry import Point
    except ImportError as exc:
        raise CrosswalkError("reviewed spatial runtime unavailable") from exc
    if (type(polygons) is not dict or not polygons
        or any(type(k) is not str or not re.fullmatch(r"22[0-9]{3}", k)
               for k in polygons)
        or type(sites) is not tuple
        or not 1 <= len(sites) <= MAX_TEST_POINTS):
        _blocked("bounded explicit Louisiana source polygons and sites required")
    ids = set()
    output = []
    for site in sites:
        if type(site) is not SyntheticPoint or site.origin != "synthetic_test_only":
            _blocked("synthetic labelled point records only")
        if type(site.asset_id) is not str or ID.fullmatch(site.asset_id) is None:
            _blocked("invalid synthetic asset identifier")
        if site.asset_id in ids:
            _blocked("duplicate synthetic asset identifier")
        ids.add(site.asset_id)
        lon, lat = site.longitude, site.latitude
        if (type(lon) not in (int, float) or type(lat) not in (int, float)
            or not math.isfinite(lon) or not math.isfinite(lat)
            or not -96.0 <= lon <= -87.0 or not 27.0 <= lat <= 34.0):
            _blocked("point outside original Louisiana coordinate sanity envelope")
        point = Point(float(lon), float(lat))
        # Boundary matching is ambiguous and fails, even if just one target
        # polygon reports touching. No assignment from fuzzy proximity.
        touching = [code for code, geom in polygons.items() if geom.touches(point)]
        if touching:
            _blocked("point touches county/parish boundary; no arbitrary tie-break")
        contained = [code for code, geom in polygons.items() if geom.contains(point)]
        if len(contained) != 1:
            _blocked("no unique polygon interior assignment; never choose nearest")
        geoid = contained[0]
        output.append({
            "asset_id":site.asset_id,
            "country_code":"US",
            "subdivisions":[MODEL_TARGET_PARENT, f"{MODEL_TARGET_PARENT}-{geoid}"],
        })
    return sorted(output, key=lambda x:x["asset_id"])


def source_sample_crosswalk(original_bytes):
    """64 intentionally geometry-derived *fake* points, exact-source QC."""
    source = inspect_all_louisiana(
        original_bytes, expected_sha256=PINNED_ORIGINAL_SHA256)
    with zipfile.ZipFile(io.BytesIO(original_bytes)) as archive:
        dbf = archive.read(f"{STEM}.dbf")
        shp = archive.read(f"{STEM}.shp")
        shx = archive.read(f"{STEM}.shx")
    positions = _la_positions(dbf)
    polygons = {
        geoid: _reconstruct_shape(shp, shx, ordinal)[0]
        for geoid, ordinal in positions.items()
    }
    # Provider-polygon-derived points are NOT new geolocated building evidence;
    # generating rather than measuring them makes the scope fully explicit.
    sites = tuple(
        SyntheticPoint(
            asset_id="synthetic_sample_"+geoid,
            longitude=polygons[geoid].representative_point().x,
            latitude=polygons[geoid].representative_point().y,
        )
        for geoid in sorted(polygons)
    )
    assignments = match_synthetic_points(polygons, sites)
    expected_codes = {f"{MODEL_TARGET_PARENT}-{code}" for code in positions}
    if len(assignments) != 64 or {
        item["subdivisions"][-1] for item in assignments
    } != expected_codes:
        _blocked("synthetic site crosswalk does not cover 64 official polygons")
    canonical = json.dumps(
        assignments, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return {
        "profile":"OC_CENSUS_2026_LA_SYNTHETIC_POINT_CROSSWALK_V0",
        "original_source_sha256":source["original_source_sha256"],
        "source_namespace":CENSUS_2026_SOURCE_NAMESPACE,
        "boundary_year":2026,
        "country_iso2":"US",
        "country_iso3":"USA",
        "synthetic_parent_regions":["US", MODEL_TARGET_PARENT],
        "original_validated_parish_polygon_count":64,
        "source_derived_synthetic_point_count":len(sites),
        "synthetic_points_with_exactly_one_polygon_interior":len(assignments),
        "points_from_polygon_representative_point_not_real_assets":True,
        "synthetic_region_assignment_sha256":sha256(canonical).hexdigest(),
        "sample_region_assignments":[
            entry for entry in assignments if entry["asset_id"] in (
                "synthetic_sample_22051", "synthetic_sample_22071",
                "synthetic_sample_22087")],
        "original_source_geometry_persisted":False,
        "original_point_coordinates_emitted":False,
        "actual_asset_geolocation_demonstrated":False,
        "insured_TIV_or_policy_terms_verified":False,
        "native_OpenCat_region_loss_model_executed":False,
        "rights_and_scientific_admission_granted":False,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip",type=Path,required=True)
    args=parser.parse_args(argv)
    f=args.source_zip
    if f.is_symlink() or not f.is_file() or f.stat().st_size>MAX_ZIP_BYTES:
        _blocked("expected bounded local original ZIP")
    print(json.dumps(
        source_sample_crosswalk(f.read_bytes()), sort_keys=True, indent=2
    ))


if __name__=="__main__":
    try:
        main()
    except (OSError, CensusZipError, PilotGeometryError,
            Louisiana64Error, CrosswalkError) as exc:
        print("BLOCKED:",exc,file=sys.stderr)
        sys.exit(2)
