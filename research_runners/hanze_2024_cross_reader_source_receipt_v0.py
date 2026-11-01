# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Frozen real-source per-feature GDAL vs pyshp validity agreement metadata."""

HANZE_GDAL_PYSHP_ORIGINAL_CROSSCHECK_V0 = {
    "schema_version": "hanze-original-v2024-gdal-pyshp-geos-crosscheck-v0",
    "publisher_url": "https://zenodo.org/records/23670886",
    "source_zip_original_sha256": "4e8a4afe47940fbe38600fa7090faf84da389e7bb65bc72c1b65244c837b1ff8",
    "source_workflow_run": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41297741284",
    "fiona_version": "1.10.1",
    "gdal_version": "3.9.2",
    "shapely_geos_version": "2.1.2",
    "pyshp_version": "2.3.1",
    "original_geometries": 1449,
    "both_readers_valid": 555,
    "both_readers_flagged_invalid": 894,
    "gdal_valid_pyshp_invalid": 0,
    "gdal_invalid_pyshp_valid": 0,
    "geometric_type_disagreements": 0,
    "dbf_code_order_consistent_without_export": True,
    "identified_invalid_family_counts": {"Ring Self-intersection": 894},
    "distinct_regions_are_not_disaster_footprints": True,
    "same_geos_topological_validity_algorithm_both_readers": True,
    "third_independent_topology_engine_or_manual_region_review_completed": False,
    "source_originals_automatically_fixed": False,
    "original_geometries_or_region_ids_exported": False,
    "historical_hazard_extent_or_insured_loss_proven": False,
    "commercial_geometry_use_rights_reviewed": False,
    "all_source_regions_model_eligible": False,
    "model_data_admitted": False,
}
