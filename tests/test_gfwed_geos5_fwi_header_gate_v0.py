# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent synthetic adversarial FWI header checks, no NASA data bytes."""
import copy
import unittest

from research_runners.gfwed_geos5_fwi_header_gate_v0 import (
    GFWEDScienceHeaderError, screen_gfwed_geos5_fwi_header_receipt,
)
from research_runners.gfwed_geos5_netcdf_preflight_v0 import SOURCE_ID, SOURCE_NAME, SOURCE_URL


def synthetic_receipt():
    dims = {"lat": 3, "lon": 4, "time": 1}
    def var(name, axes, units):
        return {"name": name, "dimensions": axes, "shape": [dims[a] for a in axes],
                "dtype_label_unverified": "float32", "units": units,
                "standard_name": "", "long_name": ""}
    return {
        "schema_version": "gfwed-geos5-v2-original-receipt-v0",
        "header_inspection_performed": True,
        "original_byte_evidence": {
            "source_id": SOURCE_ID,
            "exact_filename": SOURCE_NAME,
            "original_source_url_unfetched_by_tool": SOURCE_URL,
            "observed_sha256": "a" * 64,
            "verified_against_operator_supplied_sha256": True,
            "publisher_checksum_independently_verified": False,
            "external_pin_proven_independent_of_file_by_tool": False,
        },
        "netcdf_header_inventory": {
            "dimensions": dims,
            "variables": [var("lat", ["lat"], "degrees_north"),
                          var("lon", ["lon"], "degrees_east"),
                          var("FWI", ["time", "lat", "lon"], "1")],
            "inventory_only": True, "netcdf_values_loaded": False,
        },
        "provider_rights_cleared": False,
        "commercial_use_approved": False,
        "scientific_fitness_approved": False,
        "model_source_admitted": False,
        "source_downloaded_by_this_tool": False,
        "data_synced_to_neon": False,
    }


class GFWEDFWIHeaderGateTests(unittest.TestCase):
    def test_structural_index_and_fail_closed_claim(self):
        out = screen_gfwed_geos5_fwi_header_receipt(synthetic_receipt())
        self.assertEqual(out["fwi_spatial_shape"], [3, 4])
        self.assertEqual(out["metadata_fwi_grid_preflight"], "passed_offline_only")
        for key in ("scientific_model_input_approved", "fire_ignition_or_footprint_observed",
                    "data_ranges_checked", "coordinate_values_checked", "in_file_date_checked"):
            self.assertFalse(out[key])

    def test_2d_no_time_variable_is_allowed_without_in_file_date_claim(self):
        r = synthetic_receipt()
        r["netcdf_header_inventory"]["variables"][-1]["dimensions"] = ["lat", "lon"]
        r["netcdf_header_inventory"]["variables"][-1]["shape"] = [3, 4]
        self.assertFalse(screen_gfwed_geos5_fwi_header_receipt(r)["in_file_date_checked"])

    def test_rejects_unsafe_metadata_and_false_science_claims(self):
        bads = []
        def bad(fn):
            r = synthetic_receipt(); fn(r); bads.append(r)
        bad(lambda r: r.update(schema_version="wrong"))
        bad(lambda r: r.update(header_inspection_performed=False))
        bad(lambda r: r.update(provider_rights_cleared=True))
        bad(lambda r: r.update(scientific_fitness_approved=True))
        bad(lambda r: r.update(model_source_admitted=True))
        bad(lambda r: r["original_byte_evidence"].update(source_id="wrong"))
        bad(lambda r: r["original_byte_evidence"].update(exact_filename="wrong.nc"))
        bad(lambda r: r["original_byte_evidence"].update(observed_sha256="bad"))
        bad(lambda r: r["original_byte_evidence"].update(publisher_checksum_independently_verified=True))
        bad(lambda r: r["netcdf_header_inventory"].update(inventory_only=False))
        bad(lambda r: r["netcdf_header_inventory"].update(netcdf_values_loaded=True))
        bad(lambda r: r["netcdf_header_inventory"]["dimensions"].update(time=2))
        bad(lambda r: r["netcdf_header_inventory"]["dimensions"].update(lat=1))
        bad(lambda r: r["netcdf_header_inventory"]["dimensions"].update(latitude=5))
        bad(lambda r: r["netcdf_header_inventory"]["variables"].pop(0))
        bad(lambda r: r["netcdf_header_inventory"]["variables"].pop())
        bad(lambda r: r["netcdf_header_inventory"]["variables"][-1].update(units="m/s"))
        bad(lambda r: r["netcdf_header_inventory"]["variables"][-1].update(dtype_label_unverified="object"))
        bad(lambda r: r["netcdf_header_inventory"]["variables"][-1].update(dimensions=["lat", "time", "height"]))
        bad(lambda r: r["netcdf_header_inventory"]["variables"][-1].update(shape=[2, 3, 4]))
        bad(lambda r: r["netcdf_header_inventory"]["variables"][0].update(units="degrees_east"))
        bad(lambda r: r["netcdf_header_inventory"]["variables"][1].update(dtype_label_unverified="int32"))
        bad(lambda r: r["netcdf_header_inventory"]["variables"].append(copy.deepcopy(r["netcdf_header_inventory"]["variables"][-1])))
        for case in bads:
            with self.subTest(case=case):
                with self.assertRaises(GFWEDScienceHeaderError):
                    screen_gfwed_geos5_fwi_header_receipt(case)

if __name__ == "__main__":
    unittest.main()
