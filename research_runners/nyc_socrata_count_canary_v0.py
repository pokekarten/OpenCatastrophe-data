# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Read-only, aggregate-only original NYC Socrata source-access canary.

A canary result checks provider API accessibility and reported row classes.
It never downloads individual PLUTO/LL84 records, creates building matches,
approves source rights, infers insured values, or writes a database.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

HOST = "data.cityofnewyork.us"
PLUTO_VIEW = "64uk-42ks"
LL84_VIEW = "5zyy-y8am"
MAX_RESPONSE_BYTES = 4096
MAX_COUNT = 100_000_000
YEAR = 2024

CONDITIONS = {
    "multi_bbl": "nyc_borough_block_and_lot like '%;%'",
    "multi_bin": "nyc_building_identification like '%;%'",
    "missing_bbl_literal": "nyc_borough_block_and_lot = 'Not Available'",
    "missing_bin_literal": "nyc_building_identification = 'Not Available'",
}


class CanaryError(ValueError):
    """A source identity, transport or response contract was violated."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CanaryError("source redirected: review new identity before fetching")


def queries() -> dict[str, str]:
    """Return deterministic, non-user-configurable GET URLs for counts only."""
    base = f"https://{HOST}/resource/"
    ll84_where = f"report_year = {YEAR}"
    def make(view: str, where: str | None = None) -> str:
        params = {"$select": "count(*)"}
        if where is not None:
            params["$where"] = where
        return f"{base}{view}.json?{urlencode(params)}"

    result = {
        "pluto_total": make(PLUTO_VIEW),
        "ll84_2024_total": make(LL84_VIEW, ll84_where),
    }
    for key, condition in CONDITIONS.items():
        result[key] = make(LL84_VIEW, f"{ll84_where} AND {condition}")
    union = " OR ".join(f"({condition})" for condition in CONDITIONS.values())
    result["any_of_four_special_cases"] = make(LL84_VIEW, f"{ll84_where} AND ({union})")
    return result


def validate_query_url(url: str) -> None:
    """Defence in depth: do not accept a custom endpoint or row-level query."""
    allowed = set(queries().values())
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != HOST or url not in allowed:
        raise CanaryError("not a pinned NYC Socrata aggregate-only endpoint")


def fetch_count(url: str) -> bytes:
    validate_query_url(url)
    opener = build_opener(_NoRedirect())
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "OpenCatastrophe-research-count-canary/0"})
    try:
        with opener.open(request, timeout=20) as response:
            if response.status != 200:
                raise CanaryError("provider did not return HTTP 200")
            if response.headers.get_content_type() != "application/json":
                raise CanaryError("provider did not return JSON media type")
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, TimeoutError) as exc:
        raise CanaryError(f"provider request failed: {type(exc).__name__}") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        raise CanaryError("aggregate JSON response exceeds strict byte cap")
    return body


def parse_count(raw: bytes) -> int:
    if type(raw) is not bytes or len(raw) > MAX_RESPONSE_BYTES:
        raise CanaryError("unbounded or nonbyte JSON response")
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CanaryError("malformed count response") from exc
    if type(result) is not list or len(result) != 1 or type(result[0]) is not dict or set(result[0]) != {"count"}:
        raise CanaryError("expected one aggregate-only row with count")
    value = result[0]["count"]
    if type(value) is not str or not re.fullmatch(r"[0-9]+", value):
        raise CanaryError("count must be an integer encoded as decimal text")
    count = int(value)
    if count > MAX_COUNT:
        raise CanaryError("count exceeds guardrail")
    return count


def analyze_counts(counts: dict[str, int]) -> dict:
    required = set(queries())
    if type(counts) is not dict or set(counts) != required or any(
        type(value) is not int or value < 0 or value > MAX_COUNT for value in counts.values()
    ):
        raise CanaryError("missing or malformed named count")
    total = counts["ll84_2024_total"]
    union = counts["any_of_four_special_cases"]
    categories = {key: counts[key] for key in CONDITIONS}
    if counts["pluto_total"] <= 0 or total <= 0:
        raise CanaryError("source total must be positive to consider API accessible")
    if union > total or any(value > union for value in categories.values()) or union > sum(categories.values()):
        raise CanaryError("impossible overlap/union count relation")
    return {
        "profile": "nyc-socrata-count-canary-v0",
        "query_year": YEAR,
        "pluto_release_expected": "26v2",
        "source_scope": "aggregate_only_public_metadata_non_admission",
        "counts": {
            "pluto_taxlot_rows": counts["pluto_total"],
            "ll84_property_year_rows": total,
            "individual_overlapping_categories": categories,
            "ll84_rows_with_any_four_special_case": union,
        },
        "special_cases_can_overlap": True,
        "ll84_covers_entire_building_stock": False,
        "building_identity_proven": False,
        "model_input_admitted": False,
        "insured_tiv_or_loss_calculated": False,
        "raw_source_rows_downloaded": False,
    }


def run_canary(fetch=fetch_count) -> dict:
    counts = {key: parse_count(fetch(url)) for key, url in queries().items()}
    return analyze_counts(counts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Explicitly perform seven read-only, counts-only GET requests")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("requires explicit --live; no requests by default")
    try:
        print(json.dumps(run_canary(), sort_keys=True, separators=(",", ":")))
        return 0
    except CanaryError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
