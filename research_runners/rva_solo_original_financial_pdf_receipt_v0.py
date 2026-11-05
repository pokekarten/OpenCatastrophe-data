# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded publisher-original R+V 2025 PDF receipts; original PDF bytes remain ephemeral.

First successful run discovers source SHA-256, but never claims the hash was pinned,
independently reproduced, rights-cleared, or suitable for insurer CAT calibration.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

MAX_BYTES = 6 * 1024 * 1024
MAX_TEXT_BYTES = 1_000_000
URLS = (
    {
        "source_id": "RVA_SOLO_SFCR_2025_ISSUER_PDF",
        "url": "https://www.ruv.de/dam/jcr:9c8441a7-28dd-4d98-9b79-3eb3c8b4afa5/2025-SFCR-Allgemeine.pdf",
        "pages_expected": 86,
        "required_markers": (
            r"R\+V\s+Allgemeine\s+Versicherung\s+AG",
            r"Stichtag:\s*31\.?12\.?2025",
            r"Feuer-?\s*und\s+andere\s+Sachversicherungen\s+2\.223\.182",
            r"Gesamt\s+5\.992\.306",
        ),
        "exact_original_sha256": None,
    },
    {
        "source_id": "RVA_SOLO_HGB_2025_ISSUER_PDF",
        "url": "https://www.ruv.de/dam/jcr:e0e32e31-09ff-4b0f-b693-2c6c9bee9bb5/01_GB%202025_R%2BV%20Allgemeine%20Versicherung%20AG_final.2026-04-21-14-59-23.pdf",
        "pages_expected": 98,
        "required_markers": (
            r"R\+V\s+Allgemeine\s+Versicherung\s+AG",
            r"Verbundene\s+Gebäude\s+997\.710\s+895\.090",
            r"Verbundene\s+Gebäude\s+1\.060\.546\s+1\.073\.802",
            r"R\+V\s+Direktversicherung\s+AG",
        ),
        "exact_original_sha256": None,
    },
)


def bounded_publisher_pdf(url: str, *, opener=urlopen) -> bytes:
    if url not in {s["url"] for s in URLS}:
        raise ValueError("RVA_SOURCE_URL_NOT_ALLOWLISTED")
    request = Request(url, headers={"User-Agent": "OpenCatastrophe-original-publisher-financial-source-receipt/1.0"})
    with opener(request, timeout=50) as response:
        effective = urlsplit(response.geturl())
        if effective.scheme != "https" or effective.hostname != "www.ruv.de":
            raise ValueError("RVA_SOURCE_REDIRECT_NOT_PUBLISHER")
        chunks, size = [], 0
        while True:
            piece = response.read(64 * 1024)
            if not piece:
                break
            size += len(piece)
            if size > MAX_BYTES:
                raise ValueError("RVA_SOURCE_OVERSIZE")
            chunks.append(piece)
    raw = b"".join(chunks)
    if not (50_000 < len(raw) <= MAX_BYTES and raw.startswith(b"%PDF-")
            and b"%%EOF" in raw[-8192:]):
        raise ValueError("RVA_SOURCE_TRUNCATED_OR_NOT_PDF")
    return raw


def semantic_check(extracted_text: str, markers: tuple[str, ...]) -> int:
    if not isinstance(extracted_text, str) or not extracted_text or len(extracted_text) > MAX_TEXT_BYTES:
        raise ValueError("RVA_PDF_TEXT_INVALID")
    text = re.sub(r"\s+", " ", extracted_text)
    for marker in markers:
        if not re.search(marker, text, flags=re.I):
            raise ValueError("RVA_ORIGINAL_FINANCIAL_MARKER_MISSING: " + marker[:80])
    return len(markers)


def inspect(source: dict, raw: bytes, *, extractor: str = "pdftotext", page_tool: str = "pdfinfo") -> dict:
    if not (raw.startswith(b"%PDF-") and len(raw) <= MAX_BYTES):
        raise ValueError("RVA_SOURCE_INVALID_BYTES")
    sha = hashlib.sha256(raw).hexdigest()
    pinned = source.get("exact_original_sha256")
    if pinned is not None and sha != pinned:
        raise ValueError("RVA_ORIGINAL_SOURCE_SHA_DRIFT")
    if not shutil.which(extractor) or not shutil.which(page_tool):
        raise ValueError("RVA_POPPLER_UTILITIES_REQUIRED")
    with tempfile.TemporaryDirectory(prefix="rva-public-financial-original-") as d:
        local = Path(d) / "issuer-original.pdf"
        local.write_bytes(raw)
        text_result = subprocess.run(
            [extractor, "-layout", "-enc", "UTF-8", str(local), "-"],
            capture_output=True, timeout=45, check=False)
        info_result = subprocess.run(
            [page_tool, str(local)], capture_output=True, timeout=25, check=False)
    if text_result.returncode or info_result.returncode or len(text_result.stdout) > MAX_TEXT_BYTES * 4:
        raise ValueError("RVA_ORIGINAL_PDF_EXTRACTOR_FAILED")
    try:
        extracted = text_result.stdout.decode("utf-8", "strict")
        info = info_result.stdout.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise ValueError("RVA_ORIGINAL_PDF_DECODE_FAILED") from exc
    match = re.search(r"^Pages:\s*(\d+)\s*$", info, re.M)
    if match is None or int(match.group(1)) != source["pages_expected"]:
        raise ValueError("RVA_ORIGINAL_PAGE_COUNT_DRIFT")
    marker_count = semantic_check(extracted, source["required_markers"])
    return {
        "source_id": source["source_id"],
        "original_issuer_url": source["url"],
        "original_sha256": sha,
        "original_bytes": len(raw),
        "pages_original": int(match.group(1)),
        "original_markers_verified": marker_count,
        "original_sha_previously_pinned": pinned is not None,
        "source_byte_receipt_complete": True,
        "independently_reproduced_source_sha_via_second_environment": False,
        "copyright_and_bulk_reuse_rights_cleared": False,
        "pdf_raw_stored_or_redistributed": False,
        "legal_person_identity_derived_from_premiums": False,
        "insurer_building_coordinates_or_tiv_observed": False,
        "cat_model_calibration_admitted": False,
        "production_financial_metric_admitted": False,
    }


def main() -> int:
    output = [inspect(source, bounded_publisher_pdf(source["url"])) for source in URLS]
    if len(output) != 2 or any(x["source_byte_receipt_complete"] is not True for x in output):
        raise ValueError("RVA_SFCR_AND_HGB_NOT_BOTH_VERIFIED")
    print(json.dumps({
        "schema": "RVA_SOLO_PUBLISHER_ORIGINAL_FINANCIAL_PDF_RECEIPT_V0",
        "status": "ORIGINAL_SOURCE_DISCOVERY_ONLY_NOT_ADMITTED",
        "observed_receipts": output,
        "publisher_pdfs_uploaded": False,
        "neon_production_modified": False,
        "cat_oep_aep_run_performed": False,
    }, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"RVA_ORIGINAL_ISSUER_FINANCIAL_PDF_BLOCKED: {type(exc).__name__}: {str(exc)[:110]}", file=sys.stderr)
        raise SystemExit(2)
