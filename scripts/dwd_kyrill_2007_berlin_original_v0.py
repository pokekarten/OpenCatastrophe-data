#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Audit original DWD 2007-01-18 station gusts: one location, NOT calibration.

The provider's 10-minute FX_10 is a maximum 3-second gust within the 10min
interval ending at the provider UTC timestamp. It is NOT an ERA5 event-wide
maximum at a grid cell, not a building loss, and not a proof that the gust was
caused by Kyrill. Keep historical observations out of Git and all CAT metrics
undefined. The original archive SHA256 is established only at actual runtime.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from zipfile import BadZipFile, ZipFile

STATION = "00433"
FILENAME = "10minutenwerte_extrema_wind_00433_20000101_20091231_hist.zip"
SOURCE_URL = ("https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
              "climate/10_minutes/extreme_wind/historical/" + FILENAME)
CONTRACT = "OC_DWD_2007_KYRILL_BERLIN_TEMPELHOF_ORIGINAL_GUST_PREFLIGHT_V0"
CLIMK_NETCDF_SHA256 = "92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102"
CLIMK_BERLIN_GUST_MM_S = 31090
WINDOW_START = datetime(2007, 1, 17)
WINDOW_END = datetime(2007, 1, 20, 23, 50)
DAYS = ("2007-01-17", "2007-01-18", "2007-01-19", "2007-01-20")
REQUIRED = ("STATIONS_ID", "MESS_DATUM", "QN", "FX_10")
MAX_ARCHIVE = 4_000_000
MAX_EXPANDED_TOTAL = 85_000_000
MAX_LINE = 2048
MAX_ROWS = 600_000
MAX_MEMBERS = 30
MAX_MEMBER_BYTES = 80_000_000
MAX_OBSERVATION = Decimal("200")
START_SOURCE = datetime(1999, 12, 31, 23, 50)  # one pre-2000 MEZ edge tick, NOT UTC
UTC_SOURCE_START = datetime(2000, 1, 1)
END_SOURCE = datetime(2009, 12, 31, 23, 50)


class OriginalDWDGateError(ValueError):
    """Source bytes, date/quality semantics or window completeness unknown."""


def _utc_stamp(value: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r"\d{12}", value):
        raise OriginalDWDGateError("invalid 12-digit original DWD timestamp")
    try:
        t = datetime.strptime(value, "%Y%m%d%H%M")
    except ValueError as exc:
        raise OriginalDWDGateError("invalid original DWD calendar timestamp") from exc
    # Report only the invalid timestamp CLASS, not original observation rows.
    if t.second or t.minute % 10:
        raise OriginalDWDGateError("original timestamp off strict 10-minute cadence")
    if t < START_SOURCE:
        raise OriginalDWDGateError("original source timestamp before declared archive start; source year-month: " + t.strftime("%Y-%m"))
    if t > END_SOURCE:
        raise OriginalDWDGateError("original source timestamp after declared archive end")
    return t


def _gust(value: str) -> Decimal | None:
    try:
        v = Decimal(value)
    except InvalidOperation as exc:
        raise OriginalDWDGateError("original FX_10 is nonnumeric") from exc
    if not v.is_finite() or v < Decimal("-999") or v > MAX_OBSERVATION:
        raise OriginalDWDGateError("invalid observed FX_10 bound")
    if v == Decimal("-999"):
        return None
    if v < 0:
        raise OriginalDWDGateError("negative gust other than missing -999")
    return v


def _header(line: bytes) -> tuple[str, ...]:
    try:
        h = line.decode("utf-8-sig").strip().split(";")
    except UnicodeError as exc:
        raise OriginalDWDGateError("non UTF-8 original DWD product header") from exc
    names = tuple(s.strip().strip('"') for s in h)
    if len(set(names)) != len(names) or not set(REQUIRED).issubset(names):
        raise OriginalDWDGateError("missing or duplicate source DWD product columns")
    return names


