# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed science *metadata* gate on an existing NASA GFWED GEOS-5 receipt.

This function reads no source bytes, array values, URLs or ZIP/NetCDF files.
It only challenges the explicitly non-admitted `inventory_header` result from
`gfwed_geos5_netcdf_preflight_v0.py`. Passing never proves real data fitness.
Official context: https://data.giss.nasa.gov/impacts/gfwed/
"""
from __future__ import annotations

import re
from collections.abc import Mapping

from research_runners.gfwed_geos5_netcdf_preflight_v0 import SOURCE_ID, SOURCE_NAME, SOURCE_URL

SHA256 = re.compile(r"[a-f0-9]{64}\Z")
ALLOWED_LAT_UNITS = frozenset({"degrees_north", "degree_north", "degrees_n", "degree_n", "degrees north"})
ALLOWED_LON_UNITS = frozenset({"degrees_east", "degree_east", "degrees_e", "degree_e", "degrees east"})
ALLOWED_FWI_UNITS = frozenset({"1", "unitless", "dimensionless", "none", "no units"})
ACCEPTABLE_FLOAT_DTYPES = frozenset({"float32", "float64", "<f4", ">f4", "<f8", ">f8"})


class GFWEDScienceHeaderError(ValueError):
    """Insufficient metadata to establish an even structurally plausible FWI grid."""


def _fail(message: str) -> None:
    raise GFWEDScienceHeaderError(message)


def _units(variable: dict) -> str:
    raw = variable.get("units")
    if not isinstance(raw, str):
        _fail("NetCDF units missing or non-text")
    return raw.strip().lower()


def _dtype(variable: dict) -> str:
    raw = variable.get("dtype_label_unverified")
    if not isinstance(raw, str) or raw.strip().lower() not in ACCEPTABLE_FLOAT_DTYPES:
        _fail("FWI or coordinate storage type not an explicitly supported float")
    return raw.strip().lower()


def _spatial_dim(dimensions: dict, candidates: set[str], label: str) -> str:
    matches = [key for key in dimensions if key.lower() in candidates]
    if len(matches) != 1:
        _fail(f"requires exactly one {label} spatial axis")
    return matches[0]


def screen_gfwed_geos5_fwi_header_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    """Only an adversarial challenge of a prior local NetCDF header inventory.

    No source acquisition, grid contents, weather input provenance, wildfire
    occurrence or commercial insurance-model use is verified by this function.
    """
    if not isinstance(receipt, Mapping) or receipt.get("schema_version") != "gfwed-geos5-v2-original-receipt-v0":
        _fail("wrong original-receipt schema")
    if receipt.get("header_inspection_performed") is not True:
        _fail("NetCDF header inventory was not performed")
    if any(receipt.get(flag) is not False for flag in (
        "provider_rights_cleared", "commercial_use_approved", "scientific_fitness_approved",
        "model_source_admitted", "source_downloaded_by_this_tool", "data_synced_to_neon"
    )):
        _fail("unexpected source/admission evidence flags")
    source = receipt.get("original_byte_evidence")
    if not isinstance(source, dict):
        _fail("missing prior exact-byte descriptor")
    if (source.get("source_id") != SOURCE_ID or source.get("exact_filename") != SOURCE_NAME or
            source.get("original_source_url_unfetched_by_tool") != SOURCE_URL or
            source.get("verified_against_operator_supplied_sha256") is not True or
            source.get("publisher_checksum_independently_verified") is not False or
            source.get("external_pin_proven_independent_of_file_by_tool") is not False or
            not isinstance(source.get("observed_sha256"), str) or
            not SHA256.fullmatch(source["observed_sha256"])):
        _fail("source identity or untrusted original-byte evidence")
    inventory = receipt.get("netcdf_header_inventory")
    if not isinstance(inventory, dict) or inventory.get("inventory_only") is not True or inventory.get("netcdf_values_loaded") is not False:
        _fail("expected metadata-only NetCDF inventory")
    dimensions, variables = inventory.get("dimensions"), inventory.get("variables")
    if (not isinstance(dimensions, dict) or not isinstance(variables, list) or
            len(variables) > 160 or len(dimensions) > 24 or
            any(not isinstance(k, str) or not isinstance(v, int) or isinstance(v, bool) or v < 1 for k, v in dimensions.items())):
        _fail("invalid dimensions or variables")
    lat_dim = _spatial_dim(dimensions, {"lat", "latitude"}, "latitude")
    lon_dim = _spatial_dim(dimensions, {"lon", "longitude"}, "longitude")
    if dimensions[lat_dim] < 2 or dimensions[lon_dim] < 2:
        _fail("FWI grid cannot be degenerate")
    if not all(isinstance(var, dict) and isinstance(var.get("name"), str) for var in variables):
        _fail("bad NetCDF variable descriptors")
    if len({var["name"] for var in variables}) != len(variables):
        _fail("duplicate variable names")
    by_name = {var["name"]: var for var in variables}
    for axis, allowed_units in ((lat_dim, ALLOWED_LAT_UNITS), (lon_dim, ALLOWED_LON_UNITS)):
        v = by_name.get(axis)
        if v is None or v.get("dimensions") != [axis] or v.get("shape") != [dimensions[axis]]:
            _fail(f"missing or malformed coordinate variable {axis}")
        _dtype(v)
        if _units(v) not in allowed_units:
            _fail(f"invalid units for {axis} coordinate")
    fwis = [v for v in variables if v["name"].lower() == "fwi"]
    if len(fwis) != 1:
        _fail("requires exactly one FWI index variable")
    fwi = fwis[0]
    axes = fwi.get("dimensions")
    shape = fwi.get("shape")
    if (not isinstance(axes, list) or not isinstance(shape, list) or len(axes) not in (2, 3) or
            any(not isinstance(ax, str) for ax in axes) or
            len(axes) != len(set(axes)) or any(ax not in dimensions for ax in axes) or
            set(axes) - {lat_dim, lon_dim, "time"} or
            lat_dim not in axes or lon_dim not in axes or shape != [dimensions[ax] for ax in axes]):
        _fail("FWI dimensions incompatible with latitude/longitude grid")
    if "time" in axes and dimensions["time"] != 1:
        _fail("one daily file cannot silently represent multiple time steps")
    _dtype(fwi)
    if _units(fwi) not in ALLOWED_FWI_UNITS:
        _fail("FWI must be dimensionless; reject weather-variable units")
    return {
        "source_id": SOURCE_ID,
        "product_file": SOURCE_NAME,
        "original_byte_sha256": source["observed_sha256"],
        "metadata_fwi_grid_preflight": "passed_offline_only",
        "fwi_variable": fwi["name"],
        "fwi_spatial_shape": [dimensions[lat_dim], dimensions[lon_dim]],
        "daily_time_count_from_header": dimensions.get("time"),
        "coordinate_values_checked": False,
        "missing_values_and_scale_factors_checked": False,
        "in_file_date_checked": False,
        "data_ranges_checked": False,
        "full_provider_file_originality_verified": False,
        "source_rights_and_commercial_reuse_verified": False,
        "fire_ignition_or_footprint_observed": False,
        "scientific_model_input_approved": False,
        "neon_storage": "storage_not_verified",
    }
