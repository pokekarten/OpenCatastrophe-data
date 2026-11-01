#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only real BLD4 footprint x original BKG raster RAW support areas.

No implied water-depth units, event frequency, property TIV or CAT losses.
The source-original SHA is verified before the 47 MB TIFF is opened.
Original buildings are sourced from temporary validated BLD4 SQLite and
NEVER logged as individual geometry, coordinate, ID or attribute.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

from research_runners.berlin_alkis_gebaeude_five_feature_join_v0 import BBOX
from research_runners.berlin_bld4_synthetic_flood_cell_join_v0 import read_bld4_footprints
from research_runners.probe_bkg_berlin_kostra_direct_tiff_v0 import (
    MAX_SOURCE_BYTES, MAX_WINDOW_AXIS, MAX_SAMPLE_PIXELS, URL,
    pilot_projected_bounds,
)

PROFILE = "berlin-bld4-bkg-real-kostra-raw-cell-support-v0"
FULL_ORIGINAL_BKG_SHA256 = "7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f"
FULL_ORIGINAL_BKG_BYTES = 47_280_200
MAX_TESTED_BUILDINGS = 5


class RealSupportError(ValueError):
    """The input is not a verified, bounded two-source research pairing."""


def audit_cells(polygons_utm32, values, missing, grid_transform):
    """Exact Shapely area intersection with native 1 m TIFF cells; raw classes.

    All geometry is already projected to raster EPSG:25832. This accepts no
    source URI and emits only aggregate area/count metrics, not individual
    polygons, pixel values, cell coordinates, centroid or identifiers.
    """
    import numpy as np
    from shapely.geometry import box
    from rasterio.windows import Window, bounds

    if not 1 <= len(polygons_utm32) <= MAX_TESTED_BUILDINGS:
        raise RealSupportError("building count outside bounded review")
    raw = np.asarray(values)
    mask = np.asarray(missing)
    if (raw.ndim != 2 or raw.dtype.kind not in "iu"
            or mask.dtype.kind != "b" or raw.shape != mask.shape
            or raw.size == 0 or raw.size > MAX_SAMPLE_PIXELS
            or raw.shape[0] > MAX_WINDOW_AXIS or raw.shape[1] > MAX_WINDOW_AXIS):
        raise RealSupportError("unreviewed raw band or mask array")
    h, w = raw.shape
    if (not all(math.isfinite(float(v)) for v in grid_transform[:6])
            or abs(grid_transform.a - 1) > 1e-6
            or abs(grid_transform.e + 1) > 1e-6
            or abs(grid_transform.b) > 1e-9
            or abs(grid_transform.d) > 1e-9):
        raise RealSupportError("not exact north-up 1m raster cell support")
    b = bounds(Window(0, 0, w, h), grid_transform)
    raster_box = box(*b)
    positives = zeros = nodata = out_of_raster = total = 0.0
    any_positive, all_valid, no_valid = 0, 0, 0
    for geom in polygons_utm32:
        if (geom.is_empty or not geom.is_valid or geom.geom_type not in ("Polygon", "MultiPolygon")
                or not 0 < geom.area < 100_000 or not all(math.isfinite(c) for c in geom.bounds)):
            raise RealSupportError("invalid projected building pilot geometry")
        total += geom.area
        covered = geom.intersection(raster_box)
        out_of_raster += max(0.0, geom.area - covered.area)
        local_positive = local_zero = local_valid = 0.0
        if covered.area > 0:
            minx, miny, maxx, maxy = covered.bounds
            # Convert native metric cell bounds to integer cells.
            c0 = max(0, math.floor((minx - grid_transform.c)))
            c1 = min(w, math.ceil((maxx - grid_transform.c)))
            r0 = max(0, math.floor((grid_transform.f - maxy)))
            r1 = min(h, math.ceil((grid_transform.f - miny)))
            if c1 < c0 or r1 < r0 or (c1-c0)*(r1-r0) > MAX_SAMPLE_PIXELS:
                raise RealSupportError("unexpected building raster window footprint")
            for row in range(r0, r1):
                top = grid_transform.f - row
                for col in range(c0, c1):
                    left = grid_transform.c + col
                    a = covered.intersection(box(left, top - 1, left + 1, top)).area
                    if a <= 0:
                        continue
                    if mask[row, col]:
                        nodata += a
                    elif raw[row, col] == 0:
                        zeros += a
                        local_zero += a
                        local_valid += a
                    elif raw[row, col] > 0:
                        positives += a
                        local_positive += a
                        local_valid += a
                    else:
                        raise RealSupportError("unmasked negative raw integer flood code")
        if local_positive > 1e-8:
            any_positive += 1
        if math.isclose(local_valid, geom.area, rel_tol=2e-8, abs_tol=1e-5):
            all_valid += 1
        if local_valid <= 1e-8:
            no_valid += 1
    if not math.isclose(total, positives+zeros+nodata+out_of_raster,
                        rel_tol=1e-8, abs_tol=1e-5):
        raise RealSupportError("source-derived building area does not conserve raster support")
    return {
        "pilot_clipped_buildings_checked": len(polygons_utm32),
        "clipped_building_area_in_raster_crs_m2": round(total, 6),
        "positive_raw_code_supported_area_m2": round(positives, 6),
        "valid_zero_raw_code_supported_area_m2": round(zeros, 6),
        "original_nodata_supported_area_m2": round(nodata, 6),
        "outside_sample_window_area_m2": round(out_of_raster, 6),
        "buildings_with_any_positive_raw_code": any_positive,
        "buildings_with_all_area_valid_numeric_codes": all_valid,
        "buildings_without_valid_numeric_codes": no_valid,
        "exact_polygon_cell_area_conservation_verified": True,
        "positive_raw_code_not_confirmed_as_metres_of_depth": True,
        "zero_code_not_an_observed_no_flood_event": True,
        "nodata_never_zero_filled": True,
        "individual_building_or_cell_values_exported": False,
        "actual_insurance_exposure_or_loss_estimated": False,
    }


