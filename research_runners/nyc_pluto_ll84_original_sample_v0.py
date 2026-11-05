# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded NYC PLUTO 26v2 x LL84 2024 original-row research smoke test.

Explicit --live only; public IDs stay in memory and are never printed,
stored, uploaded, merged into exposure, or treated as insured risks.
The first 30 ascending LL84 property IDs from BBL prefix 1000 are a
deterministic *nonrepresentative* Manhattan cohort, not a random sample.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

HOST = "data.cityofnewyork.us"
LL84_VIEW = "5zyy-y8am"
PLUTO_VIEW = "64uk-42ks"
N = 30
CHUNK = 5
MAX_BYTES = 32768
BBL = re.compile(r"[1-5][0-9]{9}\Z")
BIN = re.compile(r"[1-5][0-9]{6}\Z")
RAW_PLUTO_BBL = re.compile(r"([1-5][0-9]{9})(?:\.0+)?\Z")
LL84_COLUMNS = (
    "property_id", "nyc_borough_block_and_lot",
    "nyc_building_identification", "parent_property_id",
    "number_of_buildings", "report_year",
)


class SampleError(ValueError):
    """The original source or semantic matching contract failed closed."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SampleError("original-source redirect blocked")


def _url(view: str, parameters: dict[str, str]) -> str:
    if view not in (LL84_VIEW, PLUTO_VIEW):
        raise SampleError("unrecognised original NYC view")
    return f"https://{HOST}/resource/{view}.json?{urlencode(parameters)}"


def ll84_url() -> str:
    return _url(LL84_VIEW, {
        "$select": ",".join(LL84_COLUMNS),
        "$where": "report_year = 2024 AND nyc_borough_block_and_lot like '1000%'",
        "$order": "property_id ASC",
        "$limit": str(N),
    })


def pluto_url(bbls: tuple[str, ...]) -> str:
    if not 1 <= len(bbls) <= CHUNK or any(not BBL.fullmatch(b) for b in bbls):
        raise SampleError("PLUTO query requires one to five canonical BBLs")
    if len(bbls) != len(set(bbls)):
        raise SampleError("duplicate BBL in query")
    return _url(PLUTO_VIEW, {
        "$select": "bbl,numbldgs",
        "$where": "bbl in (" + ",".join(bbls) + ")",
        "$limit": str(len(bbls)),
    })


def _original_get(url: str) -> bytes:
    parts = urlsplit(url)
    if (parts.scheme, parts.hostname, parts.username, parts.password) != ("https", HOST, None, None):
        raise SampleError("original NYC HTTPS host required")
    if parts.path not in (f"/resource/{LL84_VIEW}.json", f"/resource/{PLUTO_VIEW}.json"):
        raise SampleError("unrecognised original NYC resource path")
    try:
        req = Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "OpenCatastrophe-research-nyc-30row-smoke/0",
        })
        with build_opener(_NoRedirect()).open(req, timeout=15) as response:
            if response.status != 200 or response.headers.get_content_type() != "application/json":
                raise SampleError("original source did not return JSON HTTP 200")
            content = response.read(MAX_BYTES + 1)
    except (OSError, TimeoutError) as exc:
        raise SampleError(f"original source request failed: {type(exc).__name__}") from exc
    if len(content) > MAX_BYTES:
        raise SampleError("original source response exceeded byte cap")
    return content


def _parse_rows(raw: bytes, cap: int) -> list[dict]:
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise SampleError("invalid or oversized source response")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SampleError("malformed source JSON") from exc
    if type(obj) is not list or len(obj) > cap or any(type(r) is not dict for r in obj):
        raise SampleError("source returned unexpected row shape")
    return obj


def canonical_pluto_bbl(raw: object) -> str:
    """Reject fractional/rounded IDs; strip only a decimal all-zero suffix."""
    if type(raw) is not str:
        raise SampleError("PLUTO BBL is not original numeric text")
    match = RAW_PLUTO_BBL.fullmatch(raw)
    if match is None:
        raise SampleError("PLUTO BBL cannot be normalized losslessly")
    return match.group(1)


def summarize(ll84: list[dict], pluto: list[dict]) -> dict:
    if type(ll84) is not list or len(ll84) != N or any(type(r) is not dict for r in ll84):
        raise SampleError("LL84 cohort does not contain exactly 30 original rows")
    if type(pluto) is not list or len(pluto) > N or any(type(r) is not dict for r in pluto):
        raise SampleError("invalid PLUTO rows")

    canonical = {}
    for r in pluto:
        if set(r) != {"bbl", "numbldgs"}:
            raise SampleError("unexpected PLUTO projected columns")
        key = canonical_pluto_bbl(r["bbl"])
        count = r["numbldgs"]
        if type(count) is not str or not re.fullmatch(r"[0-9]{1,5}", count):
            raise SampleError("invalid PLUTO building count")
        if key in canonical:
            raise SampleError("duplicate PLUTO BBL")
        canonical[key] = int(count)

    seen_property = set()
    bbl_counts = Counter()
    observations = []
    for r in ll84:
        if set(r) - set(LL84_COLUMNS):
            raise SampleError("unexpected LL84 projected columns")
        prop = r.get("property_id")
        if type(prop) is not str or not re.fullmatch(r"[0-9]+", prop) or prop in seen_property:
            raise SampleError("missing or duplicated LL84 property ID")
        if r.get("report_year") != "2024":
            raise SampleError("LL84 row outside pinned report year")
        seen_property.add(prop)
        bbl_raw = r.get("nyc_borough_block_and_lot", "")
        bin_raw = r.get("nyc_building_identification", "")
        if type(bbl_raw) is not str or type(bin_raw) is not str:
            raise SampleError("unexpected LL84 identifier encoding")
        bbls = bbl_raw.split(";") if bbl_raw else []
        bins = bin_raw.split(";") if bin_raw else []
        if len(bbls) == 1 and BBL.fullmatch(bbls[0]):
            bbl_counts[bbls[0]] += 1
        observations.append((r, bbls, bins))

    reasons = Counter()
    for row, bbls, bins in observations:
        key = bbls[0] if len(bbls) == 1 and BBL.fullmatch(bbls[0]) else None
        if len(bbls) != 1 or key is None:
            reason = "ll84_multibbl_or_invalid_bbl"
        elif len(bins) != 1 or not BIN.fullmatch(bins[0]):
            reason = "ll84_multibin_or_invalid_bin"
        elif bbl_counts[key] > 1:
            reason = "same_sample_bbl_shared_by_multiple_properties"
        elif key not in canonical:
            reason = "pluto_bbl_missing_in_current_release"
        elif canonical[key] != 1:
            reason = "pluto_taxlot_not_single_building"
        elif row.get("parent_property_id") != "Not Applicable: Standalone Property":
            reason = "ll84_parent_child_or_unknown_status"
        elif row.get("number_of_buildings") != "1":
            reason = "ll84_reported_building_count_not_one"
        else:
            reason = "unverified_single_lot_building_candidate"
        reasons[reason] += 1

    if sum(reasons.values()) != N:
        raise SampleError("cohort conservation failure")
    return {
        "profile": "nyc-original-30-property-lot-smoke-v0",
        "source_grains": "2024_LL84_property_year_vs_2026_PLUTO_taxlot",
        "sample_rule": "LL84 2024 BBL like 1000 percent, ascending property_id, first 30",
        "representative": False,
        "pluto_26v2_expected_not_snapshot_verified": True,
        "ll84_rows": N,
        "unique_pluto_bbls_returned": len(canonical),
        "reason_counts": dict(sorted(reasons.items())),
        "building_identity_proven": False,
        "real_insurer_portfolio_proven": False,
        "insured_tiv_or_loss_calculated": False,
        "model_input_admitted": False,
        "raw_identifiers_exported": False,
        "raw_source_rows_committed": False,
    }


def run_live(fetch=_original_get) -> dict:
    ll84 = _parse_rows(fetch(ll84_url()), N)
    if len(ll84) != N:
        raise SampleError("source returned fewer than 30 LL84 rows: no incomplete cohort")
    keys = sorted({
        r["nyc_borough_block_and_lot"]
        for r in ll84
        if type(r.get("nyc_borough_block_and_lot")) is str
        and BBL.fullmatch(r["nyc_borough_block_and_lot"])
    })
    pluto = []
    for i in range(0, len(keys), CHUNK):
        batch = tuple(keys[i:i + CHUNK])
        try:
            pluto.extend(_parse_rows(fetch(pluto_url(batch)), len(batch)))
        except SampleError:
            # Fail-closed fallback: failed batch is retried as per-BBL requests.
            # A failed individual request is never silently counted as "missing".
            for key in batch:
                pluto.extend(_parse_rows(fetch(pluto_url((key,))), 1))
    return summarize(ll84, pluto)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Explicitly read at most 30 original public identifier-only records")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("network access requires --live")
    try:
        print(json.dumps(run_live(), sort_keys=True, separators=(",", ":")))
        return 0
    except SampleError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
