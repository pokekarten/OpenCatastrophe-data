# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Frozen aggregate-only GDW v1.0 original archive verification evidence.

This receipt was recorded from the complete, successful main-branch GitHub
Action run, not inferred from documentation or synthetic fixtures. Provider
record coordinates, IDs and archive bytes are not stored in this file.
"""
from __future__ import annotations

GDW_V1_ORIGINAL_SHAPEFILE_EVIDENCE_V0 = {
    "schema_version": "gdw-v1-original-shapefile-byte-structure-receipt-v0",
    "source_id": "globaldamwatch.gdw.v1.0",
    "exact_figshare_article_version": "https://api.figshare.com/v2/articles/25988293/versions/1",
    "original_file_id": 47913754,
    "original_file_name": "GDW_v1_0_shp.zip",
    "original_file_bytes": 69745749,
    "provider_declared_md5": "5064cf2315ef6159d9133b03596e761a",
    "independently_computed_from_original_sha256": "2fe0b367ed3fcfb299160cd9652b16a8a19338951026ee2ac91edfebf1f3b7ae",
    "original_archive_member_count": 16,
    "barrier_point_records": 41145,
    "reservoir_polygon_records": 35295,
    "point_only_barriers": 5850,
    "declared_geographic_wgs84": True,
    "zip_crc_checked": True,
    "shp_shx_dbf_row_counts_agree": True,
    "dbf_gdw_id_uniqueness_and_subset_checked": True,
    "coordinate_bounds_and_polygon_ring_closure_checked": True,
    "source_execution_run": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41885048219",
    "source_execution_commit": "2013f4f0b08750c4e43044a64625209d8a8eb1ad",
    "source_execution_date_utc": "2026-11-04",
    "caller_supplied_sha256_matches": False,
    "geos_polygon_topology_validated": False,
    "per_id_point_in_polygon_verified": False,
    "missing_value_sentinels_applied": False,
    "original_archive_bytes_published": False,
    "model_source_admitted": False,
}
