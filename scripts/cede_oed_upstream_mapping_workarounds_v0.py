# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Isolate exactly two legacy upstream example defects in temporary research copies.

Never edit, commit, distribute or treat patched external mappings as approved
production adapters. The raw pinned YAML remains the independent authority.
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

if __package__:
    from .cede_oed_upstream_full_mapping_probe_v0 import (
        UPSTREAM_COMMIT, MAPPING_PATH, _source_row, _write_csv, _write_config
    )
else:
    from cede_oed_upstream_full_mapping_probe_v0 import (
        UPSTREAM_COMMIT, MAPPING_PATH, _source_row, _write_csv, _write_config
    )

PLACEHOLDER = "  Cede Field:\n    type: ODTF Data Type\n"
UNSAFE_WHEN = "      when: ExposureSetName\n"
BOOLEAN_WHEN = "      when: ExposureSetName is not in ['', 'NULL']\n"


def probe(upstream: Path) -> dict[str, object]:
    mapping_dir = upstream.resolve(strict=True) / MAPPING_PATH
    results = []
    with tempfile.TemporaryDirectory(prefix="oc-ce10-workaround-") as tmp:
        root = Path(tmp)
        for kind, filename in (
            ("location", "mapping_loc_Cede-OED.yaml"),
            ("account", "mapping_acc_Cede-OED.yaml"),
        ):
            original = (mapping_dir / filename).read_text(encoding="utf-8")
            if original.count(UNSAFE_WHEN) != 1:
                raise ValueError("unexpected upstream ExposureSetName when expression")
            patched = original.replace(UNSAFE_WHEN, BOOLEAN_WHEN)
            patches = ["replace_nonboolean_when_clause"]
            if kind == "location":
                if patched.count(PLACEHOLDER) != 1:
                    raise ValueError("upstream untyped Cede Field placeholder changed")
                patched = patched.replace(PLACEHOLDER, "")
                patches.append("remove_undeclared_odtf_data_type_placeholder")
            parsed = yaml.safe_load(patched)
            if not isinstance(parsed, dict) or not isinstance(parsed.get("types"), dict):
                raise ValueError("patched research fixture cannot be parsed")
            source = _source_row(parsed["types"])
            source_file = root / f"{kind}_in.csv"
            output_file = root / f"{kind}_out.csv"
            mapping_file = root / f"{kind}_TEMPORARY_RESEARCH.yaml"
            config_file = root / f"{kind}_config.yaml"
            mapping_file.write_text(patched, encoding="utf-8")
            _write_csv(source_file, source)
            _write_config(config_file, source_file, output_file, mapping_file)
            try:
                completed = subprocess.run(
                    ["ods_tools", "transform", "--config-file", str(config_file)],
                    cwd=root, capture_output=True, text=True, timeout=90, check=False,
                )
                code = completed.returncode
                details = [re.sub(r"/[^\s:'\"]+", "<path>", x) for x in
                           completed.stderr.strip().splitlines() if x.strip()]
                error = details[-1][:300] if details else None
            except (OSError, subprocess.TimeoutExpired) as exc:
                code = -1
                error = type(exc).__name__
            generated = output_file.is_file() and output_file.stat().st_size > 0
            observation = {
                "kind": kind, "temporary_research_patches": patches,
                "input_field_count": len(source), "upstream_target_field_count": len(parsed["transform"]),
                "cli_returncode": code, "generated_csv": generated,
                "diagnostic": error,
            }
            if generated:
                with output_file.open("r", encoding="utf-8", newline="") as handle:
                    reader = csv.DictReader(handle)
                    observation["output_rows"] = sum(1 for _ in reader)
                    observation["output_fields"] = len(reader.fieldnames or [])
            results.append(observation)
    return {
        "profile": "cede10-oed302-temporary-upstream-example-workaround-probe-v0",
        "upstream_commit": UPSTREAM_COMMIT, "synthetic_only": True,
        "temporary_patches_never_committed": True, "source_version": "10.0.0",
        "target_version": "3.0.2", "observations": results,
        "both_generated": all(x["generated_csv"] and x.get("output_rows") == 1 for x in results),
        "full_mapping_approved": False, "oed_schema_validated": False,
        "cede13_compatible": False, "rights_approved": False, "model_input_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-checkout", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = probe(args.upstream_checkout)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.exit(2, f"BLOCKED research infrastructure: {type(exc).__name__}: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
