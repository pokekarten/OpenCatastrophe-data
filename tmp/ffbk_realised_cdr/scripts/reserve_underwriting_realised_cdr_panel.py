#!/usr/bin/env python3
"""Build a source-bound realised one-year CDR panel from legacy CAS CLRD.

Bounded research bridge only. The reserve target is constructed on the same
opening accident-year population at t-1 and t. Reserve factors are fit using
information available at each cutoff only, then re-fit after the next calendar
diagonal arrives. No downstream dependence target is used to fit reserve means.

For each company x LoB x calendar year t:
    CDR_t = paid during t on opening AY set
            + closing reserve_t on same opening AY set
            - opening reserve_{t-1}
          = closing finite-horizon ultimate_t - opening ultimate_{t-1}.

Two predeclared paid mean models are emitted:
- volume: volume-weighted age-to-age paid development factors;
- median: median individual age-to-age paid development ratios.

The terminal horizon is a finite maturity age, not an assertion of economic
ultimate. Default maturity age 5 is fixed before target inspection and permits
five rolling years (1993-1997) in the admitted 1988-1997 pilot window.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SOURCE_REPOSITORY = "casact/chainladder-python"
SOURCE_COMMIT = "221c4015d7d33c8520f57e3b522970f2e8baffab"
SOURCE_PATH = "chainladder/utils/data/clrd.csv"
SOURCE_BYTES = 3235366
SOURCE_GIT_BLOB_SHA1 = "04e54cfa41e7bd879877e5c5aea5e63a6d20d29b"
SOURCE_SHA256 = "5785a95d5d24943f601a9c46b83cb313ba5109a374331a71e28a86eb702d9eef"
PILOT_GRCODES = (337, 353, 388, 671, 715, 965, 1066)
DEFAULT_LOB = "wkcomp"
DEFAULT_START_AY = 1988
DEFAULT_END_AY = 1997
DEFAULT_MATURITY_AGE = 5
MODELS = ("volume", "median")


@dataclass(frozen=True)
class Cell:
    grcode: int
    grname: str
    lob: str
    ay: int
    calendar: int
    incurred: float
    paid: float
    prem_net: float

    @property
    def age(self) -> int:
        return self.calendar - self.ay + 1


def _finite(raw: str, name: str) -> float:
    if raw is None or raw == "":
        raise ValueError(f"missing {name}")
    x = float(raw)
    if not math.isfinite(x):
        raise ValueError(f"non-finite {name}")
    return x


def source_identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    git_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    sha256 = hashlib.sha256(data).hexdigest()
    return {"bytes": len(data), "git_blob_sha1": git_blob, "sha256": sha256}


def verify_source(path: Path) -> dict[str, object]:
    ident = source_identity(path)
    expected = {
        "bytes": SOURCE_BYTES,
        "git_blob_sha1": SOURCE_GIT_BLOB_SHA1,
        "sha256": SOURCE_SHA256,
    }
    if ident != expected:
        raise ValueError(f"source identity mismatch: {ident}")
    return ident


def load_cells(path: Path, lob: str, grcodes: Iterable[int]) -> dict[tuple[int, int, int], Cell]:
    wanted = set(grcodes)
    cells: dict[tuple[int, int, int], Cell] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        required = {
            "GRCODE", "GRNAME", "AccidentYear", "DevelopmentYear", "LOB",
            "IncurLoss", "CumPaidLoss", "EarnedPremNet",
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
            cal = int(raw["DevelopmentYear"])
            cell = Cell(
                grcode=grcode,
                grname=raw["GRNAME"].strip(),
                lob=raw["LOB"].strip().lower(),
                ay=ay,
                calendar=cal,
                incurred=_finite(raw["IncurLoss"], "IncurLoss"),
                paid=_finite(raw["CumPaidLoss"], "CumPaidLoss"),
                prem_net=_finite(raw["EarnedPremNet"], "EarnedPremNet"),
            )
            if cell.age < 1:
                raise ValueError("development/calendar coordinate precedes accident year")
            key = (grcode, ay, cal)
            if key in cells:
                raise ValueError(f"duplicate CLRD coordinate: {key}")
            cells[key] = cell
    if not cells:
        raise ValueError("no selected CLRD cells")
    return cells


def fit_factors(
    cells: dict[tuple[int, int, int], Cell],
    grcode: int,
    cutoff: int,
    maturity_age: int,
    model: str,
) -> dict[int, float]:
    if model not in MODELS:
        raise ValueError(f"unsupported reserve model: {model}")
    factors: dict[int, float] = {}
    for age in range(1, maturity_age):
        pairs: list[tuple[float, float]] = []
        for (g, ay, cal), current in cells.items():
            if g != grcode or current.age != age or cal > cutoff:
                continue
            nxt = cells.get((g, ay, cal + 1))
            if nxt is None or nxt.calendar > cutoff or nxt.age != age + 1:
                continue
            if current.paid <= 0 or nxt.paid < 0:
                continue
            pairs.append((current.paid, nxt.paid))
        if not pairs:
            raise ValueError(f"no development pairs grcode={grcode} cutoff={cutoff} age={age}")
        if model == "volume":
            denominator = sum(a for a, _ in pairs)
            if denominator <= 0:
                raise ValueError("non-positive volume denominator")
            factor = sum(b for _, b in pairs) / denominator
        else:
            factor = statistics.median(b / a for a, b in pairs)
        if not math.isfinite(factor) or factor <= 0:
            raise ValueError("invalid development factor")
        factors[age] = factor
    return factors


def ultimate_from_latest(paid: float, age: int, maturity_age: int, factors: dict[int, float]) -> float:
    if age > maturity_age:
        raise ValueError("latest age exceeds declared finite maturity")
    ultimate = paid
    for a in range(age, maturity_age):
        ultimate *= factors[a]
    return ultimate


def build_row(
    cells: dict[tuple[int, int, int], Cell],
    grcode: int,
    lob: str,
    year: int,
    start_ay: int,
    maturity_age: int,
    model: str,
) -> dict[str, object]:
    opening_cutoff = year - 1
    opening_factors = fit_factors(cells, grcode, opening_cutoff, maturity_age, model)
    closing_factors = fit_factors(cells, grcode, year, maturity_age, model)

    # Same opening population: claims with positive reserve horizon at t-1.
    opening_ays = list(range(max(start_ay, year - maturity_age + 1), year))
    if not opening_ays:
        raise ValueError("empty opening AY population")

    opening_ultimate = 0.0
    closing_ultimate = 0.0
    opening_paid = 0.0
    closing_paid = 0.0
    grname = None
    for ay in opening_ays:
        op = cells.get((grcode, ay, opening_cutoff))
        cl = cells.get((grcode, ay, year))
        if op is None or cl is None:
            raise ValueError(f"missing opening/closing cell grcode={grcode} ay={ay} year={year}")
        if op.age >= maturity_age:
            raise ValueError("opening population unexpectedly contains mature AY")
        if cl.age > maturity_age:
            raise ValueError("closing age exceeds finite maturity")
        grname = grname or op.grname
        opening_paid += op.paid
        closing_paid += cl.paid
        opening_ultimate += ultimate_from_latest(op.paid, op.age, maturity_age, opening_factors)
        closing_ultimate += ultimate_from_latest(cl.paid, cl.age, maturity_age, closing_factors)

    opening_reserve = opening_ultimate - opening_paid
    closing_reserve = closing_ultimate - closing_paid
    paid_during_year = closing_paid - opening_paid
    cdr = paid_during_year + closing_reserve - opening_reserve
    direct_difference = closing_ultimate - opening_ultimate
    scale = max(1.0, abs(cdr), abs(direct_difference))
    if abs(cdr - direct_difference) > 1e-10 * scale:
        raise AssertionError("CDR algebra identity failed")

    uw_cell = cells.get((grcode, year, year))
    if uw_cell is None or uw_cell.prem_net <= 0:
        raise ValueError(f"missing/non-positive underwriting coordinate grcode={grcode} year={year}")
    uw = uw_cell.incurred / uw_cell.prem_net
    if not math.isfinite(uw) or not math.isfinite(cdr):
        raise ValueError("non-finite panel target")

    return {
        "company": str(grcode),
        "company_name": grname or str(grcode),
        "lob": lob,
        "year": year,
        "uw": uw,
        "cdr": cdr,
        "shared_driver": float(year - start_ay),
        "reserve_model": model,
        "maturity_age": maturity_age,
        "opening_ays": opening_ays,
        "opening_ultimate": opening_ultimate,
        "closing_ultimate": closing_ultimate,
        "opening_reserve": opening_reserve,
        "closing_reserve": closing_reserve,
        "paid_during_year": paid_during_year,
    }


def build_panel(
    cells: dict[tuple[int, int, int], Cell],
    lob: str,
    grcodes: Iterable[int],
    start_ay: int,
    end_ay: int,
    maturity_age: int,
    model: str,
) -> list[dict[str, object]]:
    first_year = start_ay + maturity_age
    rows: list[dict[str, object]] = []
    for grcode in grcodes:
        for year in range(first_year, end_ay + 1):
            rows.append(build_row(cells, grcode, lob, year, start_ay, maturity_age, model))
    return rows


def write_preflight_panel(path: Path, rows: list[dict[str, object]]) -> None:
    fields = ["company", "lob", "year", "uw", "cdr", "shared_driver"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fields})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--lob", default=DEFAULT_LOB)
    parser.add_argument("--grcodes", default=",".join(map(str, PILOT_GRCODES)))
    parser.add_argument("--start-ay", type=int, default=DEFAULT_START_AY)
    parser.add_argument("--end-ay", type=int, default=DEFAULT_END_AY)
    parser.add_argument("--maturity-age", type=int, default=DEFAULT_MATURITY_AGE)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--check-source", action="store_true")
    args = parser.parse_args()

    if args.maturity_age < 2:
        raise ValueError("maturity age must be >= 2")
    grcodes = tuple(int(x.strip()) for x in args.grcodes.split(",") if x.strip())
    ident = verify_source(args.csv) if args.check_source else source_identity(args.csv)
    cells = load_cells(args.csv, args.lob, grcodes)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {
        "schema": "ffbk.reserve_underwriting.realised_cdr_panel.v0",
        "classification": "BOUNDED_REAL_DATA_TARGET_CONSTRUCTION_NO_PROMOTION",
        "source": {
            "repository": SOURCE_REPOSITORY,
            "commit": SOURCE_COMMIT,
            "path": SOURCE_PATH,
            **ident,
        },
        "design": {
            "lob": args.lob,
            "grcodes": list(grcodes),
            "start_ay": args.start_ay,
            "end_ay": args.end_ay,
            "maturity_age": args.maturity_age,
            "target": "paid during year + closing reserve - opening reserve on same opening AY population",
            "underwriting": "first-development net incurred / net earned premium",
            "shared_driver": "calendar-year offset from fixed start AY; deterministic time-trend challenger only",
            "reserve_models": list(MODELS),
        },
        "models": {},
    }
    for model in MODELS:
        rows = build_panel(cells, args.lob, grcodes, args.start_ay, args.end_ay, args.maturity_age, model)
        panel_path = args.output_dir / f"realised_cdr_panel_{model}.csv"
        write_preflight_panel(panel_path, rows)
        summary["models"][model] = {
            "rows": len(rows),
            "companies": len({r["company"] for r in rows}),
            "years": sorted({int(r["year"]) for r in rows}),
            "panel_sha256": hashlib.sha256(panel_path.read_bytes()).hexdigest(),
            "cdr_mean": sum(float(r["cdr"]) for r in rows) / len(rows),
        }
    summary_path = args.output_dir / "realised_cdr_panel_summary.json"
    summary_path.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
