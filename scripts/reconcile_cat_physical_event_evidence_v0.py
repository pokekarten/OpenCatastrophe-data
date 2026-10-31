#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Reconcile two original-source-bound physical CAT observations for synthetic sites.

Never merge EFFIS and CLIMK as one event, never synthesize insurer exposures,
financial loss, event-year probabilities, perils or cross-model event matching.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.effis_synthetic_point_overlay_v0 import (  # noqa: E402
    audit_synthetic_overlay, load_synthetic_sites,
)
from scripts.climk_era5_synthetic_native_sample_v0 import (  # noqa: E402
    sample_climk_era5,
)
from scripts.inspect_effis_burnt_area_v0 import retrieve_event  # noqa: E402
from scripts.inspect_climk_winds_era5_v0 import (  # noqa: E402
    fetch_provider_bytes, PINNED_SHA256,
)

SCHEMA = "oc-cross-peril-physical-event-evidence-v0"
MAX_SOURCE_BYTES = 8_000_000


class PhysicalEventEvidenceError(ValueError):
    """Source-bound observations cannot be matched without fabricating science."""


def _need(test: bool, why: str) -> None:
    if not test:
        raise PhysicalEventEvidenceError(why)


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _finite_number(value, low: float, high: float, why: str) -> float:
    _need(type(value) in (int, float) and math.isfinite(value) and low <= value <= high,
          why)
    return float(value)


def _ids(rows, field):
    _need(type(rows) is list and len(rows) > 0, "missing observation rows")
    out = []
    for row in rows:
        _need(type(row) is dict and type(row.get(field)) is str, "missing synthetic site ID")
        out.append(row[field])
    _need(out == sorted(set(out)), "source output has duplicate/unsorted synthetic sites")
    return out


