# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only: original crop archive filename contract, no h5py dependency."""
from __future__ import annotations

import unittest
from research_runners.swiss_crop_hail_asset_preflight_v0 import Blocked
from research_runners import swiss_crop_hail_hdf5_metadata_profile_v0 as subject


class SwissCropHailStructureTests(unittest.TestCase):
    def test_expected_24_by_role(self):
        for role in ("exposure", "damage"):
            self.assertEqual(len(subject.expected_archive_names(role)), 24)
        self.assertIn("exposure_CH_grapevine_1km.h5",
                      subject.expected_archive_names("exposure"))
        self.assertIn("hail_damage_CH_wheat_8km.h5",
                      subject.expected_archive_names("damage"))

    def test_reject_wrong_role(self):
        with self.assertRaises(Blocked):
            subject.expected_archive_names("model_code")

    def test_valid_exact_publisher_archive_filenames(self):
        for role in ("exposure", "damage"):
            originals = sorted(subject.expected_archive_names(role))
            self.assertEqual(set(subject.archive_member_index(originals, role)), set(originals))

    def test_optional_safe_directory_prefix(self):
        originals = sorted(subject.expected_archive_names("exposure"))
        self.assertEqual(len(subject.archive_member_index(
            ["release/" + x for x in originals], "exposure")), 24)

    def test_missing_member_is_blocked(self):
        originals = sorted(subject.expected_archive_names("damage"))
        with self.assertRaisesRegex(Blocked, "incomplete"):
            subject.archive_member_index(originals[1:], "damage")

    def test_extra_traversal_duplicate_or_unknown_members_blocked(self):
        originals = sorted(subject.expected_archive_names("exposure"))
        for attacker in ("README.md", "../exposure_CH_barley_1km.h5",
                         "other/exposure_CH_barley_1km.h5",
                         "malicious\\file.h5", "C:bad"):
            with self.subTest(path=attacker):
                with self.assertRaisesRegex(Blocked, "unrecognized"):
                    subject.archive_member_index(originals + [attacker], "exposure")

    def test_wrong_role_archive_blocked(self):
        with self.assertRaises(Blocked):
            subject.archive_member_index(
                sorted(subject.expected_archive_names("damage")), "exposure")


if __name__ == "__main__":
    unittest.main()
