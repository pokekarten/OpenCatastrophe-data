# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent offline/OED-format gate over the authentic 400-Kreis source portfolio.

Requires ods-tools==5.0.8, unlike the stdlib-only original generator.
This checks format/conservation only, NOT geocoding, vulnerability or CAT engine.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
from rva_2025_oed_staging_v0 import CENSUS, AGES, HGB, rows_from_validated_sources, export, NATIONAL, GWP_CENTS
import tomllib


def execute():
    from ods_tools import __version__
    from ods_tools.oed import OedExposure
    if __version__ != "5.0.8":
        raise RuntimeError("only pinned ods-tools==5.0.8 is supported")

    paths=(CENSUS,AGES,HGB)
    blobs=[p.read_bytes() for p in paths]
    inputs=[tomllib.loads(raw.decode("utf-8")) for raw in blobs]
    cells=rows_from_validated_sources(inputs,"PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY")
    hashes={p.name:hashlib.sha256(raw).hexdigest() for p,raw in zip(paths,blobs)}
    with tempfile.TemporaryDirectory(prefix="rva-2025-oed-format-") as tmp:
        out=Path(tmp)/"output"
        manifest=export(cells,out,"PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY","central",10000,hashes)
        if manifest["status"]!="NOT_GEOLOCATED_NOT_MODEL_READY" or manifest["germany_peril_model_lookup_allowed"] is not False:
            raise RuntimeError("unfounded geographic/model admission")
        if manifest["exported_fictional_locations_and_policies"]!=10000 or manifest["full_fictional_2025_book_exported"]:
            raise RuntimeError("wrong sample/full semantics")
        if manifest["company_2025_national_year_end_building_contracts_observed"]!=NATIONAL or manifest["company_2025_national_annual_building_gwp_eur_cents_observed"]!=GWP_CENTS:
            raise RuntimeError("observed publisher totals changed")
        # Native official OED format check; no model or spatial lookup performed.
        OedExposure(location=str(out/"location.csv"),
                    account=str(out/"account.csv"),check_oed=True)
        with (out/"location.csv").open(encoding="utf-8",newline="") as stream:
            loc=list(csv.DictReader(stream))
        with (out/"account.csv").open(encoding="utf-8",newline="") as stream:
            accounts=list(csv.DictReader(stream))
        with (out/"cohort_receipt.csv").open(encoding="utf-8",newline="") as stream:
            cohorts=list(csv.DictReader(stream))
        if (len(loc),len(accounts),len(cohorts))!=(10000,10000,4000):
            raise RuntimeError("portfolio row population mismatch")
        if len({x["LocNumber"] for x in loc})!=10000:
            raise RuntimeError("duplicate location")
        if {x["AccNumber"] for x in accounts}!={x["AccNumber"] for x in loc}:
            raise RuntimeError("account-to-location bijection mismatch")
        if any(x["Latitude"] or x["Longitude"] for x in loc):
            raise RuntimeError("unauthorized synthetic geocoding")
        if sum(int(r["Fictional2025FullContractCount"]) for r in cohorts)!=NATIONAL:
            raise RuntimeError("full fictional county mass changed")
        if sum(int(r["Fictional2025ExportedContractCount"]) for r in cohorts)!=10000:
            raise RuntimeError("sample cohort mass changed")
        for filename, sha in manifest["output_sha256"].items():
            if hashlib.sha256((out/filename).read_bytes()).hexdigest()!=sha:
                raise RuntimeError("output hashes mismatch")
        return {
            "gate":"SOURCE_CONSERVING_OED_FORMAT_ONLY_NO_GERMANY_CATASTROPHE_RUN",
            "ods_tools":"5.0.8","geocodes_verified":False,
            "location_rows":10000,"account_rows":10000,
            "county_age_cells":4000,"fictional_sample_tiv_eur":4500000000,
            "original_input_sha256":hashes,
            "output_sha256":manifest["output_sha256"]
        }


if __name__=="__main__":
    print(json.dumps(execute(),sort_keys=True,indent=2))
