# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fixed Figshare GDW v1.0 archive-metadata canary; never downloads source files."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import sys
from typing import Any, Callable
from urllib import error, request

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "globaldamwatch.gdw.v1.0.json"
URL = "https://api.figshare.com/v2/articles/25988293/versions/1"
DOI = "10.6084/m9.figshare.25988293.v1"
# Frozen metadata verified from the exact original Figshare v1 REST response, 2026-11-04.
# Two alternate GIS archives AND one separately listed final technical PDF.
# These are provider-declared identities, not independent download hashes.
FROZEN_FILES = {
    "GDW_TechDoc_v1_0.pdf": (47913739, 716288, "5b2fc93c384f674414fa711b657bef5e"),
    "GDW_v1_0_gdb.zip": (47913742, 57476758, "410d1ed16312ac613975fd092c193c65"),
    "GDW_v1_0_shp.zip": (47913754, 69745749, "5064cf2315ef6159d9133b03596e761a"),
}
EXPECTED_TOTAL_BYTES = 127938795
MAX_BYTES = 131072
TIMEOUT = 30
PROFILE = "oc-gdw-figshare-version1-metadata-receipt-v0"


class ProbeBlocked(ValueError):
    """Source identity, rights gate, response or network policy mismatch."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProbeBlocked("duplicate JSON property")
        result[key] = value
    return result


def _bad_number(_: str) -> None:
    raise ProbeBlocked("non-finite JSON number")


def verify_contract(path: Path = CONTRACT_PATH) -> None:
    c = validate_path(path)
    if (
        c["access_id"] != "globaldamwatch.gdw.v1.0"
        or c["source_ids"] != ["globaldamwatch.gdw.v1.0"]
        or c["service_root"] != "https://api.figshare.com"
        or c["status"] != "probe_ready"
        or c["authentication"]["mode"] != "none"
        or c["request_contract"]["allowed_operations"] != ["gdw_v10_archive_metadata_version1"]
        or c["request_contract"]["path_templates"] != ["/v2/articles/25988293/versions/1"]
        or c["probe_contract"]["mode"] != "metadata_get"
        or c["probe_contract"]["operation"] != "gdw_v10_archive_metadata_version1"
        or c["probe_contract"]["requires_credentials"] is not False
        or c["operational_constraints"]["max_probe_bytes"] != MAX_BYTES
        or c["operational_constraints"]["timeout_seconds"] != TIMEOUT
        or c["rights_and_policy"]["dataset_rights_status"] != "verified"
        or c["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or c["rights_and_policy"]["commercial_automation_status"] != "allowed"
    ):
        raise ProbeBlocked("frozen GDW source access/rights contract drift")


def inspect_metadata(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ProbeBlocked("metadata empty or oversized")
    try:
        item = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=_bad_number)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise ProbeBlocked("invalid strict UTF-8 JSON metadata") from exc
    if type(item) is not dict or type(item.get("id")) is not int or item["id"] != 25988293:
        raise ProbeBlocked("wrong Figshare article identity")
    if type(item.get("version")) is not int or item["version"] != 1:
        raise ProbeBlocked("wrong Figshare article version")
    if item.get("doi") not in (DOI, "https://doi.org/" + DOI):
        raise ProbeBlocked("missing or changed frozen dataset DOI")
    lic = item.get("license")
    if not isinstance(lic, dict) or lic.get("name") != "CC BY 4.0":
        raise ProbeBlocked("unreviewed provider licence")
    if "url" in lic and lic["url"] not in (
        "https://creativecommons.org/licenses/by/4.0/",
        "http://creativecommons.org/licenses/by/4.0/",
    ):
        raise ProbeBlocked("provider licence URI drift")
    files = item.get("files")
    if type(files) is not list or len(files) != len(FROZEN_FILES):
        raise ProbeBlocked("GDW version 1 must list two GIS archives plus its separate final PDF")
    out: list[dict[str, Any]] = []
    for f in files:
        if type(f) is not dict or f.get("name") not in FROZEN_FILES:
            raise ProbeBlocked("unreviewed original-release filename")
        if type(f.get("id")) is not int or f["id"] <= 0:
            raise ProbeBlocked("invalid Figshare file identifier")
        if type(f.get("size")) is not int or f["size"] <= 0:
            raise ProbeBlocked("invalid declared archive size")
        md5 = f.get("supplied_md5") or f.get("computed_md5")
        if md5 is not None and (type(md5) is not str or re.fullmatch(r"[a-fA-F0-9]{32}", md5) is None):
            raise ProbeBlocked("invalid provider-declared MD5")
        if (f["id"], f["size"], md5) != FROZEN_FILES[f["name"]]:
            raise ProbeBlocked("provider-declared source file identity/hash changed")
        if f.get("is_link_only") is not False:
            raise ProbeBlocked("original asset unexpectedly became external link")
        out.append({"filename": f["name"], "figshare_file_id": f["id"],
                    "provider_declared_bytes": f["size"], "provider_declared_md5": md5})
    if {f["filename"] for f in out} != set(FROZEN_FILES):
        raise ProbeBlocked("missing or duplicated GDW release asset")
    if type(item.get("size")) is not int or item["size"] != EXPECTED_TOTAL_BYTES:
        raise ProbeBlocked("GDW article total declared size changed")
    return {"article_id": 25988293, "article_version": 1, "version_doi": DOI,
            "source_licence": "CC BY 4.0", "release_file_metadata": sorted(out, key=lambda x: x["filename"]),
            "gis_archive_count": 2, "final_technical_pdf_count": 1,
            "provider_archive_bytes_verified": False}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeBlocked("redirect forbidden")


def _open(req: request.Request, timeout: int):
    return request.build_opener(request.ProxyHandler({}), NoRedirect(),
                                request.HTTPSHandler(context=ssl.create_default_context())).open(req, timeout=timeout)


def probe(*, open_request: Callable[[request.Request, int], Any] = _open,
          utc_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
          contract_path: Path = CONTRACT_PATH) -> dict[str, Any]:
    verify_contract(contract_path)
    req = request.Request(URL, headers={"Accept": "application/json"}, method="GET")
    try:
        with open_request(req, TIMEOUT) as response:
            if response.geturl() != URL or type(response.status) is not int or response.status != 200:
                raise ProbeBlocked("unapproved response URL/status")
            if response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                raise ProbeBlocked("wrong metadata content type")
            raw = response.read(MAX_BYTES + 1)
    except ProbeBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise ProbeBlocked("fixed Figshare metadata request failed") from exc
    checked = utc_clock()
    if checked.tzinfo is None or checked.utcoffset() is None:
        raise ProbeBlocked("timezone-aware receipt clock required")
    metadata = inspect_metadata(raw)
    return {"profile": PROFILE, "source_id": "globaldamwatch.gdw.v1.0",
            "access_contract": "access/globaldamwatch.gdw.v1.0.json",
            "request_url": URL, "retrieved_at_utc": checked.astimezone(timezone.utc).isoformat(),
            "response_bytes": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest(),
            "probe_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            **metadata, "provider_bytes_persisted": False, "asset_downloaded": False,
            "model_input_approved": False, "database_updated": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="opt in to one reviewed, fixed metadata GET")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("no request by default; use --live for one fixed public metadata GET")
    try:
        print(json.dumps(probe(), indent=2, sort_keys=True, allow_nan=False))
    except (ProbeBlocked, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
