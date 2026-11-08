# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-verified Kyrill single native ERA5 area peril -> 24 fictional assets.

This is not a complete Oasis OED, vulnerability calibration, GUL calculation,
financial contract, carrier-specific portfolio or annual loss/EP simulation.
The two research-only map points intentionally coincide in one native cell.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal
import hashlib
import io
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research_runners.climk_era5_original_oasis_tile_v0 import source_to_tile
from research_runners.wisc_netcdf_oasis_tile_v0 import bins_from_text
from scripts.climk_era5_synthetic_native_sample_v0 import sample_climk_era5
from scripts.inspect_climk_winds_era5_v0 import PINNED_SHA256, fetch_provider_bytes, verify_source_bytes

SITES = (
    ("SYNTH_CLIMK_A", 5.958677287830914, 52.41546239242131),
    ("SYNTH_CLIMK_B", 6.02, 52.47),
)
STORM_INDEX = 0
EXPECTED_NAME = "KYRILL"
EXPECTED_DATE_LABEL = "20070118"
EXPECTED_CELL_XY = (112, 78)
GRID_NX = 269
AREA_PERIL = 78 * GRID_NX + 112 + 1
ASSETS = 24
REPLACEMENT_EUR = 10_000_000
BIN_EDGES = "0,10,20,30,40,50,60,80,120,200"
CSV_FIELDS = ("asset_id", "synthetic_site_id", "source_storm_index_zero_based",
              "areaperil_id", "replacement_cost_eur", "source_gust_m_s")

class CrosswalkError(ValueError):
    """One physical cell cannot be reconciled to the fictional research roster."""


def synthetic_sites_bytes() -> bytes:
    obj = {"schema_version": "oc-effis-synthetic-sites-v0", "crs": "OGC:CRS84",
           "synthetic_only": True,
           "sites": [{"site_id": sid, "longitude": lon, "latitude": lat}
                     for sid, lon, lat in SITES]}
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def _original_csv_rows(data: bytes, expected: list[str]) -> list[dict[str, str]]:
    if not isinstance(data, bytes) or len(data) > 10_000:
        raise CrosswalkError("unbounded hazard CSV")
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""), strict=True)
        if reader.fieldnames != expected:
            raise CrosswalkError("source hazard CSV headers differ from native Oasis fields")
        rows = list(reader)
    except (UnicodeError, csv.Error) as exc:
        raise CrosswalkError("hazard CSV parsing failed") from exc
    if not rows or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise CrosswalkError("hazard CSV missing or ragged values")
    return rows


