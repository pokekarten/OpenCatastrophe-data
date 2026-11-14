# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed two-margin calibration of INDEPENDENTLY SYNTHETIC premium scenarios.

A bounded demonstration of regional x line-of-business marginal reconciliation,
not extraction of external insurer records or an inferred actual underwriting book.
Only direct gross written premiums with known risk-location geography are accepted.
An output cell is a *modelled synthetic allocation*, never an observed portfolio,
physical building TIV, risk-site list, reinsurance treaty or CAT model input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


class MarginalFitError(ValueError):
    """Insufficient semantics, inconsistent controls or numerical failure."""


def _number(value: object, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MarginalFitError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0 or (positive and result == 0):
        raise MarginalFitError(f"{name} must be finite and {'positive' if positive else 'nonnegative'}")
    return result


def _dimension(rows: object, name: str, key: str) -> dict[str, float]:
    if not isinstance(rows, list) or not rows or len(rows) > 100:
        raise MarginalFitError(f"{name} must contain 1..100 rows")
    out: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {key, "premium"}:
            raise MarginalFitError(f"{name} requires {key} and premium")
        code = row[key]
        if not isinstance(code, str) or not code or len(code) > 80 or code.strip() != code:
            raise MarginalFitError(f"invalid {key}")
        if code in out:
            raise MarginalFitError(f"duplicate {name} key: {code}")
        out[code] = _number(row["premium"], f"{name}/{code}")
    return dict(sorted(out.items()))


def fit_synthetic_marginals(scenario: dict, *, tolerance: float = 1e-10,
                            max_iterations: int = 10000) -> dict:
    """Iterative proportional fitting with hard observed-*synthetic* margins.

    Prior weights are explicitly supplied for EVERY allowed cell. A cell absent
    from the joint disclosure remains unobserved even when its fitted value is
    positive. No external source admission, original-data access or verification
    is implied by this calculation.
    """
    fields = {"schema_version", "scenario_kind", "premium_basis",
              "geography_basis", "currency", "as_of",
              "region_totals", "line_totals", "prior_weights", "structural_zeros"}
    if not isinstance(scenario, dict) or set(scenario) != fields:
        raise MarginalFitError("scenario keys must exactly match synthetic v0 contract")
    if (scenario["schema_version"] != "0.1.0"
            or scenario["scenario_kind"] != "fully_synthetic_test_only"
            or scenario["premium_basis"] != "direct_gross_written_premium"
            or scenario["geography_basis"] != "underlying_risk_location"):
        raise MarginalFitError("only direct GWP synthetic scenarios with risk situs are supported")
    currency = scenario["currency"]
    if (not isinstance(currency, str) or len(currency) != 3
            or not currency.isascii() or not currency.isupper() or not currency.isalpha()):
        raise MarginalFitError("currency must be an uppercase three-letter code")
    as_of = scenario["as_of"]
    if not isinstance(as_of, str) or len(as_of) != 10:
        raise MarginalFitError("as_of must be YYYY-MM-DD")
    try:
        from datetime import date
        if date.fromisoformat(as_of).isoformat() != as_of:
            raise ValueError("noncanonical")
    except ValueError as exc:
        raise MarginalFitError("as_of must be a valid YYYY-MM-DD") from exc

    regions = _dimension(scenario["region_totals"], "region_totals", "region")
    lines = _dimension(scenario["line_totals"], "line_totals", "line")
    row_total = math.fsum(regions.values())
    col_total = math.fsum(lines.values())
    scale = max(1.0, row_total, col_total)
    if row_total <= 0 or abs(row_total - col_total) > 1e-9 * scale:
        raise MarginalFitError("region and line GWP totals disagree")
    if not (isinstance(tolerance, (float, int)) and 0 < tolerance <= 1e-6):
        raise MarginalFitError("invalid tolerance")
    if not isinstance(max_iterations, int) or not 1 <= max_iterations <= 100000:
        raise MarginalFitError("invalid max_iterations")

    forbidden = scenario["structural_zeros"]
    if not isinstance(forbidden, list) or len(forbidden) > len(regions) * len(lines):
        raise MarginalFitError("invalid structural zeros")
    blocked: set[tuple[str, str]] = set()
    for cell in forbidden:
        if not isinstance(cell, dict) or set(cell) != {"region", "line"}:
            raise MarginalFitError("malformed structural zero")
        pair = (cell["region"], cell["line"])
        if pair in blocked or pair[0] not in regions or pair[1] not in lines:
            raise MarginalFitError("duplicate or unknown structural zero")
        blocked.add(pair)

    weights_raw = scenario["prior_weights"]
    if not isinstance(weights_raw, list) or len(weights_raw) > len(regions) * len(lines):
        raise MarginalFitError("invalid prior cells")
    weights: dict[tuple[str, str], float] = {}
    for cell in weights_raw:
        if not isinstance(cell, dict) or set(cell) != {"region", "line", "weight"}:
            raise MarginalFitError("malformed prior cell")
        pair = (cell["region"], cell["line"])
        if pair in weights or pair in blocked or pair[0] not in regions or pair[1] not in lines:
            raise MarginalFitError("duplicate, blocked or unknown prior cell")
        weights[pair] = _number(cell["weight"], "prior weight", positive=True)
    allowed = {(r, l) for r in regions for l in lines} - blocked
    if set(weights) != allowed:
        raise MarginalFitError("every allowed cell requires an explicit positive prior weight")
    for r, amount in regions.items():
        if amount > 0 and not any((r, l) in allowed and lines[l] > 0 for l in lines):
            raise MarginalFitError("region with positive premium has no feasible line")
    for l, amount in lines.items():
        if amount > 0 and not any((r, l) in allowed and regions[r] > 0 for r in regions):
            raise MarginalFitError("line with positive premium has no feasible region")

    matrix = {pair: v for pair, v in weights.items()}
    converged = False
    err = math.inf
    for iteration in range(1, max_iterations + 1):
        for r, target in regions.items():
            cells = [(r, l) for l in lines if (r, l) in matrix]
            current = math.fsum(matrix[p] for p in cells)
            if current == 0 and target > 0:
                raise MarginalFitError("row has no numerical support")
            factor = target / current if current else 0.0
            for pair in cells:
                matrix[pair] *= factor
        for l, target in lines.items():
            cells = [(r, l) for r in regions if (r, l) in matrix]
            current = math.fsum(matrix[p] for p in cells)
            if current == 0 and target > 0:
                raise MarginalFitError("column has no numerical support")
            factor = target / current if current else 0.0
            for pair in cells:
                matrix[pair] *= factor
        err = max(
            [abs(math.fsum(matrix.get((r, l), 0.0) for l in lines) - t)
             for r, t in regions.items()]
            + [abs(math.fsum(matrix.get((r, l), 0.0) for r in regions) - t)
               for l, t in lines.items()]
        )
        if err <= tolerance * scale:
            converged = True
            break
    if not converged or any(not math.isfinite(v) for v in matrix.values()):
        raise MarginalFitError("no numerically feasible fit at the declared structural zeros")

    canonical = json.dumps(scenario, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    cells = [{"region": r, "line": l, "synthetic_premium": matrix.get((r, l), 0.0),
              "structural_zero": (r, l) in blocked, "observed_joint_cell": False}
             for r in regions for l in lines]
    return {"schema_version": "0.1.0",
            "scenario_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "currency": currency, "as_of": as_of,
            "premium_basis": "direct_gross_written_premium",
            "geography_basis": "underlying_risk_location",
            "scenario_kind": "fully_synthetic_test_only",
            "cells": cells, "iterations": iteration, "max_absolute_margin_error": err,
            "observed_insurer_portfolio": False, "has_insured_tiv": False,
            "has_policy_locations": False, "has_cat_peril_allocation": False,
            "has_reinsurance_contracts": False, "model_input_approved": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path, help="independently synthetic JSON scenario")
    args = parser.parse_args()
    try:
        source = args.scenario.read_bytes()
        if len(source) > 1_000_000:
            raise MarginalFitError("scenario exceeds 1MB input cap")
        result = fit_synthetic_marginals(json.loads(source.decode("utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, MarginalFitError) as exc:
        parser.exit(status=2, message=f"BLOCKED: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
