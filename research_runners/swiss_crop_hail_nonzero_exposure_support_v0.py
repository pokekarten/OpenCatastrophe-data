# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Publisher-pinned *actual n_fields* support mask on Swiss crop hail sources.

The original NHESS crop-hail benchmark uses only grid cells with nonzero
exposure, where n_fields >= 1 for the default published threshold. Checking
matching coordinate keys alone is insufficient. The original ZIP bytes are
verified against Zenodo MD5 and held in an ephemeral local directory. This
script reports only aggregate event-grid counts, never raw geolocations,
field-level claims, physical hail footprints, or insured currency losses.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
from urllib.request import build_opener
import zipfile

from research_runners.swiss_crop_hail_asset_preflight_v0 import Blocked, inspect_local
from research_runners.swiss_crop_hail_zenodo_original_acquire_v0 import (
    acquire_one, OriginalOnlyRedirect,
)
from research_runners.swiss_crop_hail_hdf5_metadata_profile_v0 import (
    CROPS, RESOLUTIONS_KM, archive_member_index,
)
from research_runners.swiss_crop_hail_event_alignment_v0 import open_member, _str_label


def key(position) -> tuple[float, float]:
    if len(position) != 2:
        raise Blocked("coordinate does not have two axes")
    lat, lon = (float(position[0]), float(position[1]))
    if not (math.isfinite(lat) and math.isfinite(lon) and
            -90 <= lat <= 90 and -180 <= lon <= 180):
        raise Blocked("invalid latitude-longitude coordinate")
    return round(lat, 5), round(lon, 5)


def classify_original_support(
    exposure_positions, n_fields, damage_positions,
    dates, pointers, indices, values
) -> dict[str, object]:
    """Classify positive sparse event-grid observations into 3 disjoint supports.

    * source field-count >=1
    * coordinate exists in source but field count ==0
    * coordinate absent from the source coordinate keys

    Counts are event-grid observations, never unique claims or policy losses.
    """
    if len(exposure_positions) != len(n_fields) or not len(exposure_positions):
        raise Blocked("field counts and crop coordinate axis differ")
    source = {}
    zeros = 0
    for position, raw in zip(exposure_positions, n_fields):
        coord = key(position)
        count = float(raw)
        if not math.isfinite(count) or count < 0 or count > 1_000_000 or not count.is_integer():
            raise Blocked("noninteger, negative or nonfinite original crop-field count")
        if coord in source:
            raise Blocked("non-unique original source geography key")
        source[coord] = int(count)
        zeros += int(count == 0)
    damage_categories = []
    for position in damage_positions:
        coord = key(position)
        if coord not in source:
            damage_categories.append("missing")
        elif source[coord] == 0:
            damage_categories.append("zero")
        else:
            damage_categories.append("positive")
    date_count = len(dates)
    if not 1 <= date_count <= 12:
        raise Blocked("invalid selected storm event count")
    if (len(pointers) != date_count + 1 or int(pointers[0]) != 0 or
            int(pointers[-1]) != len(indices) or len(indices) != len(values) or
            any(int(b) < int(a) for a, b in zip(pointers, pointers[1:]))):
        raise Blocked("invalid damage CSR event axis")
    output = {"positive": 0, "zero": 0, "missing": 0}
    for j, amount in zip(indices, values):
        position_index = int(j)
        val = float(amount)
        if (not math.isfinite(val) or val < 0 or
                position_index < 0 or position_index >= len(damage_categories)):
            raise Blocked("invalid damage CSR position index or value")
        if val > 0:
            output[damage_categories[position_index]] += 1
    total = sum(output.values())
    if total == 0:
        raise Blocked("no positive observed damage matrix cells to audit")
    return {
        "crop_field_support_threshold": 1,
        "source_exposure_grid_positions": len(source),
        "source_positions_with_zero_fields": zeros,
        "damage_grid_positions": len(damage_categories),
        "damage_grid_positions_missing_from_source_coordinates": damage_categories.count("missing"),
        "damage_grid_positions_with_source_n_fields_zero": damage_categories.count("zero"),
        "original_selected_event_days": date_count,
        "positive_event_grid_damage_cells_total": total,
        "positive_event_grid_cells_with_source_n_fields_at_least_one": output["positive"],
        "positive_event_grid_cells_with_source_n_fields_zero": output["zero"],
        "positive_event_grid_cells_with_source_coordinate_absent": output["missing"],
        "positive_event_grid_cells_outside_true_source_exposure": output["zero"] + output["missing"],
        "excluded_observed_positive_fraction": round(
            (output["zero"] + output["missing"]) / total, 8
        ),
        "all_positive_event_grid_cells_conserved": True,
        "actual_insurer_claims_read": False,
        "annualized_or_valued": False,
    }


