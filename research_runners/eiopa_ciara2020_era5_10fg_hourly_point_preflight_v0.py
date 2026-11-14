# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline Ciara 2020 ERA5 gust 10fg 96-hour point intake, NO insurer model.

Two independent operations:
* --show-cds-request: print a source-verified candidate API request for
  ONE 0.25-degree ERA5 gridpoint. Never calls CDS, reads credentials or
  claims a licence was accepted.
* --normalized-hourly-csv: audit a consciously normalized local 96-row
  CSV only after external original-source download and source provenance.
  Actual original CDS CSV layout has NOT been byte-inspected; this is an
  intentional strict normalization contract, NOT a raw CDS file parser.

No ERA5 measurements currently obtained. A correct time series is a
modelled hourly wind *hazard*, not observed R+V insured losses, not
a NUTS2 area average and not an annual storm-frequency catalogue.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import pathlib
import re
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/observations/eiopa_ciara2020_era5_10fg_hourly_point_contract_v0.toml"
SCHEMA = "EIOPA_CIARA2020_ERA5_10FG_HOURLY_POINT_CONTRACT_V0"
DS = "reanalysis-era5-single-levels-timeseries"
VAR = "10m_wind_gust_since_previous_post_processing"
DATE_START = "2020-02-08"
DATE_END = "2020-02-11"
HOURS = 96
HEADERS = ["time_utc", "latitude", "longitude", VAR, "units"]
EXPECTED_FLAGS_FALSE = {
    "source_cds_license_manually_accepted",
    "source_cds_token_present_in_repo",
    "original_source_csv_acquired",
    "daily_aggregated_dataset_allowed",
    "daily_2026_plus_one_hour_bug_assumed_resolved",
    "derived_era5_daily_statistics_dataset_approved",
    "hourly_native_event_gust_max_observed",
    "1990_Daria_can_be_joined_as_same_event",
    "insurer_site_specific_loss_or_tiv_observed",
    "regional_nuts2_2020_exposure_denominator_reconciled",
    "hazard_values_from_csv_staged_into_model",
    "gross_net_OEP_AEP_admitted",
}
EXPECTED = {
    "schema": SCHEMA,
    "as_of": "2026-11-07",
    "event_name": "CIARA_SABINE_2020",
    "event_start_utc": "2020-02-08T00:00:00Z",
    "event_end_utc_inclusive": "2020-02-11T23:00:00Z",
    "expected_time_steps": HOURS,
    "source_dataset": DS,
    "source_licence": "CC-BY",
    "source_doi": "10.24381/1cf1ad76",
    "source_landing_url": "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries?tab=download",
    "source_product_guide_url": "https://confluence.ecmwf.int/pages/viewpage.action?pageId=514296174",
    "source_cds_api_instructions_url": "https://cds.climate.copernicus.eu/how-to-api",
    "original_source_csv_sha256": "NOT_ACQUIRED",
    "requested_point_description": "Single illustrative public ERA5 gridpoint near Cologne; NOT a region or R+V insured location",
    "requested_latitude_degrees": 51.0,
    "requested_longitude_degrees": 7.0,
    "actual_era5_gridpoint_rounded_to_nearest_0p25": "NOT_MEASURED_YET",
    "source_spatial_resolution_degrees": 0.25,
    "wind_variable_name": VAR,
    "ecmwf_short_name": "10fg",
    "ecmwf_parameter_id": 49,
    "wind_units": "m/s",
    "wind_metric": "10_METRE_MAXIMUM_3_SECOND_GUST_SINCE_PREVIOUS_POSTPROCESSING",
    "wind_source_kind": "ERA5_REANALYSIS_MODELED_NOT_OBSERVED_DWD_STATION",
    "2020_matching_insured_Claim_event_available_reference": "EIOPA_CIARA_SABINE_FEB_2020_NUTS2_ONLY",
}


class CiaraERA5PreflightBlocked(ValueError):
    """Wind-event source, units, time, coordinate or rights model promotion blocked."""


def validate_contract(doc: dict) -> None:
    if not isinstance(doc, dict) or set(doc) != set(EXPECTED) | EXPECTED_FLAGS_FALSE:
        raise CiaraERA5PreflightBlocked("source metadata contract drift")
    for name, correct in EXPECTED.items():
        if type(doc[name]) is not type(correct) or doc[name] != correct:
            raise CiaraERA5PreflightBlocked("source original variable, 2020 event or rights flag modified: " + name)
    for name in EXPECTED_FLAGS_FALSE:
        if doc[name] is not False:
            raise CiaraERA5PreflightBlocked("unsupported ERA5 download, daily-aggregation or insurer-model claim: " + name)


def cds_candidate_request(doc: dict) -> dict:
    validate_contract(doc)
    # Published official ERA Explorer example uses 'date', 'location',
    # 'data_format'. This small single point does not equal a whole NUTS2.
    return {
        "dataset": DS,
        "request": {
            "variable": [VAR],
            "date": [DATE_START, DATE_END],
            # Only pinned, public illustrative coordinates reach stdout.
            # validate_contract(doc) already rejects changed source fields;
            # do not propagate TOML-originated values into a printed request.
            "location": {
                "latitude": 51.0,
                "longitude": 7.0,
            },
            "data_format": "csv",
        },
        "CDS_terms_acceptance_required_by_user": True,
        "request_executed": False,
        "data_obtained": False,
    }


