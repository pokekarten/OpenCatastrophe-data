# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Extract official TED publication XML from exact daily OJ S ZIP packages.

Fallback for TED individual direct XML links returning 202 Accepted, not XML.
No raw zip or XML written to disk/repo; only exact publisher receipt metadata.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import urllib.parse
import urllib.request
import zipfile

from .ted_berlin_insurance_original_xml_preflight_v0 import (
    MAX_BYTES, SOURCES, inspect,
)

MAX_ARCHIVE_BYTES = 140_000_000
MAX_MEMBERS = 60_000
OFFICIAL = "https://ted.europa.eu"
DAILY_SOURCE = {
    "558592-2024": {"oj_s": "181/2024", "package": "202400181"},
    "668506-2026": {"oj_s": "188/2026", "package": "202600188"},
}


def url_for(notice: str) -> str:
    if notice not in DAILY_SOURCE or notice not in SOURCES:
        raise ValueError("TED_DAILY_NOTICE_NOT_ALLOWLISTED")
    return OFFICIAL + "/packages/notice/daily/" + DAILY_SOURCE[notice]["package"]


def fetch_package(notice: str, *, opener=urllib.request.urlopen) -> bytes:
    url = url_for(notice)
    request = urllib.request.Request(
        url, headers={
            "Accept": "application/zip, application/octet-stream",
            "User-Agent": "OpenCatastrophe-public-TED-original-package-check/1.0",
        }
    )
    with opener(request, timeout=65) as response:
        effective = urllib.parse.urlsplit(response.geturl())
        # TED may serve the ZIP via a provider-controlled CDN, but cross-host
        # redirects have NOT been independently reviewed; fail closed.
        if (effective.scheme != "https" or effective.hostname != "ted.europa.eu"
                or effective.path != urllib.parse.urlsplit(url).path):
            raise ValueError("TED_DAILY_PACKAGE_REDIRECT_UNREVIEWED")
        status = getattr(response, "status", 200)
        if status != 200:
            raise ValueError(f"TED_DAILY_PACKAGE_HTTP_STATUS_{status}")
        parts = []
        count = 0
        while True:
            fragment = response.read(256 * 1024)
            if not fragment:
                break
            count += len(fragment)
            if count > MAX_ARCHIVE_BYTES:
                raise ValueError("TED_DAILY_PACKAGE_OVERSIZE")
            parts.append(fragment)
    raw = b"".join(parts)
    if not (20 < len(raw) <= MAX_ARCHIVE_BYTES) or raw[:4] != b"PK\x03\x04":
        raise ValueError("TED_DAILY_PACKAGE_IS_NOT_ZIP")
    return raw


def audit_package(notice: str, package: bytes) -> dict:
    if notice not in DAILY_SOURCE:
        raise ValueError("TED_DAILY_NOTICE_NOT_ALLOWLISTED")
    if type(package) is not bytes or not 20 < len(package) <= MAX_ARCHIVE_BYTES:
        raise ValueError("TED_DAILY_BAD_ZIP_SIZE_OR_TYPE")
    try:
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_MEMBERS:
                raise ValueError("TED_DAILY_TOO_MANY_ENTRIES")
            match = []
            number, year = notice.split("-")
            for item in entries:
                base = item.filename.rsplit("/", 1)[-1]
                if re.fullmatch(r"(?:0{0,2})" + re.escape(number) +
                                "_" + re.escape(year) + r"\.xml", base,
                                flags=re.IGNORECASE):
                    match.append(item)
            if len(match) != 1:
                raise ValueError("TED_DAILY_EXACT_NOTICE_XML_MISSING_OR_DUPLICATE")
            entry = match[0]
            if (entry.is_dir() or entry.flag_bits & 0x1
                    or not 100 <= entry.file_size <= MAX_BYTES
                    or entry.compress_size < 1
                    or entry.file_size > max(entry.compress_size * 500, 500_000)):
                raise ValueError("TED_DAILY_SUSPICIOUS_XML_ENTRY")
            with archive.open(entry) as stream:
                content = stream.read(MAX_BYTES + 1)
            if len(content) != entry.file_size:
                raise ValueError("TED_DAILY_XML_TRUNCATED_OR_OVERSIZE")
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise ValueError("TED_DAILY_INVALID_ARCHIVE") from exc
    r = inspect(notice, content)
    r["original_xml_acquisition_mode"] = "publisher_daily_oj_s_archive"
    r["original_xml_acquisition_url"] = url_for(notice)
    r["original_zip_oj_s"] = DAILY_SOURCE[notice]["oj_s"]
    r["original_zip_original_bytes"] = len(package)
    r["original_zip_sha256"] = hashlib.sha256(package).hexdigest()
    r["original_zip_extracted_file_basename"] = entry.filename.rsplit("/", 1)[-1]
    r["original_daily_zip_bytes_stored_in_repository"] = False
    return r


def main() -> int:
    try:
        results = [
            audit_package(n, fetch_package(n))
            for n in sorted(DAILY_SOURCE)
        ]
        print(json.dumps({
            "schema": "TED_BERLIN_INSURANCE_OFFICIAL_DAILY_XML_ORIGINAL_PREFLIGHT_V0",
            "original_publisher_archive_retrieved": True,
            "fixed_original_source_sha256_pins_verified": all(
                r["original_sha256_immutable_pin_verified"] for r in results
            ),
            "original_xml_bytes_committed": False,
            "original_insurer_exposure_locations_or_policy_tiv_admitted": False,
            "receipts": results,
        }, sort_keys=True, ensure_ascii=False))
    except (OSError, ValueError) as exc:
        print("TED_DAILY_ORIGINAL_PREFLIGHT_BLOCKED: " + str(exc)[:160],
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
