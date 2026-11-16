# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Compare text, not just bytes, in two real ambiguous Météo-France PDFs.

Only in-memory source PDFs from an already SHA-bound original hourly station
cohort; no PDF text, station IDs or individual resource URLs leave the process.
Visible PDF page images are NOT compared. These source statistics are not a
historical instrument/site attestation and do not authorize CAT calibration.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import unicodedata

from research_runners.meteofrance_hourly_gust_v0 import Blocked, _read_url, sha256
from research_runners.meteofrance_four_north_original_v0 import MAX_COMPRESSED, asset_url, check_identity
from research_runners.meteofrance_north_hourly_catalogue_v0 import (
    CATALOGUE_URL, MAX_CATALOGUE_BYTES, audit_catalogue
)
from research_runners.meteofrance_ciara2020_duplicate_pdf_v0 import compare_pdf_candidates
from research_runners.meteofrance_ciara2020_station_pdf_proof_v0 import (
    CATALOGUE_URL_STATIONS, CATALOGUE_LIMIT, MAX_PDF_BYTES
)

DEP = "76"
EXPECTED_SOURCE_COHORT_SHA256 = "08fa1dc144c415d9485a3f2f358e0fb9b9eb952bb1db8221c2b0afe5120612d9"
MAX_PAGES = 32
MAX_PAGE_CHARACTERS = 75000
MAX_DOCUMENT_CHARACTERS = 240000


def normalized_text(s: str) -> str:
    if not isinstance(s, str):
        raise Blocked("PDF extracted text is not unicode")
    return " ".join(unicodedata.normalize("NFKC", s).casefold().split())


def text_profile(pages: list[str]) -> dict:
    """Quantify inspectable PDF text without exposing actual page contents."""
    if not isinstance(pages, list) or not 1 <= len(pages) <= MAX_PAGES:
        raise Blocked("PDF page population outside bounded scope")
    if any(not isinstance(s, str) or len(s) > MAX_PAGE_CHARACTERS for s in pages):
        raise Blocked("PDF page text exceeds safe cap or wrong type")
    if sum(len(s) for s in pages) > MAX_DOCUMENT_CHARACTERS:
        raise Blocked("PDF document text exceeds safe cap")
    text = normalized_text("\n".join(pages))
    nonempty_pages = sum(bool(normalized_text(p)) for p in pages)
    # Key phrases are only signals that a human should review the matched
    # passage and its context. They are NOT verified 2020 measurements.
    signals = {
        "mentions_2020": bool(re.search(r"\b2020\b", text)),
        "mentions_wind_word": bool(re.search(r"\b(?:vent|rafale|vents)\b", text)),
        "mentions_instrument_word": bool(re.search(r"\b(?:instrumentation|an[ée]mom[èe]tre|capteur)\b", text)),
        "mentions_site_word": bool(re.search(r"\b(?:emplacement|implantation|site|déplacement)\b", text)),
        "mentions_height_word": bool(re.search(r"\b(?:hauteur|m[èe]tre|m[èe]tres)\b", text)),
    }
    return {
        "pdf_page_count": len(pages),
        "pages_with_extracted_text": nonempty_pages,
        "normalized_extracted_text_characters": len(text),
        "normalized_extracted_text_sha256": sha256(text.encode("utf-8")),
        "has_substantive_extracted_text": len(text) >= 80,
        "possible_review_subjects": signals,
    }


def extract_pdf_profile(content: bytes) -> dict:
    # Isolated original-source job pins this dependency, while the standard
    # repository's offline unit-test matrix does not need pypdf installed.
    try:
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError
    except ImportError as exc:
        raise Blocked("pypdf must be installed in isolated original-PDF research job") from exc
    try:
        reader = PdfReader(io.BytesIO(content), strict=False)
        if reader.is_encrypted:
            raise Blocked("encrypted original station PDF not inspected")
        n = len(reader.pages)
        if not 1 <= n <= MAX_PAGES:
            raise Blocked("PDF page count outside research cap")
        pages = []
        for page in reader.pages:
            page_text = page.extract_text(extraction_mode="plain") or ""
            if len(page_text) > MAX_PAGE_CHARACTERS:
                raise Blocked("page extracted text exceeds research cap")
            pages.append(page_text)
        return text_profile(pages)
    except (PdfReadError, KeyError, IndexError, TypeError, ValueError,
            AttributeError, OSError) as exc:
        raise Blocked("original PDF text extraction could not be independently read") from exc


