# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Point-pixel sensitivity using the pinned JRC LUISA and CLIMAAX originals.

This reproduces a tiny deterministic conditional sensitivity, not a portfolio
loss model. Each sampled LUISA 50 m pixel is treated as one 2,500 m² asset;
all six source curves are evaluated separately by their literal CSV names.
No two outbuilding curves are mixed because their workbook/notebook ordering
is unresolved. Structural values remain in the source's 2010 EUR basis.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import tomllib
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research_runners.climk_germany_hazard_geojson_v0 import export, validate_bounds
from research_runners.climk_building_hazard_join_v0 import join_points

RASTER_SHA256 = "6693db65a8bb4d7f152e11533d121130c716037e82f67a55b67e8e82ef467c8a"
WORKBOOK_SHA256 = "a4ddff2c35bbc3536330389334c0fcae378799a49c6b7f3c643276065bbb8276"
CURVES_SHA256 = "d960e67ab726815974feb08e5850054d7fac2873ea5bb3b02956e6262da7fd81"
HAZARD_SHA256 = "92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def sha256_file(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _column(reference):
    letters = "".join(char for char in reference if char.isalpha())
    value = 0
    for char in letters:
        value = value * 26 + ord(char.upper()) - ord("A") + 1
    return value - 1


def read_luisa_values(path):
    """Read class-level structure/content €/m² from the pinned XLSX cache."""
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

    def values(row):
        result = {}
        for cell in row.findall("m:c", NS):
            node = cell.find("m:v", NS)
            if node is None:
                continue
            text = node.text or ""
            if cell.attrib.get("t") == "s":
                text = shared[int(text)]
            result[_column(cell.attrib["r"])] = text
        return result

    header = values(rows[0])
    names = {int(column): name for column, name in header.items()}
    required = {0: "Land use code", 1: "Description", 22: "structural €/m²", 23: "content €/m²"}
    if any(names.get(column) != label for column, label in required.items()):
        raise ValueError("unexpected LUISA workbook schema")
    result = {}
    for row in rows[1:]:
        cells = values(row)
        code = int(cells[0])
        structure = float(cells[22])
        content = float(cells[23])
        if code in result or not math.isfinite(structure + content) or min(structure, content) < 0:
            raise ValueError("duplicate class or invalid LUISA values")
        result[code] = {
            "description": cells[1],
            "structural_2010_eur_per_m2": structure,
            "content_2010_eur_per_m2": content,
        }
    if len(result) != 46:
        raise ValueError("incomplete LUISA class table")
    return result


def read_named_curves(path):
    """Read the six source curves preserving, and never guessing, CSV labels."""
    if sha256_file(path) != CURVES_SHA256:
        raise ValueError("Feuerstein/Koks curve source SHA-256 mismatch")
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        headers = [name.strip() for name in (reader.fieldnames or [])]
        if len(headers) != 7 or headers[0] != "wind speed" or len(set(headers)) != len(headers):
            raise ValueError("unexpected Feuerstein/Koks curve schema")
        rows = []
        for raw in reader:
            row = {name.strip(): float(value) for name, value in raw.items()}
            rows.append(row)
    if len(rows) < 2:
        raise ValueError("at least two curve points are required")
    speed = [row["wind speed"] for row in rows]
    if any(not math.isfinite(item) for item in speed) or any(b <= a for a, b in zip(speed, speed[1:])):
        raise ValueError("wind speed knots must be finite and increasing")
    for name in headers[1:]:
        series = [row[name] for row in rows]
        if any(not math.isfinite(item) or not 0 <= item <= 100 for item in series):
            raise ValueError(f"invalid percent values for named curve {name}")
        if any(b < a for a, b in zip(series, series[1:])):
            raise ValueError(f"nonmonotone named curve {name}")
    return headers, rows


