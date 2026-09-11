#!/usr/bin/env python3
"""Coverage-aware wrapper for the CLRD2025 realised-CDR challenge.

Primary incurred targets keep the full structurally eligible evaluation cohort.
Paid Chain-Ladder is evaluated only where both opening models produce positive
paid ultimates. Zero early paid emergence is recorded as challenger-domain
non-coverage rather than used to select the primary cohort.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import reserve_underwriting_clrd2025_realised_cdr_probe_v2 as core


def available_rows(panel, field):
    return [row for row in panel if row.get(field) is not None and math.isfinite(float(row[field]))]


def correlation_block(panel, field):
    rows = available_rows(panel, field)
    if len(rows) < 2:
        return {"n": len(rows), "raw": {"pearson": None, "spearman": None}, "two_way_demeaned": {"pearson": None, "spearman": None}}
    return core.correlation_block(rows, field)


def company_correlations(panel, field):
    grouped = defaultdict(list)
    for row in available_rows(panel, field):
        grouped[int(row["grcode"])].append(row)
    out = []
    for grcode in sorted(grouped):
        rows = sorted(grouped[grcode], key=lambda row: int(row["year"]))
        x = [float(row["uw"]) for row in rows]
        y = [float(row[field]) for row in rows]
        out.append({
            "grcode": grcode,
            "grname": rows[0]["grname"],
            "n": len(rows),
            "pearson": core.pearson(x, y) if len(rows) >= 2 else float("nan"),
            "spearman": core.spearman(x, y) if len(rows) >= 2 else float("nan"),
        })
    return out


def target_comparison(panel, a, b):
    rows = [
        row for row in panel
        if row.get(a) is not None and row.get(b) is not None
        and math.isfinite(float(row[a])) and math.isfinite(float(row[b]))
    ]
    if len(rows) < 2:
        return {"n": len(rows), "pearson": None, "spearman": None, "sign_disagreement_rate": None, "mean_absolute_difference": None, "max_absolute_difference": None}
    x = [float(row[a]) for row in rows]
    y = [float(row[b]) for row in rows]
    comparable = [(u, v) for u, v in zip(x, y) if u != 0 and v != 0]
    disagreements = sum(1 for u, v in comparable if (u > 0) != (v > 0))
    differences = [abs(u - v) for u, v in zip(x, y)]
    return {
        "n": len(rows),
        "pearson": core.pearson(x, y),
        "spearman": core.spearman(x, y),
        "sign_disagreement_rate": disagreements / len(comparable) if comparable else None,
        "mean_absolute_difference": sum(differences) / len(differences),
        "max_absolute_difference": max(differences),
    }


def run(old_csv: Path, new_csv: Path, *, lob: str = core.TARGET_LOB):
    old_rows, _ = core.load_vintage(old_csv, lob=lob, incurred_field="IncurLoss")
    new_rows, new_names = core.load_vintage(new_csv, lob=lob, incurred_field="IncurredLosses")
    eligible = core.eligible_companies(new_rows)
    if len(eligible) < 2:
        raise ValueError(f"too few complete CLRD2025 evaluation companies: {len(eligible)}")

    frozen_inc, frozen_inc_n = core.factors_from_sums(
        core.factor_sums(old_rows, {}, field="incurred", valuation=None, exclude_new_grcode=None)
    )
    frozen_paid, frozen_paid_n = core.factors_from_sums(
        core.factor_sums(old_rows, {}, field="paid", valuation=None, exclude_new_grcode=None)
    )

    panel = []
    support_min = {
        "adaptive_incurred": 10**9,
        "adaptive_paid": 10**9,
        "frozen_incurred": min(frozen_inc_n.values()),
        "frozen_paid": min(frozen_paid_n.values()),
    }
    paid_noncoverage = []

    for grcode in eligible:
        for year in range(core.EVAL_START_YEAR, core.EVAL_END_YEAR + 1):
            open_v = year - 1
            close_v = year
            opening_ays = list(range(core.NEW_START_AY, year))

            inc_open, inc_open_n = core.factors_from_sums(
                core.factor_sums(old_rows, new_rows, field="incurred", valuation=open_v, exclude_new_grcode=grcode)
            )
            inc_close, inc_close_n = core.factors_from_sums(
                core.factor_sums(old_rows, new_rows, field="incurred", valuation=close_v, exclude_new_grcode=grcode)
            )
            paid_open, paid_open_n = core.factors_from_sums(
                core.factor_sums(old_rows, new_rows, field="paid", valuation=open_v, exclude_new_grcode=grcode)
            )
            paid_close, paid_close_n = core.factors_from_sums(
                core.factor_sums(old_rows, new_rows, field="paid", valuation=close_v, exclude_new_grcode=grcode)
            )
            support_min["adaptive_incurred"] = min(support_min["adaptive_incurred"], min(inc_open_n.values()), min(inc_close_n.values()))
            support_min["adaptive_paid"] = min(support_min["adaptive_paid"], min(paid_open_n.values()), min(paid_close_n.values()))

            inc_u_open = core.predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=open_v, field="incurred", factors=inc_open)
            inc_u_close = core.predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=close_v, field="incurred", factors=inc_close)
            frozen_inc_u_open = core.predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=open_v, field="incurred", factors=frozen_inc)
            frozen_inc_u_close = core.predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=close_v, field="incurred", factors=frozen_inc)
            premium = core.opening_premium(new_rows, grcode=grcode, opening_ays=opening_ays)
            uw_cell = new_rows[(grcode, year, 1)]
            uw = float(uw_cell["incurred"]) / float(uw_cell["prem_net"])
            if min(inc_u_open, frozen_inc_u_open, premium) <= 0:
                raise ValueError(f"non-positive primary normalization base: {grcode=} {year=}")

            paid_u_open = core.predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=open_v, field="paid", factors=paid_open)
            paid_u_close = core.predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=close_v, field="paid", factors=paid_close)
            frozen_paid_u_open = core.predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=open_v, field="paid", factors=frozen_paid)
            frozen_paid_u_close = core.predicted_ultimate(new_rows, grcode=grcode, opening_ays=opening_ays, valuation=close_v, field="paid", factors=frozen_paid)
            paid_available = paid_u_open > 0 and frozen_paid_u_open > 0
            if not paid_available:
                paid_noncoverage.append({
                    "grcode": grcode,
                    "year": year,
                    "adaptive_paid_opening_ultimate": paid_u_open,
                    "frozen_paid_opening_ultimate": frozen_paid_u_open,
                })

            panel.append({
                "grcode": grcode,
                "grname": new_names.get(grcode, str(grcode)),
                "year": year,
                "uw": uw,
                "legacy_proxy": core.legacy_proxy(new_rows, grcode=grcode, opening_ays=opening_ays, open_valuation=open_v),
                "cdr_incurred": (inc_u_close - inc_u_open) / inc_u_open,
                "cdr_incurred_frozen": (frozen_inc_u_close - frozen_inc_u_open) / frozen_inc_u_open,
                "cdr_incurred_premium_norm": (inc_u_close - inc_u_open) / premium,
                "cdr_paid": ((paid_u_close - paid_u_open) / paid_u_open) if paid_available else None,
                "cdr_paid_frozen": ((frozen_paid_u_close - frozen_paid_u_open) / frozen_paid_u_open) if paid_available else None,
                "cdr_paid_premium_norm": ((paid_u_close - paid_u_open) / premium) if paid_available else None,
            })

    fields = [
        "legacy_proxy", "cdr_incurred", "cdr_incurred_frozen", "cdr_incurred_premium_norm",
        "cdr_paid", "cdr_paid_frozen", "cdr_paid_premium_norm",
    ]
    correlations = {field: correlation_block(panel, field) for field in fields}
    company_effects = {field: company_correlations(panel, field) for field in fields}
    heterogeneity = {
        field: {
            "pearson": core.heterogeneity(company_effects[field], "pearson"),
            "spearman": core.heterogeneity(company_effects[field], "spearman"),
        }
        for field in fields
    }
    comparisons = {
        "legacy_vs_adaptive_incurred_cdr": target_comparison(panel, "legacy_proxy", "cdr_incurred"),
        "adaptive_incurred_vs_paid_cdr": target_comparison(panel, "cdr_incurred", "cdr_paid"),
        "adaptive_vs_frozen_incurred_cdr": target_comparison(panel, "cdr_incurred", "cdr_incurred_frozen"),
        "adaptive_vs_frozen_paid_cdr": target_comparison(panel, "cdr_paid", "cdr_paid_frozen"),
    }
    distributions = {
        field: core.quantiles([float(row[field]) for row in available_rows(panel, field)])
        for field in ["uw", *fields]
    }
    full_paid_companies = sum(
        1 for grcode in eligible
        if sum(1 for row in panel if int(row["grcode"]) == grcode and row["cdr_paid"] is not None) == 9
    )

    return {
        "schema": "ffbk.clrd2025_realised_cdr_dependence.v2",
        "design": {
            "lob": lob,
            "calibration_vintage": {"accident_years": [core.OLD_START_AY, core.OLD_END_AY], "role": "fixed chronological pre-1998 calibration sample"},
            "evaluation_vintage": {"accident_years": [core.NEW_START_AY, core.NEW_END_AY], "evaluation_years": [core.EVAL_START_YEAR, core.EVAL_END_YEAR]},
            "opening_ay_rule": "all prior CLRD2025 AYs observed in evaluation vintage; identical opening AY set at open and close",
            "underwriting_proxy": "AY=t lag-1 net incurred / EarnedPremNet",
            "adverse_cdr_sign": "closing predicted ultimate minus opening predicted ultimate",
            "adaptive_calibration": "old-vintage pairs plus new-vintage pairs visible by valuation, excluding evaluated company from new calibration",
            "frozen_challenger": "old-vintage factors only",
            "paid_challenger_boundary": "paid CDR unavailable where opening paid ultimate is zero; those rows remain in primary incurred cohort and are reported as non-coverage",
            "company_identity_boundary": "no old-to-new company identity match assumed",
            "classification": "real benchmark as-if-historical deterministic mean-model CDR challenge; not predictive reserve-risk distribution or production dependence calibration",
        },
        "source": {
            "old": {"bytes": old_csv.stat().st_size, "sha256": core.file_sha256(old_csv)},
            "new": {"bytes": new_csv.stat().st_size, "sha256": core.file_sha256(new_csv)},
        },
        "panel": {
            "eligible_companies": len(eligible),
            "company_year_rows": len(panel),
            "years_per_company": 9,
            "eligible_grcodes": eligible,
            "minimum_factor_pair_support": support_min,
            "paid_available_rows": len(panel) - len(paid_noncoverage),
            "paid_noncoverage_rows": len(paid_noncoverage),
            "full_nine_year_paid_companies": full_paid_companies,
            "paid_noncoverage_examples": paid_noncoverage[:20],
        },
        "correlations": correlations,
        "company_effects": company_effects,
        "heterogeneity": heterogeneity,
        "target_comparisons": comparisons,
        "distributions": distributions,
    }


def clean(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("old_csv", type=Path)
    parser.add_argument("new_csv", type=Path)
    parser.add_argument("--lob", default=core.TARGET_LOB)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = run(args.old_csv, args.new_csv, lob=args.lob)
    if args.check:
        assert result["panel"]["eligible_companies"] >= 2
        assert result["panel"]["company_year_rows"] == result["panel"]["eligible_companies"] * 9
        for field in ("legacy_proxy", "cdr_incurred", "cdr_incurred_frozen"):
            for metric in ("pearson", "spearman"):
                value = result["correlations"][field]["raw"][metric]
                assert value is not None and math.isfinite(float(value)), (field, metric, value)
    print(json.dumps(clean(result), sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
