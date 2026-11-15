#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One explicitly requested bounded OpenFEMA public API smoke probe.

No arbitrary URL, credentials, pagination, full dataset download or source
admission. Provider data is validated in RAM and discarded. Return a SHA-256
receipt only. Terms permit statistical research/reporting, not reidentification
or individual eligibility/underwriting decisions.

No live traffic in unit tests or routine CI. Live calls require --live.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


API = "https://www.fema.gov"
MAX_BYTES = 8192
PROBES = {
    "fema.openfema.nfip-residential-penetration-rates.v1": (
        "/api/open/v1/NfipResidentialPenetrationRates?$top=2",
        "NfipResidentialPenetrationRates", "v1"
    ),
    "fema.openfema.disaster-declarations-summaries.v2": (
        "/api/open/v2/DisasterDeclarationsSummaries?$top=2",
        "DisasterDeclarationsSummaries", "v2"
    ),
}
TERMS = "https://www.fema.gov/about/openfema/terms-conditions"


class SourceError(ValueError):
    """Fail closed on provider identity, boundary or shape changes."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SourceError("redirect forbidden")


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SourceError("duplicate provider JSON property")
        result[key] = value
    return result


def _finite(value):
    raise SourceError("non-finite JSON number")


def validate_response(source_id: str, raw: bytes) -> dict:
    if source_id not in PROBES:
        raise SourceError("unreviewed source identifier")
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise SourceError("response byte limit")
    path, entity, version = PROBES[source_id]
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                         parse_constant=_finite)
    except (UnicodeDecodeError, ValueError) as exc:
        raise SourceError("response not strict UTF-8 JSON") from exc
    if not isinstance(doc, dict) or set(doc) != {"metadata", entity}:
        raise SourceError("wrong response entity")
    meta = doc["metadata"]
    if not isinstance(meta, dict) or (meta.get("entityname") != entity
            or meta.get("version") != version or meta.get("top") != 2
            or meta.get("format") != "json" or meta.get("url") != path
            or meta.get("skip") != 0):
        raise SourceError("wrong version, request or response metadata")
    rows = doc[entity]
    if not isinstance(rows, list) or len(rows) != 2:
        raise SourceError("not exactly two records")
    seen = set()
    abnormal_ratio = 0
    missing_denominators = 0
    for row in rows:
        if not isinstance(row, dict):
            raise SourceError("row must be JSON object")
        identity = row.get("id")
        if not isinstance(identity, str) or not identity or identity in seen:
            raise SourceError("missing or duplicate provider record")
        seen.add(identity)
        if entity == "NfipResidentialPenetrationRates":
            fips = row.get("fipsCode")
            if (not isinstance(fips, str) or not re.fullmatch(r"\d{5}", fips)
                    or not isinstance(row.get("state"), str)
                    or not isinstance(row.get("county"), str)
                    or not isinstance(row.get("asOfDate"), str)):
                raise SourceError("NFIP county identity drift")
            for field in ("resPenetrationRate", "resPenetrationRateSfha"):
                value = row.get(field)
                if value is not None:
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        raise SourceError("NFIP ratio has invalid type")
                    if not math.isfinite(value) or value < 0:
                        raise SourceError("NFIP ratio invalid")
                    abnormal_ratio += int(value > 1)
            for field in ("totalResStructures", "totalResStructuresSfha",
                          "resContractsInForce", "resContractsInForceSfha"):
                val = row.get(field)
                if val is None:
                    if field.startswith("totalResStructures"):
                        missing_denominators += 1
                elif isinstance(val, bool) or not isinstance(val, int) or val < 0:
                    raise SourceError("NFIP count invalid")
        else:
            if (isinstance(row.get("disasterNumber"), bool)
                    or not isinstance(row.get("disasterNumber"), int)
                    or row["disasterNumber"] < 1
                    or not isinstance(row.get("state"), str)
                    or not row["state"]
                    or not isinstance(row.get("designatedArea"), str)
                    or not isinstance(row.get("incidentType"), str)):
                raise SourceError("declaration metadata drift")
    return {
        "source_id": source_id,
        "profile": "openfema-exact-two-public-rows-source-probe-v0",
        "entity": entity,
        "version": version,
        "rows": 2,
        "response_bytes": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "ratio_over_100pct_field_count": abnormal_ratio if version == "v1" else None,
        "missing_structure_denominator_fields": missing_denominators if version == "v1" else None,
        "fema_terms": TERMS,
        "provider_data_bytes_persisted": False,
        "model_input_approved": False,
        "commercial_underwriting_authorized": False,
        "individual_decision_authorized": False,
    }


def probe(source_id: str, opener=None) -> dict:
    if source_id not in PROBES:
        raise SourceError("source not in fixed allowlist")
    path, _, _ = PROBES[source_id]
    url = API + path
    client = opener if opener is not None else build_opener(NoRedirect(), ProxyHandler({}))
    req = Request(url, method="GET",
                  headers={"Accept": "application/json",
                           "User-Agent": "OpenCatastrophe-research-canary/0.1"})
    try:
        with client.open(req, timeout=25) as response:
            if response.status != 200:
                raise SourceError("unexpected HTTP status")
            ctype = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if ctype != "application/json":
                raise SourceError("unexpected response content type")
            clen = response.headers.get("Content-Length")
            if clen is not None and (not clen.isdecimal() or int(clen) > MAX_BYTES):
                raise SourceError("invalid or oversized content length")
            raw = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SourceError("bounded provider request unavailable") from exc
    result = validate_response(source_id, raw)
    result["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["request_sha256"] = hashlib.sha256(url.encode("ascii")).hexdigest()
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, choices=sorted(PROBES))
    parser.add_argument("--live", action="store_true",
                        help="opt in to a single original provider GET")
    args = parser.parse_args(argv)
    if not args.live:
        print("BLOCKED: --live explicitly required; offline by default",
              file=sys.stderr)
        return 2
    try:
        receipt = probe(args.source)
    except SourceError as exc:
        print(json.dumps({"source_id": args.source, "status": "BLOCKED",
                          "reason": str(exc), "model_input_approved": False}),
              file=sys.stderr)
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
