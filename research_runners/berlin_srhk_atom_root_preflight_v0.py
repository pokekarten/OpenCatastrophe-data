#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One bounded Berlin SRHK Atom ROOT-feed metadata request, with NO followups.

The official SRHK 2025 documentation says raster depth/velocity ZIPs are
exposed through an Atom feed. This script proves ONLY whether the exact
root endpoint is a valid Atom XML feed and counts its public links.
It does not download ZIPs, TIFFs, pixels, events or buildings.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from typing import Callable
from urllib import error, request, parse
from xml.etree import ElementTree

URL = "https://gdi.berlin.de/data/ua_srhk/atom/"
CATALOGUE = "https://daten.berlin.de/datensaetze/starkregenhinweiskarte-wfs-882d18d8"
DOCUMENTATION = "https://gdi.berlin.de/data/ua_srhk/docs/Datenformatbeschreibung_SRHK_2025.pdf"
PROFILE = "berlin-srhk-2025-atom-root-one-request-v0"
ATOM_NS = "http://www.w3.org/2005/Atom"
MAX_BYTES = 1_048_576
MAX_ENTRIES = 300
MAX_LINKS = 500
TIMEOUT = 35


class AtomSourceError(ValueError):
    """The fixed provider Atom root was not safely verified."""


def _tag(e):
    return e.tag.rsplit("}", 1)[-1]


def inspect(raw: bytes) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise AtomSourceError("missing or oversized Atom XML")
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise AtomSourceError("DTD or entities are not allowed")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        raise AtomSourceError("malformed Atom XML") from exc
    if root.tag != "{" + ATOM_NS + "}feed":
        raise AtomSourceError("official Atom root is not an Atom 1.0 feed")
    entries = [e for e in root if e.tag == "{" + ATOM_NS + "}entry"]
    if len(entries) > MAX_ENTRIES:
        raise AtomSourceError("Atom entry limit exceeded")
    links = [e for e in root.iter() if e.tag == "{" + ATOM_NS + "}link"]
    if len(links) > MAX_LINKS:
        raise AtomSourceError("Atom link limit exceeded")
    rels = Counter()
    mime_types = Counter()
    zip_refs = 0
    for link in links:
        href = link.get("href", "")
        if not isinstance(href, str) or not 0 < len(href) <= 2048:
            raise AtomSourceError("invalid Atom link")
        # Links are only counted. No link is followed, never use a
        # content-provided URL to fetch anything.
        rel = link.get("rel", "alternate")
        media = link.get("type", "unspecified")
        if not 0 < len(rel) <= 120 or not 0 < len(media) <= 120:
            raise AtomSourceError("invalid Atom link metadata")
        rels[rel] += 1
        mime_types[media] += 1
        if parse.urlsplit(href).path.lower().endswith(".zip"):
            zip_refs += 1
    return {
        "root_is_atom_1_0": True,
        "root_entries": len(entries),
        "root_links": len(links),
        "link_rel_counts": dict(sorted(rels.items())),
        "link_media_type_counts": dict(sorted(mime_types.items())),
        "direct_zip_href_count": zip_refs,
        "links_not_followed": True,
        "child_feeds_not_fetched": True,
        "zip_or_geotiff_bytes_retrieved": False,
        "depth_pixel_units_or_values_verified": False,
        "approved_as_real_hazard_model_input": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AtomSourceError("original fixed Atom endpoint redirected")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(*, opener: Callable = _fetch,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict:
    req = request.Request(URL, method="GET",
                          headers={"Accept": "application/atom+xml, application/xml;q=0.9"})
    try:
        with opener(req, TIMEOUT) as response:
            if response.status != 200 or response.geturl() != URL:
                raise AtomSourceError("fixed Atom endpoint URL or HTTP status changed")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in ("application/atom+xml", "application/xml", "text/xml"):
                raise AtomSourceError("unexpected Atom response media type")
            raw = response.read(MAX_BYTES + 1)
    except AtomSourceError:
        raise
    except (error.URLError, OSError, TimeoutError) as exc:
        raise AtomSourceError("official Atom root read failed") from exc
    result = inspect(raw)
    dt = clock()
    if not isinstance(dt, datetime) or dt.tzinfo is None or dt.utcoffset() is None:
        raise AtomSourceError("receipt clock must have UTC offset")
    return {
        "profile": PROFILE,
        "source_product": "Berlin Starkregenhinweiskarte 2025 - Atom metadata root",
        "catalogue": CATALOGUE,
        "documentation": DOCUMENTATION,
        "exact_url": URL,
        "utc": dt.astimezone(timezone.utc).isoformat(),
        "original_atom_xml_size": len(raw),
        "original_atom_xml_sha256": hashlib.sha256(raw).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "raw_original_xml_persisted": False,
        "original_licence_scope_not_changed": True,
        **result,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("explicit --live required for a single fixed metadata GET")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (AtomSourceError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
