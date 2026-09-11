#!/usr/bin/env python3
"""Leakage-free rolling realised-CDR empirical challenge on sequential CAS CLRD vintages.

Purpose:
- combine legacy CLRD AY 1988-1997 with CLRD2025 AY 1998-2007;
- preserve only information available at each valuation year;
- compute the same-opening-AY one-year adverse CDR under:
  * rolling leave-one-company-out incurred Chain-Ladder,
  * rolling leave-one-company-out paid Chain-Ladder,
  * frozen pre-1998 incurred Chain-Ladder;
- compare those targets with the legacy raw incurred-emergence proxy;
- relate each reserve target to the existing net underwriting proxy.

This is research evidence, not a production reserving or dependence model.
Only the Python standard library is required.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist
from typing import Mapping, Sequence, Tuple

TARGET_LOB = "wkcomp"
OLD_START_AY = 1988
OLD_END_AY = 1997
NEW_START_AY = 1998
NEW_END_AY = 2007
EVAL_START_YEAR = 1999
EVAL_END_YEAR = 2007
MAX_LAG = 10
PILOT_GRCODES = (337, 353, 388, 671, 715, 965, 1066)

Coord = Tuple[int, int, int]


def _float(value: str) -> float:
    if value is None or value == "":
        raise ValueError("missing numeric value")
    return float(value)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_vintage(path: Path, *, lob: str, incurred_field: str) -> tuple[dict[Coord, dict], dict[int, str]]:
    rows: dict[Coord, dict] = {}
    names: dict[int, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or ())
        required = {
            "GRCODE", "GRNAME", "AccidentYear", "DevelopmentYear", "DevelopmentLag",
            incurred_field, "CumPaidLoss", "EarnedPremNet", "LOB",
        }
        missing = required.difference(fields)
        if missing:
            raise ValueError(f"{path}: missing fields {sorted(missing)}")
        for raw in reader:
            if raw["LOB"].strip().lower() != lob.lower():
                continue
            grcode = int(raw["GRCODE"])
            ay = int(raw["AccidentYear"])
            dy = int(raw["DevelopmentYear"])
            lag = int(float(raw["DevelopmentLag"]))
            if dy != ay + lag - 1:
                raise ValueError(f"unexpected calendar geometry: {grcode=} {ay=} {dy=} {lag=}")
            key = (grcode, ay, lag)
            if key in rows:
                raise ValueError(f"duplicate coordinate in {path}: {key}")
            rows[key] = {
                "grcode": grcode,
                "grname": raw["GRNAME"].strip(),
                "ay": ay,
                "dy": dy,
                "lag": lag,
                "incurred": _float(raw[incurred_field]),
                "paid": _float(raw["CumPaidLoss"]),
                "prem_net": _float(raw["EarnedPremNet"]),
            }
            names[grcode] = raw["GRNAME"].strip()
    return rows, names


def combine_vintages(old: Mapping[Coord, dict], new: Mapping[Coord, dict]) -> dict[Coord, dict]:
    overlap = set(old).intersection(new)
    if overlap:
        raise ValueError(f"unexpected coordinate overlap across vintages: {len(overlap)}")
    out = dict(old)
    out.update(new)
    return out


def complete_company(rows: Mapping[Coord, dict], grcode: int) -> bool:
    """Balanced complete-case gate using only cells consumed by the experiment.

    Requiring two complete 10x10 vintages would select on long-run reporting
    continuity far beyond what the rolling CDR actually consumes. This gate
    instead requires the UW cell, opening-premium cell, and the two successive
    cumulative observations needed for every evaluated CDR year.
    """
    for year in range(EVAL_START_YEAR, EVAL_END_YEAR + 1):
        uw_key = (grcode, year, 1)
        if uw_key not in rows:
            return False
        uw = rows[uw_key]
        if uw["prem_net"] <= 0 or uw["incurred"] <= 0:
            return False
        for ay in range(year - (MAX_LAG - 1), year):
            age_open = year - ay
            required = (
                (grcode, ay, 1),
                (grcode, ay, age_open),
                (grcode, ay, age_open + 1),
            )
            if any(key not in rows for key in required):
                return False
            if rows[(grcode, ay, 1)]["prem_net"] <= 0:
                return False
    return True


def eligible_companies(rows: Mapping[Coord, dict]) -> list[int]:
    grcodes = sorted({k[0] for k in rows})
    return [g for g in grcodes if complete_company(rows, g)]


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return float("nan")
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    sx = sum((v - mx) ** 2 for v in x)
    sy = sum((v - my) ** 2 for v in y)
    if sx <= 0 or sy <= 0:
        return float("nan")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sx * sy)


def average_ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    p = 0
    while p < len(order):
        q = p + 1
        while q < len(order) and values[order[q]] == values[order[p]]:
            q += 1
        avg = ((p + 1) + q) / 2.0
        for k in range(p, q):
            ranks[order[k]] = avg
        p = q
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    return pearson(average_ranks(x), average_ranks(y))


def two_way_demean(panel: Sequence[dict], field: str) -> list[float]:
    by_company: dict[int, list[float]] = defaultdict(list)
    by_year: dict[int, list[float]] = defaultdict(list)
    vals = [float(r[field]) for r in panel]
    for r, v in zip(panel, vals):
        by_company[int(r["grcode"])].append(v)
        by_year[int(r["year"])].append(v)
    cm = {k: sum(v) / len(v) for k, v in by_company.items()}
    ym = {k: sum(v) / len(v) for k, v in by_year.items()}
    grand = sum(vals) / len(vals)
    return [v - cm[int(r["grcode"])] - ym[int(r["year"])] + grand for r, v in zip(panel, vals)]


def correlation_block(panel: Sequence[dict], y_field: str, *, x_field: str = "uw") -> dict:
    x = [float(r[x_field]) for r in panel]
    y = [float(r[y_field]) for r in panel]
    xr = two_way_demean(panel, x_field)
    yr = two_way_demean(panel, y_field)
    return {
        "n": len(panel),
        "raw": {"pearson": pearson(x, y), "spearman": spearman(x, y)},
        "two_way_demeaned": {"pearson": pearson(xr, yr), "spearman": spearman(xr, yr)},
    }


def pair_stats(rows: Mapping[Coord, dict], *, field: str, valuation: int):
    global_acc = {lag: [0.0, 0.0, 0] for lag in range(1, MAX_LAG)}
    company_acc = defaultdict(lambda: {lag: [0.0, 0.0, 0] for lag in range(1, MAX_LAG)})
    for (grcode, ay, lag), cur in rows.items():
        if lag >= MAX_LAG:
            continue
        nxt = rows.get((grcode, ay, lag + 1))
        if nxt is None or int(nxt["dy"]) > valuation:
            continue
        a = float(cur[field])
        b = float(nxt[field])
        if not (math.isfinite(a) and math.isfinite(b)) or a <= 0 or b < 0:
            continue
        g = global_acc[lag]
        g[0] += b
        g[1] += a
        g[2] += 1
        c = company_acc[grcode][lag]
        c[0] += b
        c[1] += a
        c[2] += 1
    glob = {k: (v[0], v[1], int(v[2])) for k, v in global_acc.items()}
    comp = {g: {k: (v[0], v[1], int(v[2])) for k, v in ages.items()} for g, ages in company_acc.items()}
    return glob, comp


def loo_factors(stats, *, excluded_grcode: int) -> tuple[dict[int, float], dict[int, int]]:
    glob, comp = stats
    own = comp.get(excluded_grcode, {})
    factors: dict[int, float] = {}
    counts: dict[int, int] = {}
    for lag in range(1, MAX_LAG):
        gn, gd, gc = glob[lag]
        on, od, oc = own.get(lag, (0.0, 0.0, 0))
        num = gn - on
        den = gd - od
        count = gc - oc
        if den <= 0 or count <= 0:
            raise ValueError(f"no leave-one-company-out factor support: {excluded_grcode=} {lag=} {count=}")
        f = num / den
        if not math.isfinite(f) or f <= 0:
            raise ValueError(f"invalid factor: {excluded_grcode=} {lag=} {f=}")
        factors[lag] = f
        counts[lag] = count
    return factors, counts


def cdf_from_age(factors: Mapping[int, float], age: int) -> float:
    if age >= MAX_LAG:
        return 1.0
    out = 1.0
    for lag in range(age, MAX_LAG):
        out *= float(factors[lag])
    return out


def prediction(rows: Mapping[Coord, dict], *, grcode: int, opening_ays: Sequence[int], valuation: int, field: str, factors: Mapping[int, float]) -> float:
    total = 0.0
    for ay in opening_ays:
        age = valuation - ay + 1
        if not 1 <= age <= MAX_LAG:
            raise ValueError(f"opening AY outside live development window: {ay=} {valuation=} {age=}")
        cell = rows[(grcode, ay, age)]
        total += float(cell[field]) * cdf_from_age(factors, age)
    return total


def opening_premium(rows: Mapping[Coord, dict], *, grcode: int, opening_ays: Sequence[int]) -> float:
    total = sum(float(rows[(grcode, ay, 1)]["prem_net"]) for ay in opening_ays)
    if total <= 0:
        raise ValueError("non-positive opening premium")
    return total


def legacy_proxy(rows: Mapping[Coord, dict], *, grcode: int, opening_ays: Sequence[int], open_valuation: int) -> float:
    delta = 0.0
    opening_incurred = 0.0
    for ay in opening_ays:
        age = open_valuation - ay + 1
        prev = rows[(grcode, ay, age)]
        now = rows[(grcode, ay, age + 1)]
        delta += float(now["incurred"]) - float(prev["incurred"])
        opening_incurred += float(prev["incurred"])
    if opening_incurred <= 0:
        raise ValueError("non-positive opening incurred")
    return delta / opening_incurred


def company_correlations(panel: Sequence[dict], field: str) -> list[dict]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in panel:
        grouped[int(row["grcode"])].append(row)
    out = []
    for grcode in sorted(grouped):
        rows = sorted(grouped[grcode], key=lambda r: int(r["year"]))
        x = [float(r["uw"]) for r in rows]
        y = [float(r[field]) for r in rows]
        out.append({
            "grcode": grcode,
            "grname": rows[0]["grname"],
            "n": len(rows),
            "pearson": pearson(x, y),
            "spearman": spearman(x, y),
        })
    return out


def heterogeneity(company_effects: Sequence[dict], metric: str) -> dict:
    vals = []
    ns = []
    for r in company_effects:
        value = float(r[metric])
        n = int(r["n"])
        if math.isfinite(value) and abs(value) < 1 and n > 3:
            vals.append(math.atanh(value))
            ns.append(n)
    k = len(vals)
    if k < 2:
        return {"k": k}
    weights = [n - 3 for n in ns]
    sw = sum(weights)
    pooled_z = sum(w * z for w, z in zip(weights, vals)) / sw
    q = sum(w * (z - pooled_z) ** 2 for w, z in zip(weights, vals))
    df = k - 1
    c = sw - sum(w * w for w in weights) / sw
    tau2 = max(0.0, (q - df) / c) if c > 0 else float("nan")
    i2 = max(0.0, (q - df) / q) if q > 0 else 0.0
    if q <= 0:
        p_approx = 1.0
    else:
        zwh = ((q / df) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * df))) / math.sqrt(2.0 / (9.0 * df))
        p_approx = 1.0 - NormalDist().cdf(zwh)
    return {
        "k": k,
        "pooled_fisher_z": pooled_z,
        "pooled_r": math.tanh(pooled_z),
        "q": q,
        "df": df,
        "chi_square_p_wilson_hilferty_approx": p_approx,
        "tau2_dl_fisher_z": tau2,
        "i2": i2,
    }


def pairwise_target_comparison(panel: Sequence[dict], a: str, b: str) -> dict:
    x = [float(r[a]) for r in panel]
    y = [float(r[b]) for r in panel]
    disagreements = sum(1 for u, v in zip(x, y) if u != 0 and v != 0 and ((u > 0) != (v > 0)))
    comparable = sum(1 for u, v in zip(x, y) if u != 0 and v != 0)
    absdiff = [abs(u - v) for u, v in zip(x, y)]
    return {
        "pearson": pearson(x, y),
        "spearman": spearman(x, y),
        "sign_disagreement_rate": disagreements / comparable if comparable else None,
        "mean_absolute_difference": sum(absdiff) / len(absdiff),
        "max_absolute_difference": max(absdiff),
    }


def run(old_csv: Path, new_csv: Path, *, lob: str = TARGET_LOB) -> dict:
    old, old_names = load_vintage(old_csv, lob=lob, incurred_field="IncurLoss")
    new, new_names = load_vintage(new_csv, lob=lob, incurred_field="IncurredLosses")
    rows = combine_vintages(old, new)
    names = dict(old_names)
    names.update(new_names)

    eligible = eligible_companies(rows)
    if not eligible:
        raise ValueError("no complete two-vintage companies")

    valuations = list(range(EVAL_START_YEAR - 1, EVAL_END_YEAR + 1))
    stats_inc = {v: pair_stats(rows, field="incurred", valuation=v) for v in valuations}
    stats_paid = {v: pair_stats(rows, field="paid", valuation=v) for v in valuations}
    frozen_inc_stats = pair_stats(old, field="incurred", valuation=OLD_END_AY)

    panel: list[dict] = []
    support_min = {"incurred": MAX_LAG * 10**9, "paid": MAX_LAG * 10**9, "frozen": MAX_LAG * 10**9}
    for grcode in eligible:
        frozen_factors, frozen_counts = loo_factors(frozen_inc_stats, excluded_grcode=grcode)
        support_min["frozen"] = min(support_min["frozen"], min(frozen_counts.values()))
        for year in range(EVAL_START_YEAR, EVAL_END_YEAR + 1):
            open_v = year - 1
            close_v = year
            opening_ays = list(range(year - (MAX_LAG - 1), year))
            if opening_ays[0] < OLD_START_AY:
                raise AssertionError("insufficient prehistory")

            inc_open_f, inc_open_n = loo_factors(stats_inc[open_v], excluded_grcode=grcode)
            inc_close_f, inc_close_n = loo_factors(stats_inc[close_v], excluded_grcode=grcode)
            paid_open_f, paid_open_n = loo_factors(stats_paid[open_v], excluded_grcode=grcode)
            paid_close_f, paid_close_n = loo_factors(stats_paid[close_v], excluded_grcode=grcode)
            support_min["incurred"] = min(support_min["incurred"], min(inc_open_n.values()), min(inc_close_n.values()))
            support_min["paid"] = min(support_min["paid"], min(paid_open_n.values()), min(paid_close_n.values()))

            inc_u_open = prediction(rows, grcode=grcode, opening_ays=opening_ays, valuation=open_v, field="incurred", factors=inc_open_f)
            inc_u_close = prediction(rows, grcode=grcode, opening_ays=opening_ays, valuation=close_v, field="incurred", factors=inc_close_f)
            paid_u_open = prediction(rows, grcode=grcode, opening_ays=opening_ays, valuation=open_v, field="paid", factors=paid_open_f)
            paid_u_close = prediction(rows, grcode=grcode, opening_ays=opening_ays, valuation=close_v, field="paid", factors=paid_close_f)
            frozen_u_open = prediction(rows, grcode=grcode, opening_ays=opening_ays, valuation=open_v, field="incurred", factors=frozen_factors)
            frozen_u_close = prediction(rows, grcode=grcode, opening_ays=opening_ays, valuation=close_v, field="incurred", factors=frozen_factors)
            prem_open = opening_premium(rows, grcode=grcode, opening_ays=opening_ays)
            uw_cell = rows[(grcode, year, 1)]
            uw = float(uw_cell["incurred"]) / float(uw_cell["prem_net"])

            if min(inc_u_open, paid_u_open, frozen_u_open, prem_open) <= 0:
                raise ValueError(f"non-positive normalization base: {grcode=} {year=}")

            panel.append({
                "grcode": grcode,
                "grname": names.get(grcode, str(grcode)),
                "year": year,
                "uw": uw,
                "legacy_proxy": legacy_proxy(rows, grcode=grcode, opening_ays=opening_ays, open_valuation=open_v),
                "cdr_incurred": (inc_u_close - inc_u_open) / inc_u_open,
                "cdr_incurred_premium_norm": (inc_u_close - inc_u_open) / prem_open,
                "cdr_paid": (paid_u_close - paid_u_open) / paid_u_open,
                "cdr_paid_premium_norm": (paid_u_close - paid_u_open) / prem_open,
                "cdr_incurred_frozen": (frozen_u_close - frozen_u_open) / frozen_u_open,
                "cdr_incurred_frozen_premium_norm": (frozen_u_close - frozen_u_open) / prem_open,
            })

    target_fields = [
        "legacy_proxy", "cdr_incurred", "cdr_paid", "cdr_incurred_frozen",
        "cdr_incurred_premium_norm", "cdr_paid_premium_norm", "cdr_incurred_frozen_premium_norm",
    ]
    correlations = {field: correlation_block(panel, field) for field in target_fields}
    company = {field: company_correlations(panel, field) for field in target_fields}
    hetero = {
        field: {"pearson": heterogeneity(company[field], "pearson"), "spearman": heterogeneity(company[field], "spearman")}
        for field in target_fields
    }

    pilot_eligible = [g for g in PILOT_GRCODES if g in set(eligible)]
    pilot_panel = [r for r in panel if int(r["grcode"]) in set(pilot_eligible)]
    pilot_correlations = ({field: correlation_block(pilot_panel, field) for field in target_fields} if len(pilot_eligible) >= 2 else {})

    comparisons = {
        "legacy_vs_cdr_incurred": pairwise_target_comparison(panel, "legacy_proxy", "cdr_incurred"),
        "adaptive_incurred_vs_paid": pairwise_target_comparison(panel, "cdr_incurred", "cdr_paid"),
        "adaptive_vs_frozen_incurred": pairwise_target_comparison(panel, "cdr_incurred", "cdr_incurred_frozen"),
    }

    return {
        "schema": "ffbk.clrd2025_realised_cdr_dependence.v0",
        "design": {
            "lob": lob,
            "old_vintage_accident_years": [OLD_START_AY, OLD_END_AY],
            "new_vintage_accident_years": [NEW_START_AY, NEW_END_AY],
            "evaluation_years": [EVAL_START_YEAR, EVAL_END_YEAR],
            "development_lags": MAX_LAG,
            "opening_ay_rule": "nine AYs still live under a 10-development-period model",
            "underwriting_proxy": "AY=t development-lag-1 net incurred / EarnedPremNet",
            "adverse_cdr_sign": "closing predicted ultimate minus opening predicted ultimate",
            "rolling_calibration": "leave-one-company-out volume-weighted age-to-age factors using only cells whose second development observation is available by valuation date",
            "frozen_challenger": "leave-one-company-out incurred factors using old 1988-1997 vintage only",
            "classification": "real benchmark rolling/as-if-historical challenge; deterministic mean-model CDR; not predictive CDR distribution or production dependence calibration",
        },
        "source": {
            "old": {"bytes": old_csv.stat().st_size, "sha256": file_sha256(old_csv)},
            "new": {"bytes": new_csv.stat().st_size, "sha256": file_sha256(new_csv)},
        },
        "panel": {
            "eligible_companies": len(eligible),
            "company_year_rows": len(panel),
            "years_per_company": EVAL_END_YEAR - EVAL_START_YEAR + 1,
            "eligible_grcodes": eligible,
            "pilot_grcodes_requested": list(PILOT_GRCODES),
            "pilot_grcodes_eligible": pilot_eligible,
            "minimum_leave_one_company_out_pair_support": support_min,
        },
        "correlations": correlations,
        "pilot_correlations": pilot_correlations,
        "company_effects": company,
        "heterogeneity": hetero,
        "target_comparisons": comparisons,
    }


def json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    return value


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("old_csv", type=Path)
    ap.add_argument("new_csv", type=Path)
    ap.add_argument("--lob", default=TARGET_LOB)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    result = run(args.old_csv, args.new_csv, lob=args.lob)
    if args.check:
        if result["panel"]["years_per_company"] != 9:
            raise AssertionError(result["panel"])
        if result["panel"]["eligible_companies"] < 2:
            raise AssertionError("too few eligible companies")
        for field in ("legacy_proxy", "cdr_incurred", "cdr_paid", "cdr_incurred_frozen"):
            for metric in ("pearson", "spearman"):
                v = result["correlations"][field]["raw"][metric]
                if not math.isfinite(v):
                    raise AssertionError(f"non-finite {field} {metric}")
    print(json.dumps(json_safe(result), sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
