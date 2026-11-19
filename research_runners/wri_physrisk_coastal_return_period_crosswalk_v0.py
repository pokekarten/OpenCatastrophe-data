#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline WRI original catalogue -> Physrisk derived-Zarr return-period crosswalk.

Input is exact saved WRI provider HTML and exact saved Physrisk .zattrs bytes.
Only source names and index metadata are examined, never a GeoTIFF or Zarr chunk.
The resulting report is NOT a model-input, licence, pixel or loss admission.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin

WRI_PAGE = "https://aqueduct.wridata.org/AqueductFloods20/index.html"
PHYSRISK_ATTRS_URL = (
    "https://os-climate-physical-risk.s3.amazonaws.com/"
    "hazard-indicators/hazard.zarr/inundation/wri/v2/"
    "inuncoast_historical_nosub_hist_0/.zattrs"
)
PROFILE = "wri-physrisk-coastal-return-period-crosswalk-v0"
REQUIRED_WRI_RP = ("1.5", "2", "5", "10", "25", "50", "100", "250", "500", "1000")
REQUIRED_PHYSRISK_RP = (2, 5, 10, 25, 50, 100, 250, 500, 1000)
FILE_RE = re.compile(r"inuncoast_historical_nosub_hist_rp([0-9]{4})_([0-9])\.tif\Z")
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
MAX_HTML = 100_000
MAX_ATTRS = 4096


class SourceMismatch(ValueError):
    """Original provider identity, exact metadata or semantic contract mismatch."""


def _unique_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise SourceMismatch("duplicate Physrisk JSON attribute: " + key)
        obj[key] = value
    return obj


def _reject_nonfinite(value):
    raise SourceMismatch("non-finite Physrisk JSON: " + value)


def _original(blob: bytes, expected_sha256: str, limit: int, label: str) -> str:
    if not isinstance(expected_sha256, str) or not SHA_RE.fullmatch(expected_sha256):
        raise SourceMismatch(label + ": independently supplied SHA-256 required")
    if type(blob) is not bytes or not 0 < len(blob) <= limit:
        raise SourceMismatch(label + ": original bytes missing/over bounded cap")
    if hashlib.sha256(blob).hexdigest() != expected_sha256:
        raise SourceMismatch(label + ": original SHA-256 mismatch")
    try:
        return blob.decode("utf-8")
    except UnicodeError as exc:
        raise SourceMismatch(label + ": invalid UTF-8") from exc


class _WRIAnchorCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.files = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        hrefs = [val for key, val in attrs if key == "href"]
        if len(hrefs) > 1:
            raise SourceMismatch("duplicate HTML href attribute")
        if hrefs and hrefs[0] and FILE_RE.fullmatch(hrefs[0]):
            self.files.append(hrefs[0])


def inspect_crosswalk(wri_html: bytes, physrisk_zattrs: bytes,
                      wri_sha256: str, zattrs_sha256: str) -> dict:
    html = _original(wri_html, wri_sha256, MAX_HTML, "WRI provider index")
    raw = _original(physrisk_zattrs, zattrs_sha256, MAX_ATTRS, "Physrisk zattrs")
    if ("Aqueduct Floods Hazard Maps Version 2" not in html
            or "October 20, 2020" not in html):
        raise SourceMismatch("unexpected WRI product/release description")
    anchors = _WRIAnchorCollector()
    anchors.feed(html)
    anchors.close()
    observed = anchors.files
    if len(observed) != len(set(observed)):
        raise SourceMismatch("duplicate WRI source file link")
    expected_file_by_rp = {
        rp: "inuncoast_historical_nosub_hist_rp"
        + str(int(float(rp))).zfill(4) + "_" + (rp.split(".")[1] if "." in rp else "0") + ".tif"
        for rp in REQUIRED_WRI_RP
    }
    if set(observed) != set(expected_file_by_rp.values()):
        raise SourceMismatch("WRI original coastal historical no-subsidence listing incomplete or changed")
    try:
        attrs = json.loads(raw, object_pairs_hook=_unique_keys,
                           parse_constant=_reject_nonfinite)
    except json.JSONDecodeError as exc:
        raise SourceMismatch("invalid Physrisk attributes JSON") from exc
    if type(attrs) is not dict or attrs.get("index_name") != "return period (years)":
        raise SourceMismatch("Physrisk did not declare return-period index")
    idx = attrs.get("index_values")
    if type(idx) is not list or any(type(x) is not int for x in idx):
        raise SourceMismatch("noninteger or missing Physrisk return-period index")
    if tuple(idx) != REQUIRED_PHYSRISK_RP:
        raise SourceMismatch("Physrisk index changed or return periods were silently added/removed")
    source_only = tuple(rp for rp in REQUIRED_WRI_RP if rp not in {str(x) for x in idx})
    if source_only != ("1.5",):
        raise SourceMismatch("unexpected exact WRI/Physrisk return-period difference")
    return {
        "profile": PROFILE,
        "wri_original_index": WRI_PAGE,
        "wri_index_sha256": wri_sha256,
        "physrisk_derived_zattrs": PHYSRISK_ATTRS_URL,
        "physrisk_zattrs_sha256": zattrs_sha256,
        "wri_return_period_years": list(REQUIRED_WRI_RP),
        "physrisk_return_period_years": list(idx),
        "wri_only_return_period_years": list(source_only),
        "matching_provider_file_urls": [
            urljoin(WRI_PAGE, expected_file_by_rp[str(year)])
            for year in idx
        ],
        "wri_geotiffs_downloaded": False,
        "physrisk_zarr_chunks_read": False,
        "original_geotiff_pixel_comparison_completed": False,
        "return_period_maps_are_event_occurrences": False,
        "insured_loss_inferred": False,
        "rights_and_scientific_review_complete": False,
        "model_input_admitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wri_index_html", type=Path)
    parser.add_argument("physrisk_zattrs_json", type=Path)
    parser.add_argument("--expected-wri-sha256", required=True)
    parser.add_argument("--expected-zattrs-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    src_paths = {args.wri_index_html.resolve(), args.physrisk_zattrs_json.resolve()}
    if len(src_paths) != 2 or args.out.resolve() in src_paths:
        parser.error("original inputs must be distinct; output cannot overwrite source bytes")
    try:
        result = inspect_crosswalk(
            args.wri_index_html.read_bytes(), args.physrisk_zattrs_json.read_bytes(),
            args.expected_wri_sha256, args.expected_zattrs_sha256,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, SourceMismatch) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