def _member(zip_file: ZipFile):
    names = zip_file.infolist()
    if not 1 <= len(names) <= MAX_MEMBERS or sum(x.file_size for x in names) > MAX_EXPANDED_TOTAL:
        raise OriginalDWDGateError("unbounded original DWD archive")
    candidates = []
    for info in names:
        if info.is_dir():
            continue
        if (info.file_size > MAX_MEMBER_BYTES or info.file_size < 0 or
                info.filename.startswith("/") or ".." in info.filename.split("/")):
            raise OriginalDWDGateError("unbounded archive member or unsafe name")
        if info.filename.lower().endswith(".txt"):
            with zip_file.open(info) as f:
                probe = f.readline(MAX_LINE + 1)
            if len(probe) > MAX_LINE:
                raise OriginalDWDGateError("oversize original source member header")
            try:
                head = _header(probe)
            except OriginalDWDGateError:
                continue
            candidates.append((info, head))
    if len(candidates) != 1:
        raise OriginalDWDGateError("original ZIP must contain exactly one FX_10 product")
    return candidates[0]


def audit_original_archive(raw: bytes, *, expected_sha256: str | None = None) -> dict:
    """Complete source-byte audit; only aggregate 4-day preflight is returned.

    expected_sha256 may be set only to an independently reviewed original file
    digest after a successful provider-native byte transfer. It cannot make a
    synthetic archive into a scientifically admitted observation source.
    """
    if type(raw) is not bytes or not 100 <= len(raw) <= MAX_ARCHIVE or raw[:4] != b"PK\x03\x04":
        raise OriginalDWDGateError("complete bounded original ZIP bytes required")
    digest = sha256(raw).hexdigest()
    if expected_sha256 is not None:
        if (type(expected_sha256) is not str or not re.fullmatch("[a-f0-9]{64}", expected_sha256)
                or digest != expected_sha256):
            raise OriginalDWDGateError("original source ZIP SHA256 mismatch")
    seen = set()
    rows = 0
    first = last = None
    report = {day: {"observed_rows":0, "missing_fx_10":0, "valid_fx_10":0,
                    "quality_flags":Counter(), "max_fx_10_mps_all_quality":None,
                    "max_fx_10_mps_qn2_or_qn3":None} for day in DAYS}
    try:
        with ZipFile(BytesIO(raw)) as z:
            product, head = _member(z)
            index = {name:head.index(name) for name in REQUIRED}
            with z.open(product) as f:
                line = f.readline(MAX_LINE + 1)
                if len(line)>MAX_LINE or _header(line) != head:
                    raise OriginalDWDGateError("original product header changed during audit")
                for line in f:
                    if not line.strip():
                        continue
                    if len(line) > MAX_LINE:
                        raise OriginalDWDGateError("oversize DWD source row")
                    try:
                        columns = [x.strip().strip('"') for x in line.decode("utf-8").rstrip("\r\n").split(";")]
                    except UnicodeError as exc:
                        raise OriginalDWDGateError("non-UTF8 DWD wind value") from exc
                    if len(columns)!=len(head):
                        raise OriginalDWDGateError("DWD product row column count drift")
                    ident, stamp, qn, value = (columns[index[x]] for x in REQUIRED)
                    if ident.zfill(5)!=STATION or not ident.isascii() or not ident.isdigit():
                        raise OriginalDWDGateError("wrong DWD station ID")
                    time = _utc_stamp(stamp)
                    if last is not None and time <= last:
                        raise OriginalDWDGateError("nonmonotone or duplicate DWD source timestamps")
                    if first is None:
                        first = time
                    last = time
                    if qn not in {"1","2","3"}:
                        raise OriginalDWDGateError("unexpected source quality flag")
                    gust = _gust(value)
                    rows += 1
                    if rows > MAX_ROWS:
                        raise OriginalDWDGateError("original source exceeds row cap")
                    if WINDOW_START<=time<=WINDOW_END:
                        key=time.date().isoformat()
                        day=report[key]
                        day["observed_rows"]+=1
                        day["quality_flags"][qn]+=1
                        if gust is None:
                            day["missing_fx_10"]+=1
                        else:
                            day["valid_fx_10"]+=1
                            day["max_fx_10_mps_all_quality"]=(gust if day["max_fx_10_mps_all_quality"] is None
                                                               else max(gust,day["max_fx_10_mps_all_quality"]))
                            if qn in ("2","3"):
                                day["max_fx_10_mps_qn2_or_qn3"]=(gust if day["max_fx_10_mps_qn2_or_qn3"] is None
                                                                  else max(gust,day["max_fx_10_mps_qn2_or_qn3"]))
            # Decompress and verify CRC for other archive members without printing metadata.
            for info in z.infolist():
                if info.is_dir() or info.filename == product.filename:
                    continue
                with z.open(info) as f:
                    while f.read(65536):
                        pass
    except (BadZipFile, OSError, EOFError, RuntimeError) as exc:
        raise OriginalDWDGateError("original DWD ZIP invalid or CRC verification failed") from exc
    if first is None or last is None or rows <= 0 or not (first<=WINDOW_START and last>=WINDOW_END):
        raise OriginalDWDGateError("historical archive does not bracket January 2007")
    total = sum(day["observed_rows"] for day in report.values())
    if total < 1:
        raise OriginalDWDGateError("no actual January 2007 observations")
    days=[]
    for k,day in report.items():
        present=day["observed_rows"]
        if present > 144 or day["valid_fx_10"]+day["missing_fx_10"]!=present:
            raise OriginalDWDGateError("2007 daily gust count impossible")
        max1=day["max_fx_10_mps_all_quality"]
        max2=day["max_fx_10_mps_qn2_or_qn3"]
        days.append({"day_utc":k,
                     "observed_10minute_records":present,
                     "unobserved_10minute_slots":144-present,
                     "missing_value_records":day["missing_fx_10"],
                     "valid_gust_records":day["valid_fx_10"],
                     "quality_flag_record_counts":dict(sorted(day["quality_flags"].items())),
                     "max_3second_gust_within_10minutes_mps_all_quality":str(max1) if max1 is not None else None,
                     "max_3second_gust_within_10minutes_mps_qn2_or_qn3":str(max2) if max2 is not None else None})
    return {
        "contract":CONTRACT,"status":"ORIGINAL_DWD_GUST_PRELIMINARY_HAZARD_HOLDOUT_NOT_CALIBRATED",
        "dwd_station_id":STATION,"station_label_candidate":"Berlin-Tempelhof",
        "dwd_original_archive_filename":FILENAME,
        "original_archive_sha256":digest,
        "original_archive_byte_count":len(raw),
        "archive_first_original_clock_label":first.isoformat(),
        "archive_first_clock_is_utc":first >= UTC_SOURCE_START,
        "pre_2000_mez_edge_tick_not_analyzed":first == START_SOURCE,
        "archive_last_utc":last.isoformat()+"Z",
        "full_source_product_rows":rows,
        "window_utc_start":WINDOW_START.isoformat()+"Z",
        "window_utc_end":WINDOW_END.isoformat()+"Z",
        "daily_10minute_gust_aggregates":days,
        "original_observations_day_count":len(DAYS),
        "historical_kyrill_label_day_utc_exact_identity_confirmed":False,
        "climk_berlin_era5_source_max_gust_mps":"31.090",
        "climk_source_netcdf_sha256":CLIMK_NETCDF_SHA256,
        "dwd_gust_statistic":"MAX_3S_WITHIN_EACH_10MIN; TIMESTAMP_END_OF_INTERVAL_UTC",
        "climk_gust_statistic":"MAX_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT_NOT_SAME_OBSERVATION_OPERATOR",
        "source_station_coordinates_at_2007_original_metadata_verified":False,
        "dwd_station_identical_to_climk_synthetic_site":False,
        "one_reported_storm_attribution_proven":False,
        "observed_insured_claims":False,
        "vulnerability_fitted":False,
        "source_original_raw_gust_rows_persisted":False,
        "annual_event_rate":None,"annual_AAL":None,"annual_AEP":None,"annual_OEP":None,
        "scientific_admission":False,
    }


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip",type=Path,required=True)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args(argv)
    if args.output is not None and (args.output.exists() or args.output.resolve()==args.original_zip.resolve()):
        parser.error("new receipt path required; never overwrite raw source or existing receipt")
    path=args.original_zip
    if path.is_symlink() or not path.is_file() or not 100<=path.stat().st_size<=MAX_ARCHIVE:
        parser.error("bounded real original ZIP regular file required")
    result=audit_original_archive(path.read_bytes())
    raw=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open("x",encoding="utf-8") as f:
            f.write(raw)
    else:
        print(raw,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
