# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Profile only metadata and bounded field names of original Swiss crop hail HDF5.

No original grid coordinates, field counts or impact values are exported or retained.
A valid HDF5 schema does not imply scientific validity or CAT admission.
"""
from __future__ import annotations

import io
import json
from pathlib import Path, PurePosixPath
import tempfile
import zipfile
from urllib.request import build_opener

from research_runners.swiss_crop_hail_asset_preflight_v0 import Blocked, inspect_local
from research_runners.swiss_crop_hail_zenodo_original_acquire_v0 import (
    acquire_one, OriginalOnlyRedirect,
)

CROPS = ("barley", "field_crops", "grapevine", "maize", "rapeseed", "wheat")
RESOLUTIONS_KM = (1, 2, 4, 8)
SOURCE_ASSETS = ("radar_meshs_h5", "radar_poh_h5", "exposure_zip", "damage_zip")
MAX_H5_MEMBER_BYTES = 4_000_000


def expected_archive_names(role: str) -> set[str]:
    if role not in ("exposure", "damage"):
        raise Blocked("unknown crop archive role")
    stem = "exposure" if role == "exposure" else "hail_damage"
    return {f"{stem}_CH_{crop}_{resolution}km.h5"
            for crop in CROPS for resolution in RESOLUTIONS_KM}


def archive_member_index(members: list[str], role: str) -> dict[str, str]:
    expected = expected_archive_names(role)
    found = {}
    for name in members:
        if name.endswith("/"):
            continue
        parts = PurePosixPath(name)
        if (not name or name.startswith("/") or ".." in parts.parts
                or "\\" in name or ":" in name or parts.name not in expected
                or parts.name in found):
            raise Blocked("unrecognized, duplicate or unsafe original archive file")
        found[parts.name] = name
    if set(found) != expected:
        raise Blocked("incomplete 6 crops by 4 resolutions original archive")
    return found


def h5_metadata(file_handle) -> dict[str, object]:
    try:
        import h5py  # optional, installed only in dedicated source-profile CI
    except ImportError as exc:
        raise Blocked("h5py required in isolated structural source proof") from exc
    datasets = []
    groups = 0
    visited = 0
    try:
        with h5py.File(file_handle, "r") as h5:
            def visit(path, value):
                nonlocal visited, groups
                visited += 1
                if visited > 1000:
                    raise Blocked("HDF5 object count bound exceeded")
                if isinstance(value, h5py.Group):
                    groups += 1
                if isinstance(value, h5py.Dataset):
                    datasets.append({"path": path[:128], "shape": list(value.shape),
                                     "dtype": str(value.dtype)[:64]})
            h5.visititems(visit)
            attrs = sorted(str(n)[:80] for n in h5.attrs.keys())[:32]
            # A fixed maximum of 16 original *column-name labels* per table;
            # not crop area, coordinate, field-count or insurer-damage values.
            column_names = {}
            for label_path in (
                "exposures/block0_items", "exposures/block1_items",
                "exposures/block2_items",
            ):
                if label_path not in h5:
                    continue
                ds = h5[label_path]
                if not isinstance(ds, h5py.Dataset) or ds.ndim != 1 or len(ds) > 16:
                    raise Blocked("original source column labels exceed metadata bound")
                cleaned = []
                for label in ds[()]:
                    name = label.decode("ascii") if isinstance(label, bytes) else str(label)
                    if (not 1 <= len(name) <= 40 or not
                            all(letter.isascii() and (letter.isalnum() or letter == "_")
                                for letter in name)):
                        raise Blocked("invalid original source metadata column name")
                    cleaned.append(name)
                column_names[label_path] = cleaned
    except (OSError, RuntimeError, ValueError) as exc:
        raise Blocked("invalid original HDF5 structural metadata") from exc
    if not datasets:
        raise Blocked("HDF5 contains no datasets")
    return {
        "group_count": groups,
        "dataset_count": len(datasets),
        "root_attribute_names": attrs,
        "dataset_shape_dtype_sample": datasets[:20],
        "exposure_column_names_only": column_names,
        "no_numeric_grid_or_impact_values_read": True,
        "physical_units_validated": False,
        "crs_validated": False,
    }


def profile_zip(original_path: Path, role: str) -> dict[str, object]:
    sample_schemas = {}
    count = 0
    schema_sizes = []
    with zipfile.ZipFile(original_path) as zf:
        indexed = archive_member_index(zf.namelist(), role)
        for filename, zip_path in sorted(indexed.items()):
            member = zf.getinfo(zip_path)
            if not 0 < member.file_size <= MAX_H5_MEMBER_BYTES:
                raise Blocked("original HDF5 file outside safe size bound")
            with zf.open(member) as reader:
                contents = reader.read(MAX_H5_MEMBER_BYTES + 1)
            if len(contents) != member.file_size or not contents.startswith(b"\x89HDF\r\n\x1a\n"):
                raise Blocked("original archive member not valid HDF5")
            schema = h5_metadata(io.BytesIO(contents))
            schema_sizes.append(schema["dataset_count"])
            count += 1
            stem = "exposure" if role == "exposure" else "hail_damage"
            if filename in (f"{stem}_CH_wheat_1km.h5",
                            f"{stem}_CH_wheat_8km.h5",
                            f"{stem}_CH_grapevine_1km.h5"):
                sample_schemas[filename] = schema
    return {
        "crop_classes": list(CROPS),
        "resolutions_km": list(RESOLUTIONS_KM),
        "verified_hdf5_file_count": count,
        "hdf5_dataset_count_min": min(schema_sizes),
        "hdf5_dataset_count_max": max(schema_sizes),
        "selected_structure_samples": sample_schemas,
        "spatial_or_loss_semantics_validated": False,
    }


def main() -> int:
    opener = build_opener(OriginalOnlyRedirect())
    receipts, radar, crops = [], {}, {}
    with tempfile.TemporaryDirectory(prefix="oc-swiss-hail-h5-") as directory:
        for index, asset in enumerate(SOURCE_ASSETS):
            path = Path(directory) / f"original-{index}.bin"
            acquire_one(asset, path, opener)
            receipt = inspect_local(asset, path)
            receipts.append({"asset": asset, "sha256": receipt["sha256"],
                             "size": receipt["file_size"], "source_md5_matched": True})
            if asset in ("radar_meshs_h5", "radar_poh_h5"):
                radar[asset] = h5_metadata(path)
            else:
                crops[asset] = profile_zip(path, asset.replace("_zip", ""))
    print(json.dumps({
        "schema_version": "swiss-crop-hail-original-hdf5-schemas-v0",
        "original_file_receipts": receipts,
        "radar_hdf5": radar,
        "crop_archives": crops,
        "source_bytes_committed": False,
        "source_bytes_retained": False,
        "payload_values_exported": False,
        "model_admission": False,
        "annual_loss_exceedance_ready": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
