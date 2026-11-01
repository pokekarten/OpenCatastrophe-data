#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Run a single reviewed, fixed, read-only public-source capability probe.

NO arbitrary URL, host, query, data persistence, source admission or automated
bulk collection. The output is a small evidence receipt; actual provider data
are inspected transiently and are NEVER printed, stored or used for CAT models.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
# Exact routes taken from existing reviewed access/*.json probe contracts.
# Do not expand queries without updating the corresponding source contract.
PROBES = {
    "geoboundaries.gbopen": (
        "https://www.geoboundaries.org/api/current/gbOpen/DEU/ADM1/",
        "deu_adm1_metadata",
    ),
    "gfz.geomagnetic-kp": (
        "https://kp.gfz.de/app/json/?start=2024-01-01T00:00:00Z&"
        "end=2024-01-01T23:59:59Z&index=Kp&status=def",
        "definitive_kp_day_json",
    ),
    "noaa.swpc.real-time-solar-wind": (
        "https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json",
        "rtsw_mag_1m_json",
    ),
}


class ProbeBlocked(ValueError):
    """A source contract or provider response failed the safe capability gate."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeBlocked("redirect not allowed by fixed-source contract")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProbeBlocked("duplicate provider JSON key")
        result[key] = value
    return result


def _bad_number(value):
    raise ProbeBlocked("non-finite provider JSON numeric value")


def reviewed_probe(source: str, root: Path = ROOT):
    if source not in PROBES:
        raise ProbeBlocked("source not in the fixed reviewed probe allowlist")
    url, operation = PROBES[source]
    contract_path = root / "access" / (source + ".json")
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"),
                              object_pairs_hook=_unique_object,
                              parse_constant=_bad_number)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProbeBlocked("unavailable or invalid reviewed source contract") from exc
    if (contract.get("access_id") != source
            or contract.get("status") != "probe_ready"
            or contract.get("authentication", {}).get("mode") != "none"
            or contract.get("probe_contract", {}).get("requires_credentials") is not False
            or contract.get("probe_contract", {}).get("operation") != operation
            or contract.get("probe_contract", {}).get("mode") not in
            {"metadata_get", "catalogue_query", "provider_specific"}
            or operation not in contract.get("request_contract", {}).get("allowed_operations", [])
            or contract.get("rights_and_policy", {}).get("commercial_automation_status") != "allowed"):
        raise ProbeBlocked("reviewed probe, authentication or rights scope changed")
    request = urlsplit(url)
    root_url = urlsplit(contract.get("service_root", ""))
    if (request.scheme != "https" or root_url.scheme != "https"
            or request.netloc != root_url.netloc or request.username or request.password
            or request.fragment or root_url.query or root_url.fragment
            or request.path not in contract.get("request_contract", {}).get("path_templates", [])):
        raise ProbeBlocked("fixed endpoint diverges from source contract")
    max_bytes = contract.get("operational_constraints", {}).get("max_probe_bytes")
    timeout = contract.get("operational_constraints", {}).get("timeout_seconds")
    if not isinstance(max_bytes, int) or not 0 < max_bytes <= 4 * 1024 * 1024:
        raise ProbeBlocked("invalid probe byte bound")
    if not isinstance(timeout, int) or not 0 < timeout <= 60:
        raise ProbeBlocked("invalid timeout")
    return url, operation, max_bytes, timeout


def verify_response(source: str, raw: bytes) -> dict:
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                             parse_constant=_bad_number)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ProbeBlocked("provider response is not strict UTF-8 JSON") from exc
    if source == "geoboundaries.gbopen":
        if not isinstance(payload, dict):
            raise ProbeBlocked("geoBoundaries response is not a metadata object")
        if (payload.get("boundaryISO") != "DEU"
                or payload.get("boundaryType") != "ADM1"
                or payload.get("boundaryID") != "DEU-ADM1-10402087"
                or not isinstance(payload.get("boundaryLicense"), str)
                or not payload["boundaryLicense"].strip()
                or not isinstance(payload.get("licenseSource"), str)
                or not payload["licenseSource"].strip()):
            raise ProbeBlocked("geoBoundaries frozen canary identity/license drift")
        # Returned download links are intentionally not followed.
        return {"verified_shape": "deu_adm1_metadata", "frozen_id": payload["boundaryID"]}
    if source == "gfz.geomagnetic-kp":
        if not isinstance(payload, dict) or not payload:
            raise ProbeBlocked("GFZ response is not a nonempty JSON object")
        # A structural probe does not assert scientific Kp content or calibration.
        return {"verified_shape": "json_object_only", "scientific_values_verified": False}
    if source == "noaa.swpc.real-time-solar-wind":
        if not isinstance(payload, (list, dict)) or not payload:
            raise ProbeBlocked("NOAA response is not a nonempty JSON collection")
        return {"verified_shape": "json_collection_only", "sensor_lineage_verified": False}
    raise ProbeBlocked("unknown source")


def probe(source: str, *, root: Path = ROOT, opener=None) -> dict:
    url, operation, max_bytes, timeout = reviewed_probe(source, root)
    # No caller supplied path/headers/query, no redirect or retry. No response is
    # written to disk. Keep response values out of the log/receipt.
    client = opener if opener is not None else build_opener(NoRedirect())
    request = Request(url, headers={"Accept": "application/json",
                                   "User-Agent": "OpenCatastrophe-public-probe/0.1"},
                      method="GET")
    try:
        with client.open(request, timeout=timeout) as response:
            if response.status != 200:
                raise ProbeBlocked("provider status not 200")
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in {"application/json", "application/geo+json"}:
                raise ProbeBlocked("unexpected provider media type")
            size_header = response.headers.get("Content-Length")
            if size_header is not None:
                try:
                    declared = int(size_header)
                except ValueError as exc:
                    raise ProbeBlocked("invalid content length") from exc
                if declared < 0 or declared > max_bytes:
                    raise ProbeBlocked("provider content length exceeds fixed bound")
            raw = response.read(max_bytes + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ProbeBlocked("bounded HTTPS probe unavailable") from exc
    if not raw or len(raw) > max_bytes:
        raise ProbeBlocked("provider response empty or exceeds fixed bound")
    result = verify_response(source, raw)
    return {
        "profile": "opencatastrophe-fixed-source-capability-v0",
        "source": source,
        "operation": operation,
        "retrieval_utc": datetime.now(timezone.utc).isoformat(),
        "request_sha256": hashlib.sha256(url.encode("ascii")).hexdigest(),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
        "content_type": content_type,
        **result,
        "provider_bytes_persisted": False,
        "model_input_approved": False,
        "data_source_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, choices=sorted(PROBES))
    args = parser.parse_args(argv)
    try:
        receipt = probe(args.source)
    except ProbeBlocked as exc:
        print(json.dumps({"source": args.source, "status": "BLOCKED",
                          "reason": str(exc), "model_input_approved": False}),
              file=sys.stderr)
        return 1
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
