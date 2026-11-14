# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Compare the two unresolved middle-curve mappings across every LUISA class.

The runner reports both the literal-name interpretation and the original
CLIMAAX notebook's positional computation. It does not choose which is the
intended scientific model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research_runners.windstorm_europe_luisa_point_sensitivity_v0 import (
    CURVES_SHA256,
    WORKBOOK_SHA256,
    read_named_curves,
    sha256_file,
)

MATERIAL_COLUMNS = (
    "weakest outbuilding",
    "outbuilding",
    "strong outbuilding",
    "weak brick structure",
    "strong brick structure",
    "concrete buidling",
)
CSV_COLUMNS = (
    "weakest outbuilding",
    "outbuilding strong",
    "outbuilding",
    "weak brick structure",
    "strong brick structure",
    "concrete buidling",
)
SEMANTIC_COLUMN = {
    "weakest outbuilding": "weakest outbuilding",
    "outbuilding": "outbuilding",
    "strong outbuilding": "outbuilding strong",
    "weak brick structure": "weak brick structure",
    "strong brick structure": "strong brick structure",
    "concrete buidling": "concrete buidling",
}
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _column_index(reference: str) -> int:
    letters = "".join(char for char in reference if char.isalpha())
    result = 0
    for char in letters:
        result = result * 26 + ord(char.upper()) - ord("A") + 1
    return result - 1


def read_material_shares(path: str | Path) -> dict[int, dict[str, object]]:
    """Read the six named construction shares from the pinned workbook."""
    path = Path(path)
    if sha256_file(path) != WORKBOOK_SHA256:
        raise ValueError("LUISA damage workbook source SHA-256 mismatch")
    with zipfile.ZipFile(path) as archive:
        shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        shared = [
            "".join(node.text or "" for node in item.findall(".//m:t", NS))
            for item in shared_root.findall("m:si", NS)
        ]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    rows = sheet.findall(".//m:sheetData/m:row", NS)
    if len(rows) != 47:
        raise ValueError("expected one header and 46 LUISA classes")

    def cells(row: ET.Element) -> dict[int, str]:
        values: dict[int, str] = {}
        for cell in row.findall("m:c", NS):
            value = cell.find("m:v", NS)
            if value is None:
                continue
            text = value.text or ""
            if cell.attrib.get("t") == "s":
                text = shared[int(text)]
            values[_column_index(cell.attrib["r"])] = text
        return values

    header = cells(rows[0])
    required = {0: "Land use code", 1: "Description"}
    required.update({29 + i: name for i, name in enumerate(MATERIAL_COLUMNS)})
    if any(header.get(index) != name for index, name in required.items()):
        raise ValueError("unexpected LUISA material-share workbook schema")

    result: dict[int, dict[str, object]] = {}
    for row in rows[1:]:
        values = cells(row)
        try:
            code = int(values[0])
            description = values[1]
            shares = [float(values[29 + i]) for i in range(len(MATERIAL_COLUMNS))]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("incomplete LUISA construction-share row") from exc
        total = sum(shares)
        if (
            code in result
            or any(not math.isfinite(value) or not 0 <= value <= 1 for value in shares)
            or total > 1 + 1e-9
        ):
            raise ValueError("duplicate LUISA class or invalid construction shares")
        result[code] = {
            "description": description,
            "shares": dict(zip(MATERIAL_COLUMNS, shares)),
            "share_total": total,
        }
    if len(result) != 46:
        raise ValueError("incomplete LUISA class share table")
    return result


def mix_one_curve(
    shares: dict[str, float],
    curve_values: dict[str, float],
    *,
    mapping: str,
) -> float:
    """Return a single weighted damage percentage under an explicit mapping."""
    if set(shares) != set(MATERIAL_COLUMNS):
        raise ValueError("share labels must exactly match the LUISA workbook")
    if mapping == "semantic_names":
        value = sum(shares[name] * curve_values[SEMANTIC_COLUMN[name]] for name in MATERIAL_COLUMNS)
    elif mapping == "legacy_positional":
        value = sum(shares[name] * curve_values[CSV_COLUMNS[index]] for index, name in enumerate(MATERIAL_COLUMNS))
    else:
        raise ValueError("mapping must be semantic_names or legacy_positional")
    if not math.isfinite(value) or not 0 <= value <= 100:
        raise ValueError("mixed damage percentage outside 0..100")
    return value


