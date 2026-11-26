#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Run an original CLIMK Kyrill source cell through one synthetic native Oasis GUL.

The 24 fictional EUR10m test locations, deterministic authored vulnerability,
Oasis cell geometry and one historical event form a conditional scenario only.
No annual frequency, company exposure, calibrated loss, IL or RI is estimated.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
import hashlib
from importlib import metadata
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODEL_COMMIT = "94820c59f169b222d4c1a72256ff0a8f86a9e5bf"
OASIS_VERSION = "2.5.8"
SOURCE_SHA256 = "92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102"
SOURCE_STORM_INDEX = 0
SOURCE_ROW = 78
SOURCE_COL = 112
AREAPERIL_ID = 21095
STORM_NAME = "KYRILL"
STORM_DATE_LABEL = "20070118"  # preserve as source text; not a trusted UTC date
ASSET_COUNT = 24
ASSET_TIV_EUR = 10_000_000
SITES = (
    ("SYNTH_CLIMK_A", 5.958677287830914, 52.41546239242131),
    ("SYNTH_CLIMK_B", 6.02, 52.47),
)
INTENSITY_EDGES = "0,35.21054,35.21055,200"
DAMAGE_KNOTS = ((0, 0), (15_000, 0), (25_000, 100),
                (35_000, 2_000), (200_000, 10_000))
EXPECTED_OUTPUT = "gul_S1_splt.csv"
EXPECTED_OUTPUT_FIELDS = ("Period", "PeriodWeight", "EventId", "Year", "Month",
                         "Day", "Hour", "Minute", "SummaryId", "SampleId",
                         "Loss", "ImpactedExposure")


