# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded original publisher Berlin Senate 2025 PDF source byte+semantic receipts.

Original source PDFs never stored, uploaded or printed. Without prior trusted
original bytes an initial reproducible live run only *observes* a SHA; a
separate exact-SHA pin update is mandatory before source admission.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tomllib
import tempfile
from pathlib import Path
import urllib.parse
import urllib.request

BASE="https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr"
MAX_BYTES=5*1024*1024
MAX_EXTRACTED_TEXT=400_000
SOURCES=(
    {
        "id":"BERLIN_SENATE_19_22033_20250401",
        "url":BASE+"/S19-22033.pdf",
        "pages_expected":6,
        "markers":(
            r"19\s*/\s*22\s*033",
            r"R\+V\s+Allgemeine\s+Versicherung\s+AG",
            r"GESOBAU",
            r"WBM",
            r"degewo",
            r"Allianz\s+AG",
            r"Sturm\s*/\s*Hagel",
        ),
        "exact_original_sha256":"0671a38d440b0628088399c0ee0fa521e24d31738d19c2d8b93d65424c87143f",
        "exact_original_bytes":22528,
    },
    {
        "id":"BERLIN_SENATE_19_24229_20251111",
        "url":BASE+"/S19-24229.pdf",
        "pages_expected":5,
        "markers":(
            r"19\s*/\s*24\s*229",
            r"Degewo\s+Gesobau\s+Gewobag\s+HOWOGE",
            r"82\.637",
            r"49\.054",
            r"34\.040",
            r"376\.278",
            r"18\.666",
            r"Charlottenburg-Wilmers",
        ),
        "exact_original_sha256":"1269725e4ff8427f32db22a66a0745bc12a75dc1281ca62de7d21ddcaead307e",
        "exact_original_bytes":21842,
    },
)


def fetch_original(url: str, *, opener=urllib.request.urlopen) -> bytes:
    if url not in {s["url"] for s in SOURCES}:
        raise ValueError("SOURCE_PDF_NOT_ALLOWLISTED")
    req=urllib.request.Request(url,headers={"User-Agent":"OpenCatastrophe-public-source-audit/1.0"})
    with opener(req,timeout=55) as response:
        effective=urllib.parse.urlsplit(response.geturl())
        if effective.scheme!="https" or effective.hostname!="pardok.parlament-berlin.de":
            raise ValueError("SOURCE_PDF_REDIRECT_NOT_PUBLISHER")
        parts=[]
        size=0
        while True:
            c=response.read(128*1024)
            if not c:break
            size+=len(c)
            if size>MAX_BYTES:
                raise ValueError("SOURCE_PDF_OVERSIZE")
            parts.append(c)
    raw=b"".join(parts)
    if not (1500<len(raw)<=MAX_BYTES) or not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-4096:]:
        raise ValueError("SOURCE_PDF_NOT_COMPLETE")
    return raw


def audit_text(text: str, markers: tuple[str,...]) -> dict:
    if not isinstance(text,str) or len(text)>MAX_EXTRACTED_TEXT:
        raise ValueError("SOURCE_PDF_TEXT_EXTRACTION_INVALID")
    normalized=re.sub(r"\s+"," ",text)
    result={}
    for marker in markers:
        hit=bool(re.search(marker,normalized,flags=re.IGNORECASE))
        if not hit:raise ValueError("SOURCE_PDF_REQUIRED_FACT_NOT_LOCATED")
        result[marker]=hit
    return {"required_semantic_marker_count":len(result),
            "all_required_markers_located":all(result.values())}


