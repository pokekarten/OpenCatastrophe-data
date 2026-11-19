#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Explicit original JRC EuroCrops DE4 2023 aggregate QC, no source redistribution.

Only an opt-in authorized original-file runtime may invoke this script. It pins
previously observed ORIGINAL footer bytes and publisher-maintained codebooks,
then verifies full-file hash, sampled WKB geometry and COMPLETE area_ha column.
Does not admit original data for any insurer model, CAT loss or valuation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from research_runners.eurocrops_codebook_qc_v0 import git_blob_sha
from research_runners.eurocrops_v202_preflight_v0 import Blocked, inspect_local

JRC_FILE = "de4_2023.parquet"
FOOTER_BYTES = 16266
OBSERVED_ORIGINAL_FOOTER_SHA256 = (
    "3ccb9177c49914f95e63d3942977c0d95a174b8434c004ba31f523be574b8d53"
)
EXPECTED_FOOTER_ROWS = 285606
COMMIT = "b556d10651b98684d5d5269916f8f34c9e017151"
BOOKS = {
    "eurocrops.csv": "37a58061df29036300862dc680c769a1b2727e15",
    "hcat4.csv": "7b4a7d1b5f3312d011958d0a1943c1324c3610ca",
}
MAX_CODEBOOK_BYTES = 2_000_000
ROOT = Path(__file__).resolve().parents[1]


def verified_original(path: Path, first_seen_sha: str) -> dict:
    if (path.name != JRC_FILE or path.is_symlink() or not path.is_file()
            or not isinstance(first_seen_sha, str)
            or re.fullmatch(r"[0-9a-f]{64}", first_seen_sha) is None):
        raise Blocked("only SHA-pinned original corrected JRC DE4 2023 asset allowed")
    resolved = path.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise Blocked("original JRC bytes must remain outside the repository")
    size = path.stat().st_size
    if not 10_000_000 <= size <= 180 * 1024 * 1024:
        raise Blocked("implausible original JRC size")
    actual = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            actual.update(chunk)
        source.seek(-FOOTER_BYTES, 2)
        tail = source.read(FOOTER_BYTES)
    if actual.hexdigest() != first_seen_sha:
        raise Blocked("first-seen full-original download SHA256 mismatch")
    if len(tail) != FOOTER_BYTES or hashlib.sha256(tail).hexdigest() != OBSERVED_ORIGINAL_FOOTER_SHA256:
        raise Blocked("original DE4 2023 footer differs from independent prior observation")
    if tail[-4:] != b"PAR1" or int.from_bytes(tail[-8:-4], "little") != FOOTER_BYTES - 8:
        raise Blocked("invalid pinned original footer length or magic")
    return {
        "original_filename": JRC_FILE,
        "full_original_bytes": size,
        "first_seen_full_original_sha256": first_seen_sha,
        "original_footer_bytes": FOOTER_BYTES,
        "independently_observed_footer_sha256_matched": True,
        "original_footer_only_sha256": OBSERVED_ORIGINAL_FOOTER_SHA256,
        "original_publisher_signed_full_checksum_verified": False,
    }


def _approved_raw_url(name: str) -> str:
    if name not in BOOKS:
        raise Blocked("unapproved codebook name")
    return (
        "https://raw.githubusercontent.com/Martincccc/EuroCropsV2/"
        f"{COMMIT}/data/cropcodemapping/{name}"
    )


def download_pinned_codebook(name: str, opener=urlopen) -> bytes:
    """Read ONLY the two exact publisher commit-backed source CSVs."""
    url = _approved_raw_url(name)
    req = Request(url, headers={"Accept-Encoding": "identity",
                                "User-Agent": "OpenCatastrophe-original-QC/0.1"})
    with opener(req, timeout=30) as response:
        final = response.geturl()
        parsed = urlsplit(final)
        if (parsed.scheme != "https" or parsed.netloc != "raw.githubusercontent.com"
                or final != url or getattr(response, "status", None) != 200
                or response.headers.get("Content-Encoding", "identity").lower() != "identity"):
            raise Blocked("codebook redirected, encoded, or not from exact pinned GitHub raw URL")
        raw = response.read(MAX_CODEBOOK_BYTES + 1)
    if not raw or len(raw) > MAX_CODEBOOK_BYTES:
        raise Blocked("invalid or oversized original codebook")
    if git_blob_sha(raw) != BOOKS[name]:
        raise Blocked("publisher-commit original codebook blob mismatch")
    return raw