def compare(classes: dict[int, dict[str, object]], curve_rows: list[dict[str, float]]) -> dict[str, object]:
    speeds = [row["wind speed"] for row in curve_rows]
    if len(speeds) < 2 or any(b <= a for a, b in zip(speeds, speeds[1:])):
        raise ValueError("wind speed knots must be strictly increasing")
    if 40.0 not in speeds:
        raise ValueError("comparison requires the 40 m/s diagnostic knot")

    class_results = []
    global_max = {"difference_pp": -1.0}
    differing_classes = 0
    for code, item in sorted(classes.items()):
        shares = item["shares"]
        semantic = []
        legacy = []
        for row in curve_rows:
            semantic.append(mix_one_curve(shares, row, mapping="semantic_names"))
            legacy.append(mix_one_curve(shares, row, mapping="legacy_positional"))
        differences = [abs(left - right) for left, right in zip(semantic, legacy)]
        max_index = max(range(len(differences)), key=differences.__getitem__)
        at_40_index = speeds.index(40.0)
        class_max = differences[max_index]
        if class_max > 1e-12:
            differing_classes += 1
        record = {
            "landuse_code": code,
            "description": item["description"],
            "share_total": item["share_total"],
            "regular_outbuilding_share": shares["outbuilding"],
            "strong_outbuilding_share": shares["strong outbuilding"],
            "semantic_percent_at_40m_s": semantic[at_40_index],
            "legacy_percent_at_40m_s": legacy[at_40_index],
            "difference_pp_at_40m_s": semantic[at_40_index] - legacy[at_40_index],
            "semantic_curve_percent_at_max_difference": semantic[max_index],
            "legacy_curve_percent_at_max_difference": legacy[max_index],
            "max_absolute_difference_pp": class_max,
            "max_difference_wind_speed_m_s": speeds[max_index],
        }
        class_results.append(record)
        if class_max > global_max["difference_pp"]:
            global_max = {
                "difference_pp": class_max,
                "landuse_code": code,
                "description": item["description"],
                "wind_speed_m_s": speeds[max_index],
                "semantic_percent": semantic[max_index],
                "legacy_percent": legacy[max_index],
            }

    return {
        "class_count": len(class_results),
        "wind_speed_knot_count": len(speeds),
        "wind_speed_range_m_s": [speeds[0], speeds[-1]],
        "differing_class_count": differing_classes,
        "global_maximum_difference": global_max,
        "classes": class_results,
    }


def run(workbook_path: str | Path, curves_path: str | Path) -> dict[str, object]:
    classes = read_material_shares(workbook_path)
    headers, curve_rows = read_named_curves(curves_path)
    if tuple(headers[1:]) != CSV_COLUMNS:
        raise ValueError("unexpected pinned CSV curve order")
    result = compare(classes, curve_rows)
    return {
        "profile": "windstorm-europe-luisa-mixture-mapping-sensitivity-v0",
        "status": "two_unresolved_mappings_compared_no_mapping_selected",
        "workbook_sha256": WORKBOOK_SHA256,
        "curve_csv_sha256": CURVES_SHA256,
        "semantic_mapping": "workbook shares matched by class meaning to exact CSV labels; strong outbuilding => outbuilding strong",
        "legacy_mapping": "original notebook share order multiplied positionally by the six CSV curve columns",
        **result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--curves", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    result = run(args.workbook, args.curves)
    result["runner_sha256"] = sha256_file(__file__)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({key: result[key] for key in (
        "profile", "class_count", "wind_speed_knot_count", "differing_class_count", "global_maximum_difference"
    )}))


if __name__ == "__main__":
    main()
