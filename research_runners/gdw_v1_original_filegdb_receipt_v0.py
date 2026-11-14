# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Frozen aggregate-only true GDW v1 original FileGDB evidence from GitHub CI.

Original ZIP, source GDW_ID values and source geometries are not in Git.
"""
from __future__ import annotations

GDW_V1_ORIGINAL_FILEGDB_RECEIPT_V0 = {
    "schema_version": "gdw-v1-native-original-filegdb-geos-receipt-v0",
    "source_id": "globaldamwatch.gdw.v1.0",
    "figshare_original_file_id": 47913742,
    "original_file_name": "GDW_v1_0_gdb.zip",
    "original_file_bytes": 57476758,
    "provider_md5": "410d1ed16312ac613975fd092c193c65",
    "original_sha256_observed": "5ebb1092e355f1833132be8a16340da7de979314d06aba00e57eb7412884f09f",
    "original_filegdb_member_count": 50,
    "source_workflow": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41892321883",
    "source_workflow_main_commit": "d42e1ba05eae5249fe1e797de9ea3b69ee3882e5",
    "source_execution_date_utc": "2026-11-04",
    "source_reader": "Fiona 1.10.1 OpenFileGDB / GEOS Shapely 2.1.2",
    "barrier_points": 41145,
    "reservoir_polygons": 35295,
    "point_only_barriers": 5850,
    "valid_reservoir_polygons": 35074,
    "invalid_reservoir_polygons": 221,
    "invalid_geos_reason_families": {"ring_self_intersection": 221},
    "paired_point_inside_valid_reservoir": 35074,
    "paired_point_on_valid_boundary": 0,
    "paired_point_outside_valid_reservoir": 0,
    "unassessable_due_to_invalid_polygon": 221,
    "original_bytes_published": False,
    "cross_format_per_id_compared": False,
    "source_features_or_ids_exported": False,
    "model_input_admitted": False,
}
