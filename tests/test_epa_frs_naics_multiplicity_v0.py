# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only NAICS multiplicity tests; never insurer/asset value attribution."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import unittest

from research_runners import epa_frs_naics_multiplicity_v0 as w


def blob(header, rows):
    s = io.StringIO(newline="")
    wr = csv.DictWriter(s, header, lineterminator="\n")
    wr.writeheader()
    wr.writerows(rows)
    data = s.getvalue().encode()
    return data, hashlib.sha256(data).hexdigest()


def facility(key="FRS1"):
    return dict(frs_id=key, country_code="US", latitude="", longitude="")


def naics(key="FRS1", code="221100", program="RCRA", system="SITE1"):
    return dict(REGISTRY_ID=key, PGM_SYS_ACRNM=program, PGM_SYS_ID=system, NAICS_CODE=code)


def audit(frs=None, naics_rows=None, **options):
    return w.audit_frs_naics(*blob(w.PROJECTION_HEADERS, [facility()] if frs is None else frs),
                            *blob(w.NAICS_HEADERS, [naics()] if naics_rows is None else naics_rows),
                            frs_vintage=options.get("frs_vintage", "2026-10-30"),
                            naics_vintage=options.get("naics_vintage", "2026-10-30"))


class NAICSJoinTests(unittest.TestCase):
    def test_one_code_is_not_insurance_tiv(self):
        r = audit()
        self.assertEqual(r["state"], "RESEARCH_CLASSIFICATIONS_ONLY")
        self.assertEqual(r["frs_facilities_with_at_least_one_naics"], 1)
        self.assertEqual(r["facility_sector_memberships_by_naics2"], {"22": 1})
        self.assertFalse(r["naics_is_insurance_line_or_tiv"])
        self.assertFalse(r["sector_memberships_are_additive_exposure_counts"])
        self.assertNotIn("FRS1", json.dumps(r))

    def test_two_sectors_one_facility_counted_once_per_sector(self):
        rows = [naics(), naics(code="311100", program="TRI", system="SITE2")]
        r = audit(naics_rows=rows)
        self.assertEqual(r["frs_facilities"], 1)
        self.assertEqual(r["facilities_with_multiple_distinct_naics"], 1)
        self.assertEqual(r["facility_sector_memberships_by_naics2"], {"22": 1, "31": 1})
        self.assertEqual(r["state"], "REVIEW_MULTIPLE_OCCUPANCIES")

    def test_duplicate_naics_different_program_not_double_counted(self):
        r = audit(naics_rows=[naics(), naics(program="TRI", system="SITE2")])
        self.assertEqual(r["repeated_same_code_across_distinct_programs"], 1)
        self.assertEqual(r["facility_sector_memberships_by_naics2"], {"22": 1})

    def test_out_of_subset_link_not_new_facility(self):
        r = audit(naics_rows=[naics(key="OTHER")])
        self.assertEqual(r["frs_facilities_with_no_naics_in_selected_slice"], 1)
        self.assertEqual(r["naics_rows_for_facilities_outside_selected_perimeter"], 1)

    def test_missing_naics_is_unknown_not_residential(self):
        r = audit(frs=[facility(), facility("FRS2")])
        self.assertEqual(r["frs_facilities_with_no_naics_in_selected_slice"], 1)

    def test_identical_native_program_code_duplicates_blocked(self):
        with self.assertRaisesRegex(w.NAICSAuditBlocked, "duplicated native"):
            audit(naics_rows=[naics(), naics()])

    def test_invalid_naics_codes_blocked(self):
        for code in ("", "22", "22110X", " 221100", "0000000"):
            with self.subTest(code=code), self.assertRaises(w.NAICSAuditBlocked):
                audit(naics_rows=[naics(code=code)])

    def test_invalid_frscode_and_program_identity_blocked(self):
        with self.assertRaises(w.NAICSAuditBlocked):
            audit(frs=[facility("BAD SPACE")])
        with self.assertRaises(w.NAICSAuditBlocked):
            audit(naics_rows=[naics(program="")])

    def test_source_hash_rejected(self):
        f, _ = blob(w.PROJECTION_HEADERS, [facility()])
        n, h = blob(w.NAICS_HEADERS, [naics()])
        with self.assertRaisesRegex(w.NAICSAuditBlocked, "SHA-256 mismatch"):
            w.audit_frs_naics(f, "0"*64, n, h, frs_vintage="2026-10-30", naics_vintage="2026-10-30")

    def test_mismatched_source_vintage_is_blocked(self):
        with self.assertRaisesRegex(w.NAICSAuditBlocked, "share one explicit"):
            audit(naics_vintage="2026-10-31")

    def test_program_ids_with_spaces_are_accepted_as_source_identifiers(self):
        out = audit(naics_rows=[naics(program="TRI SOURCE", system="SITE / 2")])
        self.assertEqual(out["frs_facilities_with_at_least_one_naics"], 1)
        self.assertFalse(out["naics_taxonomy_codebook_version_verified"])

    def test_invalid_native_header_rejected(self):
        f, fh = blob(w.PROJECTION_HEADERS, [facility()])
        n, nh = blob(("REGISTRY_ID",), [{"REGISTRY_ID": "FRS1"}])
        with self.assertRaisesRegex(w.NAICSAuditBlocked, "required columns"):
            w.audit_frs_naics(f, fh, n, nh, frs_vintage="2026-10-30", naics_vintage="2026-10-30")

    def test_order_independent_sector_counts(self):
        a=naics()
        b=naics(code="311100", program="TRI", system="SITE2")
        self.assertEqual(audit(naics_rows=[a,b])["facility_sector_memberships_by_naics2"],
                         audit(naics_rows=[b,a])["facility_sector_memberships_by_naics2"])


if __name__ == "__main__":
    unittest.main()
