#!/usr/bin/env python3
"""Bounded empirical UW/reserve-development dependence probe for CAS CLRD data.

This is an exploratory real-data challenger to the synthetic identifiability
result in reserve_underwriting_horizon_coupling_probe.py. It does not estimate
economic CDR or select a production dependence model.

Default pilot:
- legacy CAS CLRD sample bundled with chainladder-python;
- Workers' Compensation;
- seven insurer groups with a complete 1988-1997 panel and positive earned
  premium on the retained coordinates;
- observations are insurer x calendar-year pairs for 1989-1997.

For calendar year t:
  UW_t = first-reported NET incurred loss for AY=t / NET earned premium AY=t.
  LEGACY_t = sum_{AY<t}(Incurred[AY,t]-Incurred[AY,t-1])
             / sum_{AY<t} Incurred[AY,t-1].

The loss triangle is net of reinsurance in this CLRD lineage, so the primary
underwriting and premium-normalized sensitivity use EarnedPremNet. Direct
earned premium is retained only as an explicitly mismatched-basis sensitivity
for comparison with the superseded v0 pilot.

A net-premium-normalized legacy sensitivity and an unscaled emergence
sensitivity are reported. Two-way demeaning removes additive insurer and
calendar-year means from both variables before a residual correlation is
computed.

Only Python's standard library is required.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Tuple

PILOT_GRCODES = (337, 353, 388, 671, 715, 965, 1066)
DEFAULT_LOB = "wkcomp"
DEFAULT_START_AY = 1988
DEFAULT_END_AY = 1997

RowKey = Tuple[int, int, int]  # GRCODE, AccidentYear, DevelopmentYear


def _to_float(value: str) -> float:
    if value is None or value == "":
        raise ValueError("missing numeric value")
    return float(value)


def load_rows(path: Path, lob: str, grcodes: Sequence[int]) -> Tuple[Dict[RowKey, dict], Dict[int, str]]:
    wanted = set(grcodes)
    rows: Dict[RowKey, dict] = {}
    names: Dict[int, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        incurred_col = "IncurLoss" if "IncurLoss" in reader.fieldnames else "IncurredLosses"
        required = {
            "GRCODE",
            "GRNAME",
            "AccidentYear",
            "DevelopmentYear",
            "EarnedPremDIR",
            "EarnedPremNet",
            "LOB",
            incurred_col,
        }
        missing = required.difference(reader.fieldnames)
        if missing:
            raise ValueError(f"missing columns: {sorted(missing)}")
        for raw in reader:
            if raw["LOB"].strip().lower() != lob.lower():
                continue
            grcode = int(raw["GRCODE"])
            if grcode not in wanted:
                continue
            ay = int(raw["AccidentYear"])
            dy = int(raw["DevelopmentYear"])
            key = (grcode, ay, dy)
            if key in rows:
                raise ValueError(
                    "duplicate CLRD coordinate: "
                    f"GRCODE={grcode} AccidentYear={ay} DevelopmentYear={dy}"
                )
            rows[key] = {
                "incurred": _to_float(raw[incurred_col]),
                "prem_net": _to_float(raw["EarnedPremNet"]),
                "prem_dir": _to_float(raw["EarnedPremDIR"]),
            }
            names[grcode] = raw["GRNAME"].strip()
    return rows, names


def build_panel(
    rows: Mapping[RowKey, dict],
    names: Mapping[int, str],
    grcodes: Sequence[int],
    start_ay: int,
    end_ay: int,
) -> List[dict]:
    panel: List[dict] = []
    for grcode in grcodes:
        for year in range(start_ay + 1, end_ay + 1):
            current = rows.get((grcode, year, year))
            if (
                current is None
                or current["prem_net"] <= 0
                or current["prem_dir"] <= 0
            ):
                continue

            uw_net = current["incurred"] / current["prem_net"]
            uw_direct_mismatched = current["incurred"] / current["prem_dir"]

            legacy_delta = 0.0
            legacy_open_incurred = 0.0
            legacy_open_net_premium = 0.0
            legacy_open_direct_premium = 0.0
            n_legacy = 0
            complete = True
            for ay in range(start_ay, year):
                prev = rows.get((grcode, ay, year - 1))
                now = rows.get((grcode, ay, year))
                base = rows.get((grcode, ay, ay))
                if (
                    prev is None
                    or now is None
                    or base is None
                    or base["prem_net"] <= 0
                    or base["prem_dir"] <= 0
                ):
                    complete = False
                    break
                legacy_delta += now["incurred"] - prev["incurred"]
                legacy_open_incurred += prev["incurred"]
                legacy_open_net_premium += base["prem_net"]
                legacy_open_direct_premium += base["prem_dir"]
                n_legacy += 1

            if not complete or n_legacy == 0:
                continue
            if (
                legacy_open_incurred <= 0
                or legacy_open_net_premium <= 0
                or legacy_open_direct_premium <= 0
            ):
                continue

            panel.append(
                {
                    "grcode": grcode,
                    "grname": names.get(grcode, str(grcode)),
                    "year": year,
                    "uw": uw_net,
                    "uw_direct_mismatched": uw_direct_mismatched,
                    "legacy_incurred_norm": legacy_delta / legacy_open_incurred,
                    "legacy_premium_norm": legacy_delta / legacy_open_net_premium,
                    "legacy_direct_premium_norm_mismatched": (
                        legacy_delta / legacy_open_direct_premium
                    ),
                    "legacy_level": legacy_delta,
                    "legacy_open_incurred": legacy_open_incurred,
                    "legacy_open_net_premium": legacy_open_net_premium,
                    "legacy_open_direct_premium": legacy_open_direct_premium,
                }
            )
    return panel


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return float("nan")
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    sx = sum((v - mx) ** 2 for v in x)
    sy = sum((v - my) ** 2 for v in y)
    if sx <= 0 or sy <= 0:
        return float("nan")
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return cov / math.sqrt(sx * sy)


def average_ranks(values: Sequence[float]) -> List[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position + 1
        while end < len(order) and values[order[end]] == values[order[position]]:
            end += 1
        avg_rank = ((position + 1) + end) / 2.0
        for k in range(position, end):
            ranks[order[k]] = avg_rank
        position = end
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    return pearson(average_ranks(x), average_ranks(y))


def two_way_demean(panel: Sequence[dict], field: str) -> List[float]:
    by_company: Dict[int, List[float]] = defaultdict(list)
    by_year: Dict[int, List[float]] = defaultdict(list)
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


def correlation_block(
    panel: Sequence[dict],
    legacy_field: str,
    *,
    uw_field: str = "uw",
) -> dict:
    uw = [float(row[uw_field]) for row in panel]
    legacy = [float(row[legacy_field]) for row in panel]
    uw_resid = two_way_demean(panel, uw_field)
    legacy_resid = two_way_demean(panel, legacy_field)
    return {
        "n": len(panel),
        "raw": {"pearson": pearson(uw, legacy), "spearman": spearman(uw, legacy)},
        "two_way_demeaned": {
            "pearson": pearson(uw_resid, legacy_resid),
            "spearman": spearman(uw_resid, legacy_resid),
        },
    }


def company_correlations(panel: Sequence[dict], legacy_field: str) -> List[dict]:
    grouped: Dict[int, List[dict]] = defaultdict(list)
    for row in panel:
        grouped[int(row["grcode"])].append(row)
    out = []
    for grcode in sorted(grouped):
        rows = sorted(grouped[grcode], key=lambda r: int(r["year"]))
        x = [float(r["uw"]) for r in rows]
        y = [float(r[legacy_field]) for r in rows]
        out.append(
            {
                "grcode": grcode,
                "grname": rows[0]["grname"],
                "n": len(rows),
                "pearson": pearson(x, y),
                "spearman": spearman(x, y),
            }
        )
    return out


def leave_one_company_out(panel: Sequence[dict], legacy_field: str) -> List[dict]:
    grcodes = sorted({int(row["grcode"]) for row in panel})
    out = []
    for excluded in grcodes:
        subset = [row for row in panel if int(row["grcode"]) != excluded]
        block = correlation_block(subset, legacy_field)
        out.append({"excluded_grcode": excluded, **block})
    return out


def run(path: Path, lob: str, grcodes: Sequence[int], start_ay: int, end_ay: int) -> dict:
    rows, names = load_rows(path, lob, grcodes)
    panel = build_panel(rows, names, grcodes, start_ay, end_ay)
    if not panel:
        raise ValueError("no eligible insurer-year rows")
    return {
        "design": {
            "lob": lob,
            "grcodes": list(grcodes),
            "start_accident_year": start_ay,
            "end_accident_year": end_ay,
            "underwriting_proxy": (
                "first-development net incurred / net earned premium"
            ),
            "legacy_proxy": (
                "older-AY calendar-year net incurred emergence / "
                "prior-calendar-year older-AY net incurred"
            ),
            "financial_basis": (
                "primary uses net incurred with EarnedPremNet; direct-premium "
                "variants are explicitly mismatched-basis sensitivities only"
            ),
            "conditioning": "two-way additive demeaning by insurer and calendar year",
            "classification": (
                "exploratory descriptive empirical challenge; not economic CDR; "
                "not tail calibration"
            ),
        },
        "panel": {
            "n": len(panel),
            "companies": len({row["grcode"] for row in panel}),
            "years": sorted({row["year"] for row in panel}),
        },
        "primary": correlation_block(panel, "legacy_incurred_norm"),
        "sensitivities": {
            "legacy_net_premium_normalized": correlation_block(
                panel, "legacy_premium_norm"
            ),
            "legacy_unscaled_level": correlation_block(panel, "legacy_level"),
            "original_direct_premium_uw_mismatch": correlation_block(
                panel,
                "legacy_incurred_norm",
                uw_field="uw_direct_mismatched",
            ),
            "original_direct_premium_both_mismatch": correlation_block(
                panel,
                "legacy_direct_premium_norm_mismatched",
                uw_field="uw_direct_mismatched",
            ),
        },
        "per_company": company_correlations(panel, "legacy_incurred_norm"),
        "leave_one_company_out": leave_one_company_out(panel, "legacy_incurred_norm"),
    }


def json_safe(value):
    """Replace non-finite floats with JSON null while preserving structure."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    return value


