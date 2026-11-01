# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only original 2016 CEMS vs current RNB CENTROID point context.

The two RNB points originate from read-only Neon 2026-11-01 current-building
footprints; neither point is a verified 2016 asset. These are point-only
diagnostics, never building footprint, event-depth or loss overlays.
Original CEMS source must be full-archive SHA-pinned outside this module.
No raw source geometries, derived geometries or exact point coordinates
are included in output. AOI04 coverage and rights remain unverified.
"""
from __future__ import annotations
from math import isfinite

# Source: CAT-only Neon insurance main, research.fr_ponthierry_rnb_ign_building_v0
# ST_Centroid(rnb_geom), EPSG:4326, read-only on 2026-11-01.
CURRENT_RNB_CENTROIDS = (
    ("5TR6PNH2YQPT", 2.546991657, 48.536003228),
    ("TCHNNF59Y27V", 2.546881985, 48.536608233),
)
MAX_ESTIMATED_LAYER = 5000


def compare_original_layers_to_current_points(gdb_path):
    import fiona
    from fiona.transform import transform
    from shapely.geometry import Point, shape
    from shapely import make_valid

    point_ids = [x[0] for x in CURRENT_RNB_CENTROIDS]
    lons = [x[1] for x in CURRENT_RNB_CENTROIDS]
    lats = [x[2] for x in CURRENT_RNB_CENTROIDS]
    east, north = transform("EPSG:4326", "EPSG:32631", lons, lats)
    pts = [Point(x, y) for x, y in zip(east, north)]
    if len(pts) != 2 or any(
        not (-1_000_000 <= p.x <= 1_000_000 and
             4_000_000 <= p.y <= 6_000_000) for p in pts
    ):
        raise ValueError("current reference points outside study CRS region")

    with fiona.open(str(gdb_path), layer="Flooded_area", mode="r") as src:
        if len(src) != 1 or not src.crs or src.crs.to_epsg() != 32631:
            raise ValueError("unexpected original Flooded_area count or CRS")
        geom = shape(next(iter(src))["geometry"])
    if geom.geom_type not in ("Polygon", "MultiPolygon") or geom.is_empty:
        raise ValueError("unexpected original flood mask type")
    source_valid = bool(geom.is_valid)
    # The source is known to have a self-intersection. Repair is *only*
    # ephemeral context, not a recommended scientific source correction.
    compared = geom if source_valid else make_valid(
        geom, method="linework", keep_collapsed=True
    )
    if not compared.is_valid or compared.is_empty or compared.geom_type not in (
        "Polygon", "MultiPolygon"
    ):
        raise ValueError("observed candidate not safe for point context")
    observed_distance = [round(float(compared.distance(p)), 2) for p in pts]
    observed_covers = [bool(compared.covers(p)) for p in pts]

    with fiona.open(str(gdb_path), layer="Estimated_Max_Flood_Extent", mode="r") as src:
        count = len(src)
        if count < 1 or count > MAX_ESTIMATED_LAYER or not src.crs or src.crs.to_epsg() != 32631:
            raise ValueError("unexpected estimated maximum layer count or CRS")
        valid_count = 0
        invalid_count = 0
        empty_count = 0
        counts = [0 for _ in pts]
        best_distance = [float("inf") for _ in pts]
        for feature in src:
            geo = feature.get("geometry")
            if geo is None:
                empty_count += 1
                continue
            area = shape(geo)
            if area.is_empty:
                empty_count += 1
                continue
            if area.geom_type not in ("Polygon", "MultiPolygon") or not area.is_valid:
                invalid_count += 1
                continue
            valid_count += 1
            for i, point in enumerate(pts):
                distance = float(area.distance(point))
                if isfinite(distance) and distance < best_distance[i]:
                    best_distance[i] = distance
                if area.covers(point):
                    counts[i] += 1
    if valid_count + invalid_count + empty_count != count:
        raise ValueError("not all maximum source rows accounted for")

    return {
        "receipt_kind": "CEMS_EMSN028_RNB_CURRENT_CENTROIDS_CONTEXT_V0",
        "source_coordinate_crs": "EPSG:4326",
        "source_rnb_centroid_coordinates_printed": False,
        "point_ids": point_ids,
        "point_reference_vintage": "CURRENT_RNB_NOT_PROVEN_2016",
        "original_observed_layer": {
            "source_rows": 1,
            "source_geometry_valid": source_valid,
            "research_only_linework_repair_used": not source_valid,
            "point_inside_or_on_boundary": observed_covers,
            "distance_from_current_point_to_repaired_observed_mask_m": observed_distance,
        },
        "original_estimated_maximum_layer": {
            "source_rows": count,
            "source_polygons_valid": valid_count,
            "source_polygons_invalid_skipped": invalid_count,
            "source_polygons_null_or_empty_skipped": empty_count,
            "source_geometry_automatically_repaired": False,
            "per_point_number_of_valid_polygon_covers": counts,
            "per_point_min_distance_to_valid_polygon_m": [
                round(d, 2) if isfinite(d) else None for d in best_distance
            ],
        },
        "aoi04_specific_original_polygon_verified": False,
        "event_time_and_building_vintage_aligned": False,
        "station_discharge_not_building_depth": True,
        "no_inundation_claim_can_be_derived_from_point_exclusion": True,
        "source_specific_rights_cleared": False,
        "historical_insurer_exposure_or_loss_proven": False,
        "cat_model_admitted": False,
        "original_or_repaired_geodata_stored": False,
    }
