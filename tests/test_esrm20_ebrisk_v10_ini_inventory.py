# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest

from scripts import profile_esrm20_ebrisk_v10_ini_inventory as target
from scripts import profile_esrm20_ebrisk_v10_tree as tree_profile


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


def _inventory() -> list[dict[str, str]]:
    return [
        _entry("Configuration_files", "1" * 40, entry_type="tree"),
        _entry("Configuration_files/config_ebrisk_Group1.ini", "2" * 40),
        _entry("Configuration_files/hazard.ini", "3" * 40, mode="100755"),
        _entry("Configuration_files/README.txt", "4" * 40),
        _entry("Configuration_files/subdir", "5" * 40, entry_type="tree"),
        _entry("Configuration_files/subdir/nested.ini", "6" * 40),
        _entry("Configuration_files/not_normalized.INI", "7" * 40),
        _entry("other/outside.ini", "8" * 40),
    ]


class EbriskIniInventoryTests(unittest.TestCase):
    def test_summary_is_identity_neutral_and_case_preserved(self) -> None:
        entries = _inventory()
        summary = target.summarize_ini_inventory(entries)

        self.assertEqual(summary["configuration_root"], "Configuration_files")
        self.assertEqual(summary["tree_entry_count"], len(entries))
        self.assertEqual(summary["ini_blob_count"], 3)
        self.assertEqual(
            [item["path"] for item in summary["ini_blobs"]],
            [
                "Configuration_files/config_ebrisk_Group1.ini",
                "Configuration_files/hazard.ini",
                "Configuration_files/subdir/nested.ini",
            ],
        )
        self.assertNotIn("Configuration_files/not_normalized.INI", str(summary))
        self.assertNotIn("other/outside.ini", str(summary))
        self.assertNotIn("source_issue", summary)
        self.assertNotIn("project_id", summary)
        self.assertNotIn("project_path", summary)
        self.assertNotIn("release_tag", summary)
        self.assertNotIn("commit_sha", summary)
        self.assertFalse(summary["provider_file_bytes_read"])
        self.assertFalse(summary["external_bytes_persisted"])
        self.assertFalse(summary["historical_group_assignment_authorized"])
        self.assertFalse(summary["publication_authorized"])
        self.assertFalse(summary["model_use_authorized"])

        canonical_tree = "".join(
            f"{item['type']}\t{item['mode']}\t{item['id']}\t{item['path']}\n"
            for item in sorted(
                entries,
                key=lambda item: (item["path"], item["type"], item["id"]),
            )
        ).encode("utf-8")
        self.assertEqual(
            summary["source_tree_identity_sha256"],
            hashlib.sha256(canonical_tree).hexdigest(),
        )

    def test_exact_configuration_root_is_required(self) -> None:
        missing = [entry for entry in _inventory() if entry["path"] != "Configuration_files"]
        with self.assertRaisesRegex(
            target.EbriskIniInventoryError,
            "exact Configuration_files root",
        ):
            target.summarize_ini_inventory(missing)

        duplicate = _inventory() + [
            _entry("Configuration_files", "9" * 40, entry_type="tree")
        ]
        with self.assertRaisesRegex(
            target.EbriskIniInventoryError,
            "paths are not unique",
        ):
            target.summarize_ini_inventory(duplicate)

    def test_ini_candidate_must_be_canonical_blob_with_matching_mode(self) -> None:
        non_blob = _inventory()
        non_blob[1] = _entry(
            "Configuration_files/config_ebrisk_Group1.ini",
            "2" * 40,
            entry_type="tree",
        )
        with self.assertRaisesRegex(target.EbriskIniInventoryError, "INI entry is not a blob"):
            target.summarize_ini_inventory(non_blob)

        bad_mode = _inventory()
        bad_mode[1] = _entry(
            "Configuration_files/config_ebrisk_Group1.ini",
            "2" * 40,
            mode="040000",
        )
        with self.assertRaisesRegex(
            target.EbriskIniInventoryError,
            "type/mode binding",
        ):
            target.summarize_ini_inventory(bad_mode)

    def test_noncanonical_paths_fail_closed(self) -> None:
        bad_paths = (
            "Configuration_files/../config.ini",
            "Configuration_files//config.ini",
            "Configuration_files/config.ini/",
            "Configuration_files\\config.ini",
        )
        for path in bad_paths:
            with self.subTest(path=path):
                entries = _inventory()
                entries[1] = _entry(path, "2" * 40)
                with self.assertRaisesRegex(
                    target.EbriskIniInventoryError,
                    "canonical relative POSIX",
                ):
                    target.summarize_ini_inventory(entries)

    def test_changed_output_is_bounded(self) -> None:
        original = target.MAX_INI_BLOBS
        try:
            target.MAX_INI_BLOBS = 1
            with self.assertRaisesRegex(
                target.EbriskIniInventoryError,
                "inventory exceeds policy",
            ):
                target.summarize_ini_inventory(_inventory())
        finally:
            target.MAX_INI_BLOBS = original

    def test_source_tree_inventory_bound_matches_upstream_and_precedes_parsing(self) -> None:
        self.assertEqual(target.MAX_TREE_ENTRIES, tree_profile.MAX_ENTRIES)
        oversized = [object()] * (target.MAX_TREE_ENTRIES + 1)
        with self.assertRaisesRegex(
            target.EbriskIniInventoryError,
            "source-tree inventory exceeds policy",
        ):
            target.summarize_ini_inventory(oversized)

    def test_fixed_wrapper_rejects_provider_authority_drift_before_network(self) -> None:
        original_project_id = tree_profile.PROJECT_ID
        try:
            tree_profile.PROJECT_ID = 999
            with self.assertRaisesRegex(
                target.EbriskIniInventoryError,
                "fixed ebrisk v1.0 authority drifted",
            ):
                target.profile_v10_ini_inventory()
        finally:
            tree_profile.PROJECT_ID = original_project_id


if __name__ == "__main__":
    unittest.main()
