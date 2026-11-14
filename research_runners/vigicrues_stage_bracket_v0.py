#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Metadata-only stage bracket review; no provider fetch or model admission.

The input is candidate metadata, not authenticated original provider bytes.
Only official_pdf_metadata counts as a currently documented PDF scenario.
historical_report_only is a research lead, never a verified ZIP/ZICH asset.
No stage match permits depth interpolation, loss, or insured exposure inference.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


class StageReviewError(ValueError):
    """Bad/ambiguous research input; do not infer a scenario."""


_ALLOWED_EVIDENCE = {"official_pdf_metadata", "historical_report_only"}
_ALLOWED_PRODUCTS = {"ZIP", "ZICH"}
_STATION_RE = re.compile(r"^[A-Z][0-9]{9}$")
# This bounded v0 research audit independently reviewed ONLY these two
# scenario PDF metadata identities. A plausible filename/URL is NOT proof
# of a currently existing source. To extend this list, independently verify
# the actual official metadata document and its station/stage/product first.
_REVIEWED_PDF_METADATA_IDENTITIES = frozenset({
    ("F700000103", "ZICH", 5660),
    ("F700000103", "ZICH", 7190),
})


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise StageReviewError("duplicate JSON key")
        result[key] = value
    return result


def _reject_number(value):
    raise StageReviewError("nonfinite JSON numbers disallowed")


def load_catalogue(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=_strict_object,
                          parse_constant=_reject_number)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StageReviewError("cannot read strict UTF-8 metadata JSON") from exc
    return data


def _integer(value, label):
    if type(value) is not int or not 0 < value < 20_000:
        raise StageReviewError(f"invalid {label} (positive integer millimetres required)")
    return value


def _metadata(value, station):
    if not isinstance(value, dict) or set(value) != {
        "station", "stage_mm", "product", "evidence", "source_url"
    }:
        raise StageReviewError("scenario has unreviewed/missing metadata fields")
    if value["station"] != station:
        raise StageReviewError("mixed or mismatched reference station")
    level = _integer(value["stage_mm"], "scenario stage")
    evidence = value["evidence"]
    product = value["product"]
    if evidence not in _ALLOWED_EVIDENCE or product not in _ALLOWED_PRODUCTS:
        raise StageReviewError("unrecognized product/evidence class")
    url = value["source_url"]
    if not isinstance(url, str) or len(url) > 1024:
        raise StageReviewError("missing or oversized source reference")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.fragment):
        raise StageReviewError("source reference must be plain HTTPS")
    if evidence == "official_pdf_metadata":
        if (station, product, level) not in _REVIEWED_PDF_METADATA_IDENTITIES:
            raise StageReviewError("source metadata not independently reviewed for this exact station/product/stage")
        expected = f"/ftp/pdf/{product}_{station}_{level}.pdf"
        if parsed.hostname not in {"www.vigicrues.gouv.fr", "vigicrues.gouv.fr"}:
            raise StageReviewError("unrecognized provider metadata host")
        if parsed.path != expected or parsed.query:
            raise StageReviewError("official filename/station/stage mismatch")
    return {"station": station, "stage_mm": level, "product": product,
            "evidence": evidence, "source_url": url}


def review_stage(observed_stage_mm, station, catalogue, product="ZICH"):
    """Return descriptive PDF distances only; never grant geodata/model use."""
    observed = _integer(observed_stage_mm, "observed stage")
    if not isinstance(station, str) or not _STATION_RE.fullmatch(station):
        raise StageReviewError("invalid station identifier")
    if product not in _ALLOWED_PRODUCTS:
        raise StageReviewError("unsupported product")
    if not isinstance(catalogue, list) or not 0 < len(catalogue) <= 50:
        raise StageReviewError("invalid candidate count")
    records = [_metadata(item, station) for item in catalogue]
    filtered = [item for item in records if item["product"] == product]
    if not filtered:
        raise StageReviewError("no candidates for requested product")
    keys = [(x["product"], x["stage_mm"], x["evidence"]) for x in records]
    if len(set(keys)) != len(keys):
        raise StageReviewError("duplicate stage/evidence identity")
    official = sorted({x["stage_mm"] for x in filtered
                       if x["evidence"] == "official_pdf_metadata"})
    historical_only = sorted({x["stage_mm"] for x in filtered
                              if x["evidence"] == "historical_report_only"}
                              - set(official))
    lower = max((v for v in official if v <= observed), default=None)
    upper = min((v for v in official if v >= observed), default=None)
    return {
        "profile": "oc-vigicrues-stage-bracket-research-v0",
        "station": station, "product": product,
        "observed_stage_mm": observed,
        "reviewed_pdf_metadata_stage_mm": official,
        "input_source_original_bytes_authenticated": False,
        "historical_report_only_stage_mm": historical_only,
        "lower_pdf_metadata_stage_mm": lower,
        "upper_pdf_metadata_stage_mm": upper,
        "lower_gap_mm": None if lower is None else observed - lower,
        "upper_gap_mm": None if upper is None else upper - observed,
        "pdf_metadata_bracket_exists": lower is not None and upper is not None,
        "full_geodata_bytes_verified": False,
        "geodata_reuse_rights_established": False,
        "observed_2016_flood_geometry_validated": False,
        "depth_interpolation_permitted": False,
        "asset_inundation_or_loss_calibration_permitted": False,
        "scientific_classification": "DESCRIPTIVE_METADATA_ONLY_NOT_MODEL_INPUT",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--metadata-json", required=True, type=Path)
    p.add_argument("--station", required=True)
    p.add_argument("--observed-mm", required=True, type=int)
    p.add_argument("--product", choices=sorted(_ALLOWED_PRODUCTS), default="ZICH")
    args = p.parse_args()
    try:
        result = review_stage(args.observed_mm, args.station,
                              load_catalogue(args.metadata_json), args.product)
    except StageReviewError as exc:
        p.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