def audit_normalized_csv(path: pathlib.Path, doc: dict) -> dict:
    validate_contract(doc)
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".csv":
        raise CiaraERA5PreflightBlocked("expected local regular normalized CSV")
    if not 100 <= path.stat().st_size <= 50_000:
        raise CiaraERA5PreflightBlocked("invalid bounded normalized CSV size")
    raw = path.read_bytes()
    if b"\x00" in raw or raw.startswith(b"\xef\xbb\xbf"):
        raise CiaraERA5PreflightBlocked("binary CSV/BOM not allowed")
    try:
        text = raw.decode("utf-8", errors="strict")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if reader.fieldnames != HEADERS:
            raise CiaraERA5PreflightBlocked("CSV must be explicitly normalized as time_utc,latitude,longitude,10fg,units; no u10/v10 or daily means")
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise CiaraERA5PreflightBlocked("CSV malformed") from exc
    if len(rows) != HOURS:
        raise CiaraERA5PreflightBlocked("2020-02-08..11 requires exactly 96 hourly ERA5 records")
    start = datetime(2020, 2, 8, tzinfo=timezone.utc)
    observed_gusts = []
    for i, row in enumerate(rows):
        if any(k is None or v is None for k, v in row.items()) or None in row:
            raise CiaraERA5PreflightBlocked("unexpected column or missing field")
        timestamp = row["time_utc"]
        expected = (start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:00:00Z")
        if timestamp != expected:
            raise CiaraERA5PreflightBlocked("missing, duplicated, shifted or non-UTC hourly timestep")
        if row["units"] != "m/s":
            raise CiaraERA5PreflightBlocked("ERA5 gust unit must be m/s, not km/h or hourly mean")
        try:
            lat = Decimal(row["latitude"])
            lon = Decimal(row["longitude"])
            val = Decimal(row[VAR])
        except (InvalidOperation, ValueError) as exc:
            raise CiaraERA5PreflightBlocked("non-finite/non-decimal gust or coordinates") from exc
        if (not lat.is_finite() or not lon.is_finite() or not val.is_finite()
            or lat != Decimal("51.0") or lon != Decimal("7.0")):
            raise CiaraERA5PreflightBlocked("gridpoint drift or nonfinite gust")
        if not Decimal("0") <= val <= Decimal("150"):
            raise CiaraERA5PreflightBlocked("gust outside conservative physical bounds")
        observed_gusts.append(val)
    return {
        "schema": "EIOPA_CIARA2020_ERA5_10FG_NORMALIZED_LOCAL_POINT_AUDIT_V0",
        "status": "HYPOTHETICAL_OR_LOCAL_HAZARD_96H_CHECKED_NO_OBSERVED_INSURER_CLAIMS",
        "local_normalized_CSV_sha256": hashlib.sha256(raw).hexdigest(),
        "source_original_CDS_CSV_SHA256_independently_attested": False,
        "source_CDS_dataset_license_accepted_by_user_verified": False,
        "time_steps": HOURS,
        "first_time_utc": doc["event_start_utc"],
        "last_time_utc": doc["event_end_utc_inclusive"],
        "variable": VAR,
        "gridpoint_lat": 51.0,
        "gridpoint_lon": 7.0,
        "gust_units": "m/s",
        "point_hourly_gust_peak_ms_from_local_CSV": str(max(observed_gusts)),
        "point_hourly_gust_peak_hour_utc_from_local_CSV": (
            start + timedelta(hours=observed_gusts.index(max(observed_gusts)))
        ).strftime("%Y-%m-%dT%H:00:00Z"),
        "point_is_2020_NUTS2_area_average": False,
        "2026_daily_statistics_hour_shift_accepted": False,
        "2020_Ciara_EIOPA_insurer_claim_values_loaded": False,
        "1990_Daria_same_insured_event": False,
        "R_V_real_policy_losses_or_annual_OEP_AEP_admitted": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--show-cds-request", action="store_true")
    p.add_argument("--normalized-hourly-csv", type=pathlib.Path)
    p.add_argument("--out-receipt", type=pathlib.Path)
    a = p.parse_args()
    try:
        if a.show_cds_request == (a.normalized_hourly_csv is not None):
            raise CiaraERA5PreflightBlocked("choose only source request preview OR offline CSV audit")
        with CONTRACT.open("rb") as fh:
            doc = tomllib.load(fh)
        if a.show_cds_request:
            if a.out_receipt:
                raise CiaraERA5PreflightBlocked("request preview does not create receipt")
            print(json.dumps(cds_candidate_request(doc), sort_keys=True, indent=2))
        else:
            if not a.out_receipt or a.out_receipt.exists() or a.out_receipt.is_symlink():
                raise CiaraERA5PreflightBlocked("new non-symlink output receipt path required")
            result = audit_normalized_csv(a.normalized_hourly_csv, doc)
            with a.out_receipt.open("x", encoding="utf-8") as out:
                json.dump(result, out, sort_keys=True, indent=2)
                out.write("\n")
            print(json.dumps({"status":result["status"],"hour_count":result["time_steps"],
                              "source_CDS_licensed_and_attested":False,"annual_EP":False},
                             sort_keys=True))
        return 0
    except (CiaraERA5PreflightBlocked, OSError, tomllib.TOMLDecodeError) as exc:
        p.exit(2, "CIARA_2020_ERA5_10FG_HAZARD_NOT_ADMITTED: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
