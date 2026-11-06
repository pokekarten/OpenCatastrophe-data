# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Run original GPL CLIMADA 6.1.0 wind impact *method bodies* for numeric parity.

NOT a full/native CLIMADA package installation or German insurer model.
Original GPL source is original-byte, pinned, locally isolated and ephemeral.
The adapter never vendors upstream source, methods or curves in this repo.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from typing import Union

from rva_nrw_daria_climada61_source_challenger_v0 import (
    SOURCE_PINS, MODEL_NAMES, FIELD_SITE, git_blob_sha1,
    parse_pinned_public_curves, run_challenger, CLIMADAChallengerBlocked,
)

SCHEMA = "XWS_DARIA_CLIMADA61_EXECUTED_ORIGINAL_GPL_METHOD_BODIES_PARITY_V0"


class OriginalMethodParityBlocked(ValueError):
    """No original source, no parity, no model promotion."""


def _extract_func(tree: ast.Module, name: str) -> ast.FunctionDef:
    found = [node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(found) != 1:
        raise OriginalMethodParityBlocked("original upstream method missing")
    return found[0]


def _read_code(directory: Path) -> dict[str, bytes]:
    if directory.is_symlink() or not directory.is_dir():
        raise OriginalMethodParityBlocked("ephemeral original CLIMADA GPL directory required")
    if {p.name for p in directory.iterdir()} != set(SOURCE_PINS):
        raise OriginalMethodParityBlocked("exact three original pinned CLIMADA files required")
    data = {}
    for name, sha in SOURCE_PINS.items():
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 120_000:
            raise OriginalMethodParityBlocked("original CLIMADA source symlink/size blocked")
        raw = path.read_bytes()
        if git_blob_sha1(raw) != sha or b"GNU General Public License" not in raw:
            raise OriginalMethodParityBlocked("original CLIMADA source identity changed")
        data[name] = raw
    return data


def _original_impact_classes(original: dict[str, bytes]):
    """Execute exactly original verified method AST in ephemeral isolated scope.

    The original published computational bodies are left unchanged. Small local
    class state replaces CLIMADA's enormous non-computational package imports.
    This is method-level parity, never asserted to be native/full CLIMADA.
    """
    try:
        import numpy as np
        from scipy import interpolate
    except ImportError as exc:
        raise OriginalMethodParityBlocked(
            "NumPy and SciPy required for original method-level parity only"
        ) from exc

    parse_pinned_public_curves(original)
    try:
        storm = ast.parse(original["storm_europe.py"].decode("utf-8"))
        base = ast.parse(original["base.py"].decode("utf-8"))
        calibration = ast.parse(original["calibration_opt.py"].decode("utf-8"))
    except (UnicodeError, SyntaxError) as exc:
        raise OriginalMethodParityBlocked("original model source parse failed") from exc
    impact_cls = [n for n in storm.body if isinstance(n, ast.ClassDef)
                  and n.name == "ImpfStormEurope"]
    base_cls = [n for n in base.body if isinstance(n, ast.ClassDef)
                and n.name == "ImpactFunc"]
    if len(impact_cls) != 1 or len(base_cls) != 1:
        raise OriginalMethodParityBlocked("original impact class missing or ambiguous")
    calc_method = [n for n in base_cls[0].body if isinstance(n, ast.FunctionDef)
                   and n.name == "calc_mdr"]
    if len(calc_method) != 1:
        raise OriginalMethodParityBlocked("original ImpactFunc.calc_mdr missing")
    original_change = _extract_func(calibration, "change_impf")
    # This method is the original CLIMADA def (not a translated loss formula).
    # It depends only on copy, np and scipy.interpolate for the given inputs.
    isolated = {
        "np": np, "copy": copy, "interpolate": interpolate, "Union": Union,
    }
    change_mod = ast.fix_missing_locations(
        ast.Module(body=[original_change], type_ignores=[])
    )
    exec(compile(change_mod, "original-gpl-change_impf@v6.1.0", "exec"), isolated)
    change_method = isolated["change_impf"]

    class MinimalImpactFunc:
        """Only nonnumeric imported-package lifecycle/state replacement."""
        def __init__(self):
            self.intensity = None
            self.paa = None
            self.mdd = None
        def check(self):
            if self.intensity is None or self.paa is None or self.mdd is None:
                raise OriginalMethodParityBlocked("original impact method not initialized")
            if (
                len(self.intensity) != len(self.paa) or len(self.paa) != len(self.mdd)
                or not np.all(np.diff(self.intensity) > 0)
                or not np.all(np.isfinite(self.intensity))
                or not np.all(np.isfinite(self.paa))
                or not np.all(np.isfinite(self.mdd))
                or np.any((self.paa < 0) | (self.paa > 1))
                or np.any((self.mdd < 0) | (self.mdd > 1))
            ):
                raise OriginalMethodParityBlocked("invalid executed original curve")

    calc_mod = ast.fix_missing_locations(
        ast.Module(body=[calc_method[0]], type_ignores=[])
    )
    exec(compile(calc_mod, "original-gpl-calc_mdr@v6.1.0", "exec"), isolated)
    MinimalImpactFunc.calc_mdr = isolated["calc_mdr"]

    def init_impf_for_impact_instance(instance, parameters):
        # The original CLIMADA init_impf dispatch for an ImpactFunc instance
        # is change_impf(instance, parameters), returning a tuple.
        return change_method(instance, parameters), None

    isolated["ImpactFunc"] = MinimalImpactFunc
    isolated["init_impf"] = init_impf_for_impact_instance
    class_mod = ast.fix_missing_locations(
        ast.Module(body=[impact_cls[0]], type_ignores=[])
    )
    exec(compile(class_mod, "original-gpl-ImpfStormEurope@v6.1.0", "exec"), isolated)
    original_type = isolated["ImpfStormEurope"]
    original_methods = {
        MODEL_NAMES[0]: original_type.from_schwierz(),
        MODEL_NAMES[1]: original_type.from_welker(),
    }
    for impl in original_methods.values():
        impl.check()
        if impl.intensity_unit != "m/s":
            raise OriginalMethodParityBlocked("original impact units unexpectedly changed")
    return original_methods


def audit_methods(
    original: dict[str, bytes], hazard_zip: Path, *,
    expected_sites: int = 10_000, expected_counties: int = 53,
    expected_tiv_eur: int = 4_826_029_500,
    source_hashes: dict[str, str] | None = None,
    model_pins: dict[str, str] | None = None,
) -> dict:
    import numpy as np
    # The exact original-source method bodies are executed separately.
    # The independent Decimal adapter supplies input and claimed output.
    if model_pins is not None:
        if set(original) != set(model_pins) or any(
            git_blob_sha1(b) != model_pins[name] for name, b in original.items()
        ):
            raise OriginalMethodParityBlocked("original method test fixtures changed")
        # Real production source pins are mandatory; synthetic test override
        # would not be admitted as true upstream class execution.
        if model_pins != SOURCE_PINS:
            raise OriginalMethodParityBlocked("cannot promote fake model pins as production")
    methods = _original_impact_classes(original)
    research = run_challenger(
        hazard_zip, original, expected_sites=expected_sites,
        expected_counties=expected_counties, expected_tiv_eur=expected_tiv_eur,
        original_source_hashes=source_hashes,
    )
    if len(research["site_rows"]) != expected_sites * 6:
        raise OriginalMethodParityBlocked("expected original input sampled 6 times")
    by_case = defaultdict(list)
    ids = defaultdict(set)
    for row in research["site_rows"]:
        if set(row) != set(FIELD_SITE) or row["ActualInsurerLossObserved"] != "false":
            raise OriginalMethodParityBlocked("money source scope or schema changed")
        key = (row["EuropeanPublishedMethodNotGermanyCalibrated"],
               row["OriginalXWSWindViewOfSame1990Storm"])
        if row["FictionalSiteId"] in ids[key]:
            raise OriginalMethodParityBlocked("duplicate source asset in method case")
        ids[key].add(row["FictionalSiteId"])
        by_case[key].append(row)
    proof = []
    for method_name in MODEL_NAMES:
        impl = methods[method_name]
        for view in ("lower95", "mean", "upper95"):
            rows = by_case[(method_name, view)]
            if len(rows) != expected_sites:
                raise OriginalMethodParityBlocked("missing original hazard sample")
            winds = np.asarray([float(r["Source3sGustMps"]) for r in rows], dtype=np.float64)
            tiv = np.asarray([int(r["Fictional2025BuildingTIVEUR"]) for r in rows], dtype=np.int64)
            selfreported = np.asarray(
                [int(r["IllustrativeDirectValueEURCents"]) for r in rows], dtype=np.int64
            )
            actual = np.asarray(impl.calc_mdr(winds), dtype=np.float64)
            paa = np.interp(winds, impl.intensity, impl.paa)
            mdd = np.interp(winds, impl.intensity, impl.mdd)
            if (not np.all(np.isfinite(actual)) or np.any((actual < 0) | (actual > 1))
                or not np.allclose(actual, paa * mdd, rtol=0, atol=1e-15)):
                raise OriginalMethodParityBlocked("original-source PAA×MDD evaluation changed")
            claimed_paa = np.asarray([float(r["ImpactPAA"]) for r in rows])
            claimed_mdd = np.asarray([float(r["ImpactMDD"]) for r in rows])
            claimed_mdr = np.asarray([float(r["ImpactMDR"]) for r in rows])
            abs_errors = (
                float(np.max(np.abs(paa - claimed_paa))),
                float(np.max(np.abs(mdd - claimed_mdd))),
                float(np.max(np.abs(actual - claimed_mdr))),
            )
            if max(abs_errors) > 5e-12:
                raise OriginalMethodParityBlocked(
                    "original CLIMADA method PAA/MDD/MDR disagrees with independent adapter"
                )
            # Reflect original CLIMADA double-precision semantics then
            # translate only to the existing per-site integer-cent contract.
            native_method_cents = np.floor(actual * tiv.astype(np.float64) * 100 + 0.5).astype(np.int64)
            diffs = native_method_cents - selfreported
            max_diff = int(np.max(np.abs(diffs)))
            mismatch = int(np.count_nonzero(diffs))
            sum_original = int(native_method_cents.sum())
            sum_bridge = int(selfreported.sum())
            if max_diff > 1 or abs(sum_original - sum_bridge) > expected_sites:
                raise OriginalMethodParityBlocked("original method cent results exceed float64 parity tolerance")
            proof.append({
                "source_method": method_name, "same_original_storm_view": view,
                "locations": expected_sites,
                "original_method_rounded_eur_cents": sum_original,
                "independent_Decimal_adapter_eur_cents": sum_bridge,
                "sites_with_cent_rounding_difference": mismatch,
                "max_site_cent_difference": max_diff,
                "max_component_float64_absolute_error": {
                    "PAA": abs_errors[0], "MDD": abs_errors[1], "MDR": abs_errors[2],
                },
            })
    return {
        "schema": SCHEMA,
        "status": "EXECUTED_PINNED_CLIMADA61_ORIGINAL_METHOD_BODIES_FLOAT64_VS_DECIMAL",
        "method_level_upstream_code_executed": True,
        "full_native_CLIMADA_package_installed": False,
        "stubbed_nonnumeric_ImpactFunc_lifecycle": True,
        "executable_source_version": "CLIMADA-project/climada_python@v6.1.0",
        "original_GPL_files_retained_or_redistributed": False,
        "original_git_blob_sha1": {n: git_blob_sha1(b) for n, b in sorted(original.items())},
        "historical_original_event": "Daria 1990",
        "public_candidate_site_vintage": 2022,
        "fictional_portfolio_values_vintage": "2025-like",
        "fictional_TIV_eur": expected_tiv_eur,
        "published_European_methods_NOT_German_RV_validated": True,
        "no_real_insurer_loss_treaty_or_annual_OEP_AEP": True,
        "separate_original_method_numerical_parity": proof,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-hazard-zip", required=True, type=Path)
    p.add_argument("--source-climada-dir", required=True, type=Path)
    p.add_argument("--out-receipt", required=True, type=Path)
    a = p.parse_args(argv)
    try:
        files = _read_code(a.source_climada_dir)
        report = audit_methods(files, a.source_hazard_zip)
        if a.out_receipt.exists() or a.out_receipt.is_symlink() or not a.out_receipt.parent.is_dir():
            raise OriginalMethodParityBlocked("fresh receipt output path required")
        with a.out_receipt.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print(json.dumps({
            "status": report["status"],
            "method_cases": len(report["separate_original_method_numerical_parity"]),
            "methods": report["separate_original_method_numerical_parity"],
            "native_package_installed": False,
            "actual_insurer_loss_or_annual_EP": False,
        }, sort_keys=True))
        return 0
    except (OriginalMethodParityBlocked, CLIMADAChallengerBlocked,
            ValueError, TypeError, OSError, KeyError) as exc:
        print("CLIMADA61_ORIGINAL_METHOD_PARITY_BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
