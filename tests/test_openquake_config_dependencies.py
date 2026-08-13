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
    def test_extracts_and_normalizes_first_order_file_dependencies(self) -> None:
        text = """
[general]
calculation_mode = event_based

[site_params]
site_model_file =
    ../Sites/site_a.xml
    ../Sites/site_b.xml

[calculation]
source_model_logic_tree_file = ../Hazard/source_logic_tree.xml
gsim_logic_tree_file = ../Hazard/gsim_logic_tree.xml
truncation_level = 3
"""
        references = extract_openquake_config_references(text, config_path=CONFIG_PATH)
        self.assertEqual(
            [(item.option, item.resolved_path) for item in references],
            [
                ("gsim_logic_tree_file", "Hazard/gsim_logic_tree.xml"),
                ("source_model_logic_tree_file", "Hazard/source_logic_tree.xml"),
                ("site_model_file", "Sites/site_a.xml"),
                ("site_model_file", "Sites/site_b.xml"),
            ],
        )

    def test_matches_openquake_314_input_suffixes(self) -> None:
        text = """
[input]
rupture_model_file = ../Hazard/ruptures.xml
sites_csv = ../Sites/sites.csv
model_cache_hdf5 = ../Hazard/cache.hdf5
source_model_files = ../Ignored/not_an_oq314_input.xml
ordinary_setting = ../Ignored/not_a_dependency.txt
"""
        references = extract_openquake_config_references(text, config_path=CONFIG_PATH)
        self.assertEqual(
            [(item.option, item.resolved_path) for item in references],
            [
                ("model_cache_hdf5", "Hazard/cache.hdf5"),
                ("rupture_model_file", "Hazard/ruptures.xml"),
                ("sites_csv", "Sites/sites.csv"),
            ],
        )

    def test_legacy_hdf5_value_is_recognized(self) -> None:
        references = extract_openquake_config_references(
            "[reqv]\nactive_crust = ../Hazard/equivalent_distance.hdf5\n",
            config_path=CONFIG_PATH,
        )
        self.assertEqual(
            [(item.option, item.resolved_path) for item in references],
            [("active_crust", "Hazard/equivalent_distance.hdf5")],
        )

    def test_empty_file_option_declares_no_dependency(self) -> None:
        references = extract_openquake_config_references(
            "[site_params]\nsite_model_file =\nvs30 = 760\n",
            config_path=CONFIG_PATH,
        )
        self.assertEqual(references, ())

    def test_dependency_may_walk_up_within_repository(self) -> None:
        self.assertEqual(
            normalize_repository_reference(
                "Configuration_files/nested/example.ini",
                "../../Hazard/tree.xml",
            ),
            "Hazard/tree.xml",
        )

    def test_repository_escape_is_rejected(self) -> None:
        with self.assertRaisesRegex(OpenQuakeConfigError, "escapes the repository root"):
            normalize_repository_reference(CONFIG_PATH, "../../outside.xml")

    def test_non_repository_path_forms_are_rejected(self) -> None:
        bad_paths = (
            "/absolute/model.xml",
            "C:/model.xml",
            "folder\\model.xml",
            "scheme:model.xml",
            "model.xml?query",
            "model.xml#fragment",
        )
        for path in bad_paths:
            with self.subTest(path=path):
                with self.assertRaises(OpenQuakeConfigError):
                    normalize_repository_reference(CONFIG_PATH, path)

    def test_ambiguous_non_file_forms_are_rejected(self) -> None:
        for path in (".", "directory/", "one.xml,two.xml"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(OpenQuakeConfigError, "ambiguous or not file-like"):
                    normalize_repository_reference(CONFIG_PATH, path)

    def test_noncanonical_config_path_is_rejected(self) -> None:
        for path in (
            "Configuration_files/../example.ini",
            "/Configuration_files/example.ini",
            "Configuration_files\\example.ini",
        ):
            with self.subTest(path=path):
                with self.assertRaises(OpenQuakeConfigError):
                    extract_openquake_config_references("[general]\nvalue = 1\n", config_path=path)

    def test_duplicate_dependency_in_one_option_is_rejected(self) -> None:
        text = """
[site_params]
site_model_file =
    ../Sites/site.xml
    ../Sites/./site.xml
"""
        with self.assertRaisesRegex(OpenQuakeConfigError, "duplicate dependency"):
            extract_openquake_config_references(text, config_path=CONFIG_PATH)

    def test_duplicate_ini_option_is_rejected(self) -> None:
        text = """
[calculation]
source_model_logic_tree_file = ../Hazard/one.xml
source_model_logic_tree_file = ../Hazard/two.xml
"""
        with self.assertRaisesRegex(OpenQuakeConfigError, "invalid INI configuration"):
            extract_openquake_config_references(text, config_path=CONFIG_PATH)

    def test_file_valued_option_in_multiple_sections_is_rejected(self) -> None:
        text = """
[hazard]
source_model_logic_tree_file = ../Hazard/one.xml

[risk]
source_model_logic_tree_file = ../Hazard/two.xml
"""
        with self.assertRaisesRegex(OpenQuakeConfigError, "defined in multiple sections"):
            extract_openquake_config_references(text, config_path=CONFIG_PATH)

    def test_generic_file_option_cannot_become_an_implicit_file_list(self) -> None:
        text = """
[calculation]
source_model_logic_tree_file =
    ../Hazard/one.xml
    ../Hazard/two.xml
"""
        with self.assertRaises(OpenQuakeConfigError):
            extract_openquake_config_references(text, config_path=CONFIG_PATH)

    def test_file_valued_default_is_rejected(self) -> None:
        text = """
[DEFAULT]
site_model_file = ../Sites/default.xml

[calculation]
truncation_level = 3
"""
        with self.assertRaisesRegex(OpenQuakeConfigError, "file-valued DEFAULT"):
            extract_openquake_config_references(text, config_path=CONFIG_PATH)

    def test_control_characters_are_rejected(self) -> None:
        with self.assertRaisesRegex(OpenQuakeConfigError, "control characters"):
            extract_openquake_config_references(
                "[calculation]\nsource_model_logic_tree_file = ../Hazard/tree.xml\x00\n",
                config_path=CONFIG_PATH,
            )

    def test_output_is_deterministic_independent_of_option_order(self) -> None:
        first = """
[calculation]
gsim_logic_tree_file = ../Hazard/g.xml
source_model_logic_tree_file = ../Hazard/s.xml
"""
        second = """
[calculation]
source_model_logic_tree_file = ../Hazard/s.xml
gsim_logic_tree_file = ../Hazard/g.xml
"""
        self.assertEqual(
            extract_openquake_config_references(first, config_path=CONFIG_PATH),
            extract_openquake_config_references(second, config_path=CONFIG_PATH),
        )


if __name__ == "__main__":
    unittest.main()
