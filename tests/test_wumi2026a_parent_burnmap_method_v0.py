# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No original event data: fictional 28-column WUMI rows only."""
import io
import unittest
from zipfile import ZipFile

from research_runners import wumi2026a_parent_burnmap_method_v0 as gate
from research_runners import wumi2026a_dryad_original_asset_receipt_v0 as receipt

FIELDS = (
    "fireid","dataset","agency","name","year","month","day",
    "lat","lon","lat_ll","lon_ll","lat_ur","lon_ur",
    "poly_area_ha","burn_area_ha","mtbs_name","mtbs_id","irwinid",
    "fod_id","fpa_id","object_id_wfaip","object_id_fpafod",
    "object_id_wfigs","object_id_calfire","object_id_usgs",
    "object_id_iafph","cause_human_or_natural","cause_specific",
)


def event(i, *, primary="fpa_fod", linked=None, burn="200"):
    fields = {name: "N/A" for name in FIELDS}
    fields.update({
        "fireid": f"20240708_{330000+i}_1110000",
        "dataset": primary, "year": "2024", "month": "7", "day": "8",
        "poly_area_ha": "350", "burn_area_ha": burn,
    })
    for key, value in (linked or {}).items():
        fields[key] = value
    return ",".join(fields[x] for x in FIELDS)


def native(*rows, header=FIELDS):
    return (",".join(header) + "\n" + "\n".join(rows) + "\n").encode()


class WumiParentMethodTests(unittest.TestCase):
    def test_author_selection_priority_all_seven_original_branches(self):
        b = native(
            event(1, primary="mtbs", linked={"mtbs_id": "M-1", "object_id_wfigs": "99"}),
            event(2, primary="calfire", linked={"object_id_calfire": "22"}),
            event(3, primary="wfigs", linked={"object_id_wfigs": "33"}),
            event(4, linked={"object_id_wfigs": "44", "object_id_usgs": "55",
                             "object_id_iafph": "66"}),
            event(5, linked={"object_id_usgs": "55", "object_id_iafph": "66"}),
            event(6, linked={"object_id_iafph": "66"}),
            event(7),
        )
        result = gate.summarize_publisher_parent_burnmap_methods(b)
        self.assertEqual(result["fire_events_in_parent_view"], 7)
        self.assertEqual(result["evidence_method_tiers"][gate.MTBS], 1)
        self.assertEqual(result["evidence_method_tiers"][gate.BOUNDARY], 5)
        self.assertEqual(result["evidence_method_tiers"][gate.CIRCLE], 1)
        self.assertEqual(result["publisher_burn_map_methods"]["wfigs"], 2)
        self.assertEqual(result["publisher_method_by_year"]["2024"][gate.CIRCLE], 1)
        self.assertEqual(result["state"], "PUBLISHER_METHOD_COUNTS_ONLY_NO_ADMISSION")
        self.assertFalse(result["event_frequency_hazard_footprint_and_insured_loss_admitted"])
        self.assertNotIn("20240708_330001", str(result))

    def test_primary_method_not_overridden_by_linked_source(self):
        data = native(event(1, primary="calfire", linked={
            "object_id_calfire": "1", "object_id_wfigs": "222",
        }))
        out = gate.summarize_publisher_parent_burnmap_methods(data)
        self.assertEqual(out["publisher_burn_map_methods"], {"calfire": 1})

    def test_missing_primary_object_id_needs_review(self):
        data = native(event(1, primary="mtbs"))
        out = gate.summarize_publisher_parent_burnmap_methods(data)
        self.assertEqual(out["state"], "REVIEW_PUBLISHER_LINK_IDENTITIES")
        self.assertEqual(out["missing_publisher_source_identity_by_method"]["mtbs"], 1)

    def test_original_circular_method_is_not_observed_geometry(self):
        out = gate.summarize_publisher_parent_burnmap_methods(native(event(1)))
        self.assertEqual(out["evidence_method_tiers"][gate.CIRCLE], 1)
        self.assertTrue(out["hypothetical_circle_is_not_observed_wildfire_perimeter"])
        self.assertFalse(out["source_rights_and_original_burn_maps_reviewed"])

    def test_header_missing_source_column_blocks(self):
        header = tuple(x for x in FIELDS if x != "object_id_usgs")
        values = {name: "N/A" for name in FIELDS}
        values.update(fireid="20240708_330001_1110000", dataset="fpa_fod",
                      year="2024", month="7", day="8", poly_area_ha="100",
                      burn_area_ha="80")
        with self.assertRaisesRegex(gate.FootprintMethodBlocked, "columns missing"):
            gate.summarize_publisher_parent_burnmap_methods(
                native(",".join(values[k] for k in header), header=header)
            )

    def test_unknown_source_blocks_but_not_silent_circle(self):
        with self.assertRaisesRegex(gate.FootprintMethodBlocked, "unknown primary"):
            gate.summarize_publisher_parent_burnmap_methods(
                native(event(1, primary="unknown-provider"))
            )

    def test_id_duplicates_malformed_and_invalid_area_block_via_parent_gate(self):
        with self.assertRaises(Exception):
            gate.summarize_publisher_parent_burnmap_methods(native(event(1), event(1)))
        with self.assertRaises(Exception):
            gate.summarize_publisher_parent_burnmap_methods(native(event(1, burn="-1")))
        with self.assertRaises(Exception):
            gate.summarize_publisher_parent_burnmap_methods(native(event(1) + ",bad"))

    def test_source_zip_bytes_must_match_exact_publisher_digest(self):
        stream = io.BytesIO()
        with ZipFile(stream, "w") as f:
            f.writestr(gate.NO_NAME, native(event(1)))
        with self.assertRaisesRegex(receipt.DryadReceiptBlocked, "byte count"):
            gate.inspect_exact_original_parent_map_methods_zip(stream.getvalue())

    def test_missing_reported_burn_area_indicated_not_classified_as_observed(self):
        out = gate.summarize_publisher_parent_burnmap_methods(
            native(event(1, primary="wfigs", linked={"object_id_wfigs": "22"}, burn="N/A"))
        )
        self.assertEqual(out["missing_publisher_burn_area_by_tier"][gate.BOUNDARY], 1)
        self.assertTrue(out["agency_perimeter_does_not_prove_observed_burned_pixels"])