def compare_pdf_text(original: bytes, catalogue: bytes, *,
                     download_pdf=_read_url, extractor=extract_pdf_profile,
                     min_resources: int = 10000,
                     expected_cohort_sha256: str = EXPECTED_SOURCE_COHORT_SHA256) -> dict:
    cache: dict[str, bytes] = {}

    def fetch_once(url: str, bound: int) -> bytes:
        if url in cache:
            raise Blocked("same original PDF URL requested for multiple resources")
        data = download_pdf(url, bound)
        cache[url] = data
        return data

    source = compare_pdf_candidates(
        original, catalogue, fetch_pdf=fetch_once, min_resources=min_resources
    )
    if source["station_bound_pdf_cohort_digest"] != expected_cohort_sha256:
        raise Blocked("exact PDF original resource/source cohort differs from prior verified CI")
    if source["candidate_pdf_resource_count"] != 2 or len(cache) != 2:
        raise Blocked("expected precisely two distinct original PDF URLs")
    if source["unique_pdf_sha256_count"] != 2:
        raise Blocked("two original PDF bytes unexpectedly equal")
    # Canonical sort is by the exact provider URL, but those URL paths and
    # their source-specific 8-digit station ID are never printed.
    profiles = [extractor(cache[key]) for key in sorted(cache)]
    if any(type(x) is not dict for x in profiles):
        raise Blocked("PDF content extraction did not yield two profiles")
    enough_text = all(x.get("has_substantive_extracted_text") is True for x in profiles)
    same_text = (profiles[0].get("normalized_extracted_text_sha256") ==
                 profiles[1].get("normalized_extracted_text_sha256")) if enough_text else None
    return {
        "profile": "meteofrance-ciara2020-station-pdf-text-comparison-v0",
        "department": DEP,
        "source_hourly_original_sha256": source["source_hourly_original_sha256"],
        "station_bound_original_pdf_cohort_sha256": source["station_bound_pdf_cohort_digest"],
        "original_pdf_resource_count": 2,
        "source_pdf_bytes_are_different": not source["all_original_pdfs_byte_identical"],
        "original_pdf_total_bytes": source["total_original_pdf_bytes_checked"],
        "pdf_content_profiles": [
            {"pdf_page_count": p["pdf_page_count"],
             "pages_with_extracted_text": p["pages_with_extracted_text"],
             "normalized_extracted_text_characters": p["normalized_extracted_text_characters"],
             "possible_review_subjects": p["possible_review_subjects"]}
            for p in profiles
        ],
        "both_original_pdfs_have_extractable_text": enough_text,
        "normalized_extracted_text_equal": same_text,
        "text_content_disagreement_detected": (not same_text) if same_text is not None else None,
        "visual_pdf_image_content_compared": False,
        "pdf_page_text_or_station_identity_published": False,
        "february_2020_site_instrument_height_verified": False,
        "historical_source_version_safely_selected": False,
        "source_admitted": False,
        "era5_station_skill_or_calibration_authorized": False,
        "annual_ep_authorized": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True)
    parser.parse_args(argv)
    try:
        overview = audit_catalogue(_read_url(CATALOGUE_URL, MAX_CATALOGUE_BYTES))
        check_identity(overview, DEP)
        original = _read_url(asset_url(DEP), MAX_COMPRESSED)
        catalogue = _read_url(CATALOGUE_URL_STATIONS, CATALOGUE_LIMIT)
        print(json.dumps(compare_pdf_text(original, catalogue), sort_keys=True, indent=2))
        return 0
    except Blocked as exc:
        # Restrict error output to controlled diagnostics without station names.
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print("BLOCKED: " + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
