# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original Swiss 1 km MESHS/POH binary hail-footprint skill smoke proof.

Publisher Zenodo MD5-pinned release files are opened only in GitHub runner
temporary storage; output aggregate *in-sample* 1 km contingency counts.
Neither original research HSS reproduction at all resolutions, cross-validation,
actual individual claim data, monetary losses, annual rate nor CAT admission.
The published impact model is exposure(n_fields>=1) AND hail intensity>=s.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
from urllib.request import build_opener
import zipfile

from research_runners.swiss_crop_hail_asset_preflight_v0 import Blocked, inspect_local
from research_runners.swiss_crop_hail_zenodo_original_acquire_v0 import (
    acquire_one, OriginalOnlyRedirect,
)
from research_runners.swiss_crop_hail_hdf5_metadata_profile_v0 import (
    CROPS, archive_member_index,
)
from research_runners.swiss_crop_hail_event_alignment_v0 import (
    open_member, verify_dates_subset, _str_label,
)
from research_runners.swiss_crop_hail_nonzero_exposure_support_v0 import key
from research_runners.swiss_crop_hail_verification_support_v0 import contingency_metrics


THRESHOLDS = {"MESHS": (20, 30, 40, 60), "POH": (40, 60, 80, 90)}
MAX_SOURCE_CENTROID_DISTANCE_M = 800.0
SOURCE_ASSETS = ("radar_meshs_h5", "radar_poh_h5", "exposure_zip", "damage_zip")


def require_threshold(variable: str, value: int, intensity: float) -> bool:
    """Source paper Eq (2): positive forecast for intensity >= threshold."""
    if variable not in THRESHOLDS or type(value) is not int or value not in THRESHOLDS[variable]:
        raise Blocked("threshold not in explicitly declared exploratory grid")
    if not (0 <= intensity <= (160 if variable == "MESHS" else 100)):
        raise Blocked("source radar intensity outside expected physical unit bound")
    return intensity >= value


def inspect_hazard(h5, label: str):
    import numpy as np
    from scipy.sparse import csr_matrix
    n = len(h5["centroids/lat"])
    if n != 454400 or len(h5["centroids/lon"]) != n:
        raise Blocked("published radar centroid axes changed")
    dates = tuple(int(x) for x in h5["date"][()])
    data = h5["intensity/data"][()]
    cols = h5["intensity/indices"][()]
    ptrs = h5["intensity/indptr"][()]
    if (len(dates) != 12 or len(set(dates)) != 12 or
            len(ptrs) != 13 or int(ptrs[0]) != 0 or
            int(ptrs[-1]) != len(data) or len(data) != len(cols) or
            np.any(np.diff(ptrs) < 0) or np.any(cols < 0) or
            np.any(cols >= n) or not np.isfinite(data).all() or
            np.any(data < 0)):
        raise Blocked("invalid published radar CSR matrix/date structure")
    maximum = float(np.max(data)) if len(data) else 0.0
    if not (20 <= maximum <= (160 if label == "MESHS" else 100)):
        raise Blocked("radar variable max outside expected MESHS mm or POH percent")
    return {
        "variable": label,
        "dates": dates,
        "lat": h5["centroids/lat"][()],
        "lon": h5["centroids/lon"][()],
        "csr": csr_matrix((data, cols, ptrs), shape=(12, n)),
        "published_nonzero_hazard_values": int(np.count_nonzero(data)),
        "max_source_intensity": round(maximum, 4),
    }