def interpolate_percent(gust_mps, name, headers, rows):
    if name not in headers[1:]:
        raise ValueError("curve must be selected by an exact source column name")
    if not math.isfinite(gust_mps) or not rows[0]["wind speed"] <= gust_mps <= rows[-1]["wind speed"]:
        raise ValueError("gust outside source curve support; extrapolation is blocked")
    for left, right in zip(rows, rows[1:]):
        if gust_mps <= right["wind speed"]:
            width = right["wind speed"] - left["wind speed"]
            fraction = (gust_mps - left["wind speed"]) / width
            return left[name] + fraction * (right[name] - left[name])
    return rows[-1][name]


def read_landuse_points(path, sites):
    """Return containing LUISA class for each point; uses raster CRS directly."""
    if sha256_file(path) != RASTER_SHA256:
        raise ValueError("JRC LUISA raster source SHA-256 mismatch")
    try:
        import rasterio
        from rasterio.warp import transform
    except ImportError as exc:
        raise RuntimeError("rasterio is required for the LUISA point lookup") from exc
    output = []
    with rasterio.open(path) as dataset:
        if dataset.crs.to_string() != "EPSG:3035" or dataset.count != 1:
            raise ValueError("unexpected JRC LUISA raster CRS or band count")
        if dataset.transform.a != 50 or dataset.transform.e != -50:
            raise ValueError("unexpected JRC LUISA raster pixel size")
        for site in sites:
            x, y = transform("EPSG:4326", dataset.crs, [site["longitude"]], [site["latitude"]])
            row, col = dataset.index(x[0], y[0])
            if not (0 <= row < dataset.height and 0 <= col < dataset.width):
                raise ValueError("site outside LUISA raster")
            code = int(dataset.read(1, window=((row, row + 1), (col, col + 1))).item())
            if code == dataset.nodata or code <= 0:
                raise ValueError("LUISA nodata/zero class at site")
            output.append({"row": row, "column": col, "landuse_code": code,
                           "pixel_area_m2": abs(dataset.transform.a * dataset.transform.e)})
    if len({(row["row"], row["column"]) for row in output}) != len(output):
        raise ValueError("duplicate point pixels would double count the same LUISA asset")
    return output


