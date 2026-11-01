# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Frozen actual-source independent CRS and polygon validity aggregate.

This is *not* a publisher attribution of invalid features: counts reflect
pyshp's polygon-ring interpretation evaluated by GEOS/Shapely. Triangulate
against independent OGR/PostGIS interpretation before claiming source topology
defects or altering a single administrative polygon.
"""

HANZE_2024_INDEPENDENT_GEOMETRY_RECEIPT_V0 = {
    "schema_version": "hanze-2024-independent-crs-geos-v0",
    "publisher_record": "https://zenodo.org/records/23670886",
    "original_region_zip_sha256": "4e8a4afe47940fbe38600fa7090faf84da389e7bb65bc72c1b65244c837b1ff8",
    "proof_workflow": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41297190012",
    "libraries": {"pyproj": "3.7.2", "shapely": "2.1.2", "pyshp": "2.3.1"},
    "identified_epsg_by_proj": 3035,
    "epsg3035_projection_parameters_ellipsoid_axes_match": True,
    "strict_source_to_modern_epsg_crs_equals": False,
    "legacy_datum_vs_modern_datum_ensemble_semantics_unresolved": True,
    "source_feature_count": 1449,
    "interpreted_feature_types": {"polygon": 397, "multipolygon": 1052},
    "geos_valid_geometries": 555,
    "geos_invalid_geometries": 894,
    "invalid_reason_families": {"Ring Self-intersection": 894},
    "null_or_empty_geometries": 0,
    "nonpositive_or_nonfinite_areas": 0,
    "geometry_validation_engine": "GEOS through Shapely after pyshp __geo_interface__ conversion",
    "independent_gdal_ogr_geometry_interpretation_verified": False,
    "invalidity_is_conclusive_source_geometry_defect": False,
    "geos_flagged_original_feature_count_needs_independent_triage": 894,
    "geometry_auto_repair_or_topology_simplification_performed": False,
    "cross_feature_overlap_and_gap_validation_complete": False,
    "flood_event_footprints_validated": False,
    "any_insurer_exposure_or_insured_losses_created": False,
    "original_geometry_or_feature_id_reproduced": False,
    "underlying_geographic_commercial_rights_approved": False,
    "all_geometry_features_eligible_for_model_input": False,
    "model_input_admitted": False,
}