def exposure_and_observed(ex, dm, hazard_dates):
    import numpy as np
    block = ex["exposures"]
    labels = [_str_label(v).lower() for v in block["block0_items"][()]]
    if any(labels.count(field) != 1 for field in ("latitude", "longitude", "n_fields")):
        raise Blocked("required original crop exposure columns absent")
    values = block["block0_values"][()]
    if values.ndim != 2 or values.shape[0] != len(block["axis1"]):
        raise Blocked("invalid source exposure array dimensions")
    nfields = values[:, labels.index("n_fields")]
    if (not np.isfinite(nfields).all() or
            np.any(nfields < 1) or np.any(nfields != np.floor(nfields))):
        raise Blocked("publisher 1 km crop source not already n_fields>=1")
    source_coords = np.stack((
        values[:, labels.index("latitude")],
        values[:, labels.index("longitude")]
    ), axis=1)
    source_keys = [key(v) for v in source_coords]
    if len(source_keys) != len(set(source_keys)):
        raise Blocked("ambiguous source exposure coordinate keys")
    rows = len(source_keys)
    source_index = {point: j for j, point in enumerate(source_keys)}
    dates = tuple(int(x) for x in dm["date"][()])
    if not verify_dates_subset(hazard_dates, dates):
        raise Blocked("observed event dates not a subset of original radar event dates")
    locations = dm["coord_exp"][()]
    index_map = [source_index.get(key(position), -1) for position in locations]
    pointers = dm["imp_mat/indptr"][()]
    indices = dm["imp_mat/indices"][()]
    damage = dm["imp_mat/data"][()]
    if (len(pointers) != len(dates) + 1 or int(pointers[0]) != 0 or
            int(pointers[-1]) != len(indices) or len(indices) != len(damage) or
            np.any(np.diff(pointers) < 0) or
            np.any(indices < 0) or np.any(indices >= len(locations)) or
            not np.isfinite(damage).all() or np.any(damage < 0)):
        raise Blocked("invalid reported 1 km sparse impact matrix")
    observations = []
    missing = 0
    for j in range(len(dates)):
        labels = np.zeros(rows, dtype=bool)
        for k, val in zip(indices[pointers[j]:pointers[j+1]],
                          damage[pointers[j]:pointers[j+1]]):
            if val > 0:
                index = index_map[int(k)]
                if index < 0:
                    missing += 1
                else:
                    labels[index] = True
        observations.append(labels)
    # The earlier 24-pair original source receipt showed all six 1 km pairs
    # have exact coordinate coverage. Fail, never silently omit observations.
    if missing:
        raise Blocked("1 km pilot positive damage not in original crop support")
    return source_coords, dict(zip(dates, observations)), missing


def radar_to_exposure_centroids(lat, lon, source_coords) -> tuple[object, float]:
    import numpy as np
    from scipy.spatial import cKDTree
    from pyproj import Transformer
    if not (np.isfinite(lat).all() and np.isfinite(lon).all() and
            np.isfinite(source_coords).all()):
        raise Blocked("nonfinite original hazard/crop coordinates")
    trans = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    rx, ry = trans.transform(lon, lat)
    sx, sy = trans.transform(source_coords[:, 1], source_coords[:, 0])
    centroid_xy = np.column_stack((rx, ry))
    selected_xy = np.column_stack((sx, sy))
    distances, nearest = cKDTree(centroid_xy).query(selected_xy, k=1)
    if (not np.isfinite(distances).all() or
            len(nearest) != len(source_coords) or
            np.any(distances > MAX_SOURCE_CENTROID_DISTANCE_M)):
        raise Blocked("published crop grid centroid not aligned with 1 km source radar grid")
    return nearest, float(np.max(distances))


def run_skill(crop: str, hazard, selected, observed: dict[int, object]):
    import numpy as np
    date_to_idx = {d: i for i, d in enumerate(hazard["dates"])}
    bins = {}
    for threshold in THRESHOLDS[hazard["variable"]]:
        a = b = c = d = 0
        for event_date, truth in observed.items():
            radar_event = date_to_idx[event_date]
            readings = hazard["csr"][radar_event, selected].toarray().reshape(-1)
            # These are binary cropped forecast cells on the 2021 exposure
            # support, not measured monetary damage or a stochastic simulation.
            if (not np.isfinite(readings).all() or
                    np.any(readings < 0) or
                    np.any(readings > (160 if hazard["variable"] == "MESHS" else 100))):
                raise Blocked("invalid original radar event intensity")
            forecast = readings >= threshold
            if forecast.shape != truth.shape:
                raise Blocked("observed and forecast support axes differ")
            a += int(np.count_nonzero(forecast & truth))
            b += int(np.count_nonzero(forecast & ~truth))
            c += int(np.count_nonzero(~forecast & truth))
            d += int(np.count_nonzero(~forecast & ~truth))
        counted = a+b+c+d
        expected = len(observed)*len(selected)
        if counted != expected:
            raise Blocked("event x crop-exposure contingency totals do not conserve")
        bins[str(threshold)] = contingency_metrics(a, b, c, d)
    return {
        "crop": crop,
        "hazard": hazard["variable"],
        "grid_resolution_km": 1,
        "threshold_unit": "mm" if hazard["variable"] == "MESHS" else "percent",
        "observed_selected_event_count": len(observed),
        "exposed_grid_centroids_per_event": len(selected),
        "evaluation_population_counts_across_selected_event_days": len(observed)*len(selected),
        "threshold_metrics": bins,
    }


