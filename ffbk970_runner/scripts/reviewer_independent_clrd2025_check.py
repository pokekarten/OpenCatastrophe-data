#!/usr/bin/env python3
"""Reviewer-owned no-import CLRD2025 reconstruction for FFBK PR #970.

This checker deliberately contains no target correlation constants and imports no
FFBK probe. It verifies the pinned raw Git object, reconstructs paid log-link
states, performs company×LoB×link centering / sample-SD normalization, and emits
headline pooled, lag-specific, company-mean and leave-one-company diagnostics.
It also separates normalized-sample eligibility from SD rescaling.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

SOURCE_BLOB = "8d0400f1ace87c3e1e1202d359ef3bb6111b3dd0"
LOBS = {"comauto", "ppauto"}
RELATIONS = ("same_step", "ca_to_pa_next", "pa_to_ca_next")


def raw_git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def arithmetic_mean(values):
    return math.fsum(values) / len(values)


def sample_sd(values):
    m = arithmetic_mean(values)
    return math.sqrt(math.fsum((v - m) ** 2 for v in values) / (len(values) - 1))


def corr(xs, ys):
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mx = arithmetic_mean(xs)
    my = arithmetic_mean(ys)
    xx = math.fsum((x - mx) ** 2 for x in xs)
    yy = math.fsum((y - my) ** 2 for y in ys)
    if xx == 0.0 or yy == 0.0:
        return None
    xy = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return xy / math.sqrt(xx * yy)


def rank_average(values):
    groups = defaultdict(list)
    for i, value in enumerate(values):
        groups[value].append(i)
    ranks = [0.0] * len(values)
    position = 1
    for value in sorted(groups):
        idxs = groups[value]
        last = position + len(idxs) - 1
        rank = (position + last) / 2.0
        for i in idxs:
            ranks[i] = rank
        position = last + 1
    return ranks


def summarize(rows):
    xs = [x for x, _, _ in rows]
    ys = [y for _, y, _ in rows]
    return {
        "n_records": len(rows),
        "n_companies": len({c for _, _, c in rows}),
        "pearson": corr(xs, ys),
        "spearman": corr(rank_average(xs), rank_average(ys)),
    }


def load_positive_links(path):
    triangles = defaultdict(dict)
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"GRCODE", "AccidentYear", "DevelopmentLag", "CumPaidLoss", "LOB"}
        assert required.issubset(reader.fieldnames or []), (reader.fieldnames, required)
        for row in reader:
            lob = row["LOB"].strip().lower()
            if lob not in LOBS:
                continue
            company = row["GRCODE"].strip()
            ay = int(row["AccidentYear"])
            lag = int(row["DevelopmentLag"])
            key = (company, lob, ay)
            if lag in triangles[key]:
                raise AssertionError(("duplicate-cell", key, lag))
            triangles[key][lag] = float(row["CumPaidLoss"])

    links = defaultdict(dict)
    for (company, lob, ay), by_lag in triangles.items():
        for lag in range(1, max(by_lag, default=0)):
            left = by_lag.get(lag)
            right = by_lag.get(lag + 1)
            if left is None or right is None or left <= 0.0 or right <= 0.0:
                continue
            # Algebraically equivalent to log(right / left), but deliberately
            # different floating operation order to challenge numeric portability.
            links[(company, lob, lag)][ay] = math.log(right) - math.log(left)
    return links


def transform_blocks(links):
    centered = {}
    normalized = {}
    for key, series in links.items():
        vals = list(series.values())
        if not vals:
            continue
        m = arithmetic_mean(vals)
        centered[key] = {ay: value - m for ay, value in series.items()}
        if len(vals) >= 2:
            sd = sample_sd(vals)
            if sd > 0.0:
                normalized[key] = {ay: (value - m) / sd for ay, value in series.items()}
    return centered, normalized


def relation_coords(relation, lag):
    if relation == "same_step":
        return "comauto", lag, "ppauto", lag
    if relation == "ca_to_pa_next":
        return "comauto", lag, "ppauto", lag + 1
    if relation == "pa_to_ca_next":
        return "ppauto", lag, "comauto", lag + 1
    raise KeyError(relation)


def pair_rows(state, relation, lag):
    x_lob, x_lag, y_lob, y_lag = relation_coords(relation, lag)
    companies = sorted({k[0] for k in state})
    rows = []
    for company in companies:
        left = state.get((company, x_lob, x_lag), {})
        right = state.get((company, y_lob, y_lag), {})
        for ay in sorted(left.keys() & right.keys()):
            rows.append((left[ay], right[ay], company))
    return rows


def pair_rows_gated(value_state, gate_state, relation, lag):
    """Use values from value_state only where both gate-state blocks/AYs exist."""
    x_lob, x_lag, y_lob, y_lag = relation_coords(relation, lag)
    companies = sorted({k[0] for k in gate_state})
    rows = []
    for company in companies:
        gx = gate_state.get((company, x_lob, x_lag), {})
        gy = gate_state.get((company, y_lob, y_lag), {})
        vx = value_state.get((company, x_lob, x_lag), {})
        vy = value_state.get((company, y_lob, y_lag), {})
        for ay in sorted(gx.keys() & gy.keys() & vx.keys() & vy.keys()):
            rows.append((vx[ay], vy[ay], company))
    return rows


def pooled_rows(state, relation, max_lag):
    last = max_lag if relation == "same_step" else max_lag - 1
    rows = []
    for lag in range(1, last + 1):
        rows.extend(pair_rows(state, relation, lag))
    return rows


def pooled_rows_gated(value_state, gate_state, relation, max_lag):
    last = max_lag if relation == "same_step" else max_lag - 1
    rows = []
    for lag in range(1, last + 1):
        rows.extend(pair_rows_gated(value_state, gate_state, relation, lag))
    return rows


def company_mean(rows):
    by_company = defaultdict(list)
    for x, y, company in rows:
        by_company[company].append((x, y))
    collapsed = []
    for company in sorted(by_company):
        pairs = by_company[company]
        collapsed.append((
            arithmetic_mean([x for x, _ in pairs]),
            arithmetic_mean([y for _, y in pairs]),
            company,
        ))
    return summarize(collapsed)


def leave_one_company(rows):
    companies = sorted({company for _, _, company in rows})
    estimates = []
    for omitted in companies:
        kept = [(x, y, c) for x, y, c in rows if c != omitted]
        estimate = summarize(kept)["pearson"]
        if estimate is not None:
            estimates.append((omitted, estimate))
    values = [value for _, value in estimates]
    ordered = sorted(values)
    median = None
    if ordered:
        n = len(ordered)
        median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0
    return {
        "n": len(estimates),
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "median": median,
        "sign_counts": {
            "negative": sum(v < 0 for v in values),
            "zero": sum(v == 0 for v in values),
            "positive": sum(v > 0 for v in values),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    path = Path(args.csv)
    data = path.read_bytes()
    blob = raw_git_blob(data)
    if blob != SOURCE_BLOB:
        raise SystemExit(f"source mismatch: {blob}")

    raw = load_positive_links(path)
    centered, normalized = transform_blocks(raw)
    max_lag = max(k[2] for k in raw)
    states = {"raw": raw, "centered": centered, "normalized": normalized}
    report = {
        "source": {
            "git_blob": blob,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        },
        "max_lag": max_lag,
        "pooled": {},
        "selected_pair_specific": {},
        "eligibility_decomposition": {},
    }

    for relation in RELATIONS:
        report["pooled"][relation] = {}
        for state_name, state in states.items():
            rows = pooled_rows(state, relation, max_lag)
            summary = summarize(rows)
            if state_name == "raw":
                summary["company_mean"] = company_mean(rows)
            if state_name in {"centered", "normalized"}:
                summary["leave_one_company"] = leave_one_company(rows)
            report["pooled"][relation][state_name] = summary

        common_centered_rows = pooled_rows_gated(centered, normalized, relation, max_lag)
        common_summary = summarize(common_centered_rows)
        common_summary["leave_one_company"] = leave_one_company(common_centered_rows)
        report["eligibility_decomposition"][relation] = {
            "centered_on_normalized_eligibility": common_summary,
            "normalized": report["pooled"][relation]["normalized"],
        }

    for lag in (5, 7):
        report["selected_pair_specific"][str(lag)] = {}
        for state_name, state in states.items():
            report["selected_pair_specific"][str(lag)][state_name] = summarize(
                pair_rows(state, "same_step", lag)
            )
        report["selected_pair_specific"][str(lag)]["centered_on_normalized_eligibility"] = summarize(
            pair_rows_gated(centered, normalized, "same_step", lag)
        )

    print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))
    print("REVIEWER_CLRD2025_RECONSTRUCTION_OK")


if __name__ == "__main__":
    main()
