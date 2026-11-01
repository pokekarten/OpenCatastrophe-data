#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One BKG official direct-GeoTIFF Berlin pilot sample; research-only, not CAT input.

Different source and vintage from GDI Berlin 2022-named Deflate ZIP GeoTIFFs.
The ONE pinned source TIFF is downloaded ephemerally with a hard byte cap.
Its actual georeferencing is checked before any small pixel window is read.
No archive ingestion, insurer information or per-building depth is produced.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import ssl
import sys
import tempfile
from urllib import error, request

URL = (
    "https://daten.gdz.bkg.bund.de/produkte/sonstige/starkregen/aktuell/"
    "be/maxdepth_kostra/s32790/"
    "starkregen_maxdepth_kostra_32790_5820_10_be.tif"
)
MAX_SOURCE_BYTES = 70 * 1024 * 1024
MAX_WINDOW_AXIS = 512
MAX_SAMPLE_PIXELS = MAX_WINDOW_AXIS**2
SOURCE_TIMEOUT_SECONDS = 45
PILOT_BBOX_EPSG25833 = (391700.0, 5819950.0, 391900.0, 5820150.0)
SOURCE_LICENSE = "Datenlizenz Deutschland Namensnennung 2.0; BKG attribution"
PROFILE = "bkg-berlin-kostra-exact-direct-geotiff-pilot-window-v0"