def main() -> int:
    import h5py
    import numpy as np
    opener = build_opener(OriginalOnlyRedirect())
    with tempfile.TemporaryDirectory(prefix="oc-swiss-crop-hail-1km-skill-") as temp:
        sources = {}
        for i, asset in enumerate(SOURCE_ASSETS):
            path = Path(temp) / f"source-{i}.bin"
            acquire_one(asset, path, opener)
            inspect_local(asset, path)
            sources[asset] = path
        with (h5py.File(sources["radar_meshs_h5"], "r") as mesh,
              h5py.File(sources["radar_poh_h5"], "r") as poh,
              zipfile.ZipFile(sources["exposure_zip"]) as expzip,
              zipfile.ZipFile(sources["damage_zip"]) as damagezip):
            mesh_haz = inspect_hazard(mesh, "MESHS")
            poh_haz = inspect_hazard(poh, "POH")
            if mesh_haz["dates"] != poh_haz["dates"] or (
                    not np.allclose(mesh_haz["lat"], poh_haz["lat"], rtol=0, atol=1e-8)) or (
                    not np.allclose(mesh_haz["lon"], poh_haz["lon"], rtol=0, atol=1e-8)):
                raise Blocked("MESHS and POH published 1 km source event/grids differ")
            exposure_names = archive_member_index(expzip.namelist(), "exposure")
            damage_names = archive_member_index(damagezip.namelist(), "damage")
            outputs = []
            maximum_centroid_offset_m = 0.0
            for crop in CROPS:
                exposure_file = exposure_names[f"exposure_CH_{crop}_1km.h5"]
                damage_file = damage_names[f"hail_damage_CH_{crop}_1km.h5"]
                with open_member(expzip, exposure_file) as ex, open_member(damagezip, damage_file) as dm:
                    coords, observations, ignored = exposure_and_observed(ex, dm, mesh_haz["dates"])
                nearest, max_distance = radar_to_exposure_centroids(
                    mesh_haz["lat"], mesh_haz["lon"], coords
                )
                maximum_centroid_offset_m = max(maximum_centroid_offset_m, max_distance)
                for hazard in (mesh_haz, poh_haz):
                    outputs.append(run_skill(crop, hazard, nearest, observations))
    print(json.dumps({
        "schema_version": "swiss-crop-hail-1km-original-binary-skill-pilot-v0",
        "source_hazard_events": len(mesh_haz["dates"]),
        "source_radar_grid_centroids": len(mesh_haz["lat"]),
        "max_nearest_crop_to_radar_centroid_offset_m": round(maximum_centroid_offset_m, 3),
        "source_mes_hazard_nonzero_entries": mesh_haz["published_nonzero_hazard_values"],
        "source_poh_hazard_nonzero_entries": poh_haz["published_nonzero_hazard_values"],
        "mesh_hazard_max_mm": mesh_haz["max_source_intensity"],
        "poh_hazard_max_percent": poh_haz["max_source_intensity"],
        "source_replay_results": outputs,
        "evaluations_in_sample_on_selected_historical_storm_days": True,
        "paper_full_multi_resolution_hss_reproduced": False,
        "published_code_executed": False,
        "holdout_or_temporal_validation_done": False,
        "missing_2021_exposure_damage_pilots_excluded": 0,
        "original_source_bytes_committed": False,
        "original_source_bytes_retained": False,
        "licensed_insurer_loss_amounts_included": False,
        "annual_rate_or_gross_net_ep_validated": False,
        "cat_model_admitted": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
