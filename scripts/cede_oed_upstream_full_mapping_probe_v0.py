# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exercise pinned upstream CEDE-v10 ODTF YAML against wholly invented fields.

A research probe, NOT a compliance gate. A caught upstream mapping failure is
reported as a blocker, never described as a successful complete conversion.
The upstream Oasis source is checked out at an immutable commit in CI.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import subprocess
import tempfile

import yaml

UPSTREAM_COMMIT = "17f1c25b095bb40111f83a6f0abc58c087652538"
MAPPING_PATH = "ods_tools/odtf/examples/oed-cede/mapping"
LOCATION_BLOB = "b5433d6bc7f5ecd926fba4899dc12245d9b1e64a"
ACCOUNT_BLOB = "81a0f2e0aab4d140e8dd403f16ebd12d42d804c8"
BASELINE = {
    "ExposureSetName": "SYNTHETIC-ONLY", "ContractID": "1", "LayerID": "1",
    "LocationID": "1", "CountryISO": "DE", "Currency": "EUR",
    "Latitude": "48.5", "Longitude": "11.5", "BuildingValue": "100.10",
    "ContentsValue": "20.05", "OtherValue": "0", "TimeElementValue": "0",
    "Perils": "EQ", "LocPerils": "EQ", "LayerPerils": "EQ",
    "InceptionDate": "2026-01-01", "ExpirationDate": "2027-12-31",
}
ALLOWED_TYPES = {"int", "float", "string"}


def duplicate_type_keys(mapping_text: str) -> list[str]:
    """Report duplicate YAML type keys before the default loader discards them."""
    if "\ntypes:\n" not in "\n" + mapping_text or "\nnull_values:\n" not in mapping_text:
        raise ValueError("upstream YAML missing types/null_values boundary")
    block = ("\n" + mapping_text).split("\ntypes:\n", 1)[1].split("\nnull_values:\n", 1)[0]
    observed: set[str] = set()
    repeated: set[str] = set()
    for match in re.finditer(r"(?m)^  ([A-Za-z][A-Za-z0-9 ]*):\\s*$", block):
        key = match.group(1)
        if key in observed:
            repeated.add(key)
        observed.add(key)
    return sorted(repeated)


def _source_row(types: dict) -> dict[str, str]:
    row = {}
    for key, definition in types.items():
        if type(key) is not str or type(definition) is not dict:
            raise ValueError("invalid source type declaration")
        name = definition.get("type")
        if name not in ALLOWED_TYPES:
            # Legacy example has a nonstandard placeholder called 'Cede Field'.
            # Keep a synthetic blank; never infer semantics from a placeholder.
            row[key] = ""
        else:
            row[key] = "0" if name in {"int", "float"} else ""
        if key in BASELINE:
            row[key] = BASELINE[key]
    return row


def _write_csv(path: Path, row: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def _write_config(path: Path, source: Path, output: Path, mapping: Path) -> None:
    path.write_text(
        f"input:\n  path: {source}\noutput:\n  path: {output}\n"
        f"mapping:\n  path: {mapping}\nbatch_size: 10000\nlogging: false\n",
        encoding="utf-8",
    )


def probe(upstream: Path, command: str = "ods_tools") -> dict[str, object]:
    # ODTF is executed with cwd=temp; mapping paths must be absolute.
    mapping_dir = upstream.resolve(strict=True) / MAPPING_PATH
    result: dict[str, object] = {
        "profile": "cede10-oed302-pinned-upstream-comprehensive-probe-v0",
        "upstream_commit": UPSTREAM_COMMIT,
        "source_version": "10.0.0", "target_version": "3.0.2",
        "synthetic_only": True, "full_mapping_compatible": False,
        "rights_approved": False, "cede13_compatible": False,
        "model_input_admitted": False, "runs": [],
    }
    with tempfile.TemporaryDirectory(prefix="oc-upstream-cede-probe-") as tmp:
        temp = Path(tmp)
        for kind, filename in (
            ("location", "mapping_loc_Cede-OED.yaml"),
            ("account", "mapping_acc_Cede-OED.yaml"),
        ):
            mapping = mapping_dir / filename
            if not mapping.is_file():
                raise FileNotFoundError(f"pinned upstream {kind} mapping missing")
            original_text = mapping.read_text(encoding="utf-8")
            duplicate_keys = duplicate_type_keys(original_text)
            config = yaml.safe_load(original_text)
            if not isinstance(config, dict) or not isinstance(config.get("types"), dict):
                raise ValueError(f"pinned upstream {kind} mapping malformed")
            row = _source_row(config["types"])
            inp = temp / f"{kind}_source.csv"
            out = temp / f"{kind}_oed.csv"
            cfg = temp / f"{kind}_config.yaml"
            _write_csv(inp, row)
            _write_config(cfg, inp, out, mapping)
            try:
                completed = subprocess.run(
                    [command, "transform", "--config-file", str(cfg)],
                    cwd=temp, capture_output=True, text=True, timeout=90, check=False,
                )
                exit_code = completed.returncode
                # Bound and sanitize diagnostics; never record source rows/locations.
                lines = [re.sub(r"/[^\s:'\"]+", "<path>", x) for x in
                         completed.stderr.strip().splitlines() if x.strip()]
                diagnostic = lines[-1][:260] if lines else None
            except (OSError, subprocess.TimeoutExpired) as exc:
                exit_code = -1
                diagnostic = type(exc).__name__
            generated = out.is_file() and out.stat().st_size > 0
            record = {
                "mapping": kind, "declared_source_fields": len(row),
                "duplicate_type_keys": duplicate_keys,
                "declared_target_fields": len(config.get("transform", {})),
                "transform_exit_code": exit_code,
                "generated_csv": generated,
                "diagnostic": diagnostic,
            }
            if generated:
                with out.open("r", encoding="utf-8", newline="") as stream:
                    reader = csv.DictReader(stream)
                    record["output_fields"] = len(reader.fieldnames or [])
                    record["output_rows"] = sum(1 for _ in reader)
            result["runs"].append(record)
        # These are strictly upstream *execution* outcomes, not OED conformance.
        result["full_mapping_executed_both"] = all(
            x["transform_exit_code"] == 0 and x["generated_csv"] and x.get("output_rows") == 1
            for x in result["runs"]
        )
        # Full mapping is *never* approved by this exploratory runner.
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-checkout", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = probe(args.upstream_checkout)
    except (FileNotFoundError, ValueError, OSError, yaml.YAMLError) as exc:
        parser.exit(2, f"BLOCKED (probe infrastructure): {type(exc).__name__}: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
