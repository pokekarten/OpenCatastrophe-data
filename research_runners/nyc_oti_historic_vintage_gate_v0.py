# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Read-only NYC historic-feature canary: NOT a year-2024 inventory.

Queries only original NYC Socrata fixed count(*) expressions plus a pinned
30-property LL84 identifier cohort. Holds those public IDs in RAM only.
Fails closed on API transport, source drift, duplicate keys, truncation and
incomplete results; NEVER equates absent historic features to 2024 presence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

HOST = "data.cityofnewyork.us"
HISTORIC_VIEW = "ipkp-snf6"
LL84_VIEW = "5zyy-y8am"
N = 30
BATCH = 5
MAX_JSON_BYTES = 24_000
BIN = re.compile(r"[1-5][0-9]{6}\Z")
BBL = re.compile(r"[1-5][0-9]{9}\Z")
DIGITS = re.compile(r"[0-9]+\Z")
LL84_FIELDS = ("property_id", "nyc_borough_block_and_lot",
               "nyc_building_identification", "report_year")
PLACEHOLDER_BINS = (1000000, 2000000, 3000000, 4000000, 5000000)
METRICS = {
    "historic_all_rows": None,
    "historic_doitt_zero_rows": "doitt_id = 0",
    "historic_placeholder_million_bin_rows": (
        "bin in (" + ",".join(str(x) for x in PLACEHOLDER_BINS) + ")"
    ),
    "historic_demolition_year_2024_rows": "demolition_year = 2024",
    "historic_demolition_year_2025_rows": "demolition_year = 2025",
    "historic_demolition_year_present_rows": "demolition_year is not null",
    "historic_last_edited_2025_or_later_rows": (
        "last_edited_date >= '2025-01-01T00:00:00'"
    ),
}


class HistoricError(ValueError):
    pass


