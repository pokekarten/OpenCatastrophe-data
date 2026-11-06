# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent real-source Swiss crop-hail 2/4/8km max-radar skill pilot.

Original published code tag 1.0 uses an EPSG:2056 grid with western/southern
extent 2255000/840000 metres and maximum of nonzero source radar intensities.
This independently implements max aggregation for a 2/4/8km exploratory
binary footprint analysis. Neither a copy of the third-party GPL algorithms
nor an assertion of paper numeric parity. Source originally downloaded only
to temporary runner storage, verified by pinned publisher MD5.
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
    CROPS, RESOLUTIONS_KM, archive_member_index,
)
from research_runners.swiss_crop_hail_event_alignment_v0 import open_member
from research_runners.swiss_crop_hail_original_1km_skill_pilot_v0 import (
    SOURCE_ASSETS, inspect_hazard, exposure_and_observed, run_skill,
)

# Version-1.0 original research utility.create_empty_grid: Swiss LV95 bounds.
MIN_X_M = 2255000
MIN_Y_M = 840000
MAX_X_M = 2964000
MAX_Y_M = 1479000
MAX_GRID_CENTER_OFFSET_M = 20.0


def grid_bins_projected(x, y, km: int):
    """Map Swiss projected point centroids to an exact LV95 fixed bin origin."""
    import numpy as np
    if type(km) is not int or km not in (2, 4, 8):
        raise Blocked("published coarser km resolutions restricted to 2/4/8")
    resolution = km * 1000
    ny = int(np.ceil((MAX_Y_M - MIN_Y_M) / resolution)) + 1
    nx = int(np.ceil((MAX_X_M - MIN_X_M) / resolution)) + 1
    ix = np.floor((x - MIN_X_M) / resolution).astype("int64")
    iy = np.floor((y - MIN_Y_M) / resolution).astype("int64")
    if (np.any(ix < 0) or np.any(iy < 0) or
            np.any(ix >= nx) or np.any(iy >= ny)):
        raise Blocked("source geographies fall outside published Swiss grid support")
    return ix * ny + iy, ix, iy, nx * ny


def aggregate_hazard_fixed_swiss_grid(original, km: int):
    """Return max hail intensity for each LV95 square, per original event."""
    import numpy as np
    from scipy.sparse import csr_matrix
    from pyproj import Transformer
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    x, y = transformer.transform(original["lon"], original["lat"])
    source_bins, _, _, n_bins = grid_bins_projected(x, y, km)
    matrix = original["csr"]
    if matrix.shape != (12, len(source_bins)):
        raise Blocked("original radar event and geography array mismatch")
    out = np.zeros((12, n_bins), dtype="float32")
    for ev in range(12):
        left, right = matrix.indptr[ev], matrix.indptr[ev+1]
        np.maximum.at(out[ev], source_bins[matrix.indices[left:right]],
                      matrix.data[left:right])
    return {
        "variable": original["variable"],
        "dates": original["dates"],
        "csr": csr_matrix(out),
        "grid_resolution_km": km,
        "aggregate_operation": "max",
        "n_grid_bins": n_bins,
        "radar_nonzero_original": original["published_nonzero_hazard_values"],
    }


def map_aggregated_crop_coords(positions, km: int):
    import numpy as np
    from pyproj import Transformer
    if np.asarray(positions).ndim != 2 or np.asarray(positions).shape[1] != 2:
        raise Blocked("crop coordinate layout incompatible with Swiss grid")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    x, y = transformer.transform(positions[:,1], positions[:,0])
    unique, ix, iy, bins = grid_bins_projected(x, y, km)
    unit = km*1000
    cx = MIN_X_M + (ix+0.5)*unit
    cy = MIN_Y_M + (iy+0.5)*unit
    errors = np.hypot(cx-x, cy-y)
    max_distance = float(np.max(errors))
    if (not np.isfinite(errors).all() or
            max_distance > MAX_GRID_CENTER_OFFSET_M or
            len(np.unique(unique)) != len(unique)):
        raise Blocked(
            f"crop HDF5 {km}km source centroids do not map one-to-one "
            f"to original LV95 max-aggregation grid (max_offset_m={max_distance:.3f})"
        )
    return unique, bins, max_distance


