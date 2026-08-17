# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import profile_esrm20_ebrisk_v10_tree as profile


class EbriskV10CanonicalPathTests(unittest.TestCase):
    @staticmethod
    def _entry(path: str, *, name: str = "config_ebrisk_group1.ini") -> dict[str, str]:
        return {
            "id": "a" * 40,
            "name": name,
            "type": "blob",
            "path": path,
            "mode": "100644",
        }

    def test_canonical_relative_posix_path_is_accepted(self) -> None:
        path = "Configuration_Files/config_ebrisk_group1.ini"
        observed = profile._validate_entry(self._entry(path))
        self.assertEqual(observed["path"], path)

    def test_normalization_drift_fails_closed(self) -> None:
        cases = (
            "./Configuration_Files/config_ebrisk_group1.ini",
            "Configuration_Files//config_ebrisk_group1.ini",
            "Configuration_Files/config_ebrisk_group1.ini/",
        )
        for path in cases:
            with self.subTest(path=path):
                with self.assertRaisesRegex(
                    profile.EbriskTreeProfileError,
                    "not canonical relative POSIX",
                ):
                    profile._validate_entry(self._entry(path))


if __name__ == "__main__":
    unittest.main()
