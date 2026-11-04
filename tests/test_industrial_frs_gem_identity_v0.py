# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only non-admission tests for industrial identity uncertainty."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import unittest

from research_runners import industrial_frs_gem_identity_v0 as w


def projection(columns, rows):
    stream = io.StringIO(newline="")
    wr = csv.DictWriter(stream, columns, lineterminator="\n")
    wr.writeheader()
    wr.writerows(rows)
    data = stream.getvalue().encode("utf-8")
    return data, hashlib.sha256(data).hexdigest()


def facility(**updates):
    row = dict(frs_id="FRS1", country_code="US", latitude="40", longitude="-75")
    row.update(updates)
    return row


def asset(**updates):
    row = dict(gem_asset_id="GEM1", country_code="US", latitude="40", longitude="-75")
    row.update(updates)
    return row


def link(**updates):
    row = dict(frs_id="FRS1", gem_asset_id="GEM1", evidence_kind="publisher_explicit_cross_id", evidence_sha256="a"*64)
    row.update(updates)
    return row


def audit(frs=None, gem=None, links=None, **vintages):
    return w.audit_identity(*projection(w.FRS_COLUMNS, [facility()] if frs is None else frs),
                            *projection(w.GEM_COLUMNS, [asset()] if gem is None else gem),
                            *projection(w.LINK_COLUMNS, [link()] if links is None else links),
                            frs_vintage=vintages.get("frs_vintage", "2026-10-30"),
                            gem_vintage=vintages.get("gem_vintage", "2026-10-01"),
                            link_vintage=vintages.get("link_vintage", "2026-11-04"))


class IndustrialIdentityTests(unittest.TestCase):
    def test_unique_asserted_pair_is_only_research_candidate(self):
        out = audit()
        self.assertEqual(out["state"], "RESEARCH_ID_CANDIDATES_ONLY")
        self.assertEqual(out["frs_row_dispositions"]["one_to_one_research_candidate"], 1)
        self.assertTrue(out["frs_rows_conserved"])
        self.assertFalse(any(out[x] for x in (
            "projection_hash_proves_publisher_byte_authenticity",
            "link_evidence_hash_independently_authenticated",
            "coordinates_or_names_prove_asset_identity",
            "corporate_ownership_or_lei_link_derived",
            "insured_asset_or_tiv_inferred", "source_rights_or_model_admission_granted")))
        self.assertNotIn("FRS1", json.dumps(out))
        self.assertNotIn("GEM1", json.dumps(out))

    def test_missing_link_is_not_no_asset(self):
        out = audit(links=[])
        self.assertEqual(out["state"], "NO_RESEARCH_ID_CANDIDATE")
        self.assertEqual(out["frs_row_dispositions"]["no_link_in_bounded_subset"], 1)

    def test_proximity_is_not_identity(self):
        out = audit(links=[link(evidence_kind="name_or_proximity_only", evidence_sha256="")])
        self.assertEqual(out["frs_row_dispositions"]["name_or_proximity_only_unverified"], 1)
        self.assertEqual(out["state"], "REVIEW_NEEDED")

    def test_one_facility_many_assets_requires_review(self):
        out = audit(gem=[asset(), asset(gem_asset_id="GEM2")], links=[link(), link(gem_asset_id="GEM2")])
        self.assertEqual(out["frs_row_dispositions"]["ambiguous_many_to_one_or_one_to_many"], 1)

    def test_many_facilities_one_asset_requires_review(self):
        out = audit(frs=[facility(), facility(frs_id="FRS2")],
                    links=[link(), link(frs_id="FRS2")])
        self.assertEqual(out["frs_row_dispositions"]["ambiguous_many_to_one_or_one_to_many"], 2)

    def test_gem_absent_is_unknown_not_nonexistent(self):
        out = audit(links=[link(gem_asset_id="ANOTHER")])
        self.assertEqual(out["frs_row_dispositions"]["missing_gem_in_bounded_subset"], 1)
        self.assertEqual(out["links_with_gem_id_absent_from_subset"], 1)

    def test_country_disagreement_never_qualifies(self):
        out = audit(gem=[asset(country_code="CA")])
        self.assertEqual(out["frs_row_dispositions"]["country_disagreement"], 1)

    def test_location_missing_not_resolved_by_id_alone(self):
        out = audit(frs=[facility(latitude="", longitude="")])
        self.assertEqual(out["frs_row_dispositions"]["location_missing"], 1)

    def test_far_coordinates_require_review_even_with_asserted_id(self):
        out = audit(gem=[asset(latitude="41")])
        self.assertEqual(out["frs_row_dispositions"]["distance_over_5km_review"], 1)

    def test_malformed_coordinates_rejected(self):
        for replace in (dict(latitude=""), dict(latitude="nan"), dict(longitude="181")):
            with self.subTest(replace=replace), self.assertRaises(w.IdentityPreflightBlocked):
                audit(frs=[facility(**replace)])

    def test_bad_hash_and_duplicate_ids_rejected(self):
        with self.assertRaisesRegex(w.IdentityPreflightBlocked, "SHA-256 mismatch"):
            f, h = projection(w.FRS_COLUMNS, [facility()])
            g, gh = projection(w.GEM_COLUMNS, [asset()])
            l, lh = projection(w.LINK_COLUMNS, [link()])
            w.audit_identity(f, "0"*64, g, gh, l, lh,
                             frs_vintage="2026-10-30", gem_vintage="2026-10-01", link_vintage="2026-11-04")
        with self.assertRaisesRegex(w.IdentityPreflightBlocked, "duplicate FRS"):
            audit(frs=[facility(), facility()])
        with self.assertRaisesRegex(w.IdentityPreflightBlocked, "duplicate asserted"):
            audit(links=[link(), link()])

    def test_invalid_evidence_kind_and_digest_rejected(self):
        with self.assertRaises(w.IdentityPreflightBlocked):
            audit(links=[link(evidence_kind="fuzzy_name")])
        with self.assertRaises(w.IdentityPreflightBlocked):
            audit(links=[link(evidence_sha256="")])

    def test_bad_vintage_rejected(self):
        for date in ("latest", "2026-02-30", "2018-01-01", "2026-11-04T00:00"):
            with self.subTest(date=date), self.assertRaises(w.IdentityPreflightBlocked):
                audit(link_vintage=date)

    def test_dispositions_conserve_facilities_without_order_dependence(self):
        first = audit(frs=[facility(), facility(frs_id="FRS2")])
        second = audit(frs=[facility(frs_id="FRS2"), facility()])
        self.assertEqual(first["frs_row_dispositions"], second["frs_row_dispositions"])
        self.assertEqual(sum(first["frs_row_dispositions"].values()), 2)
        self.assertNotEqual(first["frs_projection_sha256"], second["frs_projection_sha256"])


if __name__ == "__main__":
    unittest.main()
