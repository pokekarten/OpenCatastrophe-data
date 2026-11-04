#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, aggregate-only US EPA FRS-to-GEM industrial asset *research* crosswalk.

Inputs are caller-prepared *normalized projections*, NOT publisher CSV schemas.
No source download, name/geospatial fuzzy match, ownership inference, insured
value, portfolio inference, redistribution permission or CAT-model admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import date
import hashlib
import io
import json
from math import asin, cos, radians, sin, sqrt, isfinite
from pathlib import Path
import re

MAX_BYTES = 1_000_000
MAX_ROWS = 10_000
FRS_COLUMNS = ("frs_id", "country_code", "latitude", "longitude")
GEM_COLUMNS = ("gem_asset_id", "country_code", "latitude", "longitude")
LINK_COLUMNS = ("frs_id", "gem_asset_id", "evidence_kind", "evidence_sha256")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,99}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
EVIDENCE_KINDS = {"publisher_explicit_cross_id", "independent_document", "name_or_proximity_only"}
DISPOSITIONS = (
    "no_link_in_bounded_subset", "ambiguous_many_to_one_or_one_to_many",
    "missing_gem_in_bounded_subset", "name_or_proximity_only_unverified",
    "country_disagreement", "location_missing", "distance_over_5km_review",
    "one_to_one_research_candidate",
)


class IdentityPreflightBlocked(ValueError):
    """The supplied research projection cannot be safely interpreted."""


def _date(value: str, label: str) -> str:
    if not isinstance(value, str) or not DATE.fullmatch(value):
        raise IdentityPreflightBlocked(label + ": YYYY-MM-DD release date required")
    try:
        year, month, day = map(int, value.split("-"))
        parsed = date(year, month, day)
    except ValueError as exc:
        raise IdentityPreflightBlocked(label + ": invalid calendar date") from exc
    if not date(2020, 1, 1) <= parsed <= date(2100, 1, 1):
        raise IdentityPreflightBlocked(label + ": outside supported research vintage")
    return value


def _read(blob: bytes, expected_hash: str, columns: tuple[str, ...], label: str, *, empty_ok=False) -> list[dict[str, str]]:
    if not isinstance(expected_hash, str) or not SHA256.fullmatch(expected_hash):
        raise IdentityPreflightBlocked(label + ": lowercase SHA-256 required")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise IdentityPreflightBlocked(label + ": empty or oversized projection")
    if hashlib.sha256(blob).hexdigest() != expected_hash:
        raise IdentityPreflightBlocked(label + ": projection SHA-256 mismatch")
    try:
        reader = csv.DictReader(io.StringIO(blob.decode("utf-8"), newline=""), strict=True)
        if tuple(reader.fieldnames or ()) != columns:
            raise IdentityPreflightBlocked(label + ": exact normalized column order required")
        rows = []
        for row in reader:
            if len(rows) >= MAX_ROWS:
                raise IdentityPreflightBlocked(label + ": row limit exceeded")
            if None in row or any(v is None or v != v.strip() for v in row.values()):
                raise IdentityPreflightBlocked(label + ": malformed row or whitespace")
            rows.append(row)
        if not rows and not empty_ok:
            raise IdentityPreflightBlocked(label + ": at least one row required")
        return rows
    except (UnicodeError, csv.Error) as exc:
        raise IdentityPreflightBlocked(label + ": malformed CSV") from exc


def _id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value):
        raise IdentityPreflightBlocked(label + ": invalid identifier")
    return value


def _coordinates(row: dict[str, str], label: str):
    lat, lon = row["latitude"], row["longitude"]
    if lat == lon == "":
        return None
    if not lat or not lon:
        raise IdentityPreflightBlocked(label + ": partial coordinates")
    try:
        x, y = float(lat), float(lon)
    except ValueError as exc:
        raise IdentityPreflightBlocked(label + ": invalid coordinates") from exc
    if not all(map(isfinite, (x, y))) or not (-90 <= x <= 90 and -180 <= y <= 180):
        raise IdentityPreflightBlocked(label + ": coordinates out of range")
    return x, y


def _distance_km(a, b) -> float:
    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    q = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 2*6371.0088*asin(min(1., sqrt(q)))


