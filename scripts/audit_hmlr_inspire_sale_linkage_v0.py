# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, bounded, aggregate-only HMLR transaction→freehold-polygon QA.

Input is intentionally a tiny, stripped *analysis-only* table: no addresses,
people, title numbers, ownership, geometries, or ground-truth policy records.
The candidate sources are not admitted and this code does not grant data rights.

It tests one important failure mode: a sale with two INSPIRE polygons must NOT
count as two independent sales or be treated as two insured values.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import sys

MAX_FILE_BYTES = 2_000_000
MAX_RECORDS = 5000
FAMILY = "uk.hmlr.price-paid-to-inspire-freehold"


class CadastralLinkageError(ValueError):
    """A record is malformed, unbounded or unsafe for this diagnostic."""


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CadastralLinkageError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite(value):
    raise CadastralLinkageError("nonfinite JSON value")


def load(path):
    path = Path(path)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise CadastralLinkageError("input exceeds 2 MB bound")
    try:
        return json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=_strict_object, parse_constant=_reject_nonfinite)
    except (ValueError, OSError, UnicodeError) as exc:
        raise CadastralLinkageError("invalid input JSON") from exc


def _record(raw, allowed, label):
    if not isinstance(raw, dict) or set(raw) != allowed:
        raise CadastralLinkageError(f"{label}: unexpected or missing field")
    return raw


def _id(value, label):
    if not isinstance(value, str) or not value or len(value) > 80 or value.strip() != value:
        raise CadastralLinkageError(f"{label}: invalid identifier")
    if any(ord(ch) < 33 or ord(ch) > 126 for ch in value):
        raise CadastralLinkageError(f"{label}: identifier must be printable ASCII")
    return value


def _date(value, label):
    if not isinstance(value, str) or len(value) != 10:
        raise CadastralLinkageError(f"{label}: expected ISO date")
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError("noncanonical date")
    except ValueError as exc:
        raise CadastralLinkageError(f"{label}: invalid date") from exc
    return parsed


def _rows(value, label):
    if not isinstance(value, list) or len(value) > MAX_RECORDS:
        raise CadastralLinkageError(f"{label}: invalid bounded row array")
    return value


def audit(payload):
    """Return strictly aggregated diagnostic statistics; never individual links."""
    obj = _record(payload, {"source_family", "snapshot_date", "transactions", "lookup", "polygons"}, "payload")
    if obj["source_family"] != FAMILY:
        raise CadastralLinkageError("source family not supported by this exact diagnostic")
    as_of = _date(obj["snapshot_date"], "snapshot_date")

    sales = {}
    for raw in _rows(obj["transactions"], "transactions"):
        row = _record(raw, {"transaction_uid", "sale_date", "price_gbp"}, "transaction")
        uid = _id(row["transaction_uid"], "transaction_uid")
        if uid in sales:
            raise CadastralLinkageError("duplicate transaction UID")
        if _date(row["sale_date"], "sale_date") > as_of:
            raise CadastralLinkageError("future transaction relative to source snapshot")
        price = row["price_gbp"]
        if type(price) is not int or price <= 0 or price > 1_000_000_000_000:
            raise CadastralLinkageError("price_gbp must be bounded positive integer")
        sales[uid] = price

    polygon_ids = set()
    for raw in _rows(obj["polygons"], "polygons"):
        row = _record(raw, {"inspire_id"}, "polygon")
        pid = _id(row["inspire_id"], "inspire_id")
        if pid in polygon_ids:
            raise CadastralLinkageError("duplicate INSPIRE polygon ID")
        polygon_ids.add(pid)

    links = defaultdict(set)
    exact_duplicate = 0
    orphan_transaction = 0
    missing_polygon = 0
    for raw in _rows(obj["lookup"], "lookup"):
        row = _record(raw, {"transaction_uid", "inspire_id"}, "lookup")
        uid = _id(row["transaction_uid"], "lookup.transaction_uid")
        pid = _id(row["inspire_id"], "lookup.inspire_id")
        if uid not in sales:
            orphan_transaction += 1
            continue
        if pid not in polygon_ids:
            missing_polygon += 1
            continue
        if pid in links[uid]:
            exact_duplicate += 1
        links[uid].add(pid)

    matched = {uid: ids for uid, ids in links.items() if ids}
    distinct_value = sum(sales[uid] for uid in matched)
    naive_value = sum(sales[uid] * len(ids) for uid, ids in matched.items())
    if naive_value < distinct_value:
        raise CadastralLinkageError("internal sum invariant broken")
    return {
        "schema": "hmlr-freehold-sale-linkage-qa-v0",
        "analysis_only": True,
        "source_admitted": False,
        "may_feed_cat_model": False,
        "value_is_insured_tiv": False,
        "value_is_rebuilding_cost": False,
        "snapshot_date": as_of.isoformat(),
        "distinct_transaction_count": len(sales),
        "registered_freehold_polygon_count": len(polygon_ids),
        "matched_transaction_count": len(matched),
        "unmatched_transaction_count": len(sales) - len(matched),
        "validated_lookup_link_count": sum(len(ids) for ids in matched.values()),
        "multi_polygon_transaction_count": sum(len(ids) > 1 for ids in matched.values()),
        "duplicate_lookup_rows_suppressed": exact_duplicate,
        "lookup_rows_without_sale": orphan_transaction,
        "lookup_rows_without_polygon": missing_polygon,
        "matched_sale_price_once_gbp": distinct_value,
        "incorrect_sale_price_if_allocated_to_all_polygons_gbp": naive_value,
        "potential_overcount_from_naive_polygon_join_gbp": naive_value - distinct_value,
        "ready_for_ownership_or_policy_inference": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = audit(load(args.input))
    except (CadastralLinkageError, OSError) as exc:
        print("INVALID_INPUT: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