def main() -> int:
    import h5py
    import numpy as np
    opener = build_opener(OriginalOnlyRedirect())
    with tempfile.TemporaryDirectory(prefix="oc-swiss-crop-hail-coarse-skill-") as temp:
        paths = {}
        for i, asset in enumerate(SOURCE_ASSETS):
            path = Path(temp) / f"original-{i}.bin"
            acquire_one(asset, path, opener)
            inspect_local(asset, path)
            paths[asset] = path
        with (h5py.File(paths["radar_meshs_h5"], "r") as mesh,
              h5py.File(paths["radar_poh_h5"], "r") as poh,
              zipfile.ZipFile(paths["exposure_zip"]) as expzip,
              zipfile.ZipFile(paths["damage_zip"]) as dmzip):
            meshs = inspect_hazard(mesh, "MESHS")
            poh_haz = inspect_hazard(poh, "POH")
            if (meshs["dates"] != poh_haz["dates"] or
                    not np.allclose(meshs["lat"], poh_haz["lat"], atol=1e-8, rtol=0) or
                    not np.allclose(meshs["lon"], poh_haz["lon"], atol=1e-8, rtol=0)):
                raise Blocked("published MESHS and POH 1km source grids differ")
            exnames = archive_member_index(expzip.namelist(), "exposure")
            dmnames = archive_member_index(dmzip.namelist(), "damage")
            rows = []
            geometry = []
            for km in (2, 4, 8):
                hazards = (
                    aggregate_hazard_fixed_swiss_grid(meshs, km),
                    aggregate_hazard_fixed_swiss_grid(poh_haz, km),
                )
                for crop in CROPS:
                    ename = f"exposure_CH_{crop}_{km}km.h5"
                    dname = f"hail_damage_CH_{crop}_{km}km.h5"
                    with open_member(expzip, exnames[ename]) as exposure:
                        with open_member(dmnames and dmzip, dmnames[dname]) as damage:
                            coords, observed, missing_positives = exposure_and_observed(
                                exposure, damage, meshs["dates"], allow_unmatched=True
                            )
                    selection, n_bins, offset = map_aggregated_crop_coords(coords, km)
                    if n_bins != hazards[0]["n_grid_bins"]:
                        raise Blocked("cropped aggregate grid support bins mismatched")
                    geometry.append({
                        "crop": crop,
                        "resolution_km": km,
                        "max_crop_center_offset_from_original_grid_m": round(offset, 3),
                        "excluded_out_of_2021_exposure_positive_event_cells": missing_positives,
                    })
                    for hazard in hazards:
                        score = run_skill(crop, hazard, selection, observed)
                        score["grid_resolution_km"] = km
                        score["omitted_positive_grid_event_observations"] = missing_positives
                        rows.append(score)
    print(json.dumps({
        "schema_version": "swiss-crop-hail-real-2-4-8km-max-radar-pilot-v0",
        "source_hazard_events": 12,
        "original_grid_crs": "EPSG:2056",
        "published_grid_origin_east_m": MIN_X_M,
        "published_grid_origin_north_m": MIN_Y_M,
        "aggregation": "max",
        "real_hdf5_crop_geometry_profiles": geometry,
        "source_binary_skill_results": rows,
        "published_reference_hss_parity_established": False,
        "out_of_exposure_positive_counts_are_not_unique_claims": True,
        "all_original_input_bytes_deleted_after_run": True,
        "unreleased_insurer_claims_included": False,
        "annual_event_frequency_calibrated": False,
        "gross_net_ep_admitted": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
