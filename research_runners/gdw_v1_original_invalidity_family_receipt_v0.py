# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Frozen real original-source GDW v1.0 invalid GEOS reason-family receipt.

No source WKT, original record IDs, coordinates or provider bytes are stored.
This is a diagnostic only; no automatic geometry repair/model admission.
"""
from __future__ import annotations

GDW_V1_ORIGINAL_INVALIDITY_REASON_RECEIPT_V0 = {
    "schema_version": "gdw-v1-native-original-geos-invalidity-reason-family-v0",
    "source_id": "globaldamwatch.gdw.v1.0",
    "original_file_sha256": "2fe0b367ed3fcfb299160cd9652b16a8a19338951026ee2ac91edfebf1f3b7ae",
    "source_workflow_run": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41887835566",
    "source_main_commit": "c464b9a9088e64facb11383bd317b57c7d2eefcf",
    "source_audit_date_utc": "2026-11-04",
    "source_format": "GDW_v1_0_shp.zip",
    "original_barrier_points": 41145,
    "original_reservoir_polygons": 35295,
    "geos_valid_original_reservoir_polygons": 35074,
    "geos_invalid_original_reservoir_polygons": 221,
    "invalid_geos_reason_families": {"ring_self_intersection": 221},
    "unparseable_original_geometries": 0,
    "assessable_paired_point_inside": 35074,
    "assessable_paired_point_boundary": 0,
    "assessable_paired_point_outside": 0,
    "invalid_pair_geometry_containment_not_assessable": 221,
    "original_geodatabase_alternate_format_crosschecked": False,
    "independent_topology_engine_crosschecked": False,
    "invalid_geometries_automatically_repaired": False,
    "source_features_or_coordinates_exported": False,
    "model_input_admitted": False,
}
