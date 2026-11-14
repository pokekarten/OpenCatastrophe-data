# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only, aggregate-only EPA FRS EIA-860 plant bridge tests."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import unittest

from research_runners import epa_frs_eia860_oris_crosswalk_v0 as w


def encode(header, records):
    s=io.StringIO(newline="")
    wr=csv.DictWriter(s, header, lineterminator="\n")
    wr.writeheader()
    wr.writerows(records)
    data=s.getvalue().encode()
    return data, hashlib.sha256(data).hexdigest()


def link(fid="FRS1", program="EIA-860", plant="3136"):
    return dict(REGISTRY_ID=fid, PGM_SYS_ACRNM=program, PGM_SYS_ID=plant)


def plant(pid="3136"):
    return dict(plant_id_eia=pid)


def run(frs=None, eia=None, **kwargs):
    return w.audit_eia_frs(*encode(w.FRS_HEADERS,[link()] if frs is None else frs),
                           *encode(w.EIA_HEADERS,[plant()] if eia is None else eia),
                           frs_release=kwargs.get("frs_release","2026-10-30"),
                           eia_reporting_year=kwargs.get("eia_reporting_year",2025))


class ORISCrosswalkTests(unittest.TestCase):
    def test_exact_official_program_code_creates_research_candidate_only(self):
        r=run()
        self.assertEqual(r["unique_eia_plant_to_frs_research_candidates"],1)
        self.assertEqual(r["state"],"RESEARCH_ORIS_ID_CANDIDATES_ONLY")
        self.assertTrue(r["plant_rows_conserved"])
        for x in ("eia_to_gem_asset_ids_confirmed","frs_to_eia_original_provider_files_authenticated",
                  "plant_id_is_generator_or_building_id","facility_ownership_or_insurance_inferred",
                  "source_rights_or_model_admission_granted"):
            self.assertFalse(r[x])
        self.assertNotIn("FRS1",json.dumps(r))
        self.assertNotIn("3136",json.dumps(r))

    def test_zero_padded_eia_id_is_canonicalised_without_guessing_identity(self):
        r=run(frs=[link(plant="003136")])
        self.assertEqual(r["unique_eia_plant_to_frs_research_candidates"],1)

    def test_non_eia860_program_is_not_oris_match(self):
        r=run(frs=[link(program="E-GGRT")])
        self.assertEqual(r["unique_eia_plant_to_frs_research_candidates"],0)
        self.assertEqual(r["non_eia860_program_rows"],1)
        self.assertEqual(r["state"],"NO_EIA860_ID_CANDIDATES")

    def test_one_eia_plant_many_frs_sites_is_conflict(self):
        r=run(frs=[link(),link(fid="FRS2")])
        self.assertEqual(r["eia_plants_with_cardinality_conflict"],1)
        self.assertEqual(r["state"],"REVIEW_IDENTITY_CARDINALITY_OR_SCOPE")

    def test_one_frs_many_eia_plants_is_conflict(self):
        r=run(frs=[link(),link(plant="4567")],eia=[plant(),plant("4567")])
        self.assertEqual(r["eia_plants_with_cardinality_conflict"],2)

    def test_missing_plant_is_absence_from_slice_not_no_plant(self):
        r=run(frs=[link(plant="9999")])
        self.assertEqual(r["eia_plants_not_in_supplied_frs_slice"],1)
        self.assertEqual(r["frs_eia860_plant_ids_outside_eia_projection"],1)

    def test_duplicate_program_rows_are_counted_not_extra_facilities(self):
        r=run(frs=[link(),link()])
        self.assertEqual(r["repeated_identical_eia860_program_links"],1)
        self.assertEqual(r["unique_eia_plant_to_frs_research_candidates"],1)

    def test_eia_plant_id_padding_duplicate_rejected(self):
        with self.assertRaisesRegex(w.EIAFRSBridgeBlocked,"duplicate EIA"):
            run(eia=[plant(),plant("003136")])

    def test_invalid_program_id_rejected(self):
        for bad in ("", "0", "ABC", "1234567"):
            with self.subTest(bad=bad), self.assertRaises(w.EIAFRSBridgeBlocked):
                run(frs=[link(plant=bad)])

    def test_wrong_release_or_year_blocked(self):
        for d in ("latest","2026-02-30","2099-01-01"):
            with self.subTest(d=d), self.assertRaises(w.EIAFRSBridgeBlocked):
                run(frs_release=d)
        with self.assertRaises(w.EIAFRSBridgeBlocked):
            run(eia_reporting_year=2024)

    def test_projection_hash_mismatch(self):
        a, _=encode(w.FRS_HEADERS,[link()])
        b, bh=encode(w.EIA_HEADERS,[plant()])
        with self.assertRaisesRegex(w.EIAFRSBridgeBlocked,"SHA-256 mismatch"):
            w.audit_eia_frs(a,"0"*64,b,bh,frs_release="2026-10-30",eia_reporting_year=2025)

    def test_order_independent_link_counts(self):
        a,b=link(),link(fid="FRS2",plant="4567")
        first=run(frs=[a,b],eia=[plant(),plant("4567")])
        second=run(frs=[b,a],eia=[plant("4567"),plant()])
        for field in ("unique_eia_plant_to_frs_research_candidates","eia_plants_with_cardinality_conflict",
                      "eia_plants_not_in_supplied_frs_slice"):
            self.assertEqual(first[field],second[field])


if __name__=="__main__":
    unittest.main()