def inspect_original(source: dict, raw: bytes, *, extractor="pdftotext") -> dict:
    if raw[:5]!=b"%PDF-" or len(raw)>MAX_BYTES:
        raise ValueError("SOURCE_PDF_INVALID")
    sha=hashlib.sha256(raw).hexdigest()
    expected=source.get("exact_original_sha256")
    if expected is not None and expected!=sha:
        raise ValueError("SOURCE_PDF_ORIGINAL_SHA_CHANGED")
    exact_bytes=source.get("exact_original_bytes")
    if exact_bytes is not None and len(raw)!=exact_bytes:
        raise ValueError("SOURCE_PDF_ORIGINAL_BYTE_COUNT_CHANGED")
    exe=shutil.which(extractor)
    if not exe:raise ValueError("SOURCE_PDF_EXTRACTOR_UNAVAILABLE")
    with tempfile.TemporaryDirectory(prefix="rva-public-senate-") as folder:
        path=Path(folder)/"official.pdf"
        path.write_bytes(raw)
        proc=subprocess.run(
            [exe,"-layout","-enc","UTF-8",str(path),"-"],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=False,
        )
    if proc.returncode!=0 or len(proc.stdout)>MAX_EXTRACTED_TEXT*4:
        raise ValueError("SOURCE_PDF_EXTRACTOR_FAILED")
    try:text=proc.stdout.decode("utf-8",errors="strict")
    except UnicodeError as exc:raise ValueError("SOURCE_PDF_UNICODE_INVALID") from exc
    pages=text.count("\f")
    if pages!=source["pages_expected"]:
        raise ValueError("SOURCE_PDF_PAGE_COUNT_CHANGED")
    semantic=audit_text(text,source["markers"])
    return {
        "source_id":source["id"],
        "original_publisher_url":source["url"],
        "original_bytes":len(raw),
        "original_sha256":sha,
        "source_pdf_pages_extracted":pages,
        "semantic_marker_count":semantic["required_semantic_marker_count"],
        "semantics_all_pass":semantic["all_required_markers_located"],
        "exact_source_sha_pinned":expected is not None,
        "issuer_labeled_corporate_relationship_and_housing_borough_stock_manual_fact_scope":True,
        "raw_pdf_stored_or_exported":False,
        "housing_site_geocodes_or_insurer_TIV_observed":False,
        "degewo_RV_coinsurance_share_observed":False,
        "insurer_2026_renewal_observed":False,
        "CAT_model_exposure_admitted":False,
    }


REGISTER=Path(__file__).resolve().parents[1]/"research"/"observations"/"rva_berlin_senate_2025_original_pdf_receipts_v0.toml"


def verify_saved_exact_original_source_receipts(audited: list[dict], *, register=None) -> dict:
    if register is None:
        register=tomllib.loads(REGISTER.read_text(encoding="utf-8"))
    if (
        register.get("schema_version")!="RVA_BERLIN_SENATE_2025_ORIGINAL_PDF_BYTES_V0"
        or register.get("original_files_acquired_and_hashed_in_ephemeral_github_action") is not True
        or register.get("verified_original_source_is_public_official_berlin_senate") is not True
        or register.get("raw_pdf_files_committed_or_redistributed") is not False
        or register.get("model_CAT_admission") is not False
        or register.get("actual_RV_insured_berlin_building_sites_verified") is not False
        or register.get("actual_RV_degewo_coinsurance_participation_verified") is not False
        or register.get("real_RV_site_TIV_and_policy_limits_verified") is not False
    ):
        raise ValueError("SOURCE_PDF_ORIGINAL_RESEARCH_SCOPE_CHANGED")
    entries=register.get("documents",[])
    if len(entries)!=len(SOURCES) or len(audited)!=len(SOURCES):
        raise ValueError("SOURCE_PDF_RECORDED_DOCUMENT_COUNT_CHANGED")
    for source,record,obs in zip(SOURCES,entries,audited):
        if any((
            record.get("id")!=source["id"],
            record.get("url")!=source["url"],
            record.get("original_sha256")!=source["exact_original_sha256"],
            record.get("original_bytes")!=source["exact_original_bytes"],
            record.get("original_pages")!=source["pages_expected"],
            record.get("positive_semantic_marker_count")!=len(source["markers"]),
            record.get("company_specific_insured_asset_count_observed") is not False,
            obs.get("original_sha256")!=record.get("original_sha256"),
            obs.get("original_bytes")!=record.get("original_bytes"),
            obs.get("source_pdf_pages_extracted")!=record.get("original_pages"),
            obs.get("semantic_marker_count")!=record.get("positive_semantic_marker_count"),
            obs.get("exact_source_sha_pinned") is not True,
            obs.get("raw_pdf_stored_or_exported") is not False,
            obs.get("CAT_model_exposure_admitted") is not False,
        )):
            raise ValueError("SOURCE_PDF_RECORDED_ORIGINAL_VALUES_OR_SCOPE_DRIFT")
    return {
        "exact_official_original_sha_byte_page_marker_receipts_conserved":True,
        "actual_insurer_portfolio_source_admitted":False,
    }


def main():
    receipts=[inspect_original(s,fetch_original(s["url"])) for s in SOURCES]
    print(json.dumps({
        "schema":"RVA_BERLIN_SENATE_2025_OFFICIAL_PDF_ORIGINAL_BYTES_V0",
        "source_receipts":receipts,
        "persisted_original_receipts_check":verify_saved_exact_original_source_receipts(receipts),
        "original_publisher_bytes_written_to_github":False,
        "actual_RV_insured_2025_corporate_building_sites_observed":False,
        "validated_model_exposure":False,
    },sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    try:main()
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        print(f"BERLIN_RVA_PDF_ORIGINAL_BLOCKED: {type(exc).__name__}: "
              f"{str(exc)[:70]}",file=sys.stderr)
        sys.exit(2)