class BkgTileBlocked(ValueError):
    """Source identity, limits, or scientific gates were not satisfied."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BkgTileBlocked("fixed BKG source URL redirected")


def _open(req):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=SOURCE_TIMEOUT_SECONDS)


def download_exact_source(destination: Path, *, opener=_open) -> dict:
    """Download exactly one public fixed TIFF; never accept a caller URL."""
    req = request.Request(
        URL, method="GET",
        headers={"Accept": "image/tiff,application/octet-stream",
                 "Accept-Encoding": "identity"},
    )
    count, digest, declared_length = 0, sha256(), None
    try:
        with opener(req) as resp:
            if resp.status != 200 or resp.geturl() != URL:
                raise BkgTileBlocked("official source returned non-200 or redirect")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if media not in ("image/tiff", "image/geotiff", "application/octet-stream"):
                raise BkgTileBlocked("unreviewed source content type")
            if resp.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise BkgTileBlocked("unexpected HTTP content encoding")
            declared = resp.headers.get("Content-Length")
            if declared is not None:
                if not declared.isdecimal():
                    raise BkgTileBlocked("invalid original Content-Length")
                declared_length = int(declared)
                if not 4096 <= declared_length <= MAX_SOURCE_BYTES:
                    raise BkgTileBlocked("original TIFF larger than bounded allowance")
            with destination.open("xb") as target:
                while True:
                    chunk = resp.read(min(1024 * 1024, MAX_SOURCE_BYTES + 1 - count))
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > MAX_SOURCE_BYTES:
                        raise BkgTileBlocked("source exceeded fixed original TIFF cap")
                    digest.update(chunk)
                    target.write(chunk)
    except (error.URLError, OSError, TimeoutError) as exc:
        raise BkgTileBlocked("original BKG direct TIFF unavailable") from exc
    if count < 4096 or declared_length is not None and declared_length != count:
        raise BkgTileBlocked("original TIFF incomplete or truncated")
    return {
        "source_original_bytes": count,
        "source_full_tiff_sha256_locally_calculated": digest.hexdigest(),
        "source_http_content_length_verified": declared_length is not None,
        "original_bytes_committed_or_retained": False,
    }


def pilot_projected_bounds(*, transformer=None):
    """Densify the fixed EPSG:25833 pilot perimeter in EPSG:25832.

    The envelope is intentionally conservative; it is not a building-footprint
    or a reprojection of physical flood depth. Neither source CRS is guessed.
    """
    if transformer is None:
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:25833", "EPSG:25832",
                                           always_xy=True)
    a, b, c, d = PILOT_BBOX_EPSG25833
    pts = []
    for i in range(21):
        t = i / 20
        pts.extend(((a+(c-a)*t, b), (a+(c-a)*t, d),
                    (a, b+(d-b)*t), (c, b+(d-b)*t)))
    xy = [transformer.transform(x, y) for x, y in pts]
    if not xy or not all(math.isfinite(x) and math.isfinite(y) for x, y in xy):
        raise BkgTileBlocked("invalid pilot source CRS transform")
    return (min(x for x, _ in xy), min(y for _, y in xy),
            max(x for x, _ in xy), max(y for _, y in xy))


def inspect_bkg_tile(path: Path) -> dict:
    """Read only a fixed <=512x512-pixel window, in the provider's own CRS.

    Mask and raw numeric counts are observations, NOT physical-depth units,
    observed flooding, hazard suitability or building-level exposure.
    """
    import numpy as np
    import rasterio
    from rasterio.windows import Window, from_bounds

    transformed = pilot_projected_bounds()
    if transformed[2] <= transformed[0] or transformed[3] <= transformed[1]:
        raise BkgTileBlocked("empty pilot reprojection")
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="YES"):
        with rasterio.open(path, "r") as ds:
            if ds.driver != "GTiff" or ds.crs is None or ds.crs.to_epsg() != 25832:
                raise BkgTileBlocked("original direct TIFF is not EPSG:25832 GeoTIFF")
            if ds.count != 1 or ds.dtypes[0] not in (
                "float32", "float64", "int16", "uint16", "int32", "uint32", "uint8",
            ):
                raise BkgTileBlocked("unreviewed raster band format")
            if not (1 <= ds.width <= 15000 and 1 <= ds.height <= 15000):
                raise BkgTileBlocked("unreviewed TIFF dimensions")
            affine = ds.transform
            if not (abs(affine.a - 1.0) <= 0.01 and
                    abs(affine.e + 1.0) <= 0.01 and
                    abs(affine.b) < 1e-9 and abs(affine.d) < 1e-9):
                raise BkgTileBlocked("not an unrotated approximately 1 m source grid")
            left, bottom, right, top = transformed
            bounds = ds.bounds
            if not (bounds.left <= left < right <= bounds.right and
                    bounds.bottom <= bottom < top <= bounds.top):
                raise BkgTileBlocked("the original BKG TIFF does not fully cover pilot")
            floating = from_bounds(left, bottom, right, top, transform=affine)
            col = math.floor(floating.col_off)
            row = math.floor(floating.row_off)
            end_col = math.ceil(floating.col_off + floating.width)
            end_row = math.ceil(floating.row_off + floating.height)
            width, height = end_col - col, end_row - row
            if not (0 <= col and 0 <= row and end_col <= ds.width and
                    end_row <= ds.height and 1 <= width <= MAX_WINDOW_AXIS and
                    1 <= height <= MAX_WINDOW_AXIS and
                    width * height <= MAX_SAMPLE_PIXELS):
                raise BkgTileBlocked("bounded pilot raster window gate failed")
            # Masked=True uses the source's real on-disk mask/nodata metadata.
            # NoData is NEVER coerced to raw zero; masked cells remain separate.
            sample = ds.read(1, window=Window(col, row, width, height),
                             masked=True, boundless=False)
            mask = np.ma.getmaskarray(sample)
            raw = np.asarray(sample.data)
            if raw.shape != (height, width) or mask.shape != raw.shape:
                raise BkgTileBlocked("unexpected source pixel-array shape")
            finite = np.isfinite(raw)
            valid = ~mask & finite
            nonfinite_unmasked = int((~mask & ~finite).sum())
            if nonfinite_unmasked:
                raise BkgTileBlocked("source contains nonfinite unmasked pixel values")
            observed = raw[valid].astype("float64")
            if not np.isfinite(observed).all():
                raise BkgTileBlocked("unreviewed numeric source pixels")
            return {
                "source_tiff_crs": "EPSG:25832",
                "source_dimensions_pixels": [ds.width, ds.height],
                "source_transform_pixel_size_metres": [affine.a, -affine.e],
                "source_declared_nodata": None if ds.nodata is None else str(ds.nodata),
                "source_raw_dtype": ds.dtypes[0],
                "source_count_bands": ds.count,
                "pilot_bbox_epsg25833_m": list(PILOT_BBOX_EPSG25833),
                "source_pilot_projected_envelope_epsg25832_m": list(transformed),
                "source_window_shape_pixels": [height, width],
                "original_raw_cells_examined": height * width,
                "original_masked_cells": int(mask.sum()),
                "original_finite_unmasked_cells": int(valid.sum()),
                "original_unmasked_numeric_zeros": int((valid & (raw == 0)).sum()),
                "original_unmasked_positive_numbers": int((valid & (raw > 0)).sum()),
                "original_unmasked_negative_numbers": int((valid & (raw < 0)).sum()),
                "original_raw_min_if_valid": float(observed.min()) if observed.size else None,
                "original_raw_max_if_valid": float(observed.max()) if observed.size else None,
                "raw_pixel_physical_depth_units_verified": False,
                "source_scenario_associated_with_specific_Berlin_ZIP_verified": False,
                "individual_building_hazard_join_verified": False,
                "insured_exposure_or_cat_model_admitted": False,
            }


def probe() -> dict:
    with tempfile.TemporaryDirectory(prefix="oc-bkg-berlin-tile-") as directory:
        source_path = Path(directory) / "original-source.tif"
        download = download_exact_source(source_path)
        pixel_receipt = inspect_bkg_tile(source_path)
        return {
            "profile": PROFILE,
            "source_provider": "Bundesamt für Kartographie und Geodäsie",
            "source_exact_url": URL,
            "source_scenario": "BKG HWK_SRG KOSTRA exceptional; source 2024/2025 lineage",
            "original_source_retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_rights": SOURCE_LICENSE,
            "source_original_not_equal_to_Berlin_GDI_2022_named_ZIP": True,
            "source_is_research_only": True,
            **download,
            **pixel_receipt,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network source operation requires an explicit --live")
    try:
        result = probe()
    except (BkgTileBlocked, OSError, ImportError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
