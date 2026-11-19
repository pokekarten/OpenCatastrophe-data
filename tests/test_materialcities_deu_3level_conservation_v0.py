# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline tests for original-byte MaterialCities German level conservation."""
from __future__ import annotations

import csv
import hashlib
import io
import unittest
import zipfile

from research_runners.materialcities_adm2_gfa_preflight_v0 import (
    GFA_FIELDS, MaterialCitiesPreflightError,
)
from research_runners.materialcities_deu_3level_conservation_v0 import (
    ARCHIVE_MEMBERS, inspect_deu_three_levels,
)


def _base_rows() -> dict:
    def row(country, state="", district="", nr=0, rs=0):
        return {"GID_0": country, "GID_1": state, "GID_2": district,
                "GFA_NR_C": str(nr), "GFA_RS_M": str(rs)}
    return {
        "ADM0": [row("DEU", nr=30, rs=10)],
        "ADM1": [row("DEU", "DEU.1_1", nr=20, rs=10),
                 row("DEU", "DEU.2_1", nr=10)],
        "ADM2": [row("DEU", "DEU.1_1", "DEU.1.1_1", nr=15, rs=10),
                 row("DEU", "DEU.1_1", "DEU.1.2_1", nr=5),
                 row("DEU", "DEU.2_1", "DEU.2.1_1", nr=10)],
    }


def _build(rows=None, *, omit=None, drop_field=None):
    items = rows if rows is not None else _base_rows()
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for level, path in ARCHIVE_MEMBERS.items():
            if level == omit:
                continue
            fields = ["GID_0", *([] if level == "ADM0" else ["GID_1"]),
                      *([] if level != "ADM2" else ["GID_2"]), *GFA_FIELDS]
            if level == drop_field:
                fields.remove("GFA_NR_C")
            f = io.StringIO(newline="")
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for source in items[level]:
                writer.writerow({key: source.get(key, "0") for key in fields})
            archive.writestr(path, f.getvalue())
    return target.getvalue()


def _inspect(blob, **kwargs):
    return inspect_deu_three_levels(blob, strict_original_counts=False,
                                   expected_md5=hashlib.md5(blob).hexdigest(),
                                   expected_sha256=hashlib.sha256(blob).hexdigest(),
                                   **kwargs)


class GermanyMaterialCitiesLevelGateTests(unittest.TestCase):
    def test_15_components_conserved_without_insurance_claim(self):
        receipt = _inspect(_build())
        self.assertEqual(receipt["source_native_counts"],
                         {"ADM0": 1, "ADM1": 2, "ADM2": 3})
        self.assertEqual(receipt["distinct_adm1_parent_keys"], 2)
        self.assertEqual(receipt["distinct_adm2_source_keys"], 3)
        self.assertEqual(receipt["max_adm1_to_children_component_delta_m2"], 0)
        self.assertTrue(receipt["all_15_components_conserved_across_levels"])
        self.assertFalse(receipt["gadm_adm2_to_ags_2022_crosswalk_proven"])
        for key in ("independent_building_stock_validation", "source_rights_admitted",
                    "insurer_sites_geolocated", "insurer_tiv_inferred",
                    "cat_model_input_approved"):
            self.assertFalse(receipt[key])
        self.assertTrue(receipt["research_only"])

    def test_real_source_counts_required_by_default(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "1/16/402"):
            inspect_deu_three_levels(
                _build(), expected_md5=hashlib.md5(_build()).hexdigest(),
                expected_sha256=hashlib.sha256(_build()).hexdigest())

    def test_default_original_digest_must_not_accept_fixture(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "digest mismatch"):
            inspect_deu_three_levels(_build())

    def test_different_national_component_blocks(self):
        data = _base_rows()
        data["ADM0"][0]["GFA_NR_C"] = "32"
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "national"):
            _inspect(_build(data))

    def test_state_component_disagreement_blocks(self):
        data = _base_rows()
        data["ADM1"][0]["GFA_RS_M"] = "11"
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "GADM state"):
            _inspect(_build(data))

    def test_duplicate_state_identity_blocks(self):
        data = _base_rows()
        data["ADM1"][1]["GID_1"] = "DEU.1_1"
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "ambiguous GADM ADM1"):
            _inspect(_build(data))

    def test_orphan_adm2_parent_state_blocks(self):
        data = _base_rows()
        data["ADM2"][2]["GID_1"] = "DEU.3_1"
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "ADM2 identity"):
            _inspect(_build(data))

    def test_district_id_must_match_parent_state(self):
        data = _base_rows()
        data["ADM2"][2]["GID_2"] = "DEU.1.90_1"
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "ADM2 identity"):
            _inspect(_build(data))

    def test_duplicate_district_source_blocks(self):
        data = _base_rows()
        data["ADM2"][2]["GID_2"] = "DEU.1.2_1"
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "not unique"):
            _inspect(_build(data))

    def test_missing_adm1_member_blocks(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "missing original ADM1"):
            _inspect(_build(omit="ADM1"))

    def test_missing_gfa_field_blocks(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "schema"):
            _inspect(_build(drop_field="ADM1"))

    def test_nonfinite_component_blocks(self):
        for bad in ("-1", "NaN", "Infinity", "oops"):
            with self.subTest(bad=bad):
                data = _base_rows()
                data["ADM2"][0]["GFA_NR_C"] = bad
                with self.assertRaises(MaterialCitiesPreflightError):
                    _inspect(_build(data))

    def test_one_state_without_district_blocks(self):
        data = _base_rows()
        data["ADM2"] = data["ADM2"][:2]
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "no ADM2 child"):
            _inspect(_build(data))


if __name__ == "__main__":
    unittest.main()
