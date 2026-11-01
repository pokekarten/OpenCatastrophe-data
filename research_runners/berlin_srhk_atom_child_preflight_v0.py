#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact official Berlin SRHK Atom child metadata only (zero ZIP requests).

The parent Atom root had exactly one alternate child, 0.atom, as separately
verified. This accepts one *fixed* HTTPS URL; never follows XML hrefs and
never fetches hazard ZIP, TIFF, imagery, buildings or insurer assets.
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
from urllib import request, error
from xml.etree import ElementTree as ET

SOURCE_URL = "https://gdi.berlin.de/data/ua_srhk/atom/0.atom"
ROOT_URL = "https://gdi.berlin.de/data/ua_srhk/atom/"
NS = "{http://www.w3.org/2005/Atom}"
PROFILE = "berlin-srhk-atom-five-exact-zip-link-metadata-v0"
MAX_BYTES = 65_536
TIMEOUT = 35
FILES = {
    "wasserstand_extrem2022.zip": "depth_extreme_scenario",
    "wasserstand_aussergewoehnliches_ereignis2022.zip": "depth_extraordinary_scenario",
    "fliessgeschw_extrem2022.zip": "velocity_extreme_scenario",
    "fliessgeschw_aussergewoehnliches_ereignis2022.zip": "velocity_extraordinary_scenario",
    "vulnerabilitaetsanalyse.zip": "separate_vulnerability_product",
}
OFFICIAL_TECHNICAL_PDF_EXPECTED_CRS = "EPSG:25832"
ATOM_ADVERTISED_CRS = "EPSG:25833"


class ChildFeedError(ValueError):
    """Failed closed on changed source identity, rights or Atom link semantics."""


def inspect(raw: bytes) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ChildFeedError("Atom child source missing or outside byte budget")
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise ChildFeedError("Atom DTD/entities are not permitted")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ChildFeedError("invalid Atom child XML") from exc
    if root.tag != NS + "feed":
        raise ChildFeedError("wrong Atom 1.0 feed root")
    entries = root.findall(NS + "entry")
    if len(entries) != 1:
        raise ChildFeedError("expected exactly one independently described dataset entry")
    entry = entries[0]
    root_self = [l.get("href") for l in root.findall(NS + "link")
                 if l.get("rel") == "self"]
    entry_self = entry.findtext(NS + "id")
    if root_self != [SOURCE_URL] or entry_self != SOURCE_URL:
        raise ChildFeedError("fixed Atom child identity mismatch")
    root_rights = root.findtext(NS + "rights") or ""
    entry_rights = entry.findtext(NS + "rights") or ""
    if not ("Namensnennung" in root_rights and
            "Namensnennung" in entry_rights and "BKG" in entry_rights):
        raise ChildFeedError("original BKG attribution/licensing text not retained")
    categories = entry.findall(NS + "category")
    if len(categories) != 1 or categories[0].get("term") != (
            "http://www.opengis.net/def/crs/EPSG/0/25833"):
        raise ChildFeedError("original Atom CRS declaration changed")
    titles = entry.findtext(NS + "title") or ""
    if ATOM_ADVERTISED_CRS not in titles:
        raise ChildFeedError("original Atom ZIP bundle CRS title changed")
    links = entry.findall(NS + "link")
    if len(links) != len(FILES):
        raise ChildFeedError("unexpected number of original ZIP references")
    found = {}
    for link in links:
        href = link.get("href")
        if link.get("rel") != "section" or link.get("type") != "image/tiff":
            raise ChildFeedError("unexpected original Atom ZIP link relation or label")
        if type(href) is not str or not href.startswith(ROOT_URL):
            raise ChildFeedError("unexpected ZIP object host or path")
        filename = href[len(ROOT_URL):]
        if filename not in FILES or href != ROOT_URL + filename or filename in found:
            raise ChildFeedError("unknown, duplicate or unsafe fixed ZIP object reference")
        if not link.get("title") or len(link.get("title")) > 180:
            raise ChildFeedError("missing or oversized ZIP object title")
        found[filename] = FILES[filename]
    if set(found) != set(FILES):
        raise ChildFeedError("required official raster and vulnerability products missing")
    return {
        "atom_1_0_child_validated": True,
        "original_atom_child_crs_label": ATOM_ADVERTISED_CRS,
        "official_2025_pdf_raster_crs_label": OFFICIAL_TECHNICAL_PDF_EXPECTED_CRS,
        "atom_pdf_crs_labels_conflict": True,
        "atom_entry_reports_raster_zip_links": len(found),
        "water_depth_zip_count": 2,
        "flow_speed_zip_count": 2,
        "separate_vulnerability_zip_count": 1,
        "source_zip_filenames_and_roles": [
            {"filename": n, "source_role": role} for n, role in sorted(found.items())
        ],
        "atom_links_labelled_image_tiff_but_urls_are_zip": True,
        "original_root_and_entry_require_bkg_attribution_review": True,
        "zip_urls_are_metadata_not_download_receipts": True,
        "provider_zip_bytes_requested": False,
        "real_water_depth_pixels_inspected": False,
        "true_geotiff_crs_and_units_verified": False,
        "building_hazard_overlap_admitted": False,
        "insurer_loss_estimates_generated": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ChildFeedError("official Atom child redirected")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(*, opener: Callable = _fetch,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict:
    req = request.Request(
        SOURCE_URL, method="GET", headers={"Accept": "application/atom+xml"}
    )
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 200 or resp.geturl() != SOURCE_URL:
                raise ChildFeedError("fixed Atom URL or HTTP status changed")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in ("application/atom+xml", "application/xml", "text/xml"):
                raise ChildFeedError("official Atom response media mismatch")
            raw = resp.read(MAX_BYTES + 1)
    except ChildFeedError:
        raise
    except (OSError, error.URLError, TimeoutError) as exc:
        raise ChildFeedError("single original child metadata GET failed") from exc
    inspected = inspect(raw)
    when = clock()
    if not isinstance(when, datetime) or when.tzinfo is None or when.utcoffset() is None:
        raise ChildFeedError("receipt clock requires timezone offset")
    return {
        "profile": PROFILE,
        "fixed_original_child_url": SOURCE_URL,
        "retrieved_utc": when.astimezone(timezone.utc).isoformat(),
        "original_xml_response_bytes": len(raw),
        "original_xml_sha256": sha256(raw).hexdigest(),
        "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_xml_not_persisted": True,
        "no_sourced_file_download": True,
        "no_new_rights_or_model_admission": True,
        **inspected,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("explicit --live required for fixed Atom child metadata only")
    try:
        print(json.dumps(probe(), ensure_ascii=False, sort_keys=True, allow_nan=False))
    except (ChildFeedError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