def run(raster_path, workbook_path, curves_path, hazard_path, sites, *, storm_index=0,
        bounds=(-5, 45, 16, 56)):
    bounds = validate_bounds(bounds)
    for site in sites:
        if not isinstance(site.get("site_id"), str) or not site["site_id"]:
            raise ValueError("unique explicit site_id required")
        for key, low, high in (("longitude", -180, 180), ("latitude", -90, 90)):
            value = site.get(key)
            if type(value) not in (float, int) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError("invalid WGS84 point coordinate")
    if len({site["site_id"] for site in sites}) != len(sites) or not sites:
        raise ValueError("nonempty unique point set required")
    for path, expected, label in ((hazard_path, HAZARD_SHA256, "CLIMK hazard"),):
        if sha256_file(path) != expected:
            raise ValueError(f"{label} source SHA-256 mismatch")
    if type(storm_index) is not int or not 0 <= storm_index < 50:
        raise ValueError("CLIMK storm index must be from 0 through 49")

    classes = read_luisa_values(workbook_path)
    headers, curves = read_named_curves(curves_path)
    pixels = read_landuse_points(raster_path, sites)
    if len({(row["row"], row["column"]) for row in pixels}) != len(pixels):
        raise ValueError("duplicate point pixels would double count the same LUISA asset")
    source_bytes = Path(hazard_path).read_bytes()
    hazard = export(source_bytes, storm_index, bounds)
    weather_points = [dict(site, building_id=site["site_id"]) for site in sites]
    joined = join_points(hazard["features"], weather_points)
    if any(row["status"] != "matched" for row in joined):
        raise ValueError("one or more points lack CLIMK hazard support")

    outputs = []
    totals = {name: 0.0 for name in headers[1:]}
    for site, pixel, weather in zip(sites, pixels, joined):
        landuse = classes.get(pixel["landuse_code"])
        if landuse is None:
            raise ValueError("LUISA raster class has no workbook value row")
        max_structure = landuse["structural_2010_eur_per_m2"] * pixel["pixel_area_m2"]
        responses = {}
        for name in headers[1:]:
            percent = interpolate_percent(weather["gust_mps"], name, headers, curves)
            loss = max_structure * percent / 100
            if not math.isfinite(loss) or not 0 <= loss <= max_structure:
                raise ValueError("point-pixel loss conservation failed")
            responses[name] = {"damage_percent": percent, "structural_loss_2010_eur": loss}
            totals[name] += loss
        outputs.append({
            "site_id": site["site_id"], "longitude": site["longitude"], "latitude": site["latitude"],
            "climk_gust_mps": weather["gust_mps"], "luisa_row": pixel["row"],
            "luisa_column": pixel["column"], "luisa_landuse_code": pixel["landuse_code"],
            "luisa_description": landuse["description"], "asset_basis": "one complete 50m LUISA pixel, 2500 m2; not a building footprint",
            "structural_max_2010_eur_per_m2": landuse["structural_2010_eur_per_m2"],
            "structural_max_2010_eur_per_pixel": max_structure,
            "content_max_2010_eur_per_m2_excluded": landuse["content_2010_eur_per_m2"],
            "single_curve_sensitivity": responses,
        })
    return {
        "profile": "windstorm-europe-luisa-point-pixel-sensitivity-v0",
        "status": "conditional_deterministic_sensitivity_not_calibrated",
        "storm_index": storm_index, "hazard_bounds_wgs84": list(bounds),
        "pixel_area_m2": 2500,
        "structural_value_basis": "CLIMAAX LUISA workbook cached values; 2010 EUR per m2",
        "response_basis": "each named Feuerstein/Koks source curve evaluated independently; no LUISA curve mixing",
        "vulnerability_mixture_admitted": False,
        "annual_frequency_established": False,
        "building_or_insured_loss": False,
        "source_sha256": {"luisa_raster": RASTER_SHA256, "luisa_workbook": WORKBOOK_SHA256,
                          "construction_curves": CURVES_SHA256, "climk_hazard": HAZARD_SHA256},
        "hazard_metadata": hazard["metadata"], "points": outputs,
        "sum_of_sampled_pixels_structural_loss_2010_eur_by_single_curve": totals,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raster", type=Path, required=True)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--curves", type=Path, required=True)
    parser.add_argument("--hazard", type=Path, required=True)
    parser.add_argument("--sites", type=Path, required=True, help="JSON list of fictional point IDs and WGS84 coordinates")
    parser.add_argument("--storm-index", type=int)
    parser.add_argument("--bounds", type=float, nargs=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    raw_config = args.sites.read_bytes()
    try:
        site_config = tomllib.loads(raw_config.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        parser.error(f"sites configuration must be valid TOML: {exc}")
    if site_config.get("profile") != "windstorm-europe-luisa-point-pixel-sensitivity-v0":
        parser.error("unsupported point sensitivity configuration profile")
    expected_sources = site_config.get("source_expectations", {})
    pinned_sources = {"luisa_raster_sha256": RASTER_SHA256,
                      "luisa_workbook_sha256": WORKBOOK_SHA256,
                      "construction_curves_sha256": CURVES_SHA256,
                      "climk_hazard_sha256": HAZARD_SHA256}
    if expected_sources != pinned_sources:
        parser.error("configuration source pins do not match this runner")
    sites = site_config.get("sites")
    storm_index = args.storm_index if args.storm_index is not None else site_config.get("storm_index", 0)
    bounds = args.bounds if args.bounds is not None else site_config.get("hazard_bounds_wgs84", (-5, 45, 16, 56))
    result = run(args.raster, args.workbook, args.curves, args.hazard,
                 sites, storm_index=storm_index, bounds=bounds)
    result["runner_sha256"] = sha256_file(__file__)
    result["sites_configuration_sha256"] = hashlib.sha256(raw_config).hexdigest()
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"profile": result["profile"], "point_pixels": len(result["points"]),
                      "storm_index": result["storm_index"], "calibrated": False,
                      "annual_frequency_established": False}))


if __name__ == "__main__":
    main()
