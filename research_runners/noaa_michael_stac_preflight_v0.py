# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline NOAA Hurricane Michael STAC item metadata/provenance preflight.

Accept a *locally supplied* provider STAC item for one named image tile.
No network calls, geospatial intersection, image downloads, image classification,
or rights/model-use approval. Public STAC item extents are metadata, not proof
that a structure was imaged or that the FEMA label used different imagery.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
import re
from typing import Any
from urllib.parse import urlsplit

STAC_ROOT = (
    "https://coastalimagery.blob.core.windows.net/digitalcoast/"
    "HurricaneMichael_2018_8883/"
)
NOAA_INPORT = "https://www.fisheries.noaa.gov/inport/item/57759"
IDENTITY = re.compile(r"^2018101[1-4]aC[0-9]{7}w[0-9]{6}n$")
BANDS = ("red", "green", "blue", "alpha")
MAX_PIXELS = 120_000_000
REQUIRED_KEYS = frozenset({
    "type", "id", "stac_version", "bbox", "geometry", "properties", "assets", "links"
})


class STACPreflightError(ValueError):
    """Reject non-provider, malformed, or conflated source metadata."""


def _datetime(value: Any, field: str) -> datetime:
    if type(value) is not str:
        raise STACPreflightError(f"{field} must include explicit UTC datetime")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise STACPreflightError(f"{field} must include explicit UTC datetime") from exc
    if instant.tzinfo is None or instant.utcoffset() is None or instant.utcoffset().total_seconds() != 0:
        raise STACPreflightError(f"{field} must be UTC, not a local/naive time")
    return instant.astimezone(timezone.utc)


def _positive_number(value: Any, label: str) -> float:
    if type(value) not in (float, int):
        raise STACPreflightError(f"{label} must be a finite number")
    try:
        v = float(value)
    except (ValueError, OverflowError) as exc:
        raise STACPreflightError(f"{label} must be finite") from exc
    if not math.isfinite(v):
        raise STACPreflightError(f"{label} must be finite")
    return v


def preflight(item: Any) -> dict[str, Any]:
    """Check one source-native item and report only strict non-admission evidence."""
    if type(item) is not dict or not REQUIRED_KEYS <= set(item):
        raise STACPreflightError("STAC item lacks mandatory provider fields")
    if item["type"] != "Feature" or item["stac_version"] != "1.0.0":
        raise STACPreflightError("not a STAC 1.0.0 feature")
    tile_id = item["id"]
    if type(tile_id) is not str or not IDENTITY.fullmatch(tile_id):
        raise STACPreflightError("tile ID not in reviewed NOAA Michael naming family")
    bbox = item["bbox"]
    if type(bbox) is not list or len(bbox) != 4:
        raise STACPreflightError("bbox must be four WGS84 numbers")
    west, south, east, north = (_positive_number(v, "bbox") for v in bbox)
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise STACPreflightError("invalid bbox envelope")
    if not (-88.5 < west < -82.5 and -88.5 < east < -82.5 and 28.5 < south < 32 and 28.5 < north < 32):
        raise STACPreflightError("tile outside published NOAA Michael geographic envelope")
    geometry = item["geometry"]
    if type(geometry) is not dict or geometry.get("type") != "Polygon":
        raise STACPreflightError("expected polygon spatial tile metadata")
    if type(geometry.get("coordinates")) is not list:
        raise STACPreflightError("polygon coordinates absent")
    prop = item["properties"]
    if type(prop) is not dict:
        raise STACPreflightError("missing STAC temporal and rights properties")
    observed_day = _datetime(prop.get("datetime"), "properties.datetime")
    period_start = _datetime(prop.get("start_datetime"), "start_datetime")
    period_end = _datetime(prop.get("end_datetime"), "end_datetime")
    if (observed_day.date().isoformat() != tile_id[:4] + "-" + tile_id[4:6] + "-" + tile_id[6:8]
        or not (period_start <= observed_day <= period_end)
        or period_start.date().isoformat() != "2018-10-11"
        or period_end.date().isoformat() != "2018-10-14"):
        raise STACPreflightError("unverified acquisition date or source collection interval")
    if prop.get("license") != "NLPL":
        # Current STAC item says NLPL, InPort says CC0-1.0. This is a
        # *source contradiction*, never evidence for commercial admission.
        raise STACPreflightError("reviewed STAC item license value changed: verify provider")
    assets = item["assets"]
    if type(assets) is not dict or tile_id not in assets:
        raise STACPreflightError("tile image asset missing")
    asset = assets[tile_id]
    if type(asset) is not dict or asset.get("type") != "image/tiff" or asset.get("proj:epsg") != 4326:
        raise STACPreflightError("asset TIFF projection not as publicly inspected")
    url = asset.get("href")
    expected = STAC_ROOT + tile_id + ".tif"
    if type(url) is not str or url != expected:
        raise STACPreflightError("unreviewed asset origin, query or file path")
    parsed = urlsplit(url)
    if parsed.hostname != "coastalimagery.blob.core.windows.net" or parsed.query or parsed.fragment:
        raise STACPreflightError("unexpected asset access parameters")
    shape = asset.get("proj:shape")
    if (type(shape) is not list or len(shape) != 2
        or any(type(n) is not int or not 1 <= n <= 20000 for n in shape)
        or shape[0] * shape[1] > MAX_PIXELS):
        raise STACPreflightError("invalid bounded GeoTIFF raster dimensions")
    bands = asset.get("eo:bands")
    if (type(bands) is not list or len(bands) != 4
        or tuple(b.get("description") for b in bands if type(b) is dict) != BANDS):
        raise STACPreflightError("unexpected optical color and alpha channels")
    raster = asset.get("raster:bands")
    if (type(raster) is not list or len(raster) != 4
        or any(type(b) is not dict or b.get("data_type") != "uint8" for b in raster)):
        raise STACPreflightError("raster band metadata unverified")
    transform = asset.get("proj:transform")
    if type(transform) is not list or len(transform) != 6:
        raise STACPreflightError("missing affine raster reference")
    vals = [_positive_number(x, "proj:transform") for x in transform]
    if not (0 < vals[1] < 0.001 and -0.001 < vals[5] < 0
            and abs(vals[2]) < 1e-12 and abs(vals[4]) < 1e-12):
        raise STACPreflightError("unexpected affine grid scale/orientation")
    links = item["links"]
    if (type(links) is not list or not any(
        type(x) is dict and x.get("rel") == "self"
        and x.get("href") == STAC_ROOT + "stac/" + tile_id + ".json"
        for x in links
    )):
        raise STACPreflightError("official STAC item self-link missing")

    return {
        "profile": "noaa_michael_2018_stac_metadata_preflight_v0",
        "provider": "NOAA_NGS_DigitalCoast_8883",
        "tile_id": tile_id,
        "source_item_metadata_valid": True,
        "raster_dimensions": shape,
        "declared_crs": "EPSG:4326",
        "declared_acquisition_day": observed_day.date().isoformat(),
        "exact_capture_time_verified": False,
        "pixel_coverage_verified": False,
        "independent_of_fema_rs_labels_proven": False,
        "inport_dataset_license_claim": "CC0-1.0",
        "stac_item_license_claim": "NLPL",
        "source_license_conflict_unresolved": True,
        "source_image_bytes_downloaded_or_verified": False,
        "automatic_fema_building_join_allowed": False,
        "commercial_model_input_admitted": False,
    }
