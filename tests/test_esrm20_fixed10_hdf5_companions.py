# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import profile_esrm20_ebrisk_v10_tree as tree_profile
from scripts import profile_esrm20_fixed10_hdf5_companions as target


def _entry(
    path: str,
    object_id: str,
    *,
    entry_type: str = "blob",
    mode: str | None = None,
) -> dict[str, str]:
    return {
        "id": object_id,
        "name": path.rsplit("/", 1)[-1],
        "type": entry_type,
        "path": path,
        "mode": mode or ("040000" if entry_type == "tree" else "100644"),
    }


def _inventory(*, include_one_companion: bool = True) -> list[dict[str, str]]:
    entries = [
        _entry(path, f"{index:040x}")
        for index, path in enumerate(target.SOURCE_XML_PATHS, start=1)
    ]
    if include_one_companion:
        candidate = target.SOURCE_XML_PATHS[0][:-4] + ".hdf5"
        entries.append(_entry(candidate, "f" * 40, mode="100755"))
    entries.append(_entry("Configuration_files", "e" * 40, entry_type="tree"))
    return entries


class Fixed10Hdf5CompanionProfileTests(unittest.TestCase):
    def test_summary_reconciles_only_fixed_same_stem_candidates(self) -> None:
        summary = target.summarize_hdf5_companions(_inventory())

        self.assertEqual(summary["source_xml_count"], 10)
        self.assertEqual(summary["candidate_hdf5_count"], 10)
        self.assertEqual(summary["present_hdf5_count"], 1)
        self.assertEqual(summary["absent_hdf5_count"], 9)
        self.assertEqual(len(summary["companions"]), 10)
        first = summary["companions"][0]
        self.assertEqual(first["source_xml_path"], target.SOURCE_XML_PATHS[0])
        self.assertEqual(
            first["candidate_hdf5_path"],
            target.SOURCE_XML_PATHS[0][:-4] + ".hdf5",
        )
        self.assertTrue(first["present"])
        self.assertEqual(first["mode"], "100755")
        self.assertEqual(first["object_sha1"], "f" * 40)

        for item in summary["companions"][1:]:
            self.assertFalse(item["present"])
            self.assertIsNone(item["mode"])
            self.assertIsNone(item["object_sha1"])

        self.assertFalse(summary["provider_file_bytes_read"])
        self.assertFalse(summary["hdf5_byte_identity_verified"])
        self.assertFalse(summary["transitive_dependency_byte_closure_verified"])
        self.assertFalse(summary["runtime_compatibility_verified"])
        self.assertFalse(summary["external_bytes_persisted"])
        self.assertFalse(summary["publication_authorized"])
        self.assertFalse(summary["model_use_authorized"])

    def test_all_absent_is_valid_metadata_evidence_not_byte_closure(self) -> None:
        summary = target.summarize_hdf5_companions(
            _inventory(include_one_companion=False)
        )
        self.assertEqual(summary["present_hdf5_count"], 0)
        self.assertEqual(summary["absent_hdf5_count"], 10)
        self.assertTrue(all(not item["present"] for item in summary["companions"]))
        self.assertFalse(summary["hdf5_byte_identity_verified"])
        self.assertFalse(summary["transitive_dependency_byte_closure_verified"])

    def test_missing_fixed_xml_fails_closed(self) -> None:
        entries = _inventory()[1:]
        with self.assertRaisesRegex(
            target.Hdf5CompanionProfileError,
            "fixed source-model XML is absent",
        ):
            target.summarize_hdf5_companions(entries)

    def test_same_stem_candidate_must_be_blob(self) -> None:
        entries = _inventory(include_one_companion=False)
        candidate = target.SOURCE_XML_PATHS[0][:-4] + ".hdf5"
        entries.append(_entry(candidate, "f" * 40, entry_type="tree"))
        with self.assertRaisesRegex(
            target.Hdf5CompanionProfileError,
            "HDF5 companion is not a blob",
        ):
            target.summarize_hdf5_companions(entries)

    def test_duplicate_or_noncanonical_tree_metadata_fails_closed(self) -> None:
        duplicate = _inventory()
        duplicate.append(dict(duplicate[0]))
        with self.assertRaisesRegex(
            target.Hdf5CompanionProfileError,
            "paths are not unique",
        ):
            target.summarize_hdf5_companions(duplicate)

        noncanonical = _inventory()
        noncanonical[0] = _entry(
            "Hazard/source_models/../escape.xml",
            "1" * 40,
        )
        with self.assertRaisesRegex(
            target.Hdf5CompanionProfileError,
            "canonical relative POSIX",
        ):
            target.summarize_hdf5_companions(noncanonical)

    def test_source_tree_inventory_bound_matches_upstream(self) -> None:
        self.assertEqual(target.MAX_TREE_ENTRIES, tree_profile.MAX_ENTRIES)
        oversized = [object()] * (target.MAX_TREE_ENTRIES + 1)
        with self.assertRaisesRegex(
            target.Hdf5CompanionProfileError,
            "source-tree inventory exceeds policy",
        ):
            target.summarize_hdf5_companions(oversized)

    def test_fixed_wrapper_rejects_provider_authority_drift_before_network(self) -> None:
        original_project_id = tree_profile.PROJECT_ID
        try:
            tree_profile.PROJECT_ID = 999
            with self.assertRaisesRegex(
                target.Hdf5CompanionProfileError,
                "fixed ESRM20 v1.0 authority drifted",
            ):
                target.profile_fixed10_hdf5_companions()
        finally:
            tree_profile.PROJECT_ID = original_project_id


if __name__ == "__main__":
    unittest.main()
