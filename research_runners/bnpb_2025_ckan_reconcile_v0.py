# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline cross-resource reconciliation for two pinned BNPB 2025 CKAN JSON responses.

No network or XLSX inference. The 39th province resource row is a national total;
the 10th impact summary row is a national total. Neither is an observation.
The receipt cannot establish exact original XLSX bytes, licensing or admission.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys

PROVINCE_RESOURCE_ID = "43b83e79-c8b6-4b9a-b2f0-d1cbd9cfa636"
SUMMARY_RESOURCE_ID = "6e947c9c-2404-4c02-b743-34dc5320f399"
PERILS = (
    "BANJIR", "CUACA EKSTREM", "ERUPSI GUNUNG API",
    "GELOMBANG PASANG DAN ABRASI", "GEMPABUMI",
    "KEBAKARAN HUTAN DAN LAHAN", "KEKERINGAN", "TANAH LONGSOR", "TSUNAMI",
)
SEVERITY = ("Rumah Rusak Berat", "Rumah Rusak Sedang", "Rumah Rusak Ringan")
MAX_RESPONSE_BYTES = 128 * 1024


class BNPBReconciliationError(ValueError):
    """A provider resource, aggregation or count was unsafe or inconsistent."""


def _strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BNPBReconciliationError("duplicate JSON key")
        result[key] = value
    return result


def _bad_constant(value):
    raise BNPBReconciliationError("non-finite JSON number not allowed")


def _load(raw: bytes, expected_id: str, required: set[str], exact_rows: int) -> list[dict]:
    if type(raw) is not bytes or not 4 <= len(raw) <= MAX_RESPONSE_BYTES:
        raise BNPBReconciliationError("missing or oversized CKAN response")
    try:
        payload = json.loads(raw, object_pairs_hook=_strict_pairs,
                             parse_float=Decimal, parse_constant=_bad_constant)
    except (ValueError, UnicodeDecodeError) as exc:
        raise BNPBReconciliationError("invalid CKAN response JSON") from exc
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise BNPBReconciliationError("CKAN resource response not successful")
    result = payload.get("result")
    if not isinstance(result, dict) or result.get("resource_id") != expected_id:
        raise BNPBReconciliationError("wrong CKAN resource identity")
    records = result.get("records")
    if (not isinstance(result.get("total"), int) or type(result["total"]) is not int
        or result["total"] != exact_rows or not isinstance(records, list)
        or len(records) != exact_rows):
        raise BNPBReconciliationError("truncated, partial or unexpected CKAN row count")
    fields = result.get("fields")
    if not isinstance(fields, list) or not all(isinstance(x, dict) and isinstance(x.get("id"), str) for x in fields):
        raise BNPBReconciliationError("CKAN fields missing or malformed")
    names = [f["id"] for f in fields]
    if len(set(names)) != len(names) or not required <= set(names):
        raise BNPBReconciliationError("missing or duplicate required CKAN fields")
    if not all(isinstance(r, dict) and required <= r.keys() for r in records):
        raise BNPBReconciliationError("CKAN record missing required fields")
    return records


def _count(value, label: str) -> int:
    if value is None or isinstance(value, bool):
        raise BNPBReconciliationError("missing or boolean count in " + label)
    try:
        if isinstance(value, str) and not value.strip():
            raise InvalidOperation
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise BNPBReconciliationError("non-numeric count in " + label) from exc
    if not n.is_finite() or n < 0 or n != n.to_integral_value() or n > 1000000000:
        raise BNPBReconciliationError("fractional/negative/huge count in " + label)
    return int(n)


def reconcile(province_json: bytes, summary_json: bytes) -> dict:
    prow = _load(province_json, PROVINCE_RESOURCE_ID,
                 {"Provinsi", "Kode Wilayah Provinsi", *PERILS}, 39)
    srow = _load(summary_json, SUMMARY_RESOURCE_ID,
                 {"Jenis Bencana", "Jumlah Kejadian", *SEVERITY}, 10)

    province_sum = {peril: 0 for peril in PERILS}
    national = None
    seen_names: set[str] = set()
    seen_codes: set[int] = set()
    for record in prow:
        label = record["Provinsi"]
        if not isinstance(label, str) or not label.strip():
            raise BNPBReconciliationError("province label missing")
        label = label.strip().upper()
        counts = {p: _count(record[p], p) for p in PERILS}
        if label == "INDONESIA":
            if national is not None or record["Kode Wilayah Provinsi"] is not None:
                raise BNPBReconciliationError("duplicate/misclassified national province total")
            national = counts
            continue
        code = record["Kode Wilayah Provinsi"]
        if isinstance(code, bool) or code is None or _count(code, "province code") < 1:
            raise BNPBReconciliationError("invalid province code")
        code = _count(code, "province code")
        if label in seen_names or code in seen_codes:
            raise BNPBReconciliationError("duplicate province or geographic code")
        seen_names.add(label)
        seen_codes.add(code)
        for peril in PERILS:
            province_sum[peril] += counts[peril]
    if len(seen_names) != 38 or national is None:
        raise BNPBReconciliationError("missing national total or 38 distinct provinces")

    summary: dict[str, dict] = {}
    grand = None
    for record in srow:
        raw_label = record["Jenis Bencana"]
        if not isinstance(raw_label, str):
            raise BNPBReconciliationError("summary peril label missing")
        label = raw_label.strip().upper()
        counts = {k: _count(record[k], k) for k in ("Jumlah Kejadian", *SEVERITY)}
        if label == "TOTAL":
            if grand is not None:
                raise BNPBReconciliationError("duplicate summary grand total")
            grand = counts
            continue
        if label not in PERILS or label in summary:
            raise BNPBReconciliationError("unexpected/duplicate summary peril")
        summary[label] = counts
    if grand is None or set(summary) != set(PERILS):
        raise BNPBReconciliationError("incomplete summary perils or grand total")

    for peril in PERILS:
        severity_total = sum(summary[peril][k] for k in SEVERITY)
        if not (province_sum[peril] == national[peril] == severity_total):
            raise BNPBReconciliationError("province/national/severity mismatch for " + peril)
    for k in ("Jumlah Kejadian", *SEVERITY):
        if sum(summary[p][k] for p in PERILS) != grand[k]:
            raise BNPBReconciliationError("summary grand total mismatch for " + k)
    if sum(national.values()) != sum(grand[k] for k in SEVERITY):
        raise BNPBReconciliationError("national all-peril count does not match severity grand total")

    return {
        "evidence_class": "BNPB_2025_CKAN_JSON_CROSS_RESOURCE_RECONCILIATION_ONLY",
        "province_resource_id": PROVINCE_RESOURCE_ID,
        "summary_resource_id": SUMMARY_RESOURCE_ID,
        "province_response_sha256": hashlib.sha256(province_json).hexdigest(),
        "summary_response_sha256": hashlib.sha256(summary_json).hexdigest(),
        "province_observation_rows": len(seen_names),
        "national_total_rows_excluded": 1,
        "peril_observation_rows": len(summary),
        "summary_total_rows_excluded": 1,
        "all_nine_peril_and_severity_reconciliations_passed": True,
        "source_row_values_exported": False,
        "exact_original_xlsx_verified": False,
        "model_data_admitted": False,
        "licence_and_scientific_review_complete": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--province-json", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        for path in (args.province_json, args.summary_json):
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_RESPONSE_BYTES:
                raise BNPBReconciliationError("bounded regular source JSON file required")
        result = reconcile(args.province_json.read_bytes(), args.summary_json.read_bytes())
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, BNPBReconciliationError) as exc:
        print("BLOCKED: " + str(exc)[:200], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
