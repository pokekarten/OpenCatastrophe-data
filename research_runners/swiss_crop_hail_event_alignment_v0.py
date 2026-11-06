# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original Swiss crop hail exposure/damage/radar alignment research, fail-closed.

Only published file versions are downloaded, MD5-checked and briefly opened
in a temporary directory. Individual event impacts and coordinates stay in
memory; JSON prints aggregate alignment counts only. Never annualize 12
selected study events or interpret damaged-field counts as insured losses.
"""
from __future__ import annotations

from contextlib import contextmanager
import io
import json
from pathlib import Path
import tempfile
import zipfile
from urllib.request import build_opener

from research_runners.swiss_crop_hail_asset_preflight_v0 import Blocked, inspect_local
from research_runners.swiss_crop_hail_zenodo_original_acquire_v0 import (
    acquire_one, OriginalOnlyRedirect,
)
from research_runners.swiss_crop_hail_hdf5_metadata_profile_v0 import (
    CROPS, RESOLUTIONS_KM, archive_member_index, MAX_H5_MEMBER_BYTES,
)


def verify_dates_subset(source_dates, observed_dates) -> bool:
    """Dates must be unique and selected from the true source event set."""
    source = tuple(int(x) for x in source_dates)
    observed = tuple(int(x) for x in observed_dates)
    return (len(source) == len(set(source)) and
            len(observed) == len(set(observed)) and
            bool(observed) and
            set(observed).issubset(source))


@contextmanager
def open_member(archive: zipfile.ZipFile, name: str):
    """Open only publisher-pinned verified HDF5 bytes; never extract to disk."""
    import h5py
    member = archive.getinfo(name)
    if not 0 < member.file_size <= MAX_H5_MEMBER_BYTES:
        raise Blocked("crop HDF5 member exceeds safe bound")
    with archive.open(member) as stream:
        data = stream.read(MAX_H5_MEMBER_BYTES + 1)
    if len(data) != member.file_size or not data.startswith(b"\x89HDF\r\n\x1a\n"):
        raise Blocked("crop HDF5 member identity failed")
    with h5py.File(io.BytesIO(data), "r") as h5:
        yield h5


def _str_label(value) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def coordinate_key_coverage(exposure_positions, damage_positions) -> dict[str, object]:
    """Bounded spatial key coverage, not row matching or scientific admission.

    Five decimal places (~metre) prevent assuming equal row counts/order.
    Expose only aggregate key counts, never coordinates.
    """
    source_keys = [(round(float(lat), 5), round(float(lon), 5))
                   for lat, lon in exposure_positions]
    damage_keys = [(round(float(lat), 5), round(float(lon), 5))
                   for lat, lon in damage_positions]
    source_set = set(source_keys)
    damage_set = set(damage_keys)
    matches = sum(key in source_set for key in damage_keys)
    return {
        "source_unique_key_count": len(source_set),
        "source_duplicate_key_count": len(source_keys) - len(source_set),
        "damage_unique_key_count": len(damage_set),
        "damage_duplicate_key_count": len(damage_keys) - len(damage_set),
        "damage_positions_matching_exposure_key": matches,
        "damage_positions_without_exposure_key": len(damage_keys) - matches,
        "coordinate_key_rounding_decimals": 5,
        "full_damage_coordinate_key_coverage": (matches == len(damage_keys) and
                                                  len(damage_keys) > 0 and
                                                  len(source_keys) == len(source_set) and
                                                  len(damage_keys) == len(damage_set)),
    }


def unmatched_positive_impact_summary(
    exposure_positions, damage_positions, impact_indices, impact_values
) -> dict[str, int]:
    """Count only nonzero impact cells on unmatched damage coordinates.

    No original impact values or coordinates leave memory or enter the report.
    """
    source_keys = {(round(float(lat), 5), round(float(lon), 5))
                   for lat, lon in exposure_positions}
    missing = {i for i, (lat, lon) in enumerate(damage_positions)
               if (round(float(lat), 5), round(float(lon), 5)) not in source_keys}
    positive = [int(i) for i, value in zip(impact_indices, impact_values)
                if float(value) > 0 and int(i) in missing]
    return {
        "unmatched_damage_grid_positions": len(missing),
        "unmatched_positions_with_positive_impact": len(set(positive)),
        "positive_impact_matrix_cells_on_unmatched_positions": len(positive),
    }


def unmatched_positive_impacts_by_event(
    exposure_positions, damage_positions, event_dates, indptr, indices, values
) -> list[dict[str, int]]:
    """Aggregate *observed* positive sparse cells per original event ordinal.

    Event ordinals represent selected publication event days, not a complete
    annual frequency sample. Counts repeat across crops/resolutions and are
    neither unique claims nor monetary insurance loss.
    """
    source_keys = {(round(float(lat), 5), round(float(lon), 5))
                   for lat, lon in exposure_positions}
    missing = {i for i, (lat, lon) in enumerate(damage_positions)
               if (round(float(lat), 5), round(float(lon), 5)) not in source_keys}
    rows = []
    for event_pos, ordinal in enumerate(event_dates):
        left, right = int(indptr[event_pos]), int(indptr[event_pos + 1])
        positive_indices = [int(i) for i, impact in zip(indices[left:right],
                                                        values[left:right])
                            if float(impact) > 0]
        unmatched = [i for i in positive_indices if i in missing]
        rows.append({
            "event_ordinal": int(ordinal),
            "positive_impact_matrix_cells": len(positive_indices),
            "positive_impact_matrix_cells_on_unmatched_positions": len(unmatched),
            "unmatched_positions_with_positive_impact": len(set(unmatched)),
        })
    return rows


def source_pair_summary(exposure, damage, hazard_dates) -> dict[str, object]:
    import numpy as np
    # pandas/PyTables fixed release layout observed from real ZIP schema.
    block = exposure["exposures"]
    labels = [_str_label(v).lower() for v in block["block0_items"][()]]
    if labels.count("latitude") != 1 or labels.count("longitude") != 1:
        raise Blocked("original exposure float block lacks unique lat/lon columns")
    float_matrix = block["block0_values"][()]
    positions = damage["coord_exp"][()]
    exposure_count = len(block["axis1"])
    damage_count = len(positions)
    if (float_matrix.ndim != 2 or float_matrix.shape[0] != exposure_count or
            positions.ndim != 2 or positions.shape[1] != 2 or
            exposure_count == 0 or damage_count == 0):
        raise Blocked("original exposure or damage coordinates have invalid matrix dimensions")
    expected = np.stack([
        float_matrix[:, labels.index("latitude")],
        float_matrix[:, labels.index("longitude")],
    ], axis=1)
    finite = bool(np.isfinite(expected).all() and np.isfinite(positions).all())
    if not finite:
        raise Blocked("original spatial coordinates include nonfinite positions")
    metrics = coordinate_key_coverage(expected, positions)
    aligned = int(np.count_nonzero(np.all(
        np.isclose(expected, positions, atol=0.000001, rtol=0), axis=1
    ))) if exposure_count == damage_count else 0
    dates = damage["date"][()]
    if not verify_dates_subset(hazard_dates, dates):
        raise Blocked("reported crop damage event dates are not a strict subset of radar events")
    n_events = len(dates)
    pointers = damage["imp_mat/indptr"][()]
    indices = damage["imp_mat/indices"][()]
    values = damage["imp_mat/data"][()]
    if (len(pointers) != n_events+1 or pointers[0] != 0 or
            pointers[-1] != len(indices) or len(indices) != len(values) or
            np.any(np.diff(pointers) < 0) or
            (len(indices) and (np.min(indices) < 0 or np.max(indices) >= damage_count))):
        raise Blocked("original damage CSR data do not match event or location axes")
    if not (np.isfinite(values).all() and np.all(values >= 0)):
        raise Blocked("reported crop impact values contain nonfinite/negative entries")
    observed_dates = sorted(int(x) for x in dates)
    nonjoin = unmatched_positive_impact_summary(expected, positions, indices, values)
    by_event = unmatched_positive_impacts_by_event(
        expected, positions, dates, pointers, indices, values
    )
    if (sum(row["positive_impact_matrix_cells_on_unmatched_positions"]
            for row in by_event) !=
            nonjoin["positive_impact_matrix_cells_on_unmatched_positions"] or
            sum(row["positive_impact_matrix_cells"] for row in by_event) !=
            int(np.count_nonzero(values))):
        raise Blocked("original event-wise positive impact counts failed conservation")
    return {
        "exposure_position_count": exposure_count,
        "damage_position_count": damage_count,
        "exact_order_coordinate_matches_1e_6_degrees": aligned,
        "positions_equal_count_and_order": exposure_count == damage_count and aligned == exposure_count,
        **metrics,
        "finite_coordinates": finite,
        "observed_event_count": n_events,
        "observed_event_dates_are_radar_subset": True,
        "observed_event_ordinals": observed_dates,
        "stored_impact_matrix_cells": len(values),
        "nonzero_impact_cells": int(np.count_nonzero(values)),
        "csr_structurally_valid": True,
        "positive_impact_coverage_by_source_event": by_event,
        **nonjoin,
        "individual_observed_impacts_exported": False,
        "interpretable_as_insured_loss_currency": False,
    }


def main() -> int:
    import h5py
    import numpy as np
    opener = build_opener(OriginalOnlyRedirect())
    with tempfile.TemporaryDirectory(prefix="oc-ch-hail-alignment-") as tmp:
        paths = {}
        for i, asset in enumerate(("radar_meshs_h5", "radar_poh_h5",
                                   "exposure_zip", "damage_zip")):
            paths[asset] = Path(tmp) / f"original-{i}.bin"
            acquire_one(asset, paths[asset], opener)
            inspect_local(asset, paths[asset])
        with h5py.File(paths["radar_meshs_h5"], "r") as mesh, h5py.File(
                paths["radar_poh_h5"], "r") as poh:
            radar_dates = tuple(int(x) for x in mesh["date"][()])
            other_dates = tuple(int(x) for x in poh["date"][()])
            if len(radar_dates) != 12 or radar_dates != other_dates or (
                    len(set(radar_dates)) != 12):
                raise Blocked("MESHS and POH date axes are not the same 12 unique days")
            if (mesh["centroids/lat"].shape != poh["centroids/lat"].shape or
                    mesh["centroids/lon"].shape != poh["centroids/lon"].shape):
                raise Blocked("radar locations differ in total count")
            count = len(mesh["centroids/lat"])
            if count != 454400 or mesh["centroids/lon"].shape != (count,):
                raise Blocked("source radar grid size changed from verified profile")
            with zipfile.ZipFile(paths["exposure_zip"]) as exzip, zipfile.ZipFile(
                    paths["damage_zip"]) as dmzip:
                exnames = archive_member_index(exzip.namelist(), "exposure")
                dmnames = archive_member_index(dmzip.namelist(), "damage")
                summaries = []
                for crop in CROPS:
                    for km in RESOLUTIONS_KM:
                        exname = f"exposure_CH_{crop}_{km}km.h5"
                        dmname = f"hail_damage_CH_{crop}_{km}km.h5"
                        with open_member(exzip, exnames[exname]) as exp:
                            with open_member(dmzip, dmnames[dmname]) as impact:
                                joined = source_pair_summary(exp, impact, radar_dates)
                        summaries.append({"crop": crop, "resolution_km": km, **joined})
    # Cross-pair counts are summed over source observations, never deduped
    # into putative claims or interpreted as an annual storm sample.
    by_original_day = {int(day): 0 for day in radar_dates}
    for pair in summaries:
        for row in pair["positive_impact_coverage_by_source_event"]:
            by_original_day[row["event_ordinal"]] += (
                row["positive_impact_matrix_cells_on_unmatched_positions"]
            )
    if sum(by_original_day.values()) != sum(
        row["positive_impact_matrix_cells_on_unmatched_positions"]
        for row in summaries
    ):
        raise Blocked("cross-pair historical event-cell totals do not conserve")
    print(json.dumps({
        "schema_version": "swiss-hail-source-alignment-audit-v0",
        "original_hdf5_pairs_checked": len(summaries),
        "meshs_poh_radar_grid_points": 454400,
        "radar_event_count": 12,
        "all_event_date_sets_subset": True,
        "all_damage_position_keys_covered": all(x["full_damage_coordinate_key_coverage"] for x in summaries),
        "all_same_rows_in_same_order": all(x["positions_equal_count_and_order"] for x in summaries),
        "sum_unmatched_positive_impact_matrix_cells": sum(x["positive_impact_matrix_cells_on_unmatched_positions"] for x in summaries),
        "unmatched_positive_impact_matrix_cells_by_original_event": [
            {"event_ordinal": ordinal,
             "positive_cells_summed_across_crop_resolution_pairs": by_original_day[ordinal]}
            for ordinal in sorted(by_original_day)
        ],
        "unmatched_positive_counts_are_not_unique_claims_or_annual_samples": True,
        "sum_unmatched_positions_with_positive_impact": sum(x["unmatched_positions_with_positive_impact"] for x in summaries),
        "pair_summaries": summaries,
        "source_bytes_retained": False,
        "raw_coordinates_exported": False,
        "original_impact_values_exported": False,
        "source_rights_cleared": False,
        "insured_loss_severity_model_validated": False,
        "annual_event_frequency_calibrated": False,
        "production_gross_net_ep_admitted": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
