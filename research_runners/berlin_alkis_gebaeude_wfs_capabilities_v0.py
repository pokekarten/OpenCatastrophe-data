#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed official Berlin ALKIS building WFS GetCapabilities receipt.

The reviewed operation discovers layer names and supported coordinate systems
only. No GetFeature, building geometry, addresses, owner data or database write.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from typing import Any, Callable
from urllib import request, error
from xml.etree import ElementTree

URL = "https://gdi.berlin.de/services/wfs/alkis_gebaeude?request=GetCapabilities&service=WFS"
MAX_BYTES = 4_194_304
MAX_LAYER_NAMES = 120
TIMEOUT = 35
PROVIDER_PAGE = "https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a"
ORIGINAL_RIGHTS = "Datenlizenz Deutschland – Zero – Version 2.0"
PROFILE = "oc-berlin-alkis-gebaeude-official-wfs-capabilities-v0"


class BerlinWfsError(ValueError):
    """Unverified WFS protocol, unexpected response or source identity."""


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def inspect_capabilities(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise BerlinWfsError("empty or oversized official capabilities XML")
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise BerlinWfsError("external or internal DTD/ENTITY is forbidden")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        raise BerlinWfsError("malformed WFS capabilities XML") from exc
    if _local(root.tag) != "WFS_Capabilities":
        raise BerlinWfsError("official WFS capabilities root missing")
    version = root.get("version")
    if version not in ("1.0.0", "1.1.0", "2.0.0"):
        raise BerlinWfsError("unreviewed WFS protocol version")
    feature_lists = [e for e in root.iter() if _local(e.tag) == "FeatureTypeList"]
    if len(feature_lists) != 1:
        raise BerlinWfsError("expected one WFS FeatureTypeList")
    layers = []
    names = set()
    for el in feature_lists[0]:
        if _local(el.tag) != "FeatureType":
            continue
        n = [x.text.strip() for x in el if _local(x.tag) == "Name"
             and isinstance(x.text, str) and x.text.strip()]
        if len(n) != 1:
            raise BerlinWfsError("invalid feature type name")
        name = n[0]
        if len(name) > 180 or name in names:
            raise BerlinWfsError("duplicate or unexpectedly long feature name")
        names.add(name)
        crs = sorted({
            x.text.strip() for x in el
            if _local(x.tag) in ("DefaultCRS", "OtherCRS", "DefaultSRS", "OtherSRS", "SRS")
            and isinstance(x.text, str) and x.text.strip()
        })
        if len(crs) > 64 or any(len(x) > 180 for x in crs):
            raise BerlinWfsError("unbounded provider CRS declaration")
        layers.append({"name": name, "advertised_crs": crs})
        if len(layers) > MAX_LAYER_NAMES:
            raise BerlinWfsError("unexpectedly large feature-type catalogue")
    if not layers:
        raise BerlinWfsError("WFS advertises no feature types")

    def building_layer(layer: dict) -> bool:
        name = layer["name"].casefold()
        return "gebaeude" in name or "gebäude" in name or "building" in name

    building = [x for x in layers if building_layer(x)]
    # Fail closed: the specific official building WFS must expose at least
    # one building layer; a generic WFS root isn't adequate evidence.
    if not building:
        raise BerlinWfsError("no building feature type on official ALKIS WFS")
    # Names of feature-type layers are open service metadata, not building IDs.
    return {
        "wfs_version": version,
        "advertised_feature_type_count": len(layers),
        "candidate_building_feature_types": building,
        "building_feature_type_count": len(building),
        "other_feature_type_count": len(layers) - len(building),
        "feature_type_names_are_public_service_metadata": True,
        "source_geometry_or_owner_data_obtained": False,
        "provider_data_imported": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BerlinWfsError("provider redirected a fixed official request")


def _https_get(req: request.Request, timeout: int):
    opener = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(req, timeout=timeout)


def retrieve_capabilities(
    *, opener: Callable[[request.Request, int], Any] = _https_get,
    utc_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    req = request.Request(
        URL, method="GET",
        headers={"Accept": "application/xml, text/xml;q=0.9"},
    )
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.geturl() != URL or resp.status != 200:
                raise BerlinWfsError("WFS host, URL or status changed")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if media not in ("application/xml", "text/xml", "application/vnd.ogc.wfs_xml"):
                raise BerlinWfsError("unexpected official WFS response content type")
            raw = resp.read(MAX_BYTES + 1)
    except BerlinWfsError:
        raise
    except (error.URLError, OSError, TimeoutError) as exc:
        raise BerlinWfsError("official Berlin WFS metadata could not be retrieved") from exc
    metadata = inspect_capabilities(raw)
    dt = utc_clock()
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise BerlinWfsError("receipt clock must be timezone-aware")
    return {
        "profile": PROFILE,
        "source_title": "ALKIS Berlin Gebäude (WFS)",
        "publisher": "Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin",
        "publisher_catalogue_url": PROVIDER_PAGE,
        "catalogue_rights_label": ORIGINAL_RIGHTS,
        "request_url": URL,
        "retrieved_at_utc": dt.astimezone(timezone.utc).isoformat(),
        "response_bytes": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "raw_xml_persisted": False,
        "buildings_sampled": False,
        "model_input_admitted": False,
        **metadata,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true",
                   help="explicitly request one fixed, official WFS GetCapabilities")
    a = p.parse_args(argv)
    if not a.live:
        p.error("offline by default; pass --live to perform the single metadata request")
    try:
        print(json.dumps(retrieve_capabilities(), indent=2, sort_keys=True, allow_nan=False))
    except (BerlinWfsError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
