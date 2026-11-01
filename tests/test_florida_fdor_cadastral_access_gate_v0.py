# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tests for withdrawn UF parcels versus exact current Florida FDOR source."""

from __future__ import annotations

import unittest

from research_runners.florida_fdor_cadastral_access_gate_v0 import (
    ParcelAccessError, canonical_aggregate_query, historical_access_gate,
    validate_current_state_source,
)

SOURCE = {
    "serviceItemId": "efa909d6b1c841d298b0a649e7f71cf2",
    "name": "CADASTRAL_DOR",
    "type": "Feature Layer",
    "geometryType": "esriGeometryPolygon",
    "objectIdField": "OBJECTID",
    "fields": ["OBJECTID", "CO_NO", "ASMNT_YR", "OWN_NAME"],
}


class FDORStateOfficialAccessResearchTests(unittest.TestCase):
    def test_exact_original_state_count_only_excludes_private_fields(self):
        self.assertEqual(canonical_aggregate_query(), {
            "where": "1=1", "returnCountOnly": "true",
            "returnGeometry": "false", "f": "json",
        })
        result = validate_current_state_source(SOURCE, {"count": 10_950_670})
        self.assertEqual(result["provider_live_statewide_parcel_feature_count"], 10_950_670)
        self.assertTrue(result["contains_sensitive_owner_address_fields"])
        for key in (
            "owner_address_fields_acquired_or_released",
            "historical_2017_2018_fgdl_bytes_accessible",
            "pre_2018_building_footprints_validated",
            "original_source_reuse_rights_checked",
            "different_2025_state_product_is_historical_2017_replacement",
            "model_input_admitted",
        ):
            self.assertFalse(result[key])
        for key in ("OWN_NAME", "OWN_ADDR1", "PARCEL_ID", "geometry", "features"):
            self.assertNotIn(key, result)

    def test_withdrawn_archive_explicitly_blocks_download_and_replacement(self):
        for sid in ("florida.fgdl.parcels-2017", "florida.fgdl.parcels-2018"):
            with self.subTest(source=sid):
                x = historical_access_gate(sid)
                self.assertEqual(x["withdrawal_date"], "2025-10-08")
                self.assertFalse(x["historic_dataset_download_currently_offered_by_fgdl"])
                self.assertFalse(x["historical_pre_event_building_input_admitted"])
                with self.assertRaisesRegex(ParcelAccessError, "removed historical"):
                    historical_access_gate(sid, request_historical_zip=True)
                with self.assertRaisesRegex(ParcelAccessError, "cannot replace"):
                    historical_access_gate(sid, substitute_state_current=True)

    def test_reject_source_name_identity_and_geometry_drift(self):
        for key, value in (
            ("serviceItemId", "other"), ("name", "2022"),
            ("type", "Table"), ("geometryType", "esriGeometryPoint"),
            ("objectIdField", "PARCEL_ID"),
            ("fields", ["OBJECTID", "CO_NO", "ASMNT_YR"]),
            ("fields", ["OBJECTID", "CO_NO", "ASMNT_YR", "OWN_NAME", "OWN_ADDR1"]),
            ("fields", ["OBJECTID", "CO_NO", "ASMNT_YR", ["OWN_NAME"]]),
        ):
            with self.subTest(key=key,value=str(value)):
                with self.assertRaises(ParcelAccessError):
                    validate_current_state_source(dict(SOURCE, **{key: value}), {"count": 10_950_670})

    def test_reject_provider_rows_and_invalid_or_fake_aggregate(self):
        for reply in (
            {"count": True}, {"count": 1.0}, {"count": -1}, {"count": "10950670"},
            {"count": 40_000_000}, {"count": 10_950_670, "features": []},
            {"features": []}, None,
        ):
            with self.subTest(reply=repr(reply)):
                with self.assertRaises(ParcelAccessError):
                    validate_current_state_source(SOURCE, reply)
        with self.assertRaises(ParcelAccessError):
            validate_current_state_source(dict(SOURCE, features=[]), {"count": 10_950_670})

    def test_unreviewed_archive_id_and_boolean_types_fail(self):
        for sid in ("random", None, "florida.fdor.statewide-cadastral-2025"):
            with self.assertRaises(ParcelAccessError):
                historical_access_gate(sid)
        for val in (1, "false", None):
            with self.subTest(switch=repr(val)):
                with self.assertRaises(ParcelAccessError):
                    historical_access_gate("florida.fgdl.parcels-2017", request_historical_zip=val)


if __name__ == "__main__":
    unittest.main()
