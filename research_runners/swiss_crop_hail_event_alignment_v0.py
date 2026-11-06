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


def source_pair_summary(exposure, damage, hazard_dates) -> dict[str, object]:
    import numpy as np
    # pandas/PyTables fixed release layout observed from real ZIP schema.
    block = exposure["exposures"]
    labels = [_str_label(v).lower() for v in block["block0_items"][()]]
    if labels.count("latitude") != 1 or labels.count("longitude") != 1:
        raise Blocked("original exposure float block lacks unique lat/lon columns")
    float_matrix = block["block0_values"][()]
    positions = damage["coord_exp"][()]
    rows = len(block["axis1"])
    if (float_matrix.ndim != 2 or float_matrix.shape[0] != rows or
            positions.shape != (rows, 2) or rows == 0):
        raise Blocked("crop exposure and observed-damage positions incompatible")
    expected = np.stack([
        float_matrix[:, labels.index("latitude")],
        float_matrix[:, labels.index("longitude")],
    ], axis=1)
    finite = bool(np.isfinite(expected).all() and np.isfinite(positions).all())
    aligned = int(np.count_nonzero(
        np.all(np.isclose(expected, positions, atol=0.000001, rtol=0), axis=1)
    )) if finite else 0
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
            (len(indices) and (np.min(indices) < 0 or np.max(indices) >= rows))):
        raise Blocked("original damage CSR data do not match event or location axes")
    if not (np.isfinite(values).all() and np.all(values >= 0)):
        raise Blocked("reported crop impact values contain nonfinite/negative entries")
    observed_dates = sorted(int(x) for x in dates)
    return {
        "position_count": rows,
        "exact_order_coordinate_matches_1e_6_degrees": aligned,
        "position_alignment_complete": aligned == rows,
        "finite_coordinates": finite,
        "observed_event_count": n_events,
        "observed_event_dates_are_radar_subset": True,
        "observed_event_ordinals": observed_dates,
        "nonzero_impact_cells": len(values),
        "csr_structurally_valid": True,
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
    print(json.dumps({
        "schema_version": "swiss-hail-source-alignment-audit-v0",
        "original_hdf5_pairs_checked": len(summaries),
        "meshs_poh_radar_grid_points": 454400,
        "radar_event_count": 12,
        "all_event_date_sets_subset": True,
        "all_coordinate_pairs_row_aligned": all(x["position_alignment_complete"] for x in summaries),
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
