# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only source-pinned replay of CLIMADA 6.1.0 winterstorm impact methods.

This code is an independent interface adapter, not copied CLIMADA GPL source.
The original v6.1.0 GPL files are downloaded into ephemeral isolated CI storage;
Git blob identities are verified and only public numeric curve inputs are parsed
using Python AST. No third-party source bytes are committed or redistributed.

One 1990 historical storm + public 2022 sites + invented 2025-like values does
NOT establish actual R+V exposures, Germany-calibrated vulnerability, real
GUL/IL/RI, annual event rate, OEP or AEP. This is NOT native CLIMADA execution.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from rva_nrw_xws_daria_invented_damage_v0 import (
    calculate as validate_hazard,
    _csv as read_source_csv,
    SITE_NAME,
    SITE_COLUMNS,
    VARIANTS,
    SOURCE_HASHES,
)

VERSION = "CLIMADA-project/climada_python@v6.1.0"
SOURCE_PINS = {
    "storm_europe.py": "76973c3df21bc5dbb89f21a962846a01c0c9fce9",
    "calibration_opt.py": "5f174b5f77cc55d690a7d962d735221928838029",
    "base.py": "c51540d5738a6a6f1fa38fe8440f65ace8d9ccc4",
}
MODEL_NAMES = ("schwierz_2010_CLIMADA61", "welker_2021_CLIMADA61")
FIELD_SITE = (
    "PhysicalEvent", "EuropeanPublishedMethodNotGermanyCalibrated",
    "OriginalXWSWindViewOfSame1990Storm", "FictionalSiteId", "KreisAGS2022",
    "Source3sGustMps", "Fictional2025BuildingTIVEUR",
    "ImpactPAA", "ImpactMDD", "ImpactMDR", "IllustrativeDirectValueEURCents",
    "ActualInsurerLossObserved",
)
FIELD_COUNTY = (
    "PhysicalEvent", "EuropeanPublishedMethodNotGermanyCalibrated",
    "OriginalXWSWindViewOfSame1990Storm", "KreisAGS2022",
    "FictionalSiteCount", "FictionalBuildingTIVEUR",
    "IllustrativeDirectValueEURCents",
)
SCHEMA = "RVA_NRW_DARIA_CLIMADA61_SOURCE_PINNED_CHALLENGER_NOT_INSURER_LOSS_V0"


