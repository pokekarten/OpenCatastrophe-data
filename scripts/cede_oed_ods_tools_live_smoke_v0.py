# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Execute actual Oasis ODS Tools ODTF with wholly invented CEDE-v10-like rows.

This deliberately uses an original *minimal* mapping of reviewed direct-field
examples, NOT the upstream 80KB comprehensive YAML and NOT CEDE 13.0.
Run in a disposable CI environment with ods-tools[transform]==5.0.10.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import tempfile

if __package__:
    from .cede_oed_layer_identity_v0 import run as reconcile_layers
else:
    from cede_oed_layer_identity_v0 import run as reconcile_layers

SOURCE_LOC = [
    {"ExposureSetName": "SYNTHETIC-ONLY", "ContractID": "C1", "LocationID": "LOC-A",
     "CountryISO": "DE", "Currency": "EUR", "BuildingValue": "100.10",
     "ContentsValue": "20.05", "Latitude": "48.5", "Longitude": "11.5"},
    {"ExposureSetName": "SYNTHETIC-ONLY", "ContractID": "C1", "LocationID": "LOC-B",
     "CountryISO": "DE", "Currency": "EUR", "BuildingValue": "200.15",
     "ContentsValue": "0", "Latitude": "48.6", "Longitude": "11.6"},
]
SOURCE_LAYERS = [
    {"ExposureSetName": "SYNTHETIC-ONLY", "ContractID": "C1", "LayerID": "L1", "Currency": "EUR"},
    {"ExposureSetName": "SYNTHETIC-ONLY", "ContractID": "C1", "LayerID": "L2", "Currency": "EUR"},
]
LOCATION_MAP = {
    "ExposureSetName": "PortNumber", "ContractID": "AccNumber",
    "LocationID": "LocNumber", "CountryISO": "CountryCode",
    "Currency": "LocCurrency", "BuildingValue": "BuildingTIV",
    "ContentsValue": "ContentsTIV", "Latitude": "Latitude", "Longitude": "Longitude",
    "LocPerils": "LocPerilsCovered", "OtherValue": "OtherTIV",
    "TimeElementValue": "BITIV",
}
LAYER_MAP = {
    "ExposureSetName": "PortNumber", "ContractID": "AccNumber",
    "LayerID": "PolNumber", "Currency": "AccCurrency", "Perils": "PolPerilsCovered",
}