def parse_grcodes(value: str) -> Tuple[int, ...]:
    out = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    if not out:
        raise argparse.ArgumentTypeError("at least one GRCODE is required")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path, help="CAS/chainladder CLRD CSV")
    parser.add_argument("--lob", default=DEFAULT_LOB)
    parser.add_argument("--grcodes", type=parse_grcodes, default=PILOT_GRCODES)
    parser.add_argument("--start-ay", type=int, default=DEFAULT_START_AY)
    parser.add_argument("--end-ay", type=int, default=DEFAULT_END_AY)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail unless the default pilot is a balanced 7x9 panel",
    )
    args = parser.parse_args()

    result = run(args.csv, args.lob, args.grcodes, args.start_ay, args.end_ay)
    if args.check:
        expected_default = (
            args.lob == DEFAULT_LOB
            and tuple(args.grcodes) == PILOT_GRCODES
            and args.start_ay == DEFAULT_START_AY
            and args.end_ay == DEFAULT_END_AY
        )
        if expected_default:
            if (
                result["panel"]["n"] != 63
                or result["panel"]["companies"] != 7
                or len(result["panel"]["years"]) != 9
            ):
                raise AssertionError(
                    "default pilot is not the expected balanced 7x9 panel: "
                    f"{result['panel']}"
                )
        if not math.isfinite(result["primary"]["raw"]["pearson"]):
            raise AssertionError("primary Pearson correlation is not finite")
        if not math.isfinite(result["primary"]["raw"]["spearman"]):
            raise AssertionError("primary Spearman correlation is not finite")

    print(
        json.dumps(
            json_safe(result),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
