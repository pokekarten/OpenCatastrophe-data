#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Deterministic read-only human view of one original-provider research receipt."""
from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REL = "docs/research/insurer-directory-original-page-receipt-20261101.json"
JSON_FILE = ROOT / REL
MD_FILE = JSON_FILE.with_suffix(".md")
SHA = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_PREFIX = "https://insurers.global/api/v1/insurers/names/pages/"


class ReceiptProjectionError(ValueError):
    """Missing, mutated, unregistered or unsafe original evidence."""


def validate_receipt(obj: dict) -> None:
    if type(obj) is not dict:
        raise ReceiptProjectionError("original receipt is not an object")
    if obj.get("schema") != "oc-insurer-directory-paged-original-receipt-v0":
        raise ReceiptProjectionError("unknown research receipt schema")
    if obj.get("source_dataset_version") != "2026-09-08+97f331e66662":
        raise ReceiptProjectionError("unreviewed source version")
    if obj.get("source_index_url") != "https://insurers.global/api/v1/insurers/names.json":
        raise ReceiptProjectionError("wrong provider source")
    if obj.get("provider_data_license") != "CC-BY-4.0":
        raise ReceiptProjectionError("unreviewed source licence")
    if obj.get("page_count") != 46 or obj.get("row_count") != 18180:
        raise ReceiptProjectionError("source population mismatch")
    if obj.get("unique_source_slugs") != 18180 or obj.get("model_input_approved") is not False:
        raise ReceiptProjectionError("source identity or model admission mismatch")
    if obj.get("source_original_aggregate_file_sha256") is not None:
        raise ReceiptProjectionError("unverified historical aggregate byte hash")
    digest = obj.get("canonical_field_digest_sha256")
    if type(digest) is not str or SHA.fullmatch(digest) is None:
        raise ReceiptProjectionError("invalid canonical five-field digest")
    neon = obj.get("neon_readonly_verification")
    if type(neon) is not dict or neon.get("same_five_field_digest") is not True:
        raise ReceiptProjectionError("Neon read-only parity not established")
    if neon.get("row_count") != 18180 or neon.get("model_approvals") != 0:
        raise ReceiptProjectionError("staging rows or CAT admission mismatch")
    pages = obj.get("source_pages")
    if type(pages) is not list or len(pages) != 46:
        raise ReceiptProjectionError("incomplete original source pages")
    total_bytes, total_rows = 0, 0
    for i, page in enumerate(pages, 1):
        if type(page) is not dict or page.get("page") != i:
            raise ReceiptProjectionError("source page numbering drift")
        if page.get("source_url") != f"{SOURCE_PREFIX}{i}.json":
            raise ReceiptProjectionError("source page origin drift")
        if page.get("rows") != (400 if i < 46 else 180):
            raise ReceiptProjectionError("source page count drift")
        if type(page.get("original_bytes")) is not int or not 0 < page["original_bytes"] <= 300000:
            raise ReceiptProjectionError("missing or oversized source bytes")
        if type(page.get("sha256")) is not str or SHA.fullmatch(page["sha256"]) is None:
            raise ReceiptProjectionError("invalid original page SHA")
        total_bytes += page["original_bytes"]
        total_rows += page["rows"]
    if total_rows != 18180 or total_bytes != obj.get("original_page_bytes_total"):
        raise ReceiptProjectionError("source totals not conserved")


def render_receipt(obj: dict) -> str:
    validate_receipt(obj)
    lines = [
        "<!--",
        "SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors",
        "SPDX-" + "License-Identifier: Apache-2.0",
        "-->",
        "",
        "<!-- GENERATED FILE — DO NOT EDIT DIRECTLY; canonical JSON: " + REL + " -->",
        "",
        "# Original insurer-directory page receipt",
        "",
        f"- Dataset version: `{obj['source_dataset_version']}`",
        f"- Original pages: **{obj['page_count']}**; source rows: **{obj['row_count']}**; original page bytes: **{obj['original_page_bytes_total']}**.",
        f"- Source/Neon five-field SHA-256: `{obj['canonical_field_digest_sha256']}`",
        f"- Source run: {obj['github_actions_proof']}",
        "- Model admission: **blocked**. Aggregate `names.json` original byte hash not established.",
        "",
        "| Page | Source rows | Original bytes | Page SHA-256 | Original API |",
        "| ---: | ---: | ---: | --- | --- |",
    ]
    for p in obj["source_pages"]:
        lines.append(
            f"| {p['page']} | {p['rows']} | {p['original_bytes']} | `{p['sha256']}` | "
            f"[JSON]({p['source_url']}) |"
        )
    lines.extend([
        "",
        "This is a deterministic projection of the JSON research receipt, not an independently editable factual source.",
        "The five-field parity is not a unique legal-entity register, insured exposure, original aggregate byte hash or CAT model admission.",
        "Publisher attribution: KAFS North America, insurers.global, CC BY 4.0.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--check", action="store_true")
    choice.add_argument("--write", action="store_true")
    args = parser.parse_args()
    obj = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    expected = render_receipt(obj)
    if args.check:
        if not MD_FILE.is_file():
            raise ReceiptProjectionError("generated research Markdown view missing")
        current = MD_FILE.read_text(encoding="utf-8")
        if expected != current:
            diff = "".join(difflib.unified_diff(current.splitlines(True),
                                                expected.splitlines(True),
                                                fromfile="committed", tofile="expected"))
            raise ReceiptProjectionError("generated research Markdown view drift:\n" + diff[:2500])
        print("PASS: 46-page canonical receipt has deterministic human projection")
    else:
        MD_FILE.write_text(expected, encoding="utf-8")
        print("WROTE: " + str(MD_FILE))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ReceiptProjectionError, ValueError, OSError) as exc:
        raise SystemExit(f"BLOCKED: {exc}") from exc