class HistoricTransportError(HistoricError):
    """Only a transport error authorizes bounded per-BIN retry."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HistoricError("source redirected; provider identity requires review")


def _url(view: str, params: dict[str, str]) -> str:
    if view not in {HISTORIC_VIEW, LL84_VIEW}:
        raise HistoricError("unexpected original NYC source")
    return f"https://{HOST}/resource/{view}.json?{urlencode(params)}"


def metric_queries() -> dict[str, str]:
    result = {}
    for name, clause in METRICS.items():
        values = {"$select": "count(*)"}
        if clause is not None:
            values["$where"] = clause
        result[name] = _url(HISTORIC_VIEW, values)
    return result


def ll84_query() -> str:
    return _url(LL84_VIEW, {
        "$select": ",".join(LL84_FIELDS),
        "$where": "report_year = 2024 AND nyc_borough_block_and_lot like '1000%'",
        "$order": "property_id ASC",
        "$limit": str(N),
    })


def historic_bin_count_query(bin_values: tuple[str, ...]) -> str:
    if type(bin_values) is not tuple or not 1 <= len(bin_values) <= BATCH:
        raise HistoricError("BIN group must contain 1 to 5 IDs")
    if len(set(bin_values)) != len(bin_values) or any(
        type(b) is not str or not BIN.fullmatch(b) or b[1:] == "000000"
        for b in bin_values
    ):
        raise HistoricError("invalid, duplicated or placeholder BIN")
    return _url(HISTORIC_VIEW, {
        "$select": "count(*)",
        "$where": "bin in(" + ",".join(bin_values) + ")",
    })


def _fetch(url: str) -> bytes:
    parts = urlsplit(url)
    if (parts.scheme, parts.hostname, parts.username, parts.password) != (
        "https", HOST, None, None
    ) or parts.path not in (
        f"/resource/{HISTORIC_VIEW}.json",
        f"/resource/{LL84_VIEW}.json",
    ):
        raise HistoricError("provider URL outside pinned original NYC HTTPS views")
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "OpenCatastrophe-NYC-historic-feature-canary/0",
    })
    try:
        with build_opener(_NoRedirect()).open(request, timeout=18) as response:
            if response.status != 200 or response.headers.get_content_type() != "application/json":
                raise HistoricError("source did not return HTTP 200 JSON")
            raw = response.read(MAX_JSON_BYTES + 1)
    except (OSError, TimeoutError) as exc:
        raise HistoricTransportError(
            "original-source transport failure; cannot infer zero matches"
        ) from exc
    if len(raw) > MAX_JSON_BYTES:
        raise HistoricError("provider response exceeds fixed budget")
    return raw


def _decode(raw: bytes) -> object:
    if type(raw) is not bytes or len(raw) > MAX_JSON_BYTES:
        raise HistoricError("oversized or nonbyte source response")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise HistoricError("malformed source JSON") from exc


def parse_count(raw: bytes) -> int:
    obj = _decode(raw)
    if type(obj) is not list or len(obj) != 1 or type(obj[0]) is not dict:
        raise HistoricError("count query returned unexpected row set")
    if set(obj[0]) != {"count"} or type(obj[0]["count"]) is not str:
        raise HistoricError("count-only response required; no raw data")
    value = obj[0]["count"]
    if not DIGITS.fullmatch(value):
        raise HistoricError("count must be exact nonnegative integer text")
    count = int(value)
    if count > 10_000_000:
        raise HistoricError("source count exceeds research guardrail")
    return count


def parse_cohort(raw: bytes) -> tuple[str, ...]:
    rows = _decode(raw)
    if type(rows) is not list or len(rows) != N or any(type(r) is not dict for r in rows):
        raise HistoricError("expected exactly 30 original LL84 rows")
    props = set()
    bins = set()
    for r in rows:
        if set(r) != set(LL84_FIELDS):
            raise HistoricError("unexpected or missing LL84 projected field")
        pid, bbl, b, year = (
            r["property_id"], r["nyc_borough_block_and_lot"],
            r["nyc_building_identification"], r["report_year"],
        )
        if (type(pid) is not str or not DIGITS.fullmatch(pid) or pid in props
            or type(bbl) is not str or not BBL.fullmatch(bbl)
            or not bbl.startswith("1000")
            or type(b) is not str or not BIN.fullmatch(b)
            or b[1:] == "000000" or b in bins or year != "2024"):
            raise HistoricError("invalid or ambiguous 2024 LL84 convenience cohort")
        props.add(pid)
        bins.add(b)
    return tuple(sorted(bins))


def summarize_counts(metric_counts: dict[str, int], cohort_historic_rows: int) -> dict:
    if type(metric_counts) is not dict or set(metric_counts) != set(METRICS):
        raise HistoricError("missing original metric results")
    if any(type(value) is not int or not 0 <= value <= 10_000_000
           for value in metric_counts.values()):
        raise HistoricError("malformed original metric count")
    if type(cohort_historic_rows) is not int or cohort_historic_rows < 0:
        raise HistoricError("invalid cohort historic count")
    total = metric_counts["historic_all_rows"]
    if total == 0 or cohort_historic_rows > total:
        raise HistoricError("source counts are inconsistent")
    if any(value > total for value in metric_counts.values()):
        raise HistoricError("subset count exceeds historic-source total")
    if (metric_counts["historic_demolition_year_2024_rows"]
        + metric_counts["historic_demolition_year_2025_rows"]
        > metric_counts["historic_demolition_year_present_rows"]):
        raise HistoricError("exclusive demolition years exceed known years")
    if metric_counts["historic_demolition_year_present_rows"] > total:
        raise HistoricError("invalid demolition-year denominator")
    return {
        "profile": "nyc-original-historic-feature-and-2024-vintage-gate-v0",
        "original_source": "NYC OTI BUILDING_HISTORIC ipkp-snf6",
        "reported_aggregate_counts": dict(sorted(metric_counts.items())),
        "ll84_2024_convenience_cohort_bin_count": N,
        "historic_source_feature_rows_for_30_bins": cohort_historic_rows,
        "historical_feature_archive_is_complete_2024_building_stock": False,
        "historic_last_edit_is_demolition_date": False,
        "historical_inventory_2024_snapshot_bytes_acquired": False,
        "historical_inventory_2024_verified": False,
        "historical_2024_building_presence_inferred": False,
        "source_rights_or_model_admission_approved": False,
        "insured_tiv_or_loss_calculated": False,
        "raw_original_property_ids_or_bins_exported": False,
    }


def run_live(fetch=_fetch) -> dict:
    metrics = {name: parse_count(fetch(url)) for name, url in metric_queries().items()}
    bins = parse_cohort(fetch(ll84_query()))
    found = 0
    for i in range(0, N, BATCH):
        batch = bins[i:i + BATCH]
        try:
            found += parse_count(fetch(historic_bin_count_query(batch)))
        except HistoricTransportError:
            # Distinguish source timeouts from true zero matches; every single
            # BIN must respond or the entire output is blocked.
            for b in batch:
                found += parse_count(fetch(historic_bin_count_query((b,))))
    return summarize_counts(metrics, found)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Opt in to fixed public original NYC aggregate-only queries")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network access requires explicit --live")
    try:
        print(json.dumps(run_live(), sort_keys=True, separators=(",", ":")))
        return 0
    except HistoricError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
