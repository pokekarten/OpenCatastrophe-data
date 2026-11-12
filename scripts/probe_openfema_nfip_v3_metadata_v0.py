#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fixed metadata-only canary for two high-sensitivity OpenFEMA NFIP v3 APIs.

Only one anonymous, single-column response per named source. Provider source
values must never escape as logs/outputs or be retained. $top=0 is NOT SAFE:
OpenFEMA treats it as an absent cap and may return a large default page.

Manual --live opt-in only. This tests schema/reachability, never copyright,
commercial entitlement, full-source availability or CAT model admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, HTTPRedirectHandler, ProxyHandler, build_opener

ROOT = "https://www.fema.gov"
MAX_BYTES = 2048
PROBES = {
    "fema.openfema.nfip-redacted-claims.v3": (
        "/api/open/v3/NfipClaims?$top=1&$select=yearOfLoss",
        "NfipClaims", "yearOfLoss",
    ),
    "fema.openfema.nfip-redacted-policies.v3": (
        "/api/open/v3/NfipPolicies?$top=1&$select=policyEffectiveDate",
        "NfipPolicies", "policyEffectiveDate",
    ),
}


class SourceBlocked(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SourceBlocked("redirect not permitted")


def _object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise SourceBlocked("duplicate JSON key")
        out[key] = value
    return out


def _constant(value):
    raise SourceBlocked("non-finite JSON number")


def check_response(source_id: str, raw: bytes) -> dict:
    if source_id not in PROBES:
        raise SourceBlocked("unknown source")
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise SourceBlocked("empty or oversized provider response")
    path, entity, column = PROBES[source_id]
    try:
        body = json.loads(raw.decode("utf-8"), parse_constant=_constant,
                          object_pairs_hook=_object)
    except (UnicodeDecodeError, ValueError) as exc:
        raise SourceBlocked("invalid strict JSON") from exc
    if not isinstance(body, dict) or set(body) != {"metadata", entity}:
        raise SourceBlocked("unexpected provider envelope")
    meta = body["metadata"]
    if not isinstance(meta, dict) or any((
        meta.get("version") != "v3",
        meta.get("entityname") != entity,
        meta.get("url") != path,
        meta.get("top") != 1,
        meta.get("skip") != 0,
        meta.get("select") != column,
        meta.get("format") != "json",
    )):
        raise SourceBlocked("provider metadata/version/request identity drift")
    rows = body[entity]
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise SourceBlocked("expected only one selected source field")
    if set(rows[0]) != {column}:
        raise SourceBlocked("unexpected extra or missing field; possible PII leak")
    # Validate only the selected data type. Never return the source value.
    value = rows[0][column]
    if column == "yearOfLoss":
        if isinstance(value, bool) or (value is not None and
            (not isinstance(value, int) or not 1970 <= value <= 2100)):
            raise SourceBlocked("unexpected loss-year type")
    elif value is not None and (not isinstance(value, str)
                                or not re.match(r"^\d{4}-\d{2}-\d{2}", value)):
        raise SourceBlocked("unexpected policy effective-date type")
    return {
        "source_id": source_id,
        "profile": "openfema-nfip-v3-one-field-metadata-only-canary-v0",
        "source_version": "v3",
        "provider_entity": entity,
        "selected_field_name": column,
        "row_count": 1,
        "response_bytes": len(raw),
        "original_response_sha256": hashlib.sha256(raw).hexdigest(),
        "value_exported": False,
        "provider_raw_response_persisted": False,
        "model_input_approved": False,
        "commercial_underwriting_authorized": False,
    }


def probe(source_id: str, opener=None):
    if source_id not in PROBES:
        raise SourceBlocked("source is not allowlisted")
    path, _, _ = PROBES[source_id]
    client = opener if opener is not None else build_opener(NoRedirect(), ProxyHandler({}))
    request = Request(ROOT + path, method="GET",
                      headers={"Accept": "application/json",
                               "User-Agent": "OpenCatastrophe-safe-research-canary/0.1"})
    try:
        with client.open(request, timeout=25) as response:
            if response.status != 200:
                raise SourceBlocked("unexpected provider HTTP status")
            ctype = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if ctype != "application/json":
                raise SourceBlocked("unexpected media type")
            declared = response.headers.get("Content-Length")
            if declared is not None and (not declared.isdecimal() or int(declared) > MAX_BYTES):
                raise SourceBlocked("oversized declared response")
            raw = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SourceBlocked("bounded original API request failed") from exc
    result = check_response(source_id, raw)
    result["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["request_sha256"] = hashlib.sha256((ROOT + path).encode("ascii")).hexdigest()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(PROBES), required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live:
        print("BLOCKED: explicit --live required", file=sys.stderr)
        return 2
    try:
        result = probe(args.source)
    except SourceBlocked as exc:
        print(json.dumps({"source_id": args.source, "status": "BLOCKED",
                          "reason": str(exc), "model_input_approved": False}),
              file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