def crosswalk(sample: dict, tile_files: dict[str, bytes], tile_receipt: dict) -> tuple[bytes, dict]:
    """Strict pure reconciliation; original provider bytes must be verified by caller."""
    if type(sample) is not dict or type(tile_receipt) is not dict:
        raise CrosswalkError("source sample and original tile receipt required")
    fixed = {
        "source_sha256": PINNED_SHA256,
        "source_sha_pinned": True,
        "source_storm_name": EXPECTED_NAME,
        "source_storm_date_label": EXPECTED_DATE_LABEL,
        "storm_index_zero_based": STORM_INDEX,
        "event_identity_cross_model_matched": False,
        "source_event_frequency_inferred": False,
        "scientifically_admitted": False,
        "site_count": 2,
    }
    if any(type(sample.get(k)) is not type(v) or sample.get(k) != v for k,v in fixed.items()):
        raise CrosswalkError("original source storm or annual status drifted")
    expected_tile = {
        "original_sha256_verified": PINNED_SHA256,
        "storm_index_zero_based": STORM_INDEX,
        "original_storm_name": EXPECTED_NAME,
        "original_storm_date_label": EXPECTED_DATE_LABEL,
        "grid_shape": [181, 269],
        "tile": {"row_start": 78, "col_start": 112, "height": 1, "width": 1},
        "valid_gust_cells": 1,
        "unknown_weather_cells": 0,
        "annual_oep_aep_authorized": False,
        "native_oasis_full_model_run_verified": False,
    }
    if any(tile_receipt.get(k) != v for k,v in expected_tile.items()):
        raise CrosswalkError("source tile identity or native hazard cell mismatched")
    if type(tile_files) is not dict or set(tile_files) != {
        "events.csv", "footprint.csv", "intensity_bin_dict.csv", "areaperil_dict.csv"
    }:
        raise CrosswalkError("four exact original hazard CSVs required")
    for name,raw in tile_files.items():
        meta = tile_receipt.get("output_files", {}).get(name)
        if not isinstance(meta,dict) or meta.get("bytes") != len(raw) or meta.get("sha256") != hashlib.sha256(raw).hexdigest():
            raise CrosswalkError("source hazard CSV not bound to original tile receipt")
    rows = _original_csv_rows(
        tile_files["footprint.csv"],
        ["event_id", "areaperil_id", "intensity_bin_id", "probability"],
    )
    if len(rows) != 1 or rows[0] != {
        "event_id": "1", "areaperil_id": str(AREA_PERIL),
        "intensity_bin_id": "4", "probability": "1.0",
    }:
        raise CrosswalkError("Kyrill original physical cell not identical to Oasis footprint bin")
    locations = _original_csv_rows(
        tile_files["areaperil_dict.csv"],
        ["areaperil_id", "latitude", "longitude", "source_row", "source_col"],
    )
    if len(locations) != 1 or locations[0].get("areaperil_id") != str(AREA_PERIL) or locations[0].get("source_row") != "78" or locations[0].get("source_col") != "112":
        raise CrosswalkError("source original native geogrid index does not match Oasis area peril")

    site_samples = sample.get("site_samples")
    if type(site_samples) is not list or len(site_samples) != 2:
        raise CrosswalkError("both source-native synthetic site samples required")
    sites_seen = set()
    gusts = []
    for site in site_samples:
        if type(site) is not dict:
            raise CrosswalkError("source site metadata malformed")
        sid = site.get("site_id")
        if sid not in {x[0] for x in SITES} or sid in sites_seen:
            raise CrosswalkError("source site missing, duplicated or unexpected")
        sites_seen.add(sid)
        if (type(site.get("native_cell_x")) is not int or
            type(site.get("native_cell_y")) is not int or
            (site["native_cell_x"], site["native_cell_y"]) != EXPECTED_CELL_XY):
            raise CrosswalkError("one or both supposedly distinct sites are NOT in the original same cell")
        raw_gust = site.get("absolute_max_gust_m_s")
        if type(raw_gust) is not float or not math.isfinite(raw_gust) or not 30 < raw_gust < 40:
            raise CrosswalkError("original source gust not in bin 4")
        gusts.append(raw_gust)
    if sites_seen != {x[0] for x in SITES} or gusts[0] != gusts[1]:
        raise CrosswalkError("two fictional points have different or unknown native wind intensities")
    gust = gusts[0]

    sink = io.StringIO(newline="")
    writer = csv.writer(sink, lineterminator="\n")
    writer.writerow(CSV_FIELDS)
    for i in range(ASSETS):
        site_id = SITES[i % len(SITES)][0]
        writer.writerow([f"SYNTH_BUILDING_{i:02d}",site_id,STORM_INDEX,
                         AREA_PERIL,REPLACEMENT_EUR,repr(gust)])
    out = sink.getvalue().encode("utf-8")
    result = {
        "profile": "climk_kyrill_original_native_one_cell_24_fictional_assets_crosswalk_v0",
        "status": "source_sample_and_oasis_hazard_cell_reconciled_not_model_loss",
        "source_sha256_claim_checked_against_two_receipts": PINNED_SHA256,
        "source_storm_name": EXPECTED_NAME,
        "original_date_label": EXPECTED_DATE_LABEL,
        "source_storm_index_zero_based": STORM_INDEX,
        "source_native_cell_x": 112, "source_native_cell_y": 78,
        "oasis_areaperil_id": AREA_PERIL,
        "source_gust_m_s": gust,
        "oasis_intensity_bin_id": 4,
        "fictional_site_markers": 2,
        "distinct_physical_hazard_cells": 1,
        "fictional_asset_count": 24,
        "fictional_tiv_eur": ASSETS * REPLACEMENT_EUR,
        "crosswalk_csv_bytes": len(out),
        "crosswalk_csv_sha256": hashlib.sha256(out).hexdigest(),
        "original_provider_bytes_independently_verified_by_pure_function": False,
        "annual_oep_aep_authorized": False,
        "insurer_loss_and_vulnerability_calibrated": False,
        "native_full_oasis_gul_il_ri_verified": False,
        "financial_treaty_and_portfolio_approved": False,
        "real_insurer_locations_verified": False,
        "external_original_assets_committed": False,
    }
    return out, result


def run_original() -> tuple[bytes, dict, dict[str, bytes]]:
    original = fetch_provider_bytes()
    evidence = verify_source_bytes(original, require_sha256=True)
    if evidence["sha256_observed"] != PINNED_SHA256:
        raise CrosswalkError("original provider bytes are not the frozen source")
    sample = sample_climk_era5(
        original=original, synthetic_sites_json=synthetic_sites_bytes(), storm_index=0,
    )
    hazard, receipt = source_to_tile(
        original, storm_index=0, row_start=78, col_start=112, height=1, width=1,
        edges=bins_from_text(BIN_EDGES),
    )
    csv_bytes, result = crosswalk(sample, hazard, receipt)
    # A third, independent original-NetCDF index read verifies no aliasing or
    # accidental use of an unrelated cell when joining the two source paths.
    from netCDF4 import Dataset
    with Dataset("original-climk-crosswalk", mode="r", memory=original) as ds:
        observed = float(ds.variables["absolute_maxwindgusts"][0,78,112])
    if observed != result["source_gust_m_s"]:
        raise CrosswalkError("independent original NetCDF native 3D source gust disagrees with both site samples")
    result["original_provider_bytes_independently_verified_in_this_run"] = True
    result["original_source_gust_triple_sample_verified"] = True
    result["native_csv_converter_expected_not_executed_by_python_runner"] = True
    return csv_bytes, result, hazard


def main(argv: list[str] | None = None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True,
                   help="new directory outside repository; never overwrite")
    args=p.parse_args(argv)
    try:
        if args.out.exists() or args.out.is_symlink() or not args.out.parent.is_dir():
            raise CrosswalkError("output must be a new directory in an existing parent")
        site_csv, report, hazard = run_original()
        args.out.mkdir()
        (args.out/"fictional_asset_peril_crosswalk.csv").write_bytes(site_csv)
        for name,body in sorted(hazard.items()):
            (args.out/name).write_bytes(body)
        (args.out/"crosswalk_receipt.json").write_text(
            json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",
        )
        print(json.dumps(report,sort_keys=True,allow_nan=False))
        return 0
    except (CrosswalkError,OSError,ValueError,RuntimeError) as exc:
        print(json.dumps({"status":"blocked","reason":str(exc)},sort_keys=True),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
