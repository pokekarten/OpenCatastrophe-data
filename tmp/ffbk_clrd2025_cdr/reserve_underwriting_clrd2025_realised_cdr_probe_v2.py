#!/usr/bin/env python3
"""Rolling realised-CDR challenge on sequential CAS CLRD vintages.

The 1988-1997 CLRD vintage is treated as a fixed chronological calibration
sample. The 1998-2007 CLRD2025 vintage is the evaluation sample. For each
1999-2007 evaluation year, the opening reserve set is exactly the prior
CLRD2025 accident years already observed in that vintage. The same opening
AY set is re-reserved one year later. Development factors are either:

* frozen on the old vintage only; or
* updated with CLRD2025 development pairs visible by the valuation date,
  excluding the evaluated company from the new-vintage calibration rows.

This avoids inventing a company-level bridge between the two CAS vintages.
It is a deterministic mean-model CDR experiment, not a predictive reserve
risk distribution or production dependence calibration.
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
LEGACY_PILOT_GRCODES = (337, 353, 388, 671, 715, 965, 1066)

Coord = Tuple[int, int, int]


def _float(value: str) -> float:
    if value is None or value == "":
        raise ValueError("missing numeric value")
    return float(value)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
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


def evaluation_company_complete(rows: Mapping[Coord, dict], grcode: int) -> bool:
    """Require only cells consumed by the 1999-2007 balanced evaluation."""
    for year in range(EVAL_START_YEAR, EVAL_END_YEAR + 1):
        uw_key = (grcode, year, 1)
        if uw_key not in rows:
            return False
        uw = rows[uw_key]
        if uw["prem_net"] <= 0 or uw["incurred"] <= 0:
            return False
        for ay in range(NEW_START_AY, year):
            opening_age = year - ay
            for key in ((grcode, ay, 1), (grcode, ay, opening_age), (grcode, ay, opening_age + 1)):
                if key not in rows:
                    return False
            if rows[(grcode, ay, 1)]["prem_net"] <= 0:
                return False
    return True


def eligible_companies(rows: Mapping[Coord, dict]) -> list[int]:
    return [
        grcode
        for grcode in sorted({key[0] for key in rows})
        if evaluation_company_complete(rows, grcode)
    ]


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
    pos = 0
    while pos < len(order):
        end = pos + 1
        while end < len(order) and values[order[end]] == values[order[pos]]:
            end += 1
        rank = ((pos + 1) + end) / 2.0
        for idx in range(pos, end):
            ranks[order[idx]] = rank
        pos = end
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    return pearson(average_ranks(x), average_ranks(y))


def two_way_demean(panel: Sequence[dict], field: str) -> list[float]:
    by_company: dict[int, list[float]] = defaultdict(list)
    by_year: dict[int, list[float]] = defaultdict(list)
    values = [float(row[field]) for row in panel]
    for row, value in zip(panel, values):
        by_company[int(row["grcode"])].append(value)
        by_year[int(row["year"])].append(value)
    company_mean = {k: sum(v) / len(v) for k, v in by_company.items()}
    year_mean = {k: sum(v) / len(v) for k, v in by_year.items()}
    grand = sum(values) / len(values)
    return [
        value - company_mean[int(row["grcode"])] - year_mean[int(row["year"])] + grand
        for row, value in zip(panel, values)
    ]


def correlation_block(panel: Sequence[dict], y_field: str) -> dict:
    x = [float(row["uw"]) for row in panel]
    y = [float(row[y_field]) for row in panel]
    xd = two_way_demean(panel, "uw")
    yd = two_way_demean(panel, y_field)
    return {
        "n": len(panel),
        "raw": {"pearson": pearson(x, y), "spearman": spearman(x, y)},
        "two_way_demeaned": {"pearson": pearson(xd, yd), "spearman": spearman(xd, yd)},
    }


def factor_sums(
    old_rows: Mapping[Coord, dict],
    new_rows: Mapping[Coord, dict],
    *,
    field: str,
    valuation: int | None,
    exclude_new_grcode: int | None,
) -> dict[int, tuple[float, float, int]]:
    """Volume-weighted age-to-age sums from old history plus visible new pairs."""
    acc = {lag: [0.0, 0.0, 0] for lag in range(1, MAX_LAG)}

    def ingest(rows: Mapping[Coord, dict], *, apply_cutoff: bool, exclude_grcode: int | None) -> None:
        for (grcode, ay, lag), current in rows.items():
            if lag >= MAX_LAG or (exclude_grcode is not None and grcode == exclude_grcode):
                continue
            nxt = rows.get((grcode, ay, lag + 1))
            if nxt is None:
                continue
            if apply_cutoff and valuation is not None and int(nxt["dy"]) > valuation:
                continue
            denominator = float(current[field])
            numerator = float(nxt[field])
            if not (math.isfinite(denominator) and math.isfinite(numerator)):
                continue
            if denominator <= 0 or numerator < 0:
                continue
            slot = acc[lag]
            slot[0] += numerator
            slot[1] += denominator
            slot[2] += 1

    ingest(old_rows, apply_cutoff=False, exclude_grcode=None)
    ingest(new_rows, apply_cutoff=True, exclude_grcode=exclude_new_grcode)
    return {lag: (v[0], v[1], int(v[2])) for lag, v in acc.items()}


def factors_from_sums(sums: Mapping[int, tuple[float, float, int]]) -> tuple[dict[int, float], dict[int, int]]:
    factors: dict[int, float] = {}
    counts: dict[int, int] = {}
    for lag in range(1, MAX_LAG):
        numerator, denominator, count = sums[lag]
        if denominator <= 0 or count <= 0:
            raise ValueError(f"insufficient factor support at lag {lag}: {count=}")
        factor = numerator / denominator
        if not math.isfinite(factor) or factor <= 0:
            raise ValueError(f"invalid factor at lag {lag}: {factor=}")
        factors[lag] = factor
        counts[lag] = count
    return factors, counts


def cdf_from_age(factors: Mapping[int, float], age: int) -> float:
    if age >= MAX_LAG:
        return 1.0
    value = 1.0
    for lag in range(age, MAX_LAG):
        value *= float(factors[lag])
    return value


def predicted_ultimate(
    rows: Mapping[Coord, dict],
    *,
    grcode: int,
    opening_ays: Sequence[int],
    valuation: int,
    field: str,
    factors: Mapping[int, float],
) -> float:
    total = 0.0
    for ay in opening_ays:
        age = valuation - ay + 1
        if not 1 <= age <= MAX_LAG:
            raise ValueError(f"invalid age for opening set: {ay=} {valuation=} {age=}")
        total += float(rows[(grcode, ay, age)][field]) * cdf_from_age(factors, age)
    return total


def opening_premium(rows: Mapping[Coord, dict], *, grcode: int, opening_ays: Sequence[int]) -> float:
    value = sum(float(rows[(grcode, ay, 1)]["prem_net"]) for ay in opening_ays)
    if value <= 0:
        raise ValueError("non-positive opening premium")
    return value


def legacy_proxy(rows: Mapping[Coord, dict], *, grcode: int, opening_ays: Sequence[int], open_valuation: int) -> float:
    emergence = 0.0
    opening_incurred = 0.0
    for ay in opening_ays:
        age = open_valuation - ay + 1
        before = rows[(grcode, ay, age)]
        after = rows[(grcode, ay, age + 1)]
        emergence += float(after["incurred"]) - float(before["incurred"])
        opening_incurred += float(before["incurred"])
    if opening_incurred <= 0:
        raise ValueError("non-positive opening incurred")
    return emergence / opening_incurred


def company_correlations(panel: Sequence[dict], field: str) -> list[dict]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in panel:
        grouped[int(row["grcode"])].append(row)
    result = []
    for grcode in sorted(grouped):
        rows = sorted(grouped[grcode], key=lambda row: int(row["year"]))
        x = [float(row["uw"]) for row in rows]
        y = [float(row[field]) for row in rows]
        result.append({
            "grcode": grcode,
            "grname": rows[0]["grname"],
            "n": len(rows),
            "pearson": pearson(x, y),
            "spearman": spearman(x, y),
        })
    return result


def heterogeneity(company_effects: Sequence[dict], metric: str) -> dict:
    z_values = []
    ns = []
    for row in company_effects:
        value = float(row[metric])
        n = int(row["n"])
        if math.isfinite(value) and abs(value) < 1 and n > 3:
            z_values.append(math.atanh(value))
            ns.append(n)
    k = len(z_values)
    if k < 2:
        return {"k": k}
    weights = [n - 3 for n in ns]
    sw = sum(weights)
    pooled_z = sum(w * z for w, z in zip(weights, z_values)) / sw
    q = sum(w * (z - pooled_z) ** 2 for w, z in zip(weights, z_values))
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


def target_comparison(panel: Sequence[dict], a: str, b: str) -> dict:
    x = [float(row[a]) for row in panel]
    y = [float(row[b]) for row in panel]
    comparable = [(u, v) for u, v in zip(x, y) if u != 0 and v != 0]
    sign_disagreements = sum(1 for u, v in comparable if (u > 0) != (v > 0))
    differences = [abs(u - v) for u, v in zip(x, y)]
    return {
        "pearson": pearson(x, y),
        "spearman": spearman(x, y),
        "sign_disagreement_rate": sign_disagreements / len(comparable) if comparable else None,
        "mean_absolute_difference": sum(differences) / len(differences),
        "max_absolute_difference": max(differences),
    }


def quantiles(values: Sequence[float]) -> dict:
    ordered = sorted(values)
    if not ordered:
        return {}
    def pick(p: float) -> float:
        pos = p * (len(ordered) - 1)
        lo = int(math.floor(pos))
        hi = int(math.ceil(pos))
        if lo == hi:
            return ordered[lo]
        weight = pos - lo
        return ordered[lo] * (1 - weight) + ordered[hi] * weight
    return {"min": ordered[0], "p05": pick(0.05), "median": pick(0.5), "p95": pick(0.95), "max": ordered[-1]}


def run(old_csv: Path, new_csv: Path, *, lob: str = TARGET_LOB) -> dict:
    old_rows, _old_names = load_vintage(old_csv, lob=lob, incurred_field="IncurLoss")
    new_rows, new_names = load_vintage(new_csv, lob=lob, incurred_field="IncurredLosses")
    eligible = eligible_companies(new_rows)
    if len(eligible) < 2:
        raise ValueError(f"too few complete CLRD2025 evaluation companies: {len(eligible)}")

    frozen_inc, frozen_inc_n = factors_from_sums(
        factor_sums(old_rows, {}, field="incurred", valuation=None, exclude_new_grcode=None)
    )
    frozen_paid, frozen_paid_n = factors_from_sums(
        factor_sums(old_rows, {}, field="paid", valuation=None, exclude_new_grcode=None)
    )

    panel: list[dict] = []
    support_min = {
        "adaptive_incurred": 10**9,
        "adaptive_paid": 10**9,
        "frozen_incurred": min(frozen_inc_n.values()),
        "frozen_paid": min(frozen_paid_n.values()),
    }

    for grcode in eligible:
        for year in range(EVAL_START_YEAR, EVAL_END_YEAR + 1):
            open_v = year - 1
            close_v = year
            opening_ays = list(range(NEW_START_AY, year))

            inc_open, inc_open_n = factors_from_sums(
                factor_sums(old_rows, new_rows, field="incurred", valuation=open_v, exclude_new_grcode=grcode)
            )
            inc_close, inc_close_n = factors_from_sums(
                factor_sums(old_rows, new_rows, field="incurred", valuation=close_v, exclude_new_grcode=grcode)
            )
            paid_open, paid_open_n = factors_from_sums(
                factor_sums(old_rows, new_rows, field="paid", valuation=open_v, exclude_new_grcode=grcode)
            )
            paid_close, paid_close_n = factors_from_sums(
                factor_sums(old_rows, new_rows, field="paid", valuation=close_v, exclude_new_grcode=grcode)
            )
            support_min["adaptive_incurred"] = min(
                support_min["adaptive_incurred"], min(inc_open_n.values()), min(inc_close_n.values())
            )
            support_min["adaptive_paid"] = min(
                support_min["adaptive_paid"], min(paid_open_n.values()), min(paid_close_n.values())
            )

            inc_u_open = predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=open_v, field="incurred", factors=inc_open)
            inc_u_close = predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=close_v, field="incurred", factors=inc_close)
            paid_u_open = predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=open_v, field="paid", factors=paid_open)
            paid_u_close = predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=close_v, field="paid", factors=paid_close)
            frozen_inc_u_open = predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=open_v, field="incurred", factors=frozen_inc)
            frozen_inc_u_close = predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=close_v, field="incurred", factors=frozen_inc)
            frozen_paid_u_open = predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=open_v, field="paid", factors=frozen_paid)
            frozen_paid_u_close = predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=close_v, field="paid", factors=frozen_paid)
            premium = opening_premium(new_rows, grcode=grcode, opening_ays=opening_ays)
            uw_cell = new_rows[(grcode, year, 1)]
            uw = float(uw_cell["incurred"]) / float(uw_cell["prem_net"])

            bases = (inc_u_open, paid_u_open, frozen_inc_u_open, frozen_paid_u_open, premium)
            if min(bases) <= 0:
                raise ValueError(f"non-positive normalization base: {grcode=} {year=} {bases=}")

            panel.append({
                "grcode": grcode,
                "grname": new_names.get(grcode, str(grcode)),
                "year": year,
                "uw": uw,
                "legacy_proxy": legacy_proxy(new_rows, grcode=grcode, opening_ays=opening_ays, open_valuation=open_v),
                "cdr_incurred": (inc_u_close - inc_u_open) / inc_u_open,
                "cdr_paid": (paid_u_close - paid_u_open) / paid_u_open,
                "cdr_incurred_frozen": (frozen_inc_u_close - frozen_inc_u_open) / frozen_inc_u_open,
                "cdr_paid_frozen": (frozen_paid_u_close - frozen_paid_u_open) / frozen_paid_u_open,
                "cdr_incurred_premium_norm": (inc_u_close - inc_u_open) / premium,
                "cdr_paid_premium_norm": (paid_u_close - paid_u_open) / premium,
            })

    fields = [
        "legacy_proxy", "cdr_incurred", "cdr_paid", "cdr_incurred_frozen", "cdr_paid_frozen",
        "cdr_incurred_premium_norm", "cdr_paid_premium_norm",
    ]
    correlations = {field: correlation_block(panel, field) for field in fields}
    company_effects = {field: company_correlations(panel, field) for field in fields}
    hetero = {
        field: {
            "pearson": heterogeneity(company_effects[field], "pearson"),
            "spearman": heterogeneity(company_effects[field], "spearman"),
        }
        for field in fields
    }
    comparisons = {
        "legacy_vs_adaptive_incurred_cdr": target_comparison(panel, "legacy_proxy", "cdr_incurred"),
        "adaptive_incurred_vs_paid_cdr": target_comparison(panel, "cdr_incurred", "cdr_paid"),
        "adaptive_vs_frozen_incurred_cdr": target_comparison(panel, "cdr_incurred", "cdr_incurred_frozen"),
        "adaptive_vs_frozen_paid_cdr": target_comparison(panel, "cdr_paid", "cdr_paid_frozen"),
    }
    distributions = {field: quantiles([float(row[field]) for row in panel]) for field in ["uw", *fields]}
    legacy_code_overlap = [g for g in LEGACY_PILOT_GRCODES if g in set(eligible)]

    return {
        "schema": "ffbk.clrd2025_realised_cdr_dependence.v1",
        "design": {
            "lob": lob,
            "calibration_vintage": {
                "accident_years": [OLD_START_AY, OLD_END_AY],
                "role": "fixed chronological pre-1998 calibration sample",
            },
            "evaluation_vintage": {
                "accident_years": [NEW_START_AY, NEW_END_AY],
                "evaluation_years": [EVAL_START_YEAR, EVAL_END_YEAR],
            },
            "opening_ay_rule": "all prior CLRD2025 AYs observed in the evaluation vintage; identical opening AY set at open and close valuation",
            "underwriting_proxy": "AY=t development-lag-1 net incurred / EarnedPremNet",
            "adverse_cdr_sign": "closing predicted ultimate minus opening predicted ultimate",
            "adaptive_calibration": "all old-vintage factor pairs plus new-vintage pairs visible by valuation; evaluated new-vintage company excluded from new calibration rows",
            "frozen_challenger": "old-vintage factors only",
            "company_identity_boundary": "no old-to-new company identity matching is assumed; GRCODE overlap is not treated as identity evidence",
            "classification": "real benchmark as-if-historical mean-model CDR challenge; not predictive CDR distribution or production dependence calibration",
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
            "legacy_pilot_grcode_overlap_not_identity_evidence": legacy_code_overlap,
            "minimum_factor_pair_support": support_min,
        },
        "correlations": correlations,
        "company_effects": company_effects,
        "heterogeneity": hetero,
        "target_comparisons": comparisons,
        "distributions": distributions,
    }


def json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("old_csv", type=Path)
    parser.add_argument("new_csv", type=Path)
    parser.add_argument("--lob", default=TARGET_LOB)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = run(args.old_csv, args.new_csv, lob=args.lob)
    if args.check:
        if result["panel"]["years_per_company"] != 9:
            raise AssertionError(result["panel"])
        if result["panel"]["eligible_companies"] < 2:
            raise AssertionError("too few eligible companies")
        for field in ("legacy_proxy", "cdr_incurred", "cdr_paid", "cdr_incurred_frozen"):
            for metric in ("pearson", "spearman"):
                value = result["correlations"][field]["raw"][metric]
                if not math.isfinite(value):
                    raise AssertionError(f"non-finite correlation: {field=} {metric=}")
    print(json.dumps(json_safe(result), sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