def original_quality_report(
    original: Path, first_seen_sha: str, mapping: Path, hierarchy: Path,
    *, max_rows: int = 1024
) -> dict:
    """Bounded report: aggregate counts and pinned identity, no original rows."""
    identity = verified_original(original, first_seen_sha)
    qc = inspect_local(
        original, first_seen_sha, max_rows,
        mapping=mapping, mapping_git_blob_sha1=BOOKS["eurocrops.csv"],
        hierarchy=hierarchy, hierarchy_git_blob_sha1=BOOKS["hcat4.csv"],
        scan_full_area=True,
    )
    if (qc["source_region"] != "de4" or qc["source_year"] != 2023 or
            qc["parquet_total_rows_from_footer"] != EXPECTED_FOOTER_ROWS or
            qc["geo"]["primary_geometry_column"] != "geometry" or
            qc["geo"]["crs"] != "EPSG:3035" or not qc["taxonomy_crosswalk_checked"] or
            not qc["full_original_area_ha_scan_checked"]):
        raise Blocked("original provider metadata differs from prior DE4 pinned receipt")
    scan = qc["full_original_area_ha_scan"]
    if scan["original_area_rows_scanned"] != EXPECTED_FOOTER_ROWS:
        raise Blocked("full area attribute was not scanned")
    # No original item geometry, parcel ID, coordinate, original row/code or
    # site-identifying damage estimate is emitted in this artifact.
    return {
        "profile": "jrc-eurocrops-de4-2023-original-first-full-scan-QC-v0",
        "identity": identity,
        "provider_url": qc["source_url"],
        "parquet_total_rows": qc["parquet_total_rows_from_footer"],
        "parquet_row_groups": qc["parquet_row_groups"],
        "geo": qc["geo"],
        "original_area_footer_quality": qc["original_footer_column_quality"],
        "complete_area_ha_attribute_quality": scan,
        "sampled_wkb_rows": qc["sample"]["sampled"],
        "sampled_row_groups": qc["sampled_row_groups"],
        "sample_geometry_statistics": qc["sample"],
        "sample_taxonomy_crosswalk_statistics": qc["sample_taxonomy_crosswalk"],
        "codebook_mapping_git_blob_sha1": BOOKS["eurocrops.csv"],
        "codebook_hierarchy_git_blob_sha1": BOOKS["hcat4.csv"],
        "sample_is_a_scientifically_representative_portfolio": False,
        "real_agricultural_fields_used_for_insurer_exposure": False,
        "raw_original_source_rows_redistributed": False,
        "rights_scientific_and_insurer_model_admission": "NOT_ADMITTED",
        "insured_value_hazard_damage_and_cat_losses_calculated": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true",
                   help="explicitly authorize only exact pinned codebook downloads")
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--original-sha256", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--sample-rows", type=int, default=1024)
    args = p.parse_args(argv)
    if not args.live:
        p.exit(2, "BLOCKED: --live needed for external original codebooks\n")
    if args.output.exists() or args.output.is_symlink():
        p.exit(2, "BLOCKED: never overwrite existing receipt\n")
    if args.output.resolve() == ROOT or ROOT in args.output.resolve().parents:
        p.exit(2, "BLOCKED: receipt output must remain outside Git\n")
    try:
        verified_original(args.original, args.original_sha256)
        mapping_path = args.output.parent / "original-eurocrops-pinned.csv"
        hierarchy_path = args.output.parent / "original-hcat4-pinned.csv"
        for path in (mapping_path, hierarchy_path):
            if path.exists() or path.is_symlink():
                raise Blocked("temporary codebook output already exists")
        try:
            mapping_path.write_bytes(download_pinned_codebook("eurocrops.csv"))
            hierarchy_path.write_bytes(download_pinned_codebook("hcat4.csv"))
            report = original_quality_report(
                args.original, args.original_sha256, mapping_path, hierarchy_path,
                max_rows=args.sample_rows,
            )
            args.output.write_text(json.dumps(
                report, indent=2, sort_keys=True
            ) + "\n", encoding="utf-8")
        finally:
            mapping_path.unlink(missing_ok=True)
            hierarchy_path.unlink(missing_ok=True)
    except (Blocked, OSError, ValueError, RuntimeError) as exc:
        p.exit(2, f"BLOCKED: original-source audit failed: {exc}\n")
    print("PASS: exact original DE4 2023 source quality aggregates saved (NOT_ADMITTED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
