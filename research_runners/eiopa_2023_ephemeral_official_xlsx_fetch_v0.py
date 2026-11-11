# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One-shot original EIOPA HTTPS acquisition to metadata-only quarantine.

One GET per publisher XLSX, NO retries, NO credentials, NO proxy mirrors,
NO third-party redirects, NO worksheet financial cell parsing, NO raw
workbook upload. HTTP 429/403 are treated as blocked, not evaded.
Only run upon conscious original-source acquisition approval.
"""
from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path
import ssl
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import (
    HTTPRedirectHandler, HTTPSHandler, Request, build_opener
)

from eiopa_catastrophe_2023_local_xlsx_metadata_preflight_v0 import (
    EIOPAQuarantineBlocked, MAX_FILE_BYTES, inspect_pair
)

URLS = {
    "HISTORICAL_INSURED_LOSSES":
        "https://www.eiopa.europa.eu/document/download/50e6b095-174c-4d9c-b9dd-1376dc1d43eb_en?filename=Historical+loss+data.xlsx",
    "FLOOD_WIND_EXPOSURE":
        "https://www.eiopa.europa.eu/document/download/d2be6f79-3e44-47f1-821f-97ff41e9d7b6_en?filename=Flood+and+Windstorm_exposure_data.xlsx",
}
FIRST_SHA256 = "201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6"
ALLOWED_HOSTS = frozenset({"www.eiopa.europa.eu", "eiopa.europa.eu"})
MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SCHEMA = "EIOPA_2023_OFFICIAL_HTTPS_ORIGINAL_XLSX_INGEST_SHA_ONLY_NO_CLAIMS_V0"


class EIOPAOriginalDownloadBlocked(ValueError):
    pass


def validate_publisher_url(url: str) -> None:
    p = urlparse(url)
    if (p.scheme != "https" or p.hostname not in ALLOWED_HOSTS or
        p.port not in (None, 443) or p.username or p.password or
        p.fragment or not p.path.startswith("/document/download/")):
        raise EIOPAOriginalDownloadBlocked("off-publisher URL/redirect forbidden")


class StrictEIOPARedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_publisher_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def bounded_single_request(url: str, destination: Path, family: str, opener=None) -> None:
    validate_publisher_url(url)
    if family not in MAX_FILE_BYTES:
        raise EIOPAOriginalDownloadBlocked("EIOPA source family unknown")
    if destination.exists() or destination.is_symlink():
        raise EIOPAOriginalDownloadBlocked("refusing to overwrite source data")
    if opener is None:
        opener = build_opener(
            StrictEIOPARedirects(),
            HTTPSHandler(context=ssl.create_default_context())
        )
    req = Request(
        url,
        headers={
            "Accept": MIME,
            "User-Agent": "OpenCatastrophe-source-integrity-research/0.1",
        },
    )
    size = 0
    complete = False
    try:
        with opener.open(req, timeout=45) as response:
            final_url = response.geturl()
            validate_publisher_url(final_url)
            ctype = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if ctype != MIME:
                raise EIOPAOriginalDownloadBlocked("original response not XLSX media type")
            header_length = response.headers.get("Content-Length")
            if header_length is not None and int(header_length) > MAX_FILE_BYTES[family]:
                raise EIOPAOriginalDownloadBlocked("original source Content-Length too large")
            with destination.open("xb") as output:
                while True:
                    part = response.read(65536)
                    if not part:
                        break
                    size += len(part)
                    if size > MAX_FILE_BYTES[family]:
                        raise EIOPAOriginalDownloadBlocked("original source read exceeded binary bound")
                    output.write(part)
        if size < 300:
            raise EIOPAOriginalDownloadBlocked("original source too small to be XLSX")
        complete = True
    except HTTPError as exc:
        # No retries; respect publisher rate limiting, never log response body.
        raise EIOPAOriginalDownloadBlocked(
            f"official original publisher HTTP {exc.code}; no retry"
        ) from exc
    except (URLError, OSError, TimeoutError, ValueError) as exc:
        raise EIOPAOriginalDownloadBlocked(
            "official original publisher transfer failed or was malformed"
        ) from exc
    finally:
        # Even a midstream TLS failure after hundreds of bytes must never
        # leave an ambiguously named partial source XLSX in the workspace.
        if not complete:
            destination.unlink(missing_ok=True)


def inspect_official_original_bytes(directory: Path, opener=None) -> dict:
    """Only ephemeral filesystem. Both sources must finish or no success."""
    loss = directory / "eiopa_original_losses.xlsx"
    expo = directory / "eiopa_original_exposure.xlsx"
    bounded_single_request(URLS["HISTORICAL_INSURED_LOSSES"], loss,
                           "HISTORICAL_INSURED_LOSSES", opener=opener)
    bounded_single_request(URLS["FLOOD_WIND_EXPOSURE"], expo,
                           "FLOOD_WIND_EXPOSURE", opener=opener)
    # Byte identity is a separate gate from spreadsheet content safety.
    # We may publish verified raw SHA+size even if the *original* spreadsheet
    # contains OOXML features requiring human review. NEVER relax quarantine.
    originals = []
    for name, family in ((loss, "HISTORICAL_INSURED_LOSSES"),
                         (expo, "FLOOD_WIND_EXPOSURE")):
        sha = hashlib.sha256()
        with name.open("rb") as handle:
            for part in iter(lambda: handle.read(65536), b""):
                sha.update(part)
        originals.append({
            "source_family": family,
            "sha256": sha.hexdigest(),
            "original_file_size_bytes": name.stat().st_size,
            "original_publisher_path": URLS[family],
            "publisher_origin_only_via_strict_TLS_host": True,
            "workbook_cells_examined": False,
        })
    if (originals[0]["sha256"] != FIRST_SHA256 or
        originals[0]["original_file_size_bytes"] != 28209):
        raise EIOPAOriginalDownloadBlocked(
            "official 2023 original loss XLSX binary changed from earlier independently observed receipt"
        )
    try:
        parsed = inspect_pair(loss, expo)
    except EIOPAQuarantineBlocked:
        # Protect against changing the file format validator to let known
        # externalLinks, embedded objects or malicious OOXML slip through.
        # Only binary SHA/size identity is released as metadata.
        parsed = None
    safe_full = parsed is not None
    if safe_full:
        # Even when the parser passed, this does NOT establish provenance,
        # rights, claims event scope or any insurance model validation.
        for original, result in zip(originals, parsed["originals"]):
            if original["sha256"] != result["sha256"]:
                raise EIOPAOriginalDownloadBlocked("binary identity diverged across original readers")
            original.update({
                "zip_crc_passed": result["zip_crc_passed"],
                "zip_member_count": result["zip_member_count"],
                "sheet_count": result["sheet_count"],
                "worksheet_names_sanitized": result["worksheet_names_sanitized"],
            })
    return {
        "schema": SCHEMA,
        "status": (
            "OFFICIAL_ORIGINALS_FULL_XLSX_METADATA_CHECKED_NOT_CLAIMS"
            if safe_full else
            "OFFICIAL_ORIGINALS_BINARY_SHA_ONLY_XLSX_QUARANTINE_BLOCKED"
        ),
        "official_source": "https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en",
        "source_original_TLS_host_restricted_to_EIOPA": True,
        "source_original_get_attempts_per_file": 1,
        "original_loss_exact_previously_verified_SHA": True,
        "original_exposure_new_SHA_must_be_independently_verified_before_model": True,
        "both_original_source_binary_files_complete": True,
        "full_XLSX_worksheet_metadata_and_CRC_passed": safe_full,
        "full_XLSX_quarantine_passed": safe_full,
        "public_original_XLSX_bytes_uploaded": False,
        "insurer_claim_cells_or_NUTS2_event_loss_observed": False,
        "publisher_rights_for_workbook_analysis_verified": False,
        "actual_German_RV_insurer_model_or_annual_EP": False,
        "originals": originals,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-receipt", type=Path, required=True)
    a = parser.parse_args()
    try:
        if a.out_receipt.is_symlink() or a.out_receipt.exists() or not a.out_receipt.parent.is_dir():
            raise EIOPAOriginalDownloadBlocked("receipt must use a fresh file path")
        with tempfile.TemporaryDirectory(prefix="eiopa-original-quarantine-") as temporary:
            result = inspect_official_original_bytes(Path(temporary))
            # No workbook binary escapes the temporary directory.
            with a.out_receipt.open("x", encoding="utf-8") as output:
                output.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
        print(json.dumps({
            "status": result["status"],
            "original_binary_files": len(result["originals"]),
            "original_sha256": [v["sha256"] for v in result["originals"]],
            "original_source_bytes_published": False,
            "actual_insurer_claims_or_annual_EP": False,
        }, sort_keys=True))
        return 0
    except (EIOPAOriginalDownloadBlocked, EIOPAQuarantineBlocked, OSError) as exc:
        parser.exit(2, "EIOPA_OFFICIAL_BINARY_ACQUISITION_BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
