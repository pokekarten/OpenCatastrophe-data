# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only frozen original HANZE v2024 region polygon-code receipt.

Only counts and source fingerprints. No polygons, region names or source IDs.
"""

HANZE_NATIVE_REGION_GEOMETRY_RECEIPT_V0 = {
    "schema_version": "hanze-native-regions2024-zip-dbf-coverage-v0",
    "publisher_release": "https://zenodo.org/records/23670886",
    "source_archive_name": "Regions_v2024_simplified.zip",
    "source_archive_original_bytes": 2430309,
    "source_archive_publisher_md5": "410542984fda7e8898ccae3727b71cd8",
    "source_archive_observed_sha256": "4e8a4afe47940fbe38600fa7090faf84da389e7bb65bc72c1b65244c837b1ff8",
    "original_source_workflow": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41251815666",
    "zip_member_count": 6,
    "zip_extensions": {".cpg": 1, ".dbf": 1, ".prj": 1, ".qmd": 1, ".shp": 1, ".shx": 1},
    "uncompressed_member_bytes": 6890502,
    "shapefile_shape_type": "Polygon",
    "shapefile_declared_feature_count": 1449,
    "dbf_field_names": ["Code", "Name"],
    "dbf_distinct_valid_code_count": 1449,
    "dbf_repeated_code_surplus": 0,
    "s2_glossary_sha256": "4d5f26a28b742debf86598f1cfd99887930de1d0e45ca72a6c3cd2ea90d57edc",
    "s2_distinct_code_count": 1442,
    "in_both_original_s2_and_dbf_code_counts": 1382,
    "in_dbf_not_s2_code_count": 67,
    "in_s2_not_dbf_code_count": 60,
    "country_date_overlap_candidate_pair_count": 9,
    "candidate_original_hanze_region_lists_fully_present_in_dbf": 9,
    "original_hanze_region_token_occurrences_all_in_dbf": 150,
    "unmatched_original_candidate_region_tokens": 0,
    "the_seven_net_difference_is_not_duplicate_polygons": True,
    "spatial_crs_and_polygon_topology_verified": False,
    "any_observed_flood_inundation_footprint_mapped": False,
    "dfo_hanze_event_identity_verified": False,
    "economic_loss_or_insurer_tiv_joined": False,
    "geometry_and_third_party_licensing_review_complete": False,
    "original_polygon_geometry_or_code_rows_redistributed": False,
    "model_source_admitted": False,
}
