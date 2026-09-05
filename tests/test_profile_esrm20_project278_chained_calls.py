# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import ast
import unittest

from scripts import profile_esrm20_project278_dataflow as subject


class Project278ChainedCallTests(unittest.TestCase):
    def test_chained_crs_then_writer_is_retained(self) -> None:
        tree = ast.parse(
            """
def export_site(gdf, path):
    gdf.to_crs(\"EPSG:4326\").to_file(path)
"""
        )
        function = tree.body[0]
        self.assertIsInstance(function, ast.FunctionDef)

        profile = subject._scope_profile(function, "synthetic.py")
        self.assertIsNotNone(profile)
        assert profile is not None
        self.assertIn("gdf.to_crs", profile["crs_calls"])
        self.assertIn("to_file", profile["writer_calls"])
        self.assertIn("crs_and_writer_same_function", profile["relations"])

    def test_unclassified_chained_method_remains_ignored(self) -> None:
        tree = ast.parse(
            """
def generic_chain(gdf):
    return gdf.prepare().transform()
"""
        )
        function = tree.body[0]
        self.assertIsInstance(function, ast.FunctionDef)

        profile = subject._scope_profile(function, "synthetic.py")
        self.assertIsNone(profile)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
