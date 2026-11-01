#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, read-only official Berlin pluvial flood WFS service metadata proof.

There are TWO source products, not interchangeable event/damage data:
- Berlin 2025 Starkregenhinweiskarte (SRHK) derives some layers from BKG.
- Berlin locally modelled Starkregengefahrenkarte (SRGK) covers subsets.
This ONLY downloads one XML GetCapabilities per explicitly selected product.
No WFS features, raster pixels, modelling, hazard values or database writes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import ssl
import sys
from typing import Callable
from urllib import error, request
from xml.etree import ElementTree

SOURCES = {
    "hinweiskarte": {
        "url": "https://gdi.berlin.de/services/wfs/ua_srhk?request=GetCapabilities&service=WFS",
        "catalogue": "https://daten.berlin.de/datensaetze/starkregenhinweiskarte-wfs-882d18d8",
        "source_id": "de.berlin.starkregenhinweiskarte.2025.wfs",
        "published_licence_label": "dl-de-by-2.0",
        "scientific_scope": "BKG-based broad hazard indication; not observed flood or depth samples",
    },
    "gefahrenkarte": {
        "url": "https://gdi.berlin.de/services/wfs/ua_srgk?request=GetCapabilities&service=WFS",
        "catalogue": "https://daten.berlin.de/datensaetze/starkregengefahrenkarte-wfs-1aa4f1ef",
        "source_id": "de.berlin.starkregengefahrenkarte.2026.wfs",
        "published_licence_label": "cc-by-4.0",
        "scientific_scope": "Detailed 1D sewer/2D surface pluvial simulations; partial Berlin coverage",
    },
}
MAX_BYTES = 2_097_152
TIMEOUT = 35
MAX_LAYERS = 120
PROFILE = "berlin-pluvial-wfs-exact-capabilities-canary-v0"


class StarkregenError(ValueError):
    """Unreviewed service, malformed XML or unsafe metadata response."""


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def inspect(raw: bytes, source: str) -> dict:
    """Bounded parser of public WFS names/CRS; never interpret hazard values."""
    if source not in SOURCES:
        raise StarkregenError("not an allowlisted flood source")
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise StarkregenError("empty or oversized WFS metadata")
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise StarkregenError("DTD and entities are forbidden")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        raise StarkregenError("malformed WFS XML") from exc
    if _local(root.tag) != "WFS_Capabilities" or root.get("version") != "2.0.0":
        raise StarkregenError("unexpected WFS root or protocol version")
    lists = [e for e in root.iter() if _local(e.tag) == "FeatureTypeList"]
    if len(lists) != 1:
        raise StarkregenError("missing or duplicated feature catalogue")
    names, features = set(), []
    for item in lists[0]:
        if _local(item.tag) != "FeatureType":
            continue
        n = [e.text.strip() for e in item
             if _local(e.tag) == "Name" and type(e.text) is str and e.text.strip()]
        if len(n) != 1 or not 0 < len(n[0]) <= 180 or n[0] in names:
            raise StarkregenError("missing/duplicate/oversized feature type")
        name = n[0]
        names.add(name)
        crs = sorted({e.text.strip() for e in item
                      if _local(e.tag) in ("DefaultCRS", "OtherCRS", "DefaultSRS", "OtherSRS", "SRS")
                      and type(e.text) is str and e.text.strip()})
        if not crs or len(crs) > 64 or any(len(v) > 180 for v in crs):
            raise StarkregenError("unverified feature coordinate reference system")
        features.append({"name": name, "advertised_crs": crs})
        if len(features) > MAX_LAYERS:
            raise StarkregenError("unbounded flood-service feature catalogue")
    if not features:
        raise StarkregenError("WFS has no downloadable feature types")
    return {
        "wfs_version": "2.0.0",
        "advertised_feature_types": features,
        "advertised_feature_count": len(features),
        "epsg25832_advertised": any(
            any("25832" in crs for crs in row["advertised_crs"]) for row in features
        ),
        "epsg25833_advertised": any(
            any("25833" in crs for crs in row["advertised_crs"]) for row in features
        ),
        "feature_catalogue_only": True,
        "wfs_service_not_geo_tiff_raster": True,
        "actual_water_depth_values_retrieved": False,
        "actual_depth_units_verified": False,
        "rasters_or_atom_feeds_downloaded": False,
        "specific_berlin_bld4_box_coverage_verified": False,
        "scientific_model_input_approved": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise StarkregenError("fixed official WFS metadata redirected")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(source: str, *, opener: Callable = _fetch,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict:
    if source not in SOURCES:
        raise StarkregenError("source is not allowlisted")
    config = SOURCES[source]
    req = request.Request(config["url"], method="GET",
                          headers={"Accept": "application/xml, text/xml;q=0.9"})
    try:
        with opener(req, TIMEOUT) as response:
            if response.status != 200 or response.geturl() != config["url"]:
                raise StarkregenError("unexpected service status or URL")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in ("application/xml", "text/xml", "application/vnd.ogc.wfs_xml"):
                raise StarkregenError("WFS metadata returned wrong media type")
            raw = response.read(MAX_BYTES + 1)
    except StarkregenError:
        raise
    except (error.URLError, OSError, TimeoutError) as exc:
        raise StarkregenError("exact source WFS GetCapabilities failed") from exc
    meta = inspect(raw, source)
    now = clock()
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise StarkregenError("metadata receipt clock must have UTC offset")
    return {
        "profile": PROFILE,
        "source_product": source,
        "source_id": config["source_id"],
        "catalogue": config["catalogue"],
        "exact_request_url": config["url"],
        "catalogue_published_licence_label_only": config["published_licence_label"],
        "scientific_scope": config["scientific_scope"],
        "retrieved_utc": now.astimezone(timezone.utc).isoformat(),
        "original_response_byte_count": len(raw),
        "original_response_sha256": sha256(raw).hexdigest(),
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_xml_bytes_persisted": False,
        "provider_redistribution_authorized_by_this_probe": False,
        "automated_feature_acquisition_authorized_by_this_probe": False,
        **meta,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", choices=sorted(SOURCES), required=True)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("explicit --live is required; offline tests are the default")
    try:
        print(json.dumps(probe(args.source), ensure_ascii=False, sort_keys=True, allow_nan=False))
    except (StarkregenError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
