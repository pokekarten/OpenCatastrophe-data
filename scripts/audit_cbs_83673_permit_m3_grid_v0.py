# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed official CBS 83673NED permit EUR/m3 regional/tenure receipt.

Original CBS OData-v4 table 83673NED is a rolling permit-budgets statistic
for PURE new-housing projects, >=EUR50k, excluding VAT. It is NOT a
reconstruction cost, insurance TIV, market price, loss payout or replacement
rate applicable to mixed-use, pre-existing or unusual buildings.

Accepts only exact, separately acquired CBS /Properties and bounded
/Observations filtered on Measure=M002974, Perioden=2026VJ06. Checks
the dated CBS version, license, units and exact 2x5 region/tenure grid.
Prints only the public aggregate official data with non-admission flags.
No web calls, no per-property data, no insurer, no scenario building allocation.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys

TABLE = "83673NED"
RELEASE_VERSION = "202608200000"
MEASURE = "M002974"
PERIOD = "2026VJ06"
TENURES = {
    "A028867": "rental_new_housing",
    "A028868": "owner_occupied_new_housing",
}
REGIONS = {
    "NL01": "netherlands",
    "LD01": "north",
    "LD02": "east",
    "LD03": "west",
    "LD04": "south",
}
MIN_COST = Decimal("10")
MAX_COST = Decimal("10000")
MAX_BYTES = 300_000
EXPECTED_COMBINATIONS = {(t, r) for t in TENURES for r in REGIONS}


class CbsPermitCostError(ValueError):
    """Unreviewed source revision, incompatible metric or incomplete grid."""


def _unique(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise CbsPermitCostError("duplicate CBS JSON key")
        result[k] = v
    return result


def _bad_constant(_):
    raise CbsPermitCostError("nonfinite CBS JSON value")


def read(path):
    raw = Path(path).read_bytes()
    if not raw or len(raw) > MAX_BYTES:
        raise CbsPermitCostError("missing or oversized CBS source bytes")
    return (
        json.loads(raw.decode("utf-8"), object_pairs_hook=_unique,
                   parse_constant=_bad_constant),
        hashlib.sha256(raw).hexdigest(),
    )


def audit(properties, observations):
    if not isinstance(properties, dict) or not isinstance(observations, dict):
        raise CbsPermitCostError("CBS source metadata and observations required")
    if properties.get("Identifier") != TABLE:
        raise CbsPermitCostError("wrong CBS table identifier")
    if properties.get("Version") != RELEASE_VERSION:
        raise CbsPermitCostError("unreviewed CBS data revision")
    if properties.get("License") != "https://creativecommons.org/licenses/by/4.0/":
        raise CbsPermitCostError("missing original CBS CC BY 4.0 metadata")
    if properties.get("Modified") != "2026-08-20T00:00:00+02:00":
        raise CbsPermitCostError("source modified timestamp drift")
    if "@odata.nextLink" in observations:
        raise CbsPermitCostError("truncated result page")
    values = observations.get("value")
    if not isinstance(values, list) or len(values) != 10:
        raise CbsPermitCostError("must contain all ten bounded 2x5 CBS observations")
    grid = {}
    for row in values:
        if not isinstance(row, dict):
            raise CbsPermitCostError("invalid observation")
        if (row.get("Measure") != MEASURE or row.get("Perioden") != PERIOD):
            raise CbsPermitCostError("wrong source unit/measure or period")
        ten, reg = row.get("Eigendom"), row.get("RegioS")
        if (ten, reg) not in EXPECTED_COMBINATIONS or (ten, reg) in grid:
            raise CbsPermitCostError("unknown or duplicated tenure/region observation")
        if row.get("ValueAttribute") not in ("None", None):
            raise CbsPermitCostError("unreported or suppressed value in original CBS cell")
        x = row.get("Value")
        if isinstance(x, bool) or not isinstance(x, (int, float, str)):
            raise CbsPermitCostError("missing CBS EUR/m3 value")
        try:
            cost = Decimal(str(x))
        except InvalidOperation as exc:
            raise CbsPermitCostError("not a numeric CBS EUR/m3 value") from exc
        if not cost.is_finite() or not MIN_COST <= cost <= MAX_COST:
            raise CbsPermitCostError("implausible or nonfinite permit EUR/m3 value")
        grid[(ten, reg)] = cost
    if set(grid) != EXPECTED_COMBINATIONS:
        raise CbsPermitCostError("incomplete CBS tenure/region grid")
    # These are publicly released aggregate statistics, never individual
    # building/provider-unit observations. Keep values in original source unit.
    return {
        "schema": "cbs-83673ned-permit-cost-per-m3-grid-receipt-v0",
        "original_table": TABLE,
        "original_version": RELEASE_VERSION,
        "measure_code": MEASURE,
        "original_measure_semantics": "average_new_housing_permit_building_cost_eur_per_m3_ex_vat",
        "period": PERIOD,
        "rolling_period_start": "2025-07",
        "rolling_period_end": "2026-06",
        "data_provisional": True,
        "original_cc_by_4_metadata_verified": True,
        "observation_grid_complete": True,
        "number_of_aggregate_observations": len(grid),
        "prices_eur_per_m3": {
            REGIONS[region]: {
                TENURES[tenure]: str(grid[(tenure, region)])
                for tenure in TENURES
            }
            for region in REGIONS
        },
        "new_housing_permit_only": True,
        "valid_for_existing_building_rebuild_cost_directly": False,
        "valid_for_mixed_use_or_historic_reinstatement_directly": False,
        "real_insured_tiv_calculated": False,
        "unapproved_lod_volume_multiplication_blocked": True,
        "source_admitted": False,
        "scientific_review_approved": False,
        "model_input_approved": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--properties", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        p, ph = read(args.properties)
        o, oh = read(args.observations)
        result = audit(p, o)
        result["properties_source_sha256"] = ph
        result["observations_source_sha256"] = oh
    except (ValueError, OSError, UnicodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