def reconcile_original_physical_sources(
    *, effis_bytes: bytes, climk_era5_bytes: bytes, site_manifest_bytes: bytes,
    effis_event_id: int, climk_storm_index: int,
) -> dict:
    """Build two **separate** event records with the same synthetic site roster.

    Raw source verification is performed by the existing source-specific
    inspectors. EFFIS current REST is mutable; the exact response SHA is
    evidence of observed bytes, not an immutable vendor publication.
    """
    _need(type(effis_bytes) is bytes and 0 < len(effis_bytes) < MAX_SOURCE_BYTES,
          "EFFIS publisher source bytes absent/unbounded")
    _need(type(climk_era5_bytes) is bytes and 0 < len(climk_era5_bytes) <= MAX_SOURCE_BYTES,
          "CLIMK publisher bytes absent/unbounded")
    sites = load_synthetic_sites(site_manifest_bytes)
    site_ids = [site[0] for site in sites]
    # These calls re-validate all original data and provenance, not merely
    # accept a caller-authored JSON receipt with a plausible SHA-256.
    fire = audit_synthetic_overlay(effis_bytes, effis_event_id, site_manifest_bytes)
    wind = sample_climk_era5(original=climk_era5_bytes,
                             synthetic_sites_json=site_manifest_bytes,
                             storm_index=climk_storm_index)
    _need(_ids(fire["site_hits"], "site_id") == site_ids
          and _ids(wind["site_samples"], "site_id") == site_ids,
          "source adapters lost or reidentified a synthetic point")
    _need(fire["event_key"] == f"effis:burntarea:{effis_event_id}"
          and fire["peril"] == "WILDFIRE"
          and fire["measure"] == "BINARY_BURNT_AREA_MEMBERSHIP_NOT_INTENSITY"
          and fire["source_payload_sha256"] == _hash(effis_bytes)
          and fire["provider_source_mutable"] is True,
          "EFFIS event, intensity semantics or original source digest drift")
    _need(wind["event_key"] == f"climk-winds:v2:ERA5:storm-index:{climk_storm_index}"
          and wind["peril"] == "WINDSTORM"
          and wind["physical_intensity_unit"] == "m s**-1"
          and wind["source_sha256"] == PINNED_SHA256
          and wind["source_sha_pinned"] is True
          and wind["event_identity_cross_model_matched"] is False,
          "CLIMK event identifier, source version, units or digest drift")
    # The source sampler knows the original provider's name/date label,
    # but not a UTC instant or independently matched global storm identity.
    for key in ("source_storm_name", "source_storm_date_label"):
        label = wind.get(key)
        _need(type(label) is str and 0 < len(label) <= 120
              and label == label.strip()
              and all(32 <= ord(ch) < 127 for ch in label),
              f"CLIMK source event label missing/invalid: {key}")
    _need(wind.get("source_storm_date_parsed_as_utc") is False,
          "CLIMK date label must not be reclassified as UTC")

    for gate in ("real_exposure_used", "vulnerability_applied", "gross_loss_calculated",
                 "insured_loss_calculated", "model_admitted"):
        _need(fire.get(gate) is False, f"EFFIS financial admission gate {gate} is not false")
    for gate in ("site_asset_ownership_admitted", "source_event_frequency_inferred",
                 "damage_or_insured_loss_computed", "scientifically_admitted"):
        _need(wind.get(gate) is False, f"CLIMK financial admission gate {gate} is not false")
    _need(fire.get("site_count") == len(sites) and wind.get("site_count") == len(sites),
          "source site counts disagree")
    try:
        ts = datetime.fromisoformat(fire["event_timestamp"])
        _need(ts.tzinfo is not None and ts.utcoffset() is not None,
              "EFFIS fire timestamp lacks a timezone")
        fire_time_utc = ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, KeyError) as exc:
        raise PhysicalEventEvidenceError("EFFIS event timestamp is not grounded") from exc
    fire_rows, wind_rows = [], []
    for row in fire["site_hits"]:
        _need(type(row.get("within_observed_burnt_polygon")) is bool,
              "polygon membership must be boolean, not a loss")
        fire_rows.append({"site_id": row["site_id"],
                          "measure": "BURNED_AREA_POINT_MEMBERSHIP",
                          "unit": "boolean",
                          "value": row["within_observed_burnt_polygon"]})
    for row in wind["site_samples"]:
        _need(type(row) is dict and
              "absolute_max_gust_m_s" in row and
              "relative_max_gust_dimensionless" in row,
              "source gust measure missing")
        gust = _finite_number(row["absolute_max_gust_m_s"], 0, 200,
                              "invalid/missing absolute physical gust")
        ratio = _finite_number(row["relative_max_gust_dimensionless"], 0, 100,
                               "invalid/missing relative physical gust")
        _need(type(row.get("native_cell_x")) is int
              and type(row.get("native_cell_y")) is int
              and 0 <= row["native_cell_x"] < 269
              and 0 <= row["native_cell_y"] < 181,
              "native ERA5 location index out of range")
        # Explicit source-native cell only; no user coordinates or TIV output.
        wind_rows.append({"site_id": row["site_id"],
                          "native_grid_cell": [row["native_cell_y"], row["native_cell_x"]],
                          "measure": "STORM_FOOTPRINT_ABSOLUTE_MAX_WIND_GUST",
                          "unit": "m s**-1",
                          "value": gust,
                          "relative_98p_climatology_ratio": ratio})
    records = [
        {
            "event_key": fire["event_key"],
            "source": "EFFIS_REST_V2_CURRENT",
            "source_content_sha256": fire["source_payload_sha256"],
            "source_mutable": True,
            "peril": "WILDFIRE",
            "event_time": {"state": "PROVIDER_TIMESTAMP", "utc": fire_time_utc},
            "spatial_type": "OBSERVED_BURNT_AREA_MULTIPOLYGON",
            "observation_type": "BOOLEAN_POINT_MEMBERSHIP",
            "observations": fire_rows,
        },
        {
            "event_key": wind["event_key"],
            "source": "CLIMK_WINDS_V2_ERA5",
            "source_content_sha256": wind["source_sha256"],
            "source_mutable": False,
            "peril": "WINDSTORM",
            # The actual provider label is preserved, but it does not
            # authorize an exact UTC instant or annual event frequency.
            "event_time": {
                "state": "SOURCE_DATE_LABEL_WITHOUT_VERIFIED_UTC_INSTANT",
                "utc": None,
                "provider_date_label": wind["source_storm_date_label"],
            },
            "provider_storm_name": wind["source_storm_name"],
            "spatial_type": "NATIVE_ERA5_GRID_NEAREST_CELL",
            "observation_type": "PHYSICAL_GUST_M_S",
            "observations": wind_rows,
        },
    ]
    result = {
        "schema_version": SCHEMA,
        "status": "ORIGINAL_BYTES_BOUND_RESEARCH_PHYSICAL_EVENTS_ONLY",
        "event_identity_scope": "INDEPENDENT_PROVIDER_LOCAL_IDENTITIES",
        "shared_synthetic_site_roster_sha256": _hash(_canonical(sites)),
        "site_count": len(sites),
        "events": records,
        "events_are_the_same_physical_occurrence": False,
        "cross_peril_dependency_inferred": False,
        "event_frequency_or_simulation_year_inferred": False,
        "real_insurer_assets_mapped": False,
        "vulnerability_used": False,
        "ground_up_loss_computed": False,
        "insured_loss_computed": False,
        "reinsurance_or_retro_computed": False,
        "model_admitted": False,
    }
    result["receipt_sha256"] = _hash(_canonical(result))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites", type=Path, required=True)
    parser.add_argument("--effis-event-id", type=int, required=True)
    parser.add_argument("--climk-storm-index", type=int, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fetch", action="store_true")
    mode.add_argument("--sources-directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.fetch:
        effis = retrieve_event(args.effis_event_id)
        climk = fetch_provider_bytes()
    else:
        effis = (args.sources_directory / "EFFIS.json").read_bytes()
        climk = (args.sources_directory /
                 "ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc").read_bytes()
    out = reconcile_original_physical_sources(
        effis_bytes=effis, climk_era5_bytes=climk,
        site_manifest_bytes=args.sites.read_bytes(),
        effis_event_id=args.effis_event_id,
        climk_storm_index=args.climk_storm_index,
    )
    rendered = json.dumps(out, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.output:
        if args.output.resolve() == args.sites.resolve():
            raise PhysicalEventEvidenceError("metadata output must not replace source sites")
        if args.sources_directory and args.output.resolve() in (
            (args.sources_directory / "EFFIS.json").resolve(),
            (args.sources_directory /
             "ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc").resolve(),
        ):
            raise PhysicalEventEvidenceError("metadata output must not overwrite provider bytes")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
