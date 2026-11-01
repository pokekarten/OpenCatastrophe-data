#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Inspect original exact BKG Berlin GeoTIFF band scale/unit *claims* only.

No pixel/sample decoding, provider GET, building position, loss or CAT admission.
Runtime GDAL scale/offset may be implicit defaults; they are never asserted
to convert source signed Int16 codes into physical flood-water depth.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

from research_runners.berlin_bld4_bkg_original_raw_cell_support_v0 import (
    FULL_ORIGINAL_BKG_BYTES, FULL_ORIGINAL_BKG_SHA256,
)

MAX_TAGS = 128
MAX_KEY_LENGTH = 100
MAX_UNIT_LENGTH = 64
UNIT_ALIASES = {
    "m": "metres", "meter": "metres", "metre": "metres",
    "meters": "metres", "metres": "metres",
    "cm": "centimetres", "centimeter": "centimetres",
    "centimetre": "centimetres", "centimeters": "centimetres",
    "centimetres": "centimetres",
    "mm": "millimetres", "millimeter": "millimetres",
    "millimetre": "millimetres", "millimeters": "millimetres",
    "millimetres": "millimetres",
}
CANDIDATE_UNIT_TAG_KEYS = ("UNITTYPE", "UNIT", "UNITS", "unit")


class SourceBandSemanticsBlocked(ValueError):
    """Exact original source or scalar metadata invariant rejected."""


def _tags(value, name: str) -> dict:
    if not isinstance(value, dict) or len(value) > MAX_TAGS:
        raise SourceBandSemanticsBlocked(f"{name}: invalid or excessive GDAL tags")
    if any(not isinstance(k, str) or not 0 < len(k) <= MAX_KEY_LENGTH for k in value):
        raise SourceBandSemanticsBlocked(f"{name}: invalid GDAL tag key")
    return value


def _unit(value):
    if value is None or value == "":
        return None
    if not isinstance(value, str) or len(value) > MAX_UNIT_LENGTH:
        raise SourceBandSemanticsBlocked("unsupported source unit metadata")
    return UNIT_ALIASES.get(value.strip().lower(), "UNRECOGNIZED")


def _number(value, kind: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise SourceBandSemanticsBlocked(f"{kind}: numeric runtime scalar required")
    if not math.isfinite(value):
        raise SourceBandSemanticsBlocked(f"{kind}: nonfinite runtime scalar")
    return float(value)


def inspect_unit_claims(*, global_tags, band_tags,
                        gdal_scale, gdal_offset, gdal_unit,
                        band_description) -> dict:
    """Report bounded unit/scale evidence; never certify physical conversion."""
    global_tags = _tags(global_tags, "dataset")
    band_tags = _tags(band_tags, "band")
    if band_description is not None and (
        not isinstance(band_description, str) or len(band_description) > 256
    ):
        raise SourceBandSemanticsBlocked("unbounded original band description")
    scale = _number(gdal_scale, "GDAL scale")
    offset = _number(gdal_offset, "GDAL offset")
    units = {"rasterio_band_unit": _unit(gdal_unit)}
    for label, tags in (("dataset_unit_tag", global_tags), ("band_unit_tag", band_tags)):
        found = [tags[k] for k in CANDIDATE_UNIT_TAG_KEYS if k in tags]
        if len(found) > 1:
            raise SourceBandSemanticsBlocked(f"{label}: multiple unit labels")
        units[label] = _unit(found[0]) if found else None
    known = {x for x in units.values() if x and x != "UNRECOGNIZED"}
    if len(known) > 1:
        raise SourceBandSemanticsBlocked("conflicting source unit metadata claims")
    return {
        "declared_or_runtime_recognized_unit_candidate": next(iter(known)) if known else None,
        "unit_metadata_present": any(x is not None for x in units.values()),
        "unit_metadata_unrecognized_or_ambiguous": any(x == "UNRECOGNIZED" for x in units.values()),
        "unit_source_fields_with_claims": sorted(k for k, v in units.items() if v is not None),
        "runtime_gdal_band_scale": scale,
        "runtime_gdal_band_offset": offset,
        "explicit_scale_or_offset_tag_keys_present": any(
            k.lower() in ("scale", "offset") for k in set(global_tags) | set(band_tags)
        ),
        "band_description_present": bool(band_description),
        "source_units_and_scale_physically_calibrated": False,
        "gdal_scale_and_offset_may_be_implicit_defaults": True,
        "raw_int16_values_not_imputed_as_m_or_cm": True,
        "source_nodata_not_interpreted_as_dry": True,
        "no_original_pixel_values_or_building_geometry_reported": True,
        "model_input_approved": False,
    }


def probe(path: Path) -> dict:
    import rasterio

    if (not path.is_file() or path.is_symlink()
            or path.stat().st_size != FULL_ORIGINAL_BKG_BYTES):
        raise SourceBandSemanticsBlocked("original BKG TIFF size or file type mismatch")
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != FULL_ORIGINAL_BKG_SHA256:
        raise SourceBandSemanticsBlocked("original BKG TIFF SHA-256 drift")
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="YES"):
        with rasterio.open(path) as ds:
            if (ds.driver != "GTiff" or ds.crs is None or
                    ds.crs.to_epsg() != 25832 or ds.count != 1 or
                    ds.width != 10000 or ds.height != 10000 or
                    ds.dtypes != ("int16",) or ds.nodata != -9999):
                raise SourceBandSemanticsBlocked("original BKG band format/CRS mismatch")
            report = inspect_unit_claims(
                global_tags=ds.tags(),
                band_tags=ds.tags(1),
                gdal_scale=ds.scales[0],
                gdal_offset=ds.offsets[0],
                gdal_unit=ds.units[0],
                band_description=ds.descriptions[0],
            )
    return {
        "profile": "oc-bkg-berlin-original-int16-scalar-unit-claims-v0",
        "original_bkg_full_tiff_sha256": FULL_ORIGINAL_BKG_SHA256,
        "original_bkg_tiff_bytes": FULL_ORIGINAL_BKG_BYTES,
        "original_raster_crs": "EPSG:25832",
        "original_int16_nodata": -9999,
        "source_provider": "BKG",
        **report,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_bkg_tiff", type=Path)
    args = parser.parse_args(argv)
    try:
        result = probe(args.original_bkg_tiff)
    except (OSError, ValueError, ImportError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, allow_nan=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
