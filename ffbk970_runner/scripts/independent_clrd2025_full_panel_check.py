#!/usr/bin/env python3
"""Independent no-import reconstruction for FFBK #970 headline CLRD2025 results.

This deliberately does not import the FFBK probe. It re-parses the pinned CSV,
rebuilds adjacent paid-development log links, company×LoB×link centering and
sample-SD normalization, then checks pre-recorded headline results from the
first exact full-panel run.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

EXPECTED = {
    "same_step": {
        "raw": (6401, 87, 0.65009477870791, 0.6682113273080356),
        "centered": (6401, 87, 0.12355800431009611, 0.10175622762793342),
        "normalized": (5606, 85, 0.07374950689577407, 0.07026174755916961),
        "loo_centered_signs": {"negative": 0, "zero": 0, "positive": 87},
        "loo_normalized_signs": {"negative": 0, "zero": 0, "positive": 85},
    },
    "ca_to_pa_next": {
        "raw": (5685, 87, 0.4351249303634477, 0.6144751835873031),
        "centered": (5685, 87, -0.022030475251296137, 0.048859012624105434),
        "normalized": (5051, 84, 0.04650826826361383, 0.053857865726907976),
        "loo_centered_signs": {"negative": 87, "zero": 0, "positive": 0},
        "loo_normalized_signs": {"negative": 0, "zero": 0, "positive": 84},
    },
    "pa_to_ca_next": {
        "raw": (5708, 87, 0.4734838303722828, 0.5872596704708778),
        "centered": (5708, 87, 0.07843595955760888, 0.05989304395514325),
        "normalized": (4991, 84, 0.02394639812623256, 0.02841998771075054),
        "loo_centered_signs": {"negative": 0, "zero": 0, "positive": 87},
        "loo_normalized_signs": {"negative": 0, "zero": 0, "positive": 84},
    },
}
LOBS = ("comauto", "ppauto")


def avg(xs):
    return sum(xs) / len(xs)


def sd_sample(xs):
    m = avg(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def pearson(xs, ys):
    if len(xs) < 2:
        return None
    mx, my = avg(xs), avg(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    sx = math.sqrt(sum(x * x for x in dx))
    sy = math.sqrt(sum(y * y for y in dy))
    return None if sx == 0.0 or sy == 0.0 else sum(x*y for x,y in zip(dx,dy))/(sx*sy)


def ranks(xs):
    indexed = sorted(enumerate(xs), key=lambda p: p[1])
    out = [0.0] * len(xs)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        r = (i + 1 + j) / 2.0
        for k in range(i, j):
            out[indexed[k][0]] = r
        i = j
    return out


def assoc(rows):
    xs = [r[0] for r in rows]
    ys = [r[1] for r in rows]
    return {
        "n_records": len(rows),
        "n_companies": len({r[2] for r in rows}),
        "pearson": pearson(xs, ys),
        "spearman": pearson(ranks(xs), ranks(ys)),
    }


def load_links(path):
    cells = defaultdict(dict)
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lob = row["LOB"].strip().lower()
            if lob not in LOBS:
                continue
            company = row["GRCODE"].strip()
            ay = int(row["AccidentYear"])
            lag = int(row["DevelopmentLag"])
            value = float(row["CumPaidLoss"])
            cells[(company, lob, ay)][lag] = value

    links = defaultdict(dict)
    for (company, lob, ay), by_lag in cells.items():
        for lag in range(1, max(by_lag, default=0)):
            a = by_lag.get(lag)
            b = by_lag.get(lag + 1)
            if a is None or b is None or a <= 0.0 or b <= 0.0:
                continue
            links[(company, lob, lag)][ay] = math.log(b / a)
    return links


def transforms(links):
    centered = {}
    normalized = {}
    for key, by_ay in links.items():
        vals = list(by_ay.values())
        if not vals:
            continue
        m = avg(vals)
        centered[key] = {ay: v - m for ay, v in by_ay.items()}
        if len(vals) >= 2:
            s = sd_sample(vals)
            if s != 0.0:
                normalized[key] = {ay: (v - m) / s for ay, v in by_ay.items()}
    return centered, normalized


def paired(state, relation, lag):
    if relation == "same_step":
        xl, xlag, yl, ylag = "comauto", lag, "ppauto", lag
    elif relation == "ca_to_pa_next":
        xl, xlag, yl, ylag = "comauto", lag, "ppauto", lag + 1
    else:
        xl, xlag, yl, ylag = "ppauto", lag, "comauto", lag + 1
    companies = sorted({k[0] for k in state})
    out = []
    for c in companies:
        xs = state.get((c, xl, xlag), {})
        ys = state.get((c, yl, ylag), {})
        for ay in sorted(set(xs) & set(ys)):
            out.append((xs[ay], ys[ay], c))
    return out


def pooled(state, relation, maxlag):
    last = maxlag if relation == "same_step" else maxlag - 1
    out = []
    for lag in range(1, last + 1):
        out.extend(paired(state, relation, lag))
    return out


def loo(rows):
    comps = sorted({r[2] for r in rows})
    values = []
    for omitted in comps:
        kept = [r for r in rows if r[2] != omitted]
        p = assoc(kept)["pearson"]
        if p is not None:
            values.append((omitted, p))
    vs = [v for _, v in values]
    signs = {
        "negative": sum(v < 0 for v in vs),
        "zero": sum(v == 0 for v in vs),
        "positive": sum(v > 0 for v in vs),
    }
    return {
        "n": len(values),
        "min": min(vs),
        "median": statistics.median(vs),
        "max": max(vs),
        "sign_counts": signs,
    }


def close(a, b, tol=1e-12):
    return abs(a - b) <= tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    args = ap.parse_args()

    raw = load_links(args.csv)
    centered, normalized = transforms(raw)
    maxlag = max(k[2] for k in raw)
    report = {"maxlag": maxlag, "relations": {}}

    for rel in ("same_step", "ca_to_pa_next", "pa_to_ca_next"):
        rr = pooled(raw, rel, maxlag)
        cr = pooled(centered, rel, maxlag)
        nr = pooled(normalized, rel, maxlag)
        got = {
            "raw": assoc(rr),
            "centered": assoc(cr),
            "normalized": assoc(nr),
            "loo_centered": loo(cr),
            "loo_normalized": loo(nr),
        }
        report["relations"][rel] = got
        exp = EXPECTED[rel]
        for state in ("raw", "centered", "normalized"):
            nrec, nco, p, s = exp[state]
            assert got[state]["n_records"] == nrec, (rel, state, got[state]["n_records"], nrec)
            assert got[state]["n_companies"] == nco, (rel, state, got[state]["n_companies"], nco)
            assert close(got[state]["pearson"], p), (rel, state, "pearson", got[state]["pearson"], p)
            assert close(got[state]["spearman"], s), (rel, state, "spearman", got[state]["spearman"], s)
        assert got["loo_centered"]["sign_counts"] == exp["loo_centered_signs"], (rel, "loo-centered")
        assert got["loo_normalized"]["sign_counts"] == exp["loo_normalized_signs"], (rel, "loo-normalized")

    assert maxlag == 9
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    print("INDEPENDENT_CLRD2025_FULL_PANEL_HEADLINES_OK")


if __name__ == "__main__":
    main()
