# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-bound Ciara 2020 northern-France 72h gust observation envelope.

One verified official Météo-France original archive is read in ephemeral
memory per run. Output is source-identity + non-identifying aggregates only.
This is NOT a calibrated grid footprint, independent sensor attestation,
annual EP frequency estimate, insured loss, or permission to redistribute.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime
import gzip
import io
import json
import math
import sys

from research_runners.meteofrance_hourly_gust_v0 import (
    Blocked, CATALOGUE_URL, DOCUMENT_URL, MAX_CATALOGUE_BYTES,
    MAX_DOCUMENT_BYTES, _read_url, verify_dictionary,
)
from research_runners import meteofrance_four_north_original_v0 as fr
from research_runners.meteofrance_north_hourly_catalogue_v0 import audit_catalogue

START_UTC = datetime(2020, 2, 9, 0)
END_UTC_EXCLUSIVE = datetime(2020, 2, 12, 0)
HOURS = 72
EVENT = "Ciara/Sabine 2020, 9-11 February fixed observation envelope"
MAX_WINDOW_STATION_HOURS = 80_000


def _peak_band(value: float) -> str:
    if value < 20:
        return "below_20_mps"
    if value < 30:
        return "20_to_below_30_mps"
    if value < 40:
        return "30_to_below_40_mps"
    return "40_mps_or_more"


def event_envelope(department: str, original: bytes) -> dict:
    """Validate *all* original rows first, then summarize only fixed event hours."""
    # Existing bounded full-original scanner checks exact original SHA256, CSV,
    # station IDs, every real-calendar UTC hour, wind units and gust flags.
    receipt = fr.audit_original(department, original)
    observed_hours: dict[str, set[str]] = {}
    valid_hours: dict[str, set[str]] = {}
    peak_by_station: dict[str, float] = {}
    seen: set[tuple[str, str]] = set()
    quality: Counter[str] = Counter()
    derived = not_transfer = valid = count = 0
    max_gust: float | None = None
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(original)) as gz:
            bounded = fr.LimitedInflation(gz, fr.MAX_INFLATED)
            with io.TextIOWrapper(io.BufferedReader(bounded), encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream, delimiter=";")
                if reader.fieldnames is None or any(f not in reader.fieldnames for f in fr.FIELDS):
                    raise Blocked("original event source missing required schema")
                for row in reader:
                    stamp = row["AAAAMMJJHH"].strip()
                    # Full original already calendar-validated; the lexicographic
                    # fixed-hour filter is exact for YYYYMMDDHH in a single year.
                    if not ("2020020900" <= stamp < "2020021200"):
                        continue
                    station = row["NUM_POSTE"].strip()
                    key = station, stamp
                    if key in seen:
                        raise Blocked("duplicate source station-hour in event envelope")
                    seen.add(key)
                    count += 1
                    if count > MAX_WINDOW_STATION_HOURS:
                        raise Blocked("event source station-hour cap exceeded")
                    observed_hours.setdefault(station, set()).add(stamp)
                    q = row["QFXI3S"].strip() or "missing"
                    quality[q] += 1
                    raw = row["FXI3S"].strip()
                    if not raw or q not in ("0", "1"):
                        continue
                    gust = float(raw)
                    if not math.isfinite(gust) or not 0 <= gust <= 120:
                        raise Blocked("invalid event-window FXI3S")
                    status = row["STATUS_FXI3S"].strip()
                    if status not in ("0", "1"):
                        raise Blocked("quality-passed event FXI3S has unknown transfer status")
                    valid += 1
                    if status == "1":
                        derived += 1
                    else:
                        not_transfer += 1
                    valid_hours.setdefault(station, set()).add(stamp)
                    peak_by_station[station] = max(peak_by_station.get(station, gust), gust)
                    max_gust = gust if max_gust is None else max(max_gust, gust)
    except (OSError, EOFError, UnicodeError, csv.Error) as exc:
        raise Blocked("event envelope gzip/CSV stream failed") from exc
    if not count or not valid or not observed_hours:
        raise Blocked("selected original source has no valid Ciara-window FXI3S")
    if derived + not_transfer != valid:
        raise Blocked("event FXI3S calculation lineage is incomplete")
    peak_bins = dict(sorted(Counter(_peak_band(v) for v in peak_by_station.values()).items()))
    return {
        "profile": "meteofrance-ciara2020-northern-four-hourly-envelope-v0",
        "window_start_utc_inclusive": START_UTC.isoformat() + "Z",
        "window_end_utc_exclusive": END_UTC_EXCLUSIVE.isoformat() + "Z",
        "nominal_hours": HOURS,
        "event_name_for_context_only": EVENT,
        "department": department,
        "original_gzip_sha256": receipt["original_gzip_sha256"],
        "original_gzip_bytes": receipt["original_gzip_bytes"],
        "original_sha256_pinned": receipt["original_sha256_pinned"],
        "station_hour_rows_in_window": count,
        "stations_with_any_hour": len(observed_hours),
        "stations_with_full_72_hour_labels": sum(len(x) == HOURS for x in observed_hours.values()),
        "quality_checked_three_second_gusts": valid,
        "quality_checked_hourly_station_count": len(valid_hours),
        "quality_checked_full_72_hour_stations": sum(len(x) == HOURS for x in valid_hours.values()),
        "quality_checked_gust_peak_mps": max_gust,
        "station_quality_checked_peak_bins": peak_bins,
        "quality_counts_all_window_rows": dict(sorted(quality.items())),
        "transfer_derived_valid_gusts": derived,
        "not_transfer_derived_valid_gusts": not_transfer,
        "station_ids_or_locations_disclosed": False,
        "observation_hour_to_era5_interval_equivalence_proven": False,
        "station_site_and_sensor_history_verified": False,
        "original_rows_stored_or_distributed": False,
        "source_admitted": False,
        "hazard_calibration_authorized": False,
        "annual_ep_authorized": False,
        "insured_loss_calibration_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--department", required=True, choices=sorted(fr.ASSETS))
    p.add_argument("--live", action="store_true", required=True,
                   help="manual or explicitly PR-bounded one original provider file")
    args = p.parse_args(argv)
    try:
        catalog = audit_catalogue(_read_url(CATALOGUE_URL, MAX_CATALOGUE_BYTES))
        fr.check_identity(catalog, args.department)
        dictionary_sha = verify_dictionary(_read_url(DOCUMENT_URL, MAX_DOCUMENT_BYTES))
        original = _read_url(fr.asset_url(args.department), fr.MAX_COMPRESSED)
        result = event_envelope(args.department, original)
        result.update({
            "resource_id": fr.ASSETS[args.department][0],
            "dictionary_sha256": dictionary_sha,
            "catalogue_sha256": catalog["catalogue_sha256"],
        })
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (Blocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
