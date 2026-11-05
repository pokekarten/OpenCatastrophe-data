# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline-testable, opt-in original NYC LL84 BIN -> footprint identity probe.

Reads a fixed 30-row, nonrepresentative LL84 2024 cohort and a small set
of identifier-only NYC OTI BUILDING 5zhs-2jue records. No geometry, addresses,
owner details, policy records, insured values or source rows are exported.
A matching BIN/DOITT_ID is NOT a validated physical building or insured risk.
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
LL84 = "5zyy-y8am"
FOOTPRINT = "5zhs-2jue"
N = 30
CHUNK = 5
BATCH_LIMIT = 100
SINGLE_LIMIT = 20
MAX_BYTES = 32768
BBL = re.compile(r"[1-5][0-9]{9}\Z")
BIN = re.compile(r"[1-5][0-9]{6}\Z")
DECIMAL_ID = re.compile(r"[0-9]+\Z")
LL_FIELDS = (
    "property_id", "nyc_borough_block_and_lot",
    "nyc_building_identification", "parent_property_id",
    "number_of_buildings", "report_year",
)
FP_FIELDS = ("bin", "doitt_id", "base_bbl", "feature_code")


class ProbeError(ValueError):
    pass


class TransportError(ProbeError):
    """Transport errors may be retried only using an individually pinned BIN."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeError("NYC source redirected; identity review required")


def _url(view: str, query: dict[str, str]) -> str:
    if view not in {LL84, FOOTPRINT}:
        raise ProbeError("unexpected original source")
    return f"https://{HOST}/resource/{view}.json?{urlencode(query)}"


def ll84_url() -> str:
    return _url(LL84, {
        "$select": ",".join(LL_FIELDS),
        "$where": "report_year = 2024 AND nyc_borough_block_and_lot like '1000%'",
        "$order": "property_id ASC",
        "$limit": str(N),
    })


def footprint_url(bins: tuple[str, ...]) -> str:
    if not 1 <= len(bins) <= CHUNK or len(set(bins)) != len(bins):
        raise ProbeError("BIN batch must contain 1 to 5 distinct identifiers")
    if any(type(b) is not str or not BIN.fullmatch(b) for b in bins):
        raise ProbeError("unsafe or invalid original BIN")
    return _url(FOOTPRINT, {
        "$select": ",".join(FP_FIELDS),
        "$where": "bin in (" + ",".join(bins) + ")",
        "$limit": str(SINGLE_LIMIT if len(bins) == 1 else BATCH_LIMIT),
    })


def _fetch(url: str) -> bytes:
    p = urlsplit(url)
    if (p.scheme, p.hostname, p.username, p.password) != ("https", HOST, None, None):
        raise ProbeError("non-original public source URL forbidden")
    if p.path not in (f"/resource/{LL84}.json", f"/resource/{FOOTPRINT}.json"):
        raise ProbeError("unrecognised NYC resource")
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "OpenCatastrophe-nyc-bin-identity-research/0"})
        with build_opener(_NoRedirect()).open(req, timeout=15) as response:
            if response.status != 200 or response.headers.get_content_type() != "application/json":
                raise ProbeError("NYC response was not HTTP 200 JSON")
            body = response.read(MAX_BYTES + 1)
    except (OSError, TimeoutError) as exc:
        raise TransportError("NYC data request failed; result cannot be treated as absent") from exc
    if len(body) > MAX_BYTES:
        raise ProbeError("NYC source response exceeds byte budget")
    return body


def _parse(raw: bytes, limit: int) -> list[dict]:
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ProbeError("oversized/nonbinary source response")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProbeError("malformed NYC JSON") from exc
    if type(obj) is not list or len(obj) > limit or any(type(r) is not dict for r in obj):
        raise ProbeError("unexpected row representation")
    # Hitting the cap cannot prove a complete BIN-to-footprint fanout.
    if len(obj) == limit:
        raise ProbeError("provider response reached limit: cardinality is unknown")
    return obj


def _identifier(row: dict, name: str) -> str:
    v = row.get(name, "")
    if type(v) is not str:
        raise ProbeError("unexpected source identifier type")
    return v


def summarize(ll84: list[dict], footprints: list[dict]) -> dict:
    if type(ll84) is not list or len(ll84) != N or any(type(r) is not dict for r in ll84):
        raise ProbeError("expected exactly 30 original LL84 property-year rows")
    if type(footprints) is not list or len(footprints) > N * SINGLE_LIMIT or any(type(r) is not dict for r in footprints):
        raise ProbeError("unexpected footprint rows")

    ll_bin_frequency = Counter()
    properties = set()
    parsed = []
    for row in ll84:
        if set(row) - set(LL_FIELDS):
            raise ProbeError("unexpected LL84 column")
        prop = _identifier(row, "property_id")
        if not DECIMAL_ID.fullmatch(prop) or prop in properties:
            raise ProbeError("invalid/repeated LL84 property ID")
        if row.get("report_year") != "2024":
            raise ProbeError("wrong LL84 reporting year")
        properties.add(prop)
        bbl_text = _identifier(row, "nyc_borough_block_and_lot")
        bin_text = _identifier(row, "nyc_building_identification")
        bbls = bbl_text.split(";") if bbl_text else []
        bins = bin_text.split(";") if bin_text else []
        if len(bins) == 1 and BIN.fullmatch(bins[0]):
            ll_bin_frequency[bins[0]] += 1
        parsed.append((row, bbls, bins))

    by_bin: dict[str, list[dict]] = {}
    doitt_seen = set()
    for row in footprints:
        if set(row) != set(FP_FIELDS):
            raise ProbeError("unexpected footprint field projection")
        bin_value = _identifier(row, "bin")
        doitt = _identifier(row, "doitt_id")
        feature = _identifier(row, "feature_code")
        base = _identifier(row, "base_bbl")
        if not BIN.fullmatch(bin_value) or not DECIMAL_ID.fullmatch(doitt) or not DECIMAL_ID.fullmatch(feature):
            raise ProbeError("malformed original footprint BIN, DOITT or feature code")
        if base and not BBL.fullmatch(base):
            raise ProbeError("malformed footprint BASE_BBL; do not guess")
        if doitt in doitt_seen:
            raise ProbeError("repeated footprint DOITT_ID; ambiguous feature identity")
        doitt_seen.add(doitt)
        by_bin.setdefault(bin_value, []).append(row)

    reasons = Counter()
    base_relation = Counter()
    footprint_feature_rows = 0
    for row, bbls, bins in parsed:
        if len(bbls) != 1 or not BBL.fullmatch(bbls[0]):
            reason = "ll84_missing_multilot_or_invalid_bbl"
        elif len(bins) != 1 or not BIN.fullmatch(bins[0]):
            reason = "ll84_missing_multibin_or_invalid_bin"
        elif bins[0][1:] == "000000":
            reason = "placeholder_million_bin"
        elif ll_bin_frequency[bins[0]] > 1:
            reason = "shared_bin_across_ll84_properties"
        else:
            matches = by_bin.get(bins[0], [])
            if not matches:
                reason = "bin_absent_from_current_footprint_source"
            elif len(matches) != 1:
                reason = "nonunique_bin_multiple_footprint_features"
            else:
                footprint = matches[0]
                footprint_feature_rows += 1
                if footprint["feature_code"] != "2100":
                    reason = "non_standard_building_or_placeholder_feature"
                elif row.get("parent_property_id") != "Not Applicable: Standalone Property":
                    reason = "ll84_campus_parent_or_unknown"
                elif row.get("number_of_buildings") != "1":
                    reason = "ll84_reported_building_count_not_one"
                elif not footprint.get("base_bbl"):
                    reason = "missing_base_bbl"
                elif footprint["base_bbl"] == bbls[0]:
                    reason = "unique_bin_matching_base_bbl_unverified"
                    base_relation["same"] += 1
                else:
                    reason = "unique_bin_different_base_bbl_requires_billing_crosswalk"
                    base_relation["different"] += 1
        reasons[reason] += 1

    if sum(reasons.values()) != N:
        raise ProbeError("cohort conservation failed")
    return {
        "profile": "nyc-ll84-building-footprint-bin-research-v0",
        "cohort_rule": "LL84 2024, BBL prefix 1000, first 30 ascending property IDs",
        "ll84_property_year_rows": N,
        "provider_footprint_rows": len(footprints),
        "distinct_footprint_bin_values": len(by_bin),
        "distinct_doitt_features": len(doitt_seen),
        "reason_counts": dict(sorted(reasons.items())),
        "single_bin_base_bbl_relation": dict(sorted(base_relation.items())),
        "nonrepresentative_sample": True,
        "actual_polygon_geometries_examined": False,
        "building_identity_proven": False,
        "insured_value_or_losses_inferred": False,
        "source_admitted_for_models": False,
        "raw_external_source_rows_exported": False,
    }


def run_live(fetch=_fetch) -> dict:
    ll84 = _parse(fetch(ll84_url()), N + 1)
    if len(ll84) != N:
        raise ProbeError("incomplete original LL84 sample")
    # A multi-BIN campus is never auto-split. Only single validated BIN
    # observations are requested; max 30 source-identification lookups.
    bins = sorted({
        row["nyc_building_identification"]
        for row in ll84
        if type(row.get("nyc_building_identification")) is str
        and BIN.fullmatch(row["nyc_building_identification"])
        and row["nyc_building_identification"][1:] != "000000"
    })
    all_rows = []
    for i in range(0, len(bins), CHUNK):
        batch = tuple(bins[i:i + CHUNK])
        try:
            rows = _parse(fetch(footprint_url(batch)), SINGLE_LIMIT if len(batch) == 1 else BATCH_LIMIT)
        except TransportError:
            rows = []
            for bin_value in batch:
                rows.extend(_parse(fetch(footprint_url((bin_value,))), SINGLE_LIMIT))
        all_rows.extend(rows)
    if any(r.get("bin") not in bins for r in all_rows):
        raise ProbeError("original source returned BIN outside requested identity set")
    return summarize(ll84, all_rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Read a fixed 30-row public-source sample and identifier-only footprints")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("explicit --live required; offline-only by default")
    try:
        print(json.dumps(run_live(), sort_keys=True, separators=(",", ":")))
        return 0
    except ProbeError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
