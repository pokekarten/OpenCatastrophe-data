#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded 2016 D077 SHP research-only geometry check, never an insured CAT risk."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pyproj import CRS, Transformer
from shapely.geometry import box, shape as as_shape
import shapefile

FAMILIES = ("BATI_INDIFFERENCIE", "BATI_INDUSTRIEL", "BATI_REMARQUABLE")
PONTHIERRY_LONLAT_BBOX = (2.5465, 48.5360, 2.5490, 48.5380)
EXPECTED_CRS = CRS.from_epsg(2154)
MAX_CANDIDATES = 10000


class BoundedBuildingError(ValueError):
    """Unsafe shape or uncertain CRS: refuse to report model input."""


def profile(folder: Path, *,
            bbox_lonlat: tuple[float, float, float, float] = PONTHIERRY_LONLAT_BBOX
            ) -> dict[str, Any]:
    if folder.is_symlink() or not folder.is_dir():
        raise BoundedBuildingError("must provide regular local extraction folder")
    if len(bbox_lonlat) != 4 or not (
        -180 <= bbox_lonlat[0] < bbox_lonlat[2] <= 180
        and -90 <= bbox_lonlat[1] < bbox_lonlat[3] <= 90
        and bbox_lonlat[2] - bbox_lonlat[0] <= 0.1
        and bbox_lonlat[3] - bbox_lonlat[1] <= 0.1
    ):
        raise BoundedBuildingError("must select a bounded geographic research area")
    count: dict[str, int] = {}
    total_candidates = 0
    selected = 0
    for family in FAMILIES:
        shp = folder / (family + ".shp")
        prj = folder / (family + ".prj")
        if any((folder / (family + s)).is_symlink()
               for s in (".shp", ".shx", ".dbf", ".prj")):
            raise BoundedBuildingError("symlink shapefile component")
        if any(not (folder / (family + s)).is_file()
               for s in (".shp", ".shx", ".dbf", ".prj")):
            raise BoundedBuildingError("incomplete mandatory SHP/SHX/DBF/PRJ building family")
        try:
            crs = CRS.from_wkt(prj.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            raise BoundedBuildingError("invalid source PRJ CRS") from exc
        if not crs.equals(EXPECTED_CRS, ignore_axis_order=True):
            raise BoundedBuildingError("unverified source CRS; expected Lambert-93 EPSG:2154")
        t = Transformer.from_crs(CRS.from_epsg(4326), crs, always_xy=True)
        x0, y0, x1, y1 = bbox_lonlat
        xx, yy = t.transform([x0, x1, x0, x1], [y0, y0, y1, y1])
        projected_bounds = (min(xx), min(yy), max(xx), max(yy))
        rectangle = box(*projected_bounds)
        c = 0
        try:
            with shapefile.Reader(str(shp)) as reader:
                if reader.shapeType not in (
                    shapefile.POLYGON, shapefile.POLYGONZ, shapefile.POLYGONM
                ):
                    raise BoundedBuildingError("source layer is not polygonal")
                for feature in reader.iterShapes(bbox=projected_bounds):
                    total_candidates += 1
                    if total_candidates > MAX_CANDIDATES:
                        raise BoundedBuildingError("bounded pilot feature budget exceeded")
                    try:
                        geometry = as_shape(feature.__geo_interface__)
                    except Exception as exc:
                        raise BoundedBuildingError("cannot decode source building polygon") from exc
                    if not geometry.is_valid or geometry.is_empty:
                        raise BoundedBuildingError("invalid source building polygon")
                    if geometry.intersects(rectangle):
                        c += 1
        except (OSError, shapefile.ShapefileException) as exc:
            raise BoundedBuildingError("unable to read source building shapefile") from exc
        count[family] = c
        selected += c
    return {
        "schema": "fr-bdtopo-d077-2016-ponthierry-bounded-building-profile-v0",
        "source_edition": "BD TOPO v2.1 D077 2016-03-24",
        "source_crs_verified": "EPSG:2154",
        "aoi_bbox_wgs84": list(bbox_lonlat),
        "candidate_geometries_checked": total_candidates,
        "source_footprints_intersecting_pilot_box_by_class": count,
        "historical_mapped_footprint_candidates_in_pilot_box": selected,
        "individual_building_records_exported": False,
        "building_identity_linked_to_current_rnb": False,
        "licensed_2016_flood_footprint_intersected": False,
        "insured_replacement_value_known": False,
        "model_input_approved": False,
        "research_only": True,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--extracted-building-shapefiles", required=True, type=Path)
    args = p.parse_args()
    try:
        report = profile(args.extracted_building_shapefiles)
    except (BoundedBuildingError, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
