#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-locked Berlin detailed SRGK Atom child and three ZIP HEAD proofs.

GET the pinned root and exact child *metadata only*. HEAD the three
officially published scenario ZIPs; NEVER GET ZIP/TIFF bytes, dereference
unreviewed links, assign depth units, or import CAT/insurance inputs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import ssl
import sys
from urllib import error, request
from xml.etree import ElementTree as ET

ROOT_URL = "https://gdi.berlin.de/data/ua_srgk/atom/"
ROOT_SHA256 = "471becbd22ba5a862133ce0d59ed32981ccd30e44e3c7650b95d745d2c9d5eb4"
CHILD_URL = "https://gdi.berlin.de/data/ua_srgk/atom/0.atom"
ATOM = "{http://www.w3.org/2005/Atom}"
ZIP_PATHS = (
    ("selten", "wasserstand_seltenes_ereignis.zip"),
    ("aussergewoehnlich", "wasserstand_aussergewoehnliches_ereignis.zip"),
    ("extrem", "wasserstand_extrem.zip"),
)
ZIP_URLS = tuple("https://gdi.berlin.de/data/ua_srgk/atom/" + p for _, p in ZIP_PATHS)
PROFILE = "berlin-srgk-detailed-child-scenarios-head-metadata-v0"
ROOT_MAX_BYTES = 16_384
CHILD_MAX_BYTES = 32_768
TIMEOUT = 35


class AtomScenarioBlocked(ValueError):
    """A required original provider feed identity, structure or rights gate failed."""


def _xml(raw: bytes, cap: int) -> ET.Element:
    if type(raw) is not bytes or not 0 < len(raw) <= cap:
        raise AtomScenarioBlocked("empty or oversized provider Atom metadata")
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise AtomScenarioBlocked("original Atom DTD or entity forbidden")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AtomScenarioBlocked("invalid original Atom XML") from exc
    if root.tag != ATOM + "feed":
        raise AtomScenarioBlocked("source not official Atom 1.0 feed")
    return root


def _links(parent: ET.Element) -> list[dict]:
    links = [elem for elem in parent if elem.tag == ATOM + "link"]
    if len(links) > 16:
        raise AtomScenarioBlocked("unexpected link inventory size")
    result = []
    for e in links:
        href, rel, media = e.get("href"), e.get("rel"), e.get("type")
        if any(not isinstance(v, str) or not 0 < len(v) <= 2048 for v in (href, rel, media)):
            raise AtomScenarioBlocked("untrusted Atom link attributes")
        result.append({"href": href, "rel": rel, "media": media})
    return result


def inspect_root(raw: bytes) -> dict:
    if sha256(raw).hexdigest() != ROOT_SHA256:
        raise AtomScenarioBlocked("previously reviewed root source SHA-256 changed")
    root = _xml(raw, ROOT_MAX_BYTES)
    entries = root.findall(ATOM + "entry")
    if len(entries) != 1:
        raise AtomScenarioBlocked("root expected exactly one official dataset entry")
    links = _links(entries[0])
    alternate = [l for l in links if l["rel"] == "alternate"
                 and l["media"] == "application/atom+xml"]
    if len(alternate) != 1 or alternate[0]["href"] != CHILD_URL:
        raise AtomScenarioBlocked("root no longer points uniquely to pinned child")
    return {"root_sha256": ROOT_SHA256, "root_child_identity_verified": True}


