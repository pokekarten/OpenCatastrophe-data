#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict offline source audit of Zenodo 5795435 Copernicus Rapid Mapping AOIs.

The archive is a CC-BY4 DERIVED, seasonal 30m mask source, not independent
2016 Montargis observations. Never interpret projected EPSG3035 coordinates
as RFC7946 WGS84 GeoJSON or equate one AOI point to its flood geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re


class AOISourceBlocked(ValueError):
    """Unreviewed source edition, ambiguous projection or event scope."""


_ZENODO_RECORD = "5795435"
_EXPECTED_BYTES = 203733
_EXPECTED_MD5 = "cda186323fe76195b183316fd06c2547"
_EXPECTED_CRS = "urn:ogc:def:crs:EPSG::3035"
_EXPECTED_AOIS = frozenset({"POISSY", "MANTESLAJOLIE", "PARIS", "YERRES"})
_EXPECTED_RASTER = (
    "clm_flood.events_copernicus.ems_p_30m_0..0cm_"
    "20160301..20160531_eumap_epsg3035_v0.2.tif"
)
_FIELDS = frozenset({"EMS_ID", "EMS_AOI", "EMS_LINK", "YEAR_START",
                     "YEAR_END", "SEASON", "geo_harmonizer_raster"})


def _pairs_unique(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise AOISourceBlocked("duplicate JSON property")
        d[k] = v
    return d


def _reject_constant(_):
    raise AOISourceBlocked("nonfinite JSON number")


def _one_coordinate_pair(feature):
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise AOISourceBlocked("malformed GeoJSON AOI feature")
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        raise AOISourceBlocked("AOI index must contain point, not event extent")
    coords = geometry.get("coordinates")
    if not isinstance(coords, list) or len(coords) != 2:
        raise AOISourceBlocked("projected AOI centroid requires two numbers")
    for value in coords:
        if type(value) not in (float, int):
            raise AOISourceBlocked("invalid projected AOI coordinate type")
        if not 1_000_000 <= value <= 7_000_000:
            raise AOISourceBlocked("AOI coordinate is not a projected EPSG3035 metre value")
        if type(value) is float and not math.isfinite(value):
            raise AOISourceBlocked("nonfinite AOI coordinate")
    return coords


def audit_index(document):
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise AOISourceBlocked("not the archived GeoJSON FeatureCollection")
    crs = document.get("crs")
    if (not isinstance(crs, dict) or crs.get("type") != "name" or
            not isinstance(crs.get("properties"), dict) or
            crs["properties"].get("name") != _EXPECTED_CRS):
        raise AOISourceBlocked("projected EPSG3035 original CRS must be explicit")
    rows = document.get("features")
    if not isinstance(rows, list) or not 4 <= len(rows) <= 1000:
        raise AOISourceBlocked("bounded source AOI collection required")
    selected = {}
    spring2016 = summer2016 = 0
    published_year_conflicts = []
    for row in rows:
        _one_coordinate_pair(row)
        props = row.get("properties")
        if not isinstance(props, dict) or not _FIELDS <= set(props):
            raise AOISourceBlocked("incomplete original AOI index properties")
        year, season = props["YEAR_START"], props["SEASON"]
        if type(year) is not int or not (2012 <= year <= 2020 or year == 2000):
            raise AOISourceBlocked("year malformed/outside reviewed archive anomalies")
        if type(props["YEAR_END"]) is not int:
            raise AOISourceBlocked("event end-year malformed")
        if season not in {"winter", "spring", "summer", "autumn"}:
            raise AOISourceBlocked("unknown seasonal mosaic identifier")
        source_file = props["geo_harmonizer_raster"]
        if not isinstance(source_file, str):
            raise AOISourceBlocked("seasonal original raster reference missing")
        m = re.search(r"_(\d{8})\.\.(\d{8})_eumap_", source_file)
        if m is None:
            raise AOISourceBlocked("unreviewed seasonal raster naming structure")
        raster_start_year = int(m.group(1)[:4])
        if raster_start_year != year:
            # An actual published anomaly, not permission to infer YEAR_START=2020.
            if (year != 2000 or raster_start_year != 2020 or
                    props["EMS_ID"] not in {"EMSR441", "EMSR442", "EMSR445"}):
                raise AOISourceBlocked("unreviewed year-vs-raster conflict")
            published_year_conflicts.append(props["EMS_ID"])
        if year == 2016 and season == "spring":
            spring2016 += 1
        if year == 2016 and season == "summer":
            summer2016 += 1
        if props["EMS_ID"] == "EMSN028":
            raise AOISourceBlocked("non-Rapid-Mapping activation in Rapid source index")
        if props["EMS_ID"] != "EMSR165":
            continue
        aoi = props["EMS_AOI"]
        if not isinstance(aoi, str) or aoi not in _EXPECTED_AOIS or aoi in selected:
            raise AOISourceBlocked("EMSR165 AOI set differs from original index")
        if (props["YEAR_START"] != 2016 or props["YEAR_END"] != 2016 or
                season != "spring" or
                props["geo_harmonizer_raster"] != _EXPECTED_RASTER or
                props["EMS_LINK"] !=
                "https://emergency.copernicus.eu/mapping/list-of-components/EMSR165"):
            raise AOISourceBlocked("original EMSR165 source/season mapping differs")
        selected[aoi] = tuple(row["geometry"]["coordinates"])
    if set(selected) != _EXPECTED_AOIS:
        raise AOISourceBlocked("incomplete or altered source-verified EMSR165 subset")
    return {
        "profile": "oc-zenodo5795435-rapid-flood-aoi-index-v0",
        "zenodo_record": _ZENODO_RECORD,
        "publisher_dataset_license": "CC-BY-4.0",
        "source_structure": "legacy_GeoJSON_with_projected_CRS",
        "source_crs": _EXPECTED_CRS,
        "treat_coordinates_as_wgs84_lon_lat": False,
        "all_index_aoi_point_rows": len(rows),
        "2016_spring_index_aoi_point_rows": spring2016,
        "original_index_year_mismatch_count": len(published_year_conflicts),
        "year_mismatch_activation_codes": sorted(set(published_year_conflicts)),
        "year_2000_metadata_may_not_be_silently_corrected": True,
        "2016_summer_index_aoi_point_rows": summer2016,
        "emsr165_aoi_points_in_this_archive": len(selected),
        "emsr165_aoi_names_in_this_archive": sorted(selected),
        "emsr165_assigned_mosaic": _EXPECTED_RASTER,
        "emsr165_mosaic_season": "spring",
        "montargis_name_present_for_emsr165": False,
        "emsn028_montargis_covered_by_this_rapid_index": False,
        "aoi_centroids_are_original_flood_extent_polygons": False,
        "mosaic_pixels_are_event_specific_or_daily": False,
        "building_or_property_water_depth_established": False,
        "source_2016_peak_observation_proven": False,
        "independent_2016_montargis_holdout_established": False,
        "provider_raster_original_bytes_authenticated": False,
        "risk_model_input_admitted": False,
        "report": "historical_rapid_mapping_index_only_not_montargis_2016",
    }


def audit_original_bytes(raw):
    if not isinstance(raw, bytes) or len(raw) != _EXPECTED_BYTES:
        raise AOISourceBlocked("Zenodo source byte count differs from pinned record")
    md5 = hashlib.md5(raw, usedforsecurity=False).hexdigest()
    if md5 != _EXPECTED_MD5:
        raise AOISourceBlocked("original GeoJSON MD5 differs from Zenodo source receipt")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs_unique,
                          parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AOISourceBlocked("malformed original GeoJSON") from exc
    report = audit_index(data)
    if (report["all_index_aoi_point_rows"] != 455 or
            report["original_index_year_mismatch_count"] != 13):
        raise AOISourceBlocked("original record AOI cardinality changed")
    report["geojson_publisher_md5_matches_local_bytes"] = True
    report["geojson_sha256_local_bytes"] = hashlib.sha256(raw).hexdigest()
    report["raw_source_license_attribution_required"] = True
    # It verifies integrity against published MD5, not original provider
    # geospatial truth, third-party imagery rights, or event-specific validity.
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-geojson", required=True, type=Path)
    args = parser.parse_args()
    try:
        if (not args.original_geojson.is_file() or
                args.original_geojson.stat().st_size != _EXPECTED_BYTES):
            raise AOISourceBlocked("original source file missing/wrong declared size")
        result = audit_original_bytes(args.original_geojson.read_bytes())
    except (OSError, AOISourceBlocked) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