class KyrillNativeGULError(ValueError):
    """Original-source, keying, native execution or output contract failed."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_site_json() -> bytes:
    obj = {
        "schema_version": "oc-effis-synthetic-sites-v0",
        "crs": "OGC:CRS84",
        "synthetic_only": True,
        "sites": [
            {"site_id": ident, "longitude": lon, "latitude": lat}
            for ident, lon, lat in SITES
        ],
    }
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def authored_damage_ratio(gust_m_s: float) -> float:
    """Interpolate the explicitly uncalibrated authored VLT in integer mm/s/bps."""
    if type(gust_m_s) is not float or not 0 <= gust_m_s <= 200:
        raise KyrillNativeGULError("source gust is outside authored VLT bounds")
    gust_mm_s = int((Decimal(str(gust_m_s)) * 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if gust_mm_s > DAMAGE_KNOTS[-1][0]:
        raise KyrillNativeGULError("authored VLT does not permit extrapolation")
    for (lo_x, lo_y), (hi_x, hi_y) in zip(DAMAGE_KNOTS, DAMAGE_KNOTS[1:]):
        if gust_mm_s <= hi_x:
            bps = Fraction(lo_y) + Fraction(gust_mm_s - lo_x, hi_x - lo_x) * (hi_y - lo_y)
            return float(bps / 10_000)
    raise KyrillNativeGULError("gust was not covered by authored VLT")


def synthetic_location_csv() -> bytes:
    fields = ["PortNumber", "AccNumber", "LocNumber", "CountryCode",
              "Latitude", "Longitude", "OccupancyCode", "ConstructionCode",
              "LocPerilsCovered", "BuildingTIV", "OtherTIV", "ContentsTIV",
              "BITIV", "LocCurrency", "OEDVersion"]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for index in range(ASSET_COUNT):
        _, lon, lat = SITES[index // (ASSET_COUNT // len(SITES))]
        writer.writerow({
            "PortNumber": 1, "AccNumber": "SYNTH_KYRILL_1",
            "LocNumber": f"SYNTH_{index:02d}", "CountryCode": "NL",
            "Latitude": repr(lat), "Longitude": repr(lon),
            "OccupancyCode": 1000, "ConstructionCode": 5000,
            "LocPerilsCovered": "WEC", "BuildingTIV": ASSET_TIV_EUR,
            "OtherTIV": 0, "ContentsTIV": 0, "BITIV": 0,
            "LocCurrency": "EUR", "OEDVersion": "latest version",
        })
    return output.getvalue().encode("utf-8")


def validate_gul_output(raw: bytes, *, expected_loss: float,
                        expected_tiv: float) -> list[dict[str, str]]:
    if type(raw) is not bytes or not 1 <= len(raw) <= 1_000_000:
        raise KyrillNativeGULError("GUL output missing or outside bounded size")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""), strict=True)
        if tuple(reader.fieldnames or ()) != EXPECTED_OUTPUT_FIELDS:
            raise KyrillNativeGULError("GUL output header differs from expected Oasis PLT schema")
        rows = list(reader)
    except (UnicodeError, csv.Error) as exc:
        raise KyrillNativeGULError("GUL output CSV is malformed") from exc
    if not rows:
        raise KyrillNativeGULError("GUL output has no data rows")
    if len(rows) != 2:
        raise KyrillNativeGULError("expected deterministic summary and one sample row")
    if {row["EventId"] for row in rows} != {"1"} or {row["SampleId"] for row in rows} != {"-1", "1"}:
        raise KyrillNativeGULError("native output event/sample identity changed")
    for row in rows:
        try:
            loss, tiv = Decimal(row["Loss"]), Decimal(row["ImpactedExposure"])
        except Exception as exc:
            raise KyrillNativeGULError("GUL output has nonnumeric loss/TIV") from exc
        if not loss.is_finite() or loss < 0 or not tiv.is_finite() or tiv != Decimal(str(expected_tiv)):
            raise KyrillNativeGULError("GUL output exposure differs from synthetic TIV")
        if abs(float(loss) - expected_loss) > 10.0:
            raise KyrillNativeGULError("native GUL differs from authored curve by more than EUR 10")
    if Decimal(rows[0]["Loss"]) != Decimal(rows[1]["Loss"]):
        raise KyrillNativeGULError("deterministic authored severity produced inconsistent sample loss")
    return rows


def _write(path: Path, content: bytes) -> None:
    if path.exists() or path.is_symlink():
        raise KyrillNativeGULError(f"refuse to overwrite existing file: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _pin_piwind(piwind_dir: Path) -> str:
    result = subprocess.run(["git", "-C", str(piwind_dir), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True, timeout=15)
    if result.stdout.strip() != MODEL_COMMIT:
        raise KyrillNativeGULError("OasisPiWind scaffold does not match pinned Git commit")
    return result.stdout.strip()


def _cell_polygon(latitude: list[float], longitude: list[float]):
    from shapely.geometry import Point, Polygon
    def axis_bounds(values: list[float], index: int) -> tuple[float, float]:
        if index <= 0 or index >= len(values) - 1:
            raise KyrillNativeGULError("cell requires adjacent native coordinate centers")
        first, center, after = values[index - 1:index + 2]
        a, b = (first + center) / 2, (center + after) / 2
        return min(a, b), max(a, b)
    lat_low, lat_high = axis_bounds(latitude, SOURCE_ROW)
    lon_low, lon_high = axis_bounds(longitude, SOURCE_COL)
    polygon = Polygon([(lon_low, lat_low), (lon_high, lat_low),
                       (lon_high, lat_high), (lon_low, lat_high),
                       (lon_low, lat_low)])
    if not polygon.is_valid or polygon.area <= 0:
        raise KyrillNativeGULError("original source cell polygon is invalid")
    for _, lon, lat in SITES:
        if not polygon.covers(Point(lon, lat)):
            raise KyrillNativeGULError("a synthetic marker falls outside the source cell polygon")
    return polygon


def _prepare_model(root: Path, *, piwind_dir: Path, hazard: dict[str, bytes],
                   gust: float, polygon) -> dict[str, object]:
    import geopandas as gpd

    root.mkdir(parents=True, exist_ok=False)
    for folder in ("meta-data", "keys_data/CLIMK", "model_data/CLIMK", "tests/inputs"):
        (root / folder).mkdir(parents=True, exist_ok=False)
    shutil.copyfile(piwind_dir / "meta-data/model_settings.json", root / "meta-data/model_settings.json")
    shutil.copyfile(piwind_dir / "keys_data/PiWind/lookup_config.json", root / "keys_data/CLIMK/lookup_config.json")

    lookup_dir = root / "keys_data/CLIMK"
    lookup_config = json.loads((lookup_dir / "lookup_config.json").read_text(encoding="utf-8"))
    lookup_config["model"] = {"supplier_id": "OpenCatastrophe", "model_id": "CLIMKKyrillSynthetic", "model_version": "0.1.0"}
    lookup_config["keys_data_path"] = "./"
    lookup_config["step_definition"]["peril"]["parameters"]["file_path"] = "%%KEYS_DATA_PATH%%/areaperil_dict.parquet"
    lookup_config["step_definition"]["peril"]["parameters"]["file_type"] = "parquet"
    lookup_config["step_definition"]["split_loc_perils_covered"]["parameters"]["model_perils_covered"] = ["WEC"]
    lookup_config["step_definition"]["vulnerability"]["parameters"]["file_path"] = "%%KEYS_DATA_PATH%%/vulnerability_dict.csv"
    (lookup_dir / "lookup_config.json").write_text(json.dumps(lookup_config, indent=2) + "\n", encoding="utf-8")
    model_settings = json.loads((root / "meta-data/model_settings.json").read_text(encoding="utf-8"))
    model_settings["model_settings"]["event_set"]["default"] = "p"
    model_settings["model_settings"]["event_set"]["options"] = [{"id": "p", "desc": "single conditional Kyrill source event", "number_of_events": 1}]
    model_settings["model_settings"]["event_occurrence_id"]["default"] = "lt"
    model_settings["model_settings"]["event_occurrence_id"]["options"] = [{"id": "lt", "desc": "placeholder occurrence only; no annual frequency"}]
    model_settings["lookup_settings"]["supported_perils"] = [{"id": "WEC", "desc": "European windstorm scenario", "peril_correlation_group": 1}]
    model_settings["correlation_settings"] = [{"peril_correlation_group": 1, "damage_correlation_value": "0.0", "hazard_correlation_value": "0.0"}]
    (root / "meta-data/model_settings.json").write_text(json.dumps(model_settings, indent=2) + "\n", encoding="utf-8")
    _write(lookup_dir / "ModelVersion.csv", b"OpenCatastrophe,CLIMKKyrillSynthetic,0.1.0\n")
    _write(lookup_dir / "vulnerability_dict.csv", b"PERIL_ID,COVERAGE_TYPE,OCCUPANCYCODE,VULNERABILITY_ID\nWEC,1,1000,1\nWEC,3,1000,1\n")
    geodata = gpd.GeoDataFrame([{"peril_id": "WEC", "area_peril_id": AREAPERIL_ID, "geometry": polygon}], geometry="geometry", crs="EPSG:4326")
    geodata.to_parquet(lookup_dir / "areaperil_dict.parquet", index=False)
    _write(lookup_dir / "areaperil_dict.csv", hazard["areaperil_dict.csv"])

    model_dir = root / "model_data/CLIMK"
    _write(model_dir / "events_p.csv", hazard["events.csv"])
    _write(model_dir / "occurrence_lt.csv", b"event_id,period_no,occ_year,occ_month,occ_day\n1,1,1,1,1\n")
    _write(model_dir / "footprint.csv", hazard["footprint.csv"])
    _write(model_dir / "intensity_bin_dict.csv", hazard["intensity_bin_dict.csv"])
    ratio = authored_damage_ratio(gust)
    _write(model_dir / "damage_bin_dict.csv", ("bin_index,bin_from,bin_to,interpolation,damage_type\n"
        f"1,0,0,0,0\n2,{ratio:.12f},{ratio:.12f},{ratio:.12f},0\n3,1,1,1,0\n").encode())
    _write(model_dir / "vulnerability.csv", b"vulnerability_id,intensity_bin_id,damage_bin_id,probability\n1,1,1,1.0\n1,2,2,1.0\n1,3,3,1.0\n")
    locations = synthetic_location_csv()
    _write(root / "tests/inputs/SourceLocOEDSynthetic.csv", locations)
    _write(root / "analysis_settings.json", json.dumps({
        "version": "3", "analysis_tag": "climk_kyrill_synthetic_conditional_gul",
        "source_tag": "CLIMK-WINDS-v2-ERA5-KYRILL", "model_name_id": "CLIMKKyrillSynthetic",
        "model_supplier_id": "OpenCatastrophe", "gul_threshold": 0, "gul_output": True,
        "model_settings": {"event_set": "p", "event_occurrence_id": "lt"},
        "gul_summaries": [{"id": 1, "ord_output": {"plt_sample": True}}],
        "il_output": False, "ri_output": False, "number_of_samples": 1,
    }, indent=2).encode() + b"\n")
    _write(root / "oasislmf.json", json.dumps({
        "analysis_settings_json": "analysis_settings.json", "lookup_config_json": "keys_data/CLIMK/lookup_config.json",
        "lookup_data_dir": "keys_data/CLIMK", "model_data_dir": "model_data/CLIMK",
        "model_settings_json": "meta-data/model_settings.json", "oed_location_csv": "tests/inputs/SourceLocOEDSynthetic.csv",
        "gulmc": True, "ktools_alloc_rule_gul": 1, "intermediary_csv": True,
    }, indent=2).encode() + b"\n")
    _write(root / "currency_settings.json", b'{"currency_conversion_type":"DictBasedCurrencyRates","source_type":"csv","file_path":"tests/inputs/roe.csv"}\n')
    _write(root / "tests/inputs/roe.csv", b"cur_from,cur_to,roe\nEUR,EUR,1\n")

    env = os.environ.copy()
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    converter = shutil.which("csvtobin", path=env["PATH"])
    if not converter:
        raise KyrillNativeGULError("Oasis csvtobin executable is not on PATH")
    conversions = [
        [converter, "eve", "-i", "events_p.csv", "-o", "events_p.bin"],
        [converter, "occurrence", "-P", "1", "-i", "occurrence_lt.csv", "-o", "occurrence_lt.bin"],
        [converter, "footprint", "-m", "3", "-i", "footprint.csv", "-o", "footprint.bin", "-x", "footprint.idx"],
        [converter, "damagebin", "-i", "damage_bin_dict.csv", "-o", "damage_bin_dict.bin"],
        [converter, "vulnerability", "-d", "3", "-i", "vulnerability.csv", "-o", "vulnerability.bin"],
    ]
    for command in conversions:
        subprocess.run(command, cwd=model_dir, env=env, check=True, capture_output=True, timeout=60)
    binaries = ("events_p.bin", "occurrence_lt.bin", "footprint.bin", "footprint.idx", "damage_bin_dict.bin", "vulnerability.bin")
    if any(not (model_dir / name).is_file() or (model_dir / name).stat().st_size <= 0 for name in binaries):
        raise KyrillNativeGULError("native model input binary missing/empty after csvtobin")
    return {"damage_ratio": ratio, "location_sha256": sha256(locations),
            "input_sha256": {name: sha256((model_dir / name).read_bytes()) for name in (
                "events_p.csv", "occurrence_lt.csv", "footprint.csv", "intensity_bin_dict.csv",
                "damage_bin_dict.csv", "vulnerability.csv")}}


def _native_run(root: Path, *, timeout_seconds: int, expected_loss: float) -> dict[str, object]:
    cli = shutil.which("oasislmf")
    if not cli:
        raise KyrillNativeGULError("oasislmf executable is not on PATH")
    if metadata.version("oasislmf") != OASIS_VERSION:
        raise KyrillNativeGULError("installed OasisLMF differs from pinned 2.5.8")
    if (root / "runs").exists():
        raise KyrillNativeGULError("refusing a model directory that already contains runs")
    log_path = root.parent / f"{root.name}-native.log"
    env = os.environ.copy()
    env.update({"NUMBA_NUM_THREADS": "2", "OMP_NUM_THREADS": "2"})
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    started = time.monotonic()
    try:
        with log_path.open("xb") as log:
            proc = subprocess.run([cli, "model", "run", "-C", "oasislmf.json", "--check-oed"],
                                  cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
                                  timeout=timeout_seconds, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise KyrillNativeGULError("native Oasis model run failed to start or timed out") from exc
    duration = round(time.monotonic() - started, 3)
    if proc.returncode != 0:
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-5000:]
        raise KyrillNativeGULError(f"native Oasis exited {proc.returncode}; log tail:\n{tail}")
    matches = list((root / "runs").glob("*/output/" + EXPECTED_OUTPUT))
    if len(matches) != 1:
        raise KyrillNativeGULError("expected exactly one native GUL sample-PLT output")
    raw = matches[0].read_bytes()
    output_rows = validate_gul_output(raw, expected_loss=expected_loss, expected_tiv=ASSET_COUNT * ASSET_TIV_EUR)
    input_dir = matches[0].parents[1] / "input"
    import pandas as pd
    keys = pd.read_parquet(input_dir / "keys.parquet")
    errors = pd.read_parquet(input_dir / "keys-errors.parquet")
    coverages = pd.read_csv(input_dir / "coverages.csv")
    if len(keys) != 48 or keys["LocID"].nunique() != ASSET_COUNT or len(errors) != 0:
        raise KyrillNativeGULError("Oasis key count/errors differ from 24 locations × 2 coverages")
    if len(coverages) != ASSET_COUNT or abs(float(coverages["tiv"].sum()) - ASSET_COUNT * ASSET_TIV_EUR) > 0.01:
        raise KyrillNativeGULError("Oasis coverage records do not conserve synthetic TIV")
    return {"duration_seconds": duration, "output_path": str(matches[0]),
            "output_sha256": sha256(raw), "output_bytes": len(raw),
            "output_rows": len(output_rows), "gul_eur": float(output_rows[0]["Loss"]),
            "keys": len(keys), "key_errors": len(errors), "coverage_rows": len(coverages),
            "tiv_eur": float(coverages["tiv"].sum())}


def run(*, piwind_dir: Path, work_dir: Path, timeout_seconds: int = 300) -> dict[str, object]:
    if not 30 <= timeout_seconds <= 900:
        raise KyrillNativeGULError("timeout must be in [30, 900] seconds")
    commit = _pin_piwind(piwind_dir)
    from research_runners.climk_era5_original_oasis_tile_v0 import source_to_tile
    from research_runners.wisc_netcdf_oasis_tile_v0 import bins_from_text
    from scripts.climk_era5_synthetic_native_sample_v0 import sample_climk_era5
    from scripts.inspect_climk_winds_era5_v0 import fetch_provider_bytes, verify_source_bytes
    original = fetch_provider_bytes()
    source_receipt = verify_source_bytes(original, require_sha256=True)
    if source_receipt["sha256_observed"] != SOURCE_SHA256:
        raise KyrillNativeGULError("CLIMK source bytes differ from the pinned original")
    sample = sample_climk_era5(original=original, synthetic_sites_json=source_site_json(), storm_index=SOURCE_STORM_INDEX)
    if sample["source_storm_name"] != STORM_NAME or sample["source_storm_date_label"] != STORM_DATE_LABEL:
        raise KyrillNativeGULError("original CLIMK event identity changed")
    points = sample["site_samples"]
    if len(points) != 2 or any((x["native_cell_x"], x["native_cell_y"]) != (SOURCE_COL, SOURCE_ROW) for x in points):
        raise KyrillNativeGULError("the two synthetic points no longer map to the pinned original cell")
    gusts = {x["absolute_max_gust_m_s"] for x in points}
    if len(gusts) != 1:
        raise KyrillNativeGULError("same-cell synthetic markers have inconsistent source gusts")
    gust = points[0]["absolute_max_gust_m_s"]
    hazard, tile_receipt = source_to_tile(original, storm_index=SOURCE_STORM_INDEX,
        row_start=SOURCE_ROW, col_start=SOURCE_COL, height=1, width=1,
        edges=bins_from_text(INTENSITY_EDGES))
    if tile_receipt["original_sha256_verified"] != SOURCE_SHA256 or tile_receipt["valid_gust_cells"] != 1 or tile_receipt["unknown_weather_cells"] != 0:
        raise KyrillNativeGULError("original hazard cell receipt failed source gate")
    if list(csv.DictReader(io.StringIO(hazard["footprint.csv"].decode()))) != [{"event_id":"1","areaperil_id":str(AREAPERIL_ID),"intensity_bin_id":"2","probability":"1.0"}]:
        raise KyrillNativeGULError("fine-bin Oasis hazard mapping differs from the original source gust")
    from netCDF4 import Dataset
    with Dataset("climk-native-gul", mode="r", memory=original) as ds:
        direct = float(ds.variables["absolute_maxwindgusts"][SOURCE_STORM_INDEX,SOURCE_ROW,SOURCE_COL])
        latitude = [float(x) for x in ds.variables["latitude"][:]]
        longitude = [float(x) for x in ds.variables["longitude"][:]]
    if direct != gust:
        raise KyrillNativeGULError("direct original NetCDF value differs from point sample")
    polygon = _cell_polygon(latitude, longitude)
    if work_dir.exists() or work_dir.is_symlink() or not work_dir.parent.is_dir():
        raise KyrillNativeGULError("work_dir must be a new directory under an existing parent")
    work_dir.mkdir()
    runs = []
    for i in (1, 2):
        root = work_dir / f"run-{i}"
        built = _prepare_model(root, piwind_dir=piwind_dir, hazard=hazard, gust=gust, polygon=polygon)
        outcome = _native_run(root, timeout_seconds=timeout_seconds, expected_loss=ASSET_COUNT * ASSET_TIV_EUR * authored_damage_ratio(gust))
        runs.append({"input_sha256": built["input_sha256"], **outcome})
    if runs[0]["output_sha256"] != runs[1]["output_sha256"]:
        raise KyrillNativeGULError("fresh deterministic GUL runs did not produce byte-identical output")
    expected_loss = ASSET_COUNT * ASSET_TIV_EUR * authored_damage_ratio(gust)
    ratio = authored_damage_ratio(gust)
    return {
        "profile": "climk-kyrill-single-event-native-oasis-gul-synthetic-v0",
        "status": "native_gul_completed_twice_identical_output_synthetic_uncalibrated_not_annual",
        "source_sha256": SOURCE_SHA256, "source_storm": STORM_NAME,
        "source_storm_date_label": STORM_DATE_LABEL, "source_storm_index_zero_based": SOURCE_STORM_INDEX,
        "source_grid_row": SOURCE_ROW, "source_grid_col": SOURCE_COL, "gust_m_s": gust,
        "areaperil_id": AREAPERIL_ID, "intensity_bin_id": 2, "intensity_bin_bounds_m_s": [35.21054,35.21055],
        "synthetic_asset_count": ASSET_COUNT, "synthetic_tiv_eur": ASSET_COUNT * ASSET_TIV_EUR,
        "assumed_damage_ratio": ratio, "analytical_expected_gul_eur": expected_loss,
        "native_rounding_tolerance_eur": 10.0, "runs": runs,
        "repeat_output_sha256_matches": True,
        "model_scaffold_repository": "OasisLMF/OasisPiWind", "model_scaffold_commit": commit,
        "oasislmf_version": metadata.version("oasislmf"),
        "annual_frequency_inferred": False, "annual_aal_oep_aep_authorized": False,
        "empirical_vulnerability_calibration_verified": False, "real_insurer_exposure_verified": False,
        "il_or_ri_included": False, "policy_or_reinsurance_terms_verified": False,
        "source_bytes_committed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--piwind-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args(argv)
    try:
        if args.receipt.exists() or args.receipt.is_symlink() or not args.receipt.parent.is_dir():
            raise KyrillNativeGULError("receipt must be a new file under an existing parent")
        receipt = run(piwind_dir=args.piwind_dir.resolve(), work_dir=args.work_dir.resolve(), timeout_seconds=args.timeout_seconds)
        payload = json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n"
        with args.receipt.open("x", encoding="utf-8") as handle:
            handle.write(payload)
        print(payload, end="")
        return 0
    except (KyrillNativeGULError, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status":"blocked","reason":str(exc)},sort_keys=True),file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
