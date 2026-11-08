# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""10k fictional-year nine-site OED -> invented hazard/curve -> GUL -> toy CAT-XL.

Reuses the already merged nine-site OED fixture and the already reviewed
synthetic damage-ratio bridge. Does NOT run OasisLMF or a physical CAT model,
does NOT use actual Berlin wind/flood intensity, insurer shares, policies,
building geocodes, model keys, contractual occurrences or valid treaties.
No external inputs, network, database, third-party assets or file outputs.
"""
from __future__ import annotations

import hashlib
from collections import Counter
from decimal import Decimal
from typing import Any

from research_runners import wbm_like_nine_fictional_oed_v0 as portfolio
from research_runners.synthetic_ci_curve_catxl_bridge_v0 import (
    fictional_event_loss_cells,
)
from research_runners.synthetic_neon_10k_curve_gul_bridge_v0 import (
    _percentile_disc, synthetic_curve_for_factor, TOY_HAZARD_UNIT,
)

WORLDS = 10_000
RECIPE = "OC-NINE-UNAFFILIATED-FICTIONAL-10K-V0"
PERIL_THRESHOLD = (("flood", 13), ("windstorm", 26))
# Invented per-event loss allocation. NO actual policy FM or reinsurance.
TOY_ATTACHMENT_EUR = 5_000_000
TOY_OCCURRENCE_LIMIT_EUR = 5_000_000
TOY_ANNUAL_AGGREGATE_LIMIT_EUR = 10_000_000


def _hash(source: str) -> bytes:
    # MD5 is a deterministic pseudorandom *toy* seed, never source integrity.
    return hashlib.md5(source.encode("ascii")).digest()


def original_fictional_positions() -> dict[str, int]:
    """Require exact previously validated nine OED records with invented TIV."""
    locations, accounts, manifest = portfolio.prepare()
    portfolio.validate(locations, accounts, manifest)
    positions = {
        f"SYNTH-{i:02d}": int(row["BuildingTIV"])
        for i, row in enumerate(locations, 1)
    }
    if (len(positions) != 9 or sum(positions.values()) != 108_000_000
            or len({row["LocNumber"] for row in locations}) != 9):
        raise ValueError("fictional exposure nine-location identity or TIV mismatch")
    return positions


def toy_year_financial(events: tuple[tuple[str, int], ...]) -> dict[str, Any]:
    """Single fictional year: gross=GUL by EXPLICIT fake zero-deductible rule.

    Per-event CAT-XL: (gross-5m)+ capped at 5m; first and only *free*
    reinstatement is modelled by 10m aggregate annual cession capacity.
    No premium, hours clause, deductible, reinstatement price or signed
    participation share. Zero-event years must remain in AEP/OEP.
    """
    if type(events) is not tuple or len(events) > 2:
        raise ValueError("fictional events must be tuple with max two events")
    if any(type(x) is not tuple or len(x) != 2
           or x[0] not in ("flood", "windstorm")
           or type(x[1]) is not int or not 0 <= x[1] <= 108_000_000
           for x in events):
        raise ValueError("unsupported invented event or gross loss amount")
    names = tuple(x[0] for x in events)
    if names != tuple(sorted(set(names))):
        raise ValueError("fictional event perils must be unique and sorted")
    gross = ceded = max_gross = max_net = 0
    per_event = []
    for peril, loss in events:
        prospective = min(max(loss - TOY_ATTACHMENT_EUR, 0),
                          TOY_OCCURRENCE_LIMIT_EUR)
        remaining = TOY_ANNUAL_AGGREGATE_LIMIT_EUR - ceded
        cession = min(prospective, remaining)
        net = loss - cession
        if not 0 <= cession <= prospective <= loss or net + cession != loss:
            raise AssertionError("toy event GUL/ceded/net not conserved")
        gross += loss
        ceded += cession
        max_gross = max(max_gross, loss)
        max_net = max(max_net, net)
        per_event.append({
            "peril": peril, "gross_eur": loss,
            "ceded_eur": cession, "net_eur": net,
        })
    if (not 0 <= ceded <= TOY_ANNUAL_AGGREGATE_LIMIT_EUR
            or sum(e["net_eur"] for e in per_event) + ceded != gross):
        raise AssertionError("toy annual gross/ceded/net not conserved")
    return {
        "gross_eur": gross, "ceded_eur": ceded, "net_eur": gross - ceded,
        "occurrence_gross_max_eur": max_gross,
        "occurrence_net_max_eur": max_net,
        "events": per_event,
    }


def replay() -> dict[str, Any]:
    """Replay 10,000 wholly invented deterministic annual worlds."""
    positions = original_fictional_positions()
    annual_gross = []
    annual_net = []
    annual_ogross = []
    annual_onet = []
    counts: Counter[str] = Counter()
    perils_gross: Counter[str] = Counter()
    events_count = zero_years = both = 0
    total_ceded = 0
    annual_rows: list[str] = []
    event_rows: list[str] = []

    for year in range(WORLDS):
        events = []
        for peril, threshold in PERIL_THRESHOLD:
            random = _hash(f"{RECIPE}|{year}|{peril}")
            if random[0] >= threshold:
                continue
            score = 1 + random[1] % 5
            # Local susceptibility changes the *fictional damage curve*
            # rather than changing the common invented intensity index.
            factor_assets: dict[int, dict[str, int]] = {1:{}, 2:{}, 3:{}}
            for asset in positions:
                local = _hash(f"{RECIPE}|local|{year}|{peril}|{asset}")
                factor = 1 + local[2] % 3
                factor_assets[factor][asset] = score
            cells = {}
            for factor, intensities in factor_assets.items():
                if intensities:
                    cells.update(fictional_event_loss_cells(
                        positions_eur=positions,
                        intensities=intensities,
                        curve_points=synthetic_curve_for_factor(factor),
                        source_curve_id=f"SYNTH-NINE-FACTOR-{factor}",
                        asset_class="SYNTH-UNAFFILIATED-COMMERCIAL",
                        curve_unit=TOY_HAZARD_UNIT,
                        event_unit=TOY_HAZARD_UNIT,
                        output_metric="fractional_damage_ratio",
                    ))
            if set(cells) != set(positions):
                raise AssertionError("fictional event must cover exactly nine locations")
            amount = sum(cells.values())
            if amount < 0 or amount > sum(positions.values()):
                raise AssertionError("toy GUL out of source fictitious bounds")
            events.append((peril, amount))
            counts[peril] += 1
            perils_gross[peril] += amount

        year_result = toy_year_financial(tuple(events))
        if len(events) == 0:
            zero_years += 1
        if len(events) == 2:
            both += 1
        events_count += len(events)
        if year_result["gross_eur"] != year_result["net_eur"]+year_result["ceded_eur"]:
            raise AssertionError("annual toy CAT-XL conservation failed")
        annual_gross.append(year_result["gross_eur"])
        annual_net.append(year_result["net_eur"])
        annual_ogross.append(year_result["occurrence_gross_max_eur"])
        annual_onet.append(year_result["occurrence_net_max_eur"])
        total_ceded += year_result["ceded_eur"]
        annual_rows.append(
            f'{year}:{year_result["gross_eur"]}:{year_result["ceded_eur"]}:'
            f'{year_result["net_eur"]}:{year_result["occurrence_gross_max_eur"]}:'
            f'{year_result["occurrence_net_max_eur"]}:{len(events)}')
        for event in year_result["events"]:
            event_rows.append(
                f'{year}:{event["peril"]}:{event["gross_eur"]}:'
                f'{event["ceded_eur"]}:{event["net_eur"]}')

    gross_total = sum(annual_gross)
    net_total = sum(annual_net)
    if (gross_total != net_total + total_ceded
            or sum(perils_gross.values()) != gross_total
            or zero_years + events_count - both != WORLDS):
        raise AssertionError("fictional 10k annual/peril aggregation failed")
    return {
        "schema_version": "OC_NINE_FICTIONAL_OED_10K_HAZARD_CURVE_GUL_CATXL_V0",
        "classification": "REPRODUCIBLE_TOY_ANNUAL_GUL_AND_CATXL_NOT_A_PHYSICAL_MODEL",
        "worlds": WORLDS,
        "invented_asset_count": len(positions),
        "invented_building_total_eur": sum(positions.values()),
        "fictional_event_count": events_count,
        "zero_event_years": zero_years,
        "years_with_two_perils": both,
        "peril_event_counts": dict(sorted(counts.items())),
        "peril_gul_totals_eur": dict(sorted(perils_gross.items())),
        "toy_gul_aggregate_eur": gross_total,
        "toy_insured_gross_aggregate_eur": gross_total,
        "toy_ceded_aggregate_eur": total_ceded,
        "toy_net_aggregate_eur": net_total,
        "toy_gross_aal_eur": str(Decimal(gross_total) / WORLDS),
        "toy_net_aal_eur": str(Decimal(net_total) / WORLDS),
        "toy_aep99_gross_eur": _percentile_disc(annual_gross, 99, 100),
        "toy_aep995_gross_eur": _percentile_disc(annual_gross, 995, 1000),
        "toy_oep99_gross_eur": _percentile_disc(annual_ogross, 99, 100),
        "toy_oep995_gross_eur": _percentile_disc(annual_ogross, 995, 1000),
        "toy_aep99_net_eur": _percentile_disc(annual_net, 99, 100),
        "toy_aep995_net_eur": _percentile_disc(annual_net, 995, 1000),
        "toy_oep99_net_eur": _percentile_disc(annual_onet, 99, 100),
        "toy_oep995_net_eur": _percentile_disc(annual_onet, 995, 1000),
        "toy_catxl_attachment_per_event_eur": TOY_ATTACHMENT_EUR,
        "toy_catxl_per_occurrence_limit_eur": TOY_OCCURRENCE_LIMIT_EUR,
        "toy_catxl_annual_aggregate_limit_eur": TOY_ANNUAL_AGGREGATE_LIMIT_EUR,
        "toy_annual_aggregate_resets_each_world": True,
        "toy_insured_gross_equals_gul_by_invented_zero_deductible_assumption": True,
        "toy_hash_event_probability_is_calibrated": False,
        "toy_curve_is_empirically_validated": False,
        "oasis_engine_executed": False,
        "actual_hazard_vulnerability_or_model_keys_used": False,
        "real_insurer_or_policy_TIV_used": False,
        "real_contract_coinsurance_or_reinsurance_verified": False,
        "physical_event_occurrence_hours_clause_verified": False,
        "commercial_or_real_CAT_model_input_approved": False,
        "md5_seed_is_provider_data_authentication": False,
        "toy_annual_rows_sha256": hashlib.sha256(
            "|".join(annual_rows).encode("ascii")).hexdigest(),
        "toy_event_rows_sha256": hashlib.sha256(
            "|".join(event_rows).encode("ascii")).hexdigest(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(replay(), sort_keys=True, indent=2))