def audit_identity(frs_blob: bytes, frs_sha256: str, gem_blob: bytes, gem_sha256: str,
                   links_blob: bytes, links_sha256: str, *, frs_vintage: str,
                   gem_vintage: str, link_vintage: str) -> dict:
    """Aggregate diagnostics only. A source ID or evidence hash is not proof of insurance."""
    for label, value in (("FRS", frs_vintage), ("GEM", gem_vintage), ("crosswalk", link_vintage)):
        _date(value, label)
    frs = _read(frs_blob, frs_sha256, FRS_COLUMNS, "FRS")
    gem = _read(gem_blob, gem_sha256, GEM_COLUMNS, "GEM")
    links = _read(links_blob, links_sha256, LINK_COLUMNS, "link evidence", empty_ok=True)
    facilities, assets, by_facility, asset_degree = {}, {}, {}, Counter()
    for row in frs:
        key = _id(row["frs_id"], "FRS")
        if key in facilities:
            raise IdentityPreflightBlocked("duplicate FRS source identifier")
        if row["country_code"] != "US":
            raise IdentityPreflightBlocked("FRS selected US facility scope required")
        facilities[key] = (row["country_code"], _coordinates(row, "FRS"))
    for row in gem:
        key = _id(row["gem_asset_id"], "GEM")
        if key in assets:
            raise IdentityPreflightBlocked("duplicate GEM asset identifier")
        if not re.fullmatch(r"[A-Z]{2}", row["country_code"]):
            raise IdentityPreflightBlocked("GEM invalid country code")
        assets[key] = (row["country_code"], _coordinates(row, "GEM"))
    seen_links = set()
    for row in links:
        frs_id, gem_id = _id(row["frs_id"], "link FRS"), _id(row["gem_asset_id"], "link GEM")
        if (frs_id, gem_id) in seen_links:
            raise IdentityPreflightBlocked("duplicate asserted FRS-GEM pair")
        seen_links.add((frs_id, gem_id))
        if frs_id not in facilities:
            raise IdentityPreflightBlocked("link FRS identifier outside bounded subset")
        kind = row["evidence_kind"]
        if kind not in EVIDENCE_KINDS:
            raise IdentityPreflightBlocked("unrecognized link evidence kind")
        if kind != "name_or_proximity_only" and not SHA256.fullmatch(row["evidence_sha256"]):
            raise IdentityPreflightBlocked("documented link needs original evidence hash claim")
        if kind == "name_or_proximity_only" and row["evidence_sha256"] and not SHA256.fullmatch(row["evidence_sha256"]):
            raise IdentityPreflightBlocked("invalid link evidence hash")
        by_facility.setdefault(frs_id, []).append((gem_id, kind))
        asset_degree[gem_id] += 1
    counts = Counter()
    for frs_id, (country, point) in facilities.items():
        related = by_facility.get(frs_id, [])
        if not related:
            disposition = "no_link_in_bounded_subset"
        elif len(related) != 1 or asset_degree[related[0][0]] != 1:
            disposition = "ambiguous_many_to_one_or_one_to_many"
        else:
            gem_id, kind = related[0]
            if gem_id not in assets:
                disposition = "missing_gem_in_bounded_subset"
            elif kind == "name_or_proximity_only":
                disposition = "name_or_proximity_only_unverified"
            elif country != assets[gem_id][0]:
                disposition = "country_disagreement"
            elif point is None or assets[gem_id][1] is None:
                disposition = "location_missing"
            elif _distance_km(point, assets[gem_id][1]) > 5:
                disposition = "distance_over_5km_review"
            else:
                disposition = "one_to_one_research_candidate"
        counts[disposition] += 1
    result_counts = {key: counts[key] for key in DISPOSITIONS}
    if sum(result_counts.values()) != len(facilities):
        raise IdentityPreflightBlocked("FRS row conservation failed")
    severe = sum(counts[k] for k in DISPOSITIONS[1:7])
    return {
        "audit": "industrial-frs-gem-identity-v0",
        "frs_vintage": frs_vintage, "gem_vintage": gem_vintage, "link_vintage": link_vintage,
        "frs_projection_sha256": frs_sha256, "gem_projection_sha256": gem_sha256,
        "link_projection_sha256": links_sha256,
        "frs_rows": len(frs), "gem_rows": len(gem), "asserted_link_rows": len(links),
        "frs_row_dispositions": result_counts, "frs_rows_conserved": True,
        "links_with_gem_id_absent_from_subset": sum(1 for x in links if x["gem_asset_id"] not in assets),
        "state": "REVIEW_NEEDED" if severe else (
            "RESEARCH_ID_CANDIDATES_ONLY" if counts["one_to_one_research_candidate"]
            else "NO_RESEARCH_ID_CANDIDATE"),
        "projection_hash_proves_publisher_byte_authenticity": False,
        "link_evidence_hash_independently_authenticated": False,
        "coordinates_or_names_prove_asset_identity": False,
        "corporate_ownership_or_lei_link_derived": False,
        "insured_asset_or_tiv_inferred": False,
        "source_rights_or_model_admission_granted": False,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("frs", "gem", "links"):
        ap.add_argument("--"+name+"-projection", required=True, type=Path)
        ap.add_argument("--"+name+"-sha256", required=True)
    for name in ("frs", "gem", "link"):
        ap.add_argument("--"+name+"-vintage", required=True)
    args = ap.parse_args(argv)
    try:
        blobs = []
        for name in ("frs", "gem", "links"):
            path = getattr(args, name+"_projection")
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
                raise IdentityPreflightBlocked("expected bounded regular local projection")
            blobs.extend((path.read_bytes(), getattr(args, name+"_sha256")))
        report = audit_identity(*blobs, frs_vintage=args.frs_vintage,
                                gem_vintage=args.gem_vintage, link_vintage=args.link_vintage)
    except (OSError, IdentityPreflightBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 1 if report["state"] == "REVIEW_NEEDED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