class CLIMADAChallengerBlocked(ValueError):
    """Unverified public source, inconsistent source portfolio or false loss admission."""


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _method(c: ast.ClassDef, name: str) -> ast.FunctionDef:
    m = [n for n in c.body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(m) != 1:
        raise CLIMADAChallengerBlocked("pinned CLIMADA method changed")
    return m[0]


def _literal_array(fn: ast.FunctionDef, attribute: str) -> tuple[Decimal, ...]:
    vals = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target, value = node.targets[0], node.value
        if (
            isinstance(target, ast.Attribute) and target.attr == attribute
            and isinstance(target.value, ast.Name) and target.value.id == "impf"
            and isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
            and isinstance(value.func.value, ast.Name)
            and value.func.value.id == "np" and value.func.attr == "array"
            and len(value.args) == 1
        ):
            try:
                literal = ast.literal_eval(value.args[0])
                vals.append(tuple(Decimal(str(v)) for v in literal))
            except (ValueError, TypeError, InvalidOperation) as exc:
                raise CLIMADAChallengerBlocked("provider array literal unsupported") from exc
    if len(vals) != 1:
        raise CLIMADAChallengerBlocked("published component definition ambiguous")
    return vals[0]


def parse_pinned_public_curves(
    sources: dict[str, bytes], *,
    expected_pins: dict[str, str] | None = None,
) -> dict[str, dict[str, tuple[Decimal, ...]]]:
    pins = SOURCE_PINS if expected_pins is None else expected_pins
    if type(sources) is not dict or set(sources) != set(pins):
        raise CLIMADAChallengerBlocked("three exact original CLIMADA source files required")
    for name, pin in pins.items():
        raw = sources[name]
        if (
            not isinstance(raw, bytes) or not 100 <= len(raw) <= 120_000
            or len(pin) != 40 or git_blob_sha1(raw) != pin
            or b"GNU General Public License" not in raw
        ):
            raise CLIMADAChallengerBlocked("original CLIMADA GPL code hash/licence changed")
    try:
        storm = ast.parse(sources["storm_europe.py"].decode("utf-8"))
        calibration = ast.parse(sources["calibration_opt.py"].decode("utf-8"))
        base = ast.parse(sources["base.py"].decode("utf-8"))
    except (SyntaxError, UnicodeError) as exc:
        raise CLIMADAChallengerBlocked("original CLIMADA source is not parseable") from exc
    classes = [
        n for n in storm.body if isinstance(n, ast.ClassDef) and n.name == "ImpfStormEurope"
    ]
    if len(classes) != 1:
        raise CLIMADAChallengerBlocked("CLIMADA original impact class missing")
    source = _method(classes[0], "from_schwierz")
    welker = _method(classes[0], "from_welker")
    knots = _literal_array(source, "intensity")
    paa = _literal_array(source, "paa")
    mdd = _literal_array(source, "mdd")
    if (
        len(knots) < 3 or len(knots) != len(paa) or len(knots) != len(mdd)
        or knots[0] < 0 or any(right <= left for left, right in zip(knots, knots[1:]))
        or any(not x.is_finite() or not 0 <= x <= 1 for x in paa + mdd)
    ):
        raise CLIMADAChallengerBlocked("original impact curves physically malformed")
    scale = [
        ast.literal_eval(node.value)
        for node in ast.walk(welker)
        if isinstance(node, ast.Assign) and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "scaling_factor"
    ]
    if len(scale) != 1 or set(scale[0]) != {"paa_scale", "mdd_scale"}:
        raise CLIMADAChallengerBlocked("published Welker scaling unsupported")
    paa_scale = Decimal(str(scale[0]["paa_scale"]))
    mdd_scale = Decimal(str(scale[0]["mdd_scale"]))
    if not 0 < paa_scale <= 5 or not 0 < mdd_scale <= 5:
        raise CLIMADAChallengerBlocked("published scaling factors invalid")
    calibration_names = {n.name for n in ast.walk(calibration) if isinstance(n, ast.FunctionDef)}
    base_names = {n.name for n in ast.walk(base) if isinstance(n, ast.FunctionDef)}
    if "change_impf" not in calibration_names or "calc_mdr" not in base_names:
        raise CLIMADAChallengerBlocked("referenced published interpolation function missing")
    # Verified CLIMADA 6.1.0 source: change_impf resamples to (N+1)*10+1
    # evenly spaced intensities, scales and clips PAA/MDD to [0,1].
    # ImpactFunc.calc_mdr interpolates PAA and MDD *separately*, then multiplies.
    with localcontext() as ctx:
        ctx.prec = 46
        n = (len(knots) + 1) * 10 + 1
        dense_x = tuple(knots[0] + (knots[-1] - knots[0]) * Decimal(i) /
                        Decimal(n - 1) for i in range(n))
        dense_paa = tuple(min(Decimal(1), max(Decimal(0),
                           _interp(knots, paa, x) * paa_scale)) for x in dense_x)
        dense_mdd = tuple(min(Decimal(1), max(Decimal(0),
                           _interp(knots, mdd, x) * mdd_scale)) for x in dense_x)
    return {
        MODEL_NAMES[0]: {"wind": knots, "paa": paa, "mdd": mdd},
        MODEL_NAMES[1]: {"wind": dense_x, "paa": dense_paa, "mdd": dense_mdd},
    }


def _interp(xs: tuple[Decimal, ...], ys: tuple[Decimal, ...], x: Decimal) -> Decimal:
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    lo, hi = 0, len(xs) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if x < xs[mid]:
            hi = mid
        else:
            lo = mid
    return ys[lo] + (ys[hi] - ys[lo]) * (x - xs[lo]) / (xs[hi] - xs[lo])


def _csv_bytes(rows: list[dict], fields: tuple[str, ...]) -> bytes:
    s = io.StringIO(newline="")
    writer = csv.DictWriter(s, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return s.getvalue().encode("utf-8")


def run_challenger(
    source_zip: Path, model_source_files: dict[str, bytes], *,
    expected_sites: int = 10_000,
    expected_counties: int = 53,
    expected_tiv_eur: int = 4_826_029_500,
    original_source_hashes: dict[str, str] | None = None,
    expected_model_pins: dict[str, str] | None = None,
) -> dict:
    curves = parse_pinned_public_curves(model_source_files, expected_pins=expected_model_pins)
    checked = validate_hazard(
        source_zip, expected_sites=expected_sites, expected_counties=expected_counties,
        expected_tiv_eur=expected_tiv_eur, source_hashes=original_source_hashes
    )
    with zipfile.ZipFile(source_zip) as z:
        site_bytes = z.read(SITE_NAME)
    if hashlib.sha256(site_bytes).hexdigest() != checked["receipt"]["input_site_csv_sha256"]:
        raise CLIMADAChallengerBlocked("source-validated site CSV changed")
    original = read_source_csv(site_bytes, SITE_COLUMNS)
    if len(original) != expected_sites:
        raise CLIMADAChallengerBlocked("source site count changed")
    unique = set()
    rows = []
    counters = defaultdict(lambda: [0, 0, 0])
    national = defaultdict(lambda: [0, 0, 0])
    counties = set()
    total_tiv = 0
    with localcontext() as ctx:
        ctx.prec = 46
        for site in original:
            sid = site["FictionalSiteId"]
            county = site["Original2022KreisAGS"]
            tiv = int(site["Fictional2025BuildingTIVEUR"])
            if sid in unique or len(county) != 5 or site["ActualRVInsuredSiteObserved"] != "false":
                raise CLIMADAChallengerBlocked("site duplicated or insurer-admitted")
            unique.add(sid)
            counties.add(county)
            total_tiv += tiv
            for method_name, curve in curves.items():
                for view, windfield in VARIANTS.items():
                    w = Decimal(site[windfield])
                    if not w.is_finite() or not 0 <= w <= 300:
                        raise CLIMADAChallengerBlocked("original gust invalid")
                    paa = _interp(curve["wind"], curve["paa"], w)
                    mdd = _interp(curve["wind"], curve["mdd"], w)
                    mdr = paa * mdd
                    if not 0 <= mdr <= 1:
                        raise CLIMADAChallengerBlocked("published curve direct ratio invalid")
                    cents = int((Decimal(tiv) * 100 * mdr).quantize(
                        Decimal(1), rounding=ROUND_HALF_UP
                    ))
                    key = method_name, view, county
                    counters[key][0] += 1
                    counters[key][1] += tiv
                    counters[key][2] += cents
                    totals = national[method_name, view]
                    totals[0] += 1
                    totals[1] += tiv
                    totals[2] += cents
                    rows.append({
                        "PhysicalEvent": "XWS_DARIA_1990",
                        "EuropeanPublishedMethodNotGermanyCalibrated": method_name,
                        "OriginalXWSWindViewOfSame1990Storm": view,
                        "FictionalSiteId": sid,
                        "KreisAGS2022": county,
                        "Source3sGustMps": str(w),
                        "Fictional2025BuildingTIVEUR": tiv,
                        "ImpactPAA": format(paa, ".15f"),
                        "ImpactMDD": format(mdd, ".15f"),
                        "ImpactMDR": format(mdr, ".15f"),
                        "IllustrativeDirectValueEURCents": cents,
                        "ActualInsurerLossObserved": "false",
                    })
    if len(unique) != expected_sites or len(counties) != expected_counties or total_tiv != expected_tiv_eur:
        raise CLIMADAChallengerBlocked("source site geography or fictional TIV not conserved")
    county_rows, comparisons = [], []
    for method_name in MODEL_NAMES:
        for view in VARIANTS:
            n, tiv, cents = national[method_name, view]
            if n != expected_sites or tiv != expected_tiv_eur:
                raise CLIMADAChallengerBlocked("source exposure not reconciled")
            county_sum = 0
            for county in sorted(counties):
                a, b, c = counters[method_name, view, county]
                county_sum += c
                county_rows.append({
                    "PhysicalEvent": "XWS_DARIA_1990",
                    "EuropeanPublishedMethodNotGermanyCalibrated": method_name,
                    "OriginalXWSWindViewOfSame1990Storm": view,
                    "KreisAGS2022": county,
                    "FictionalSiteCount": a,
                    "FictionalBuildingTIVEUR": b,
                    "IllustrativeDirectValueEURCents": c,
                })
            if cents != county_sum or not 0 <= cents <= expected_tiv_eur * 100:
                raise CLIMADAChallengerBlocked("illustrative county damages are inconsistent")
            comparisons.append({
                "method": method_name, "same_physical_storm": "XWS_DARIA_1990",
                "source_gust_view": view, "invented_tiv_eur": expected_tiv_eur,
                "conditional_direct_value_eur_cents": cents,
            })
    receipt = {
        "schema": SCHEMA,
        "status": "PUBLISHED_EU_WIND_CURVE_INTEROP_REPLAY_NOT_GERMANY_INSURANCE_LOSS",
        "original_climada_release": VERSION,
        "independent_AST_interpolator_not_native_CLIMADA_execution": True,
        "original_provider_GPL_source_bytes_not_committed": True,
        "model_original_git_blob_sha1": {
            n: git_blob_sha1(b) for n, b in sorted(model_source_files.items())
        },
        "model_source_sha256": {
            n: hashlib.sha256(b).hexdigest() for n, b in sorted(model_source_files.items())
        },
        "source_original_xws_hashes": original_source_hashes or SOURCE_HASHES,
        "source_hazard_derived_zip_sha256":
            checked["receipt"]["input_hazard_derived_zip_sha256"],
        "published_methods": list(MODEL_NAMES),
        "loss_calculation_definition": "PAA(v) * MDD(v) * fictional EUR TIV; rounded per site to cents",
        "no_German_building_vulnerability_calibration": True,
        "no_actual_insurer_policy_or_loss_observed": True,
        "one_original_historical_storm_not_independent_simulation_years": True,
        "no_annual_event_rates_OEP_AEP": True,
        "no_insured_GUL_IL_RI_or_treaty": True,
        "fictional_sites": expected_sites,
        "fictional_counties": expected_counties,
        "fictional_tiv_eur": expected_tiv_eur,
        "scenario_comparisons": comparisons,
    }
    return {"site_rows": rows, "county_rows": county_rows, "receipt": receipt}


def save_output(target: Path, result: dict) -> dict:
    if target.exists() or target.is_symlink() or not target.parent.is_dir():
        raise CLIMADAChallengerBlocked("output ZIP must be a fresh non-symlink path")
    parts = {
        "climada61_challenger_original_daria_site_sensitivity_NOT_INSURER.csv":
            _csv_bytes(result["site_rows"], FIELD_SITE),
        "climada61_challenger_original_daria_53_kreis_sensitivity_NOT_INSURER.csv":
            _csv_bytes(result["county_rows"], FIELD_COUNTY),
    }
    receipt = dict(result["receipt"])
    receipt["output_sha256"] = {name: hashlib.sha256(data).hexdigest()
                                for name, data in sorted(parts.items())}
    parts["source_pinned_challenger_NOT_GUL_IL_RI_OEP_AEP.json"] = (
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    try:
        with zipfile.ZipFile(target, "x") as z:
            for name, data in sorted(parts.items()):
                entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                entry.external_attr = 0o644 << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(entry, data)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return receipt


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-hazard-zip", type=Path, required=True)
    p.add_argument("--source-climada-dir", type=Path, required=True)
    p.add_argument("--out-comparison-zip", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        if a.source_climada_dir.is_symlink() or not a.source_climada_dir.is_dir():
            raise CLIMADAChallengerBlocked("original CLIMADA code directory invalid")
        files = {}
        if {f.name for f in a.source_climada_dir.iterdir()} != set(SOURCE_PINS):
            raise CLIMADAChallengerBlocked("three exactly pinned source files required")
        for name in SOURCE_PINS:
            file = a.source_climada_dir / name
            if file.is_symlink() or not file.is_file():
                raise CLIMADAChallengerBlocked("original CLIMADA source path is a symlink")
            files[name] = file.read_bytes()
        result = run_challenger(a.source_hazard_zip, files)
        manifest = save_output(a.out_comparison_zip, result)
        print(json.dumps({
            "status": manifest["status"],
            "release": manifest["original_climada_release"],
            "fictional_sites": manifest["fictional_sites"],
            "comparison_values": manifest["scenario_comparisons"],
            "original_provider_executable_redistributed": False,
            "real_insurer_loss_or_OEP_AEP": False,
        }, sort_keys=True))
        return 0
    except (CLIMADAChallengerBlocked, OSError, ValueError, TypeError, KeyError,
            zipfile.BadZipFile) as exc:
        print("CLIMADA61_CHALLENGER_BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