def inspect_child(raw: bytes) -> dict:
    root = _xml(raw, CHILD_MAX_BYTES)
    entries = root.findall(ATOM+"entry")
    if len(entries) != 1:
        raise AtomScenarioBlocked("child Atom does not contain one scenario manifest entry")
    if root.findtext(ATOM+"id") != CHILD_URL or entries[0].findtext(ATOM+"id") != CHILD_URL:
        raise AtomScenarioBlocked("child Atom ID mismatch")
    links = _links(entries[0])
    sections = [l for l in links if l["rel"] == "section"]
    by_href = {l["href"]: l for l in sections}
    if len(sections) != 3 or set(by_href) != set(ZIP_URLS):
        raise AtomScenarioBlocked("scenario ZIP URL identity or number drift")
    for link in sections:
        if link["media"] != "image/tiff":
            raise AtomScenarioBlocked("provider-declared scenario link media drift")
    rights = " ".join((root.findtext(ATOM+"rights") or "",
                       entries[0].findtext(ATOM+"rights") or ""))
    if ("Zero - Version 2.0" not in rights
            or "CC-BY-4.0" not in rights
            or "Moabit" not in rights
            or "Flughafensee" not in rights):
        raise AtomScenarioBlocked("published mixed rights or geography notice changed")
    text = (entries[0].findtext(ATOM+"content") or "")
    if ("nicht für alle Modellgebiete" not in text
            or "ZIP-Dateien" not in text):
        raise AtomScenarioBlocked("published scenario availability caveat changed")
    return {
        "child_original_sha256": sha256(raw).hexdigest(),
        "child_original_bytes": len(raw),
        "official_scenarios": [
            {"scenario": name, "exact_zip_url": url,
             "published_link_media": "image/tiff", "link_points_to_zip": True,
             "zip_body_retrieved": False, "site_raster_coverage_verified": False}
            for (name, _), url in zip(ZIP_PATHS, ZIP_URLS)
        ],
        "scenario_count": 3,
        "extreme_scenario_not_for_all_model_areas": True,
        "catalogue_mixed_rights_research_only": True,
        "rights_areas_require_per_product_attribution_review": True,
        "specific_zip_redistribution_approved": False,
        "source_raster_crs_depth_units_nodata_verified": False,
        "insurance_cat_model_input_admitted": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AtomScenarioBlocked("exact official URL redirected")


def _open(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def _get_atom(url: str, opener) -> bytes:
    if url not in (ROOT_URL, CHILD_URL):
        raise AtomScenarioBlocked("unknown or unapproved Atom feed URL")
    cap = ROOT_MAX_BYTES if url == ROOT_URL else CHILD_MAX_BYTES
    req = request.Request(url, method="GET",
                          headers={"Accept": "application/atom+xml",
                                   "Accept-Encoding": "identity"})
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != url:
                raise AtomScenarioBlocked("original source URL/status drift")
            ct = resp.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if ct not in ("application/atom+xml", "application/xml", "text/xml"):
                raise AtomScenarioBlocked("source did not return Atom metadata")
            if resp.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise AtomScenarioBlocked("unsupported original source compression")
            return resp.read(cap + 1)
    except AtomScenarioBlocked:
        raise
    except (OSError, error.URLError, TimeoutError) as exc:
        raise AtomScenarioBlocked("official Atom source unavailable") from exc


def _head_zip(url: str, opener) -> dict:
    if url not in ZIP_URLS:
        raise AtomScenarioBlocked("unapproved ZIP HEAD URL")
    req = request.Request(url, method="HEAD",
                          headers={"Accept-Encoding": "identity"})
    # A HEAD failure does not prove a ZIP is missing: document uncertainty.
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != url:
                return {"head_status": "UNVERIFIED_HTTP_STATUS",
                        "length_bytes": None, "http_status": resp.status}
            size = resp.headers.get("Content-Length")
            if size is not None and (not size.isascii() or not size.isdecimal()
                                     or len(size) > 15 or int(size) == 0):
                return {"head_status": "UNVERIFIED_CONTENT_LENGTH",
                        "length_bytes": None, "http_status": 200}
            return {
                "head_status": "METADATA_HEADERS_RETURNED",
                "http_status": 200,
                "length_bytes": int(size) if size is not None else None,
                "declared_http_media_type": resp.headers.get("Content-Type", "")[:100],
                "zip_bytes_downloaded": False,
                "zip_content_or_checksum_verified": False,
            }
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        code = exc.code if isinstance(exc, error.HTTPError) else None
        return {"head_status": "UNVERIFIED_HEAD_REQUEST",
                "http_status": code, "length_bytes": None,
                "zip_bytes_downloaded": False,
                "zip_content_or_checksum_verified": False}


def probe(*, opener=_open, clock=lambda: datetime.now(timezone.utc)) -> dict:
    root_raw = _get_atom(ROOT_URL, opener)
    root = inspect_root(root_raw)
    child_raw = _get_atom(CHILD_URL, opener)
    child = inspect_child(child_raw)
    heads = {url: _head_zip(url, opener) for url in ZIP_URLS}
    for scenario in child["official_scenarios"]:
        scenario.update(heads[scenario["exact_zip_url"]])
    now = clock()
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise AtomScenarioBlocked("source clock not timezone-aware")
    return {
        "profile": PROFILE,
        "source_root_url": ROOT_URL,
        "source_child_url": CHILD_URL,
        "retrieval_utc": now.astimezone(timezone.utc).isoformat(),
        "original_root_bytes": len(root_raw),
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_source_feed_get_requests": 2,
        "official_source_zip_head_requests": 3,
        "source_zip_get_requests": 0,
        "original_atom_xml_or_zip_bytes_persisted": False,
        "model_area_verified_second_pilot_epsg25833": [391860,5816840,392060,5817040],
        "this_probe_does_not_check_zip_spatial_coverage": True,
        **root, **child,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("explicit --live required for fixed 2 Atom GET + 3 ZIP HEAD")
    try:
        print(json.dumps(probe(), ensure_ascii=False, sort_keys=True, allow_nan=False))
    except (AtomScenarioBlocked, ValueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
