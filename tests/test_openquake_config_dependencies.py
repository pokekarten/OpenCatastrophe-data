# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.openquake_config_dependencies import (
    OpenQuakeConfigError,
    extract_openquake_config_references,
    normalize_repository_reference,
)


CONFIG_PATH = "Configuration_files/example.ini"


class OpenQuakeConfigDependencyTests(unittest.TestCase):
    def test_dependency_may_walk_up_within_repository(self) -> None:
        self.assertEqual(
            normalize_repository_reference(
                "Configuration_files/nested/example.ini",
                "../../Hazard/tree.xml",
            ),
            "Hazard/tree.xml",
        )


if __name__ == "__main__":
    unittest.main()