def profile_pair(exp, damage) -> dict[str, object]:
    import numpy as np
    block = exp["exposures"]
    labels = [_str_label(v).lower() for v in block["block0_items"][()]]
    if any(labels.count(label) != 1 for label in ("latitude", "longitude", "n_fields")):
        raise Blocked("original field-count and coordinate labels missing or ambiguous")
    floating = block["block0_values"][()]
    coords = damage["coord_exp"][()]
    if floating.ndim != 2 or len(floating) != len(block["axis1"]) or coords.ndim != 2 or coords.shape[1] != 2:
        raise Blocked("original exposure or damage HDF5 axes are invalid")
    positions = np.stack(
        [floating[:, labels.index("latitude")],
         floating[:, labels.index("longitude")]],
        axis=1,
    )
    return classify_original_support(
        positions, floating[:, labels.index("n_fields")], coords,
        damage["date"][()], damage["imp_mat/indptr"][()],
        damage["imp_mat/indices"][()], damage["imp_mat/data"][()],
    )


def main() -> int:
    opener = build_opener(OriginalOnlyRedirect())
    with tempfile.TemporaryDirectory(prefix="oc-swiss-hail-crop-fields-") as temp:
        paths = {}
        for i, asset in enumerate(("exposure_zip", "damage_zip")):
            path = Path(temp) / f"publisher-{i}.bin"
            acquire_one(asset, path, opener)
            inspect_local(asset, path)
            paths[asset] = path
        with zipfile.ZipFile(paths["exposure_zip"]) as exzip, zipfile.ZipFile(
            paths["damage_zip"]
        ) as dmzip:
            exnames = archive_member_index(exzip.namelist(), "exposure")
            dmnames = archive_member_index(dmzip.namelist(), "damage")
            rows = []
            for crop in CROPS:
                for km in RESOLUTIONS_KM:
                    e = f"exposure_CH_{crop}_{km}km.h5"
                    d = f"hail_damage_CH_{crop}_{km}km.h5"
                    with open_member(exzip, exnames[e]) as exp, open_member(
                        dmzip, dmnames[d]
                    ) as damage:
                        info = profile_pair(exp, damage)
                    rows.append({"crop": crop, "resolution_km": km, **info})
    keys = ("positive_event_grid_damage_cells_total",
            "positive_event_grid_cells_with_source_n_fields_at_least_one",
            "positive_event_grid_cells_with_source_n_fields_zero",
            "positive_event_grid_cells_with_source_coordinate_absent",
            "positive_event_grid_cells_outside_true_source_exposure")
    agg = {name: sum(row[name] for row in rows) for name in keys}
    if agg[keys[0]] != agg[keys[1]] + agg[keys[2]] + agg[keys[3]]:
        raise Blocked("cross-crop source positive observations do not conserve")
    print(json.dumps({
        "schema_version": "swiss-crop-hail-original-n-fields-support-v0",
        "original_source_hdf5_pairs": len(rows),
        "source_field_count_threshold": 1,
        "aggregate_repeated_crop_resolution_event_grid_counts": agg,
        "pair_profiles": rows,
        "source_bytes_committed": False,
        "source_bytes_retained": False,
        "raw_coordinates_exported": False,
        "insurer_claim_values_exported": False,
        "reported_metrics_are_not_paper_hss_or_pod": True,
        "source_rights_admitted": False,
        "annual_model_admitted": False,
        "gross_net_oep_aep_ready": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