def audit(buildings: Path, original_tiff: Path, *, expected_sha=FULL_ORIGINAL_BKG_SHA256):
    from shapely.geometry import box
    from shapely.ops import transform
    from pyproj import Transformer
    import numpy as np
    import rasterio
    from rasterio.windows import Window, from_bounds, transform as window_transform

    if (not original_tiff.is_file() or original_tiff.is_symlink()
            or original_tiff.stat().st_size != FULL_ORIGINAL_BKG_BYTES
            or original_tiff.stat().st_size > MAX_SOURCE_BYTES):
        raise RealSupportError("source TIFF missing or exact original size changed")
    digest = sha256()
    with original_tiff.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""):
            digest.update(block)
    actual_sha = digest.hexdigest()
    if actual_sha != expected_sha or expected_sha != FULL_ORIGINAL_BKG_SHA256:
        raise RealSupportError("full original provider SHA differs from reviewed BKG receipt")
    originals, building_sha = read_bld4_footprints(buildings)
    pilot = box(*BBOX)
    clipped = [g.intersection(pilot) for g in originals]
    clipped = [g for g in clipped if g.area > 1e-8]
    if not clipped or len(clipped) > MAX_TESTED_BUILDINGS:
        raise RealSupportError("no building polygon with positive pilot overlap")
    # Densify long polygon segments before projection, rather than moving
    # only corner vertices from UTM33 to UTM32 across zone boundaries.
    transformer = Transformer.from_crs("EPSG:25833", "EPSG:25832",
                                       always_xy=True, allow_ballpark=False,
                                       only_best=True)
    projected = [transform(transformer.transform, g.segmentize(1.0))
                 for g in clipped]
    box32 = pilot_projected_bounds(transformer=transformer)
    # Exact transformed original pilot polygon, NOT its loose raster bbox.
    pilot_utm32 = transform(transformer.transform, pilot.segmentize(1.0))
    from research_runners.berlin_bld4_bkg_exterior_ring_raw_support_v0 import (
        audit_disjoint_exterior_bands,
    )
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="YES"):
        with rasterio.open(original_tiff, "r") as ds:
            a = ds.transform
            if (ds.driver != "GTiff" or ds.crs is None or ds.crs.to_epsg() != 25832
                    or ds.count != 1 or ds.dtypes[0] != "int16" or ds.nodata != -9999
                    or (ds.width, ds.height) != (10_000, 10_000)
                    or abs(a.a - 1)>1e-9 or abs(a.e+1)>1e-9
                    or abs(a.b)>1e-9 or abs(a.d)>1e-9):
                raise RealSupportError("unexpected original BKG raster CRS/format/nodata")
            left, bottom, right, top = box32
            bounds = ds.bounds
            if not (bounds.left <= left < right <= bounds.right
                    and bounds.bottom <= bottom < top <= bounds.top):
                raise RealSupportError("original source does not cover transformed pilot")
            fl = from_bounds(left,bottom,right,top,transform=a)
            col,row = math.floor(fl.col_off),math.floor(fl.row_off)
            end_col = math.ceil(fl.col_off+fl.width)
            end_row = math.ceil(fl.row_off+fl.height)
            h,w = end_row-row,end_col-col
            if not (0<=row and 0<=col and end_row<=ds.height and end_col<=ds.width
                    and 1<=h<=MAX_WINDOW_AXIS and 1<=w<=MAX_WINDOW_AXIS
                    and h*w<=MAX_SAMPLE_PIXELS):
                raise RealSupportError("pilot raster-window bound exceeded")
            window = Window(col,row,w,h)
            cells = ds.read(1, window=window, masked=True, boundless=False)
            values = np.asarray(cells.data)
            missing = np.ma.getmaskarray(cells)
            if values.shape != (h,w) or missing.shape != values.shape:
                raise RealSupportError("source mask/data array mismatch")
            if np.any((values == -9999) & ~missing):
                raise RealSupportError("source -9999 escaped original mask")
            result = audit_cells(projected, values, missing, window_transform(window,a))
            exterior = audit_disjoint_exterior_bands(
                projected, pilot_utm32, values, missing,
                window_transform(window,a),
            )
    return {
        "profile": PROFILE,
        "source_bkg_original_tiff_sha256": actual_sha,
        "source_bkg_original_size_bytes": FULL_ORIGINAL_BKG_BYTES,
        "source_bkg_exact_url": URL,
        "source_bld4_wfs_response_sha256": building_sha,
        "source_bld4_buildings_mutable_date_not_historic": True,
        "source_hazard_bkg_kostra_design_scenario": True,
        "source_products_temporal_alignment_proven": False,
        "original_bkg_bounded_real_pixel_window_used": True,
        "pilot_window_cells_examined": h*w,
        "building_coverage_from_real_bkg_raw_codes_not_depth": True,
        "real_water_depth_units_verified": False,
        "cat_model_admitted": False,
        "any_property_ids_or_coordinates_written": False,
        **result,
        "exterior_raw_code_support_research": exterior,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--buildings", type=Path, required=True)
    p.add_argument("--original-bkg-tiff", type=Path, required=True)
    args=p.parse_args(argv)
    try:
        print(json.dumps(audit(args.buildings,args.original_bkg_tiff),
                         sort_keys=True,allow_nan=False))
    except (RealSupportError, ValueError, OSError, ImportError) as exc:
        print("BLOCKED: "+str(exc), file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())