class SmokeError(ValueError):
    """ODS Tools did not produce a verified synthetic output."""


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_mapping(path: Path, mapping: dict[str, str], types: dict[str, str]) -> None:
    # YAML here is an original bounded test mapping; never copied from Verisk or
    # from the comprehensive upstream Oasis example. All keys are static.
    lines = ["types:"]
    for source, value_type in types.items():
        lines.extend((f"  {source}:", f"    type: {value_type}"))
    lines.extend(("null_values:", "  - \"''\"", "  - Null", "  - NULL", "transform:"))
    for source, target in mapping.items():
        lines.extend((f"  {target}:", f"    - transformation: {source}"))
    if path.name.startswith("layer_"):
        lines.extend(("  LayerNumber:", "    - transformation: LayerID"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_config(path: Path, input_path: Path, output_path: Path, mapping: Path) -> None:
    # No user-controlled paths or secrets; files only exist in a temporary dir.
    path.write_text(
        f"input:\n  path: {input_path}\n"
        f"output:\n  path: {output_path}\n"
        f"mapping:\n  path: {mapping}\n"
        "batch_size: 10000\nlogging: false\n", encoding="utf-8"
    )


def _probe_oed_v302(location: Path, account: Path) -> dict[str, object]:
    """Check the *explicit* legacy OED 3.0.2 schema; diagnostics never imply admission.

    Do not use the CLI's exit code as validation evidence: the ODS Tools check
    command may log a caught OdsException without returning a failure status.
    """
    try:
        from ods_tools.oed import OedExposure
        from ods_tools.oed.common import DEFAULT_VALIDATION_CONFIG

        exposure = OedExposure(
            location=str(location), account=str(account),
            oed_schema_info="3.0.2",
            check_oed=False, disable_oed_version_update=True,
        )
        checks = [{**item, "on_error": "return"} for item in DEFAULT_VALIDATION_CONFIG]
        findings = exposure.check(checks)
        if type(findings) is not list:
            return {"attempted": True, "passed": False,
                    "blocked_reason": "unexpected_validator_return"}
        # Do not copy raw records or detailed validation messages to logs.
        return {"attempted": True, "passed": len(findings) == 0,
                "finding_count": len(findings),
                "finding_sources": sorted({str(item.get("name", "unknown")) for item in findings}),
                "blocked_reason": None}
    except Exception as exc:
        return {"attempted": True, "passed": False,
                "blocked_reason": type(exc).__name__}


def execute(command: str = "ods_tools") -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="oc-synthetic-cede-oed-") as directory:
        root = Path(directory)
        loc_in, layer_in = root / "loc_input.csv", root / "layer_input.csv"
        loc_out, layer_out = root / "loc_oed.csv", root / "layer_oed.csv"
        exposure_json, layers_json = root / "exposure.json", root / "layers.json"
        # These extra fields are invented solely to satisfy published minimum
        # OED exposure requirements; they do not represent CEDE-v13 fields.
        synthetic_location_csv = [
            {**row, "LocPerils": "WEC", "OtherValue": "0", "TimeElementValue": "0"}
            for row in SOURCE_LOC
        ]
        synthetic_layer_csv = [{**row, "Perils": "WEC"} for row in SOURCE_LAYERS]
        _write_csv(loc_in, synthetic_location_csv)
        _write_csv(layer_in, synthetic_layer_csv)
        exposure_json.write_text(json.dumps({
            "source_format": "CEDE", "source_version": "10.0.0",
            "target_format": "OED", "target_version": "3.0.2",
            "synthetic_only": True, "rows": SOURCE_LOC,
        }), encoding="utf-8")
        layers_json.write_text(json.dumps({
            "source_version": "10.0.0", "target_version": "3.0.2",
            "synthetic_only": True, "layers": SOURCE_LAYERS,
        }), encoding="utf-8")
        loc_types = {name: ("float" if name in {"BuildingValue", "ContentsValue", "OtherValue", "TimeElementValue", "Latitude", "Longitude"} else "string")
                     for name in LOCATION_MAP}
        layer_types = {name: "string" for name in LAYER_MAP}
        for label, inp, out, fields, ty in (
            ("loc", loc_in, loc_out, LOCATION_MAP, loc_types),
            ("layer", layer_in, layer_out, LAYER_MAP, layer_types),
        ):
            mapping = root / f"{label}_mapping.yaml"
            config = root / f"{label}_config.yaml"
            _write_mapping(mapping, fields, ty)
            _write_config(config, inp, out, mapping)
            try:
                proc = subprocess.run([command, "transform", "--config-file", str(config)],
                                      cwd=root, capture_output=True, text=True, timeout=90, check=False)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise SmokeError(f"ODS Tools {label} execution unavailable") from exc
            if proc.returncode != 0:
                raise SmokeError(
                    f"ODS Tools {label} conversion failed (exit {proc.returncode}); "
                    f"stderr tail: {proc.stderr[-450:]}"
                )
            if not out.is_file() or not out.stat().st_size:
                raise SmokeError(f"ODS Tools {label} produced no CSV output")
        checked = reconcile_layers(exposure_json, layers_json, loc_out, layer_out)
        oed_validation = _probe_oed_v302(loc_out, layer_out)
        if not checked["layer_identity_consistent"]:
            raise SmokeError("synthetic layer integrity check failed")
        return {
            "profile": "cede-oed-ods-tools-direct-fields-smoke-v0",
            "mapping_scope": "original_minimal_direct_fields_plus_oed_required_perils_and_values",
            "source_version": "10.0.0", "target_version": "3.0.2",
            "source_location_count": checked["source_location_count"],
            "oed_location_count": checked["oed_location_count"],
            "oed_layer_count": checked["oed_layer_count"],
            "synthetic_totals_by_currency": checked["synthetic_totals_by_currency"],
            "executed_ods_tools": True, "minimal_field_mapping_reconciled": True,
            "upstream_comprehensive_mapping_executed": False,
            "oed_schema_validated": oed_validation["passed"],
            "oed_schema_probe": oed_validation, "cede_13_compatible": False,
            "financial_terms_validated": False, "rights_approved": False,
            "model_input_admitted": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ods-tools-command", default="ods_tools")
    args = parser.parse_args()
    try:
        result = execute(args.ods_tools_command)
    except (SmokeError, ValueError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
