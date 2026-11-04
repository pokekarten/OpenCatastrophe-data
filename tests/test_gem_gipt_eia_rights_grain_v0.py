# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only checks for GEM 2026 GIPT location-vs-unit and CC BY-NC gates."""
from __future__ import annotations

import csv
from hashlib import sha256
from io import StringIO
import json
import unittest

from research_runners import gem_gipt_eia_rights_grain_v0 as m


def row(unit="G100",location="L100",country="United States",other=""):
    return dict(gem_unit_phase_id=unit,gem_location_id=location,
                country_area=country,other_ids_unit_phase=other)


def pack(rows, header=m.HEADERS):
    out=StringIO(newline="")
    writer=csv.DictWriter(out,fieldnames=header,lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    buf=out.getvalue().encode()
    return buf,sha256(buf).hexdigest()


def run(rows=None, **kwargs):
    data,h=pack([row()] if rows is None else rows)
    return m.review_gipt_projection(data,h,native_original_sha=kwargs.get("original"),
                                    release=kwargs.get("release","2026-09"))


class GEMGIPTGates(unittest.TestCase):
    def test_no_eia_token_is_not_negative_eia_plant_evidence(self):
        r=run()
        self.assertEqual(r["state"],"NO_EIA_860_PUBLISHER_CROSS_IDS_IN_THIS_SLICE")
        self.assertEqual(r["epa_delaware_ids_without_gem_location_claim_in_slice"],15)
        self.assertFalse(r["eia860_external_id_text_proves_cross_provider_plant_identity"])
        self.assertFalse(r["non_tz_marker_proves_unrestricted_commercial_rights"])
        self.assertFalse(r["original_workbook_bytes_independently_authenticated"])
        self.assertNotIn("G100",json.dumps(r))

    def test_one_eia_claim_remains_unverified(self):
        r=run([row(other="EIA-860: 599")])
        self.assertEqual(r["epa_delaware_ids_with_any_gem_location_claim"],1)
        self.assertEqual(r["state"],"PUBLISHER_ID_CLAIMS_ONLY")
        self.assertFalse(r["epa_gem_site_or_owner_identity_confirmed"])

    def test_multiple_unit_rows_at_one_gem_location_not_multiple_locations(self):
        r=run([row(unit="G100",other="EIA-860: 599"),
               row(unit="G101",other="EIA-860: 599")])
        self.assertEqual(r["rows"],2)
        self.assertEqual(r["location_id_groups_including_missing_sentinels"],1)
        self.assertEqual(r["epa_delaware_ids_claimed_by_multiple_gem_locations"],0)

    def test_one_eia_id_claimed_at_two_gem_locations_is_ambiguous(self):
        r=run([row(unit="G100",location="L100",other="EIA-860: 599"),
               row(unit="G101",location="L200",other="EIA-860: 599")])
        self.assertEqual(r["epa_delaware_ids_claimed_by_multiple_gem_locations"],1)
        self.assertEqual(r["state"],"REVIEW_CARDINALITY")

    def test_one_unit_with_multiple_external_eia_ids_flags_review(self):
        r=run([row(other="EIA-860: 593; EIA-860: 7153")])
        self.assertEqual(r["rows_with_multiple_eia860_tokens"],1)
        self.assertEqual(r["epa_delaware_ids_with_any_gem_location_claim"],2)
        self.assertEqual(r["state"],"REVIEW_CARDINALITY")

    def test_transitionzero_license_exception_quarantines_row(self):
        r=run([row(other="TZ ID: TZ-MAP-123; EIA-860: 599")])
        self.assertEqual(r["rows_with_transitionzero_id"],1)
        self.assertEqual(r["state"],"REVIEW_TZ_NONCOMMERCIAL_AND_IDENTITY")
        self.assertFalse(r["transitionzero_marked_rows_permitted_for_commercial_use"])

    def test_mixed_license_at_same_location_is_reported(self):
        r=run([row(unit="G1",other="TZ ID: A"),
               row(unit="G2",other="EIA-860: 599")])
        self.assertEqual(r["locations_containing_both_tz_and_non_tz_units"],1)
        self.assertEqual(r["state"],"REVIEW_TZ_NONCOMMERCIAL_AND_IDENTITY")

    def test_country_mismatch_is_not_us_eia_link(self):
        r=run([row(country="Germany",other="EIA-860: 599")])
        self.assertEqual(r["rows_with_eia_claim_in_non_us_country_area"],1)
        self.assertEqual(r["epa_delaware_ids_with_any_gem_location_claim"],0)

    def test_missing_location_is_not_site_id(self):
        r=run([row(location="",other="EIA-860: 599")])
        self.assertEqual(r["rows_missing_gem_location_id"],1)
        self.assertEqual(r["epa_delaware_ids_with_any_gem_location_claim"],0)

    def test_unstructured_oris_or_name_not_authoritative_gem_cross_id(self):
        r=run([row(other="ORIS code 599; matching project name")])
        self.assertEqual(r["rows_with_no_explicit_eia860_token"],1)

    def test_duplicate_gem_unit_phase_id_blocks(self):
        with self.assertRaisesRegex(m.GIPTBlocked,"repeated GEM"):
            run([row(),row(location="L200")])

    def test_original_sha_claim_is_not_authentication(self):
        r=run(original="a"*64)
        self.assertEqual(r["original_workbook_sha256_claim"],"a"*64)
        self.assertFalse(r["original_workbook_bytes_independently_authenticated"])
        with self.assertRaisesRegex(m.GIPTBlocked,"workbook SHA"):
            run(original="invalid")

    def test_wrong_release_fails(self):
        for release in ("2026-03","2025-09","latest"):
            with self.subTest(release=release),self.assertRaises(m.GIPTBlocked):
                run(release=release)

    def test_wrong_sha_is_not_soft_failure(self):
        raw,_=pack([row()])
        with self.assertRaisesRegex(m.GIPTBlocked,"hash mismatch"):
            m.review_gipt_projection(raw,"0"*64,native_original_sha=None)

    def test_columns_exact_and_repeated_headers_not_allowed(self):
        raw,h=pack([row()])
        data=raw.replace(b"gem_location_id",b"other_ids_unit_")
        with self.assertRaises(m.GIPTBlocked):
            m.review_gipt_projection(data,sha256(data).hexdigest(),native_original_sha=None)

    def test_bad_id_or_empty_country_blocks(self):
        for r in (row(unit=""),row(location="!!"),row(country="")):
            with self.subTest(r=r),self.assertRaises(m.GIPTBlocked):
                run([r])

    def test_results_conserve_cohort_ids(self):
        r=run([row(other="EIA-860: 599; EIA-860: 7318"),
               row(unit="G101",location="L200",other="EIA-860: 3136")])
        self.assertEqual(r["epa_delaware_ids_with_any_gem_location_claim"] +
                         r["epa_delaware_ids_without_gem_location_claim_in_slice"],15)


if __name__=="__main__":
    unittest.main()
