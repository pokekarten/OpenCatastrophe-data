# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/oq313-kosovo-reconstructed-run.yml")


class OQ313KosovoExactSourceDependencyReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_frozen_source_requirements_are_installed_before_editable_source(self) -> None:
        text = self.text
        requirements_install = (
            "python -m pip install --disable-pip-version-check --no-warn-script-location \\\n"
            "                   -r /oq-engine/requirements-py38-linux64.txt"
        )
        editable_install = "python -m pip install --no-deps -e /oq-engine"

        self.assertIn(requirements_install, text)
        self.assertIn(editable_install, text)
        self.assertLess(text.index(requirements_install), text.index(editable_install))

    def test_runtime_receipt_keeps_frozen_source_recipe_versions(self) -> None:
        text = self.text
        for package, version in (
            ("h5py", "3.1.0"),
            ("numpy", "1.20.0"),
            ("pandas", "1.1.5"),
            ("psutil", "5.6.7"),
            ("pyzmq", "19.0.0"),
            ("scipy", "1.4.1"),
            ("shapely", "1.7.1"),
        ):
            self.assertIn(f'"{package}": "{version}"', text)

        self.assertIn('sys.version_info[:2] != (3, 8)', text)
        self.assertIn('raise SystemExit("OQ3.13 runtime dependency receipt drifted")', text)

    def test_dependency_fix_does_not_relax_exact_source_version_fence(self) -> None:
        text = self.text
        self.assertIn(
            'test "$(git -C /oq-engine rev-parse --short HEAD)" = "16dd69ecea"',
            text,
        )
        self.assertIn('if openquake_version != "3.13.0-git16dd69ecea":', text)


if __name__ == "__main__":
    unittest.main()
