#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed original Berlin detailed SRGK Atom root metadata request only.

No follow-up child, ZIP/TIFF download, source bytes persistence, geometry,
building exposure or hazard/loss claim. Original root may not list raster URLs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import ssl
import sys
from urllib import error, parse, request
from xml.etree import ElementTree

URL = "https://gdi.berlin.de/data/ua_srgk/atom/"
PROFILE = "berlin-detailed-srgk-depth-atom-root-bounded-v0"
CATALOGUE = "https://daten.berlin.de/datensaetze/starkregengefahrenkarte-wfs-1aa4f1ef"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
MAX_BYTES = 262_144
MAX_LINKS = 500
MAX_ENTRIES = 100
TIMEOUT = 35


class DetailedAtomBlocked(ValueError):
    """Exact source feed or metadata shape not independently confirmed."""


def inspect(raw: bytes) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise DetailedAtomBlocked("empty or oversized official detailed Atom root")
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise DetailedAtomBlocked("DTD/ENTITY forbidden in public source feed")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        raise DetailedAtomBlocked("source not parseable as Atom XML") from exc
    if root.tag != ATOM_NS + "feed":
        raise DetailedAtomBlocked("not official Atom 1.0 feed root")
    entries = [e for e in root if e.tag == ATOM_NS+"entry"]
    links = [e for e in root.iter() if e.tag == ATOM_NS+"link"]
    if len(entries) > MAX_ENTRIES or not 0 < len(links) <= MAX_LINKS:
        raise DetailedAtomBlocked("missing or unbounded feed links/entries")
    media_counts, rel_counts = Counter(), Counter()
    zip_links = 0
    same_provider_links = 0
    for link in links:
        href, rel, media = link.get("href"), link.get("rel","alternate"), link.get("type","unspecified")
        if (not isinstance(href,str) or not 0 < len(href) <= 2048 or
            not isinstance(rel,str) or not 0 < len(rel) <= 100 or
            not isinstance(media,str) or not 0 < len(media) <= 120):
            raise DetailedAtomBlocked("invalid or oversized Atom link property")
        split = parse.urlsplit(href)
        if split.scheme not in ("", "https") or (split.netloc and split.hostname != "gdi.berlin.de"):
            # External links such as schema/attribution references may appear,
            # but are NOT followed or admitted. Keep aggregate counts.
            pass
        else:
            same_provider_links += 1
        if split.path.lower().endswith(".zip"):
            zip_links += 1
        rel_counts[rel] += 1
        media_counts[media.lower()] += 1
    return {
        "profile": PROFILE,
        "atom_v1_root_confirmed": True,
        "original_root_entries": len(entries),
        "original_root_link_count": len(links),
        "original_root_link_rel_counts": dict(sorted(rel_counts.items())),
        "original_root_link_media_counts": dict(sorted(media_counts.items())),
        "same_provider_or_relative_link_count": same_provider_links,
        "direct_root_zip_href_count": zip_links,
        "child_atom_feeds_or_zip_links_not_followed": True,
        "real_depth_tiff_or_water_units_retrieved": False,
        "model_area_to_raster_coverage_join_verified": False,
        "source_licence_for_each_raster_verified": False,
        "insurance_cat_input_admitted": False,
        "raw_atom_payload_persisted": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DetailedAtomBlocked("source Atom root redirected")


def _opener(req, timeout):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(*, opener=_opener, clock=lambda: datetime.now(timezone.utc)) -> dict:
    req = request.Request(URL, method="GET",
                          headers={"Accept":"application/atom+xml, application/xml;q=0.9",
                                   "Accept-Encoding":"identity"})
    try:
        with opener(req,TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != URL:
                raise DetailedAtomBlocked("source URL/status mismatch")
            media = resp.headers.get("Content-Type","").split(";",1)[0].lower().strip()
            if media not in ("application/atom+xml","application/xml","text/xml"):
                raise DetailedAtomBlocked("unexpected original Atom media type")
            if resp.headers.get("Content-Encoding","identity").lower() != "identity":
                raise DetailedAtomBlocked("unreviewed Atom encoding")
            raw=resp.read(MAX_BYTES+1)
    except DetailedAtomBlocked:
        raise
    except (error.URLError,OSError,TimeoutError) as exc:
        raise DetailedAtomBlocked("official source Atom root unreachable") from exc
    data=inspect(raw)
    now=clock()
    if not isinstance(now,datetime) or now.utcoffset() is None:
        raise DetailedAtomBlocked("original source timestamp not timezone aware")
    return {
        **data,
        "source_official_catalogue": CATALOGUE,
        "exact_original_source_url": URL,
        "original_xml_sha256": sha256(raw).hexdigest(),
        "original_xml_byte_count": len(raw),
        "retrieved_utc": now.astimezone(timezone.utc).isoformat(),
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "provider_source_gets": 1,
    }


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true")
    args=p.parse_args(argv)
    if not args.live:
        p.error("explicit --live required for one exact public metadata query")
    try:
        print(json.dumps(probe(),sort_keys=True,allow_nan=False))
    except (DetailedAtomBlocked,ValueError,OSError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())
