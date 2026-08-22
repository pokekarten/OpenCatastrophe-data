# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/oq313-kosovo-reconstructed-run.yml")


class OQ313KosovoExactSourceVersionReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_derived_runtime_can_compute_the_frozen_git_suffix(self) -> None:
        text = self.text
        install_git = "apt-get install -y --no-install-recommends git"
        pin_abbrev = "git -C /oq-engine config core.abbrev 10"
        verify_abbrev = (
            'test "$(git -C /oq-engine rev-parse --short HEAD)" = "16dd69ecea"'
        )
        install_source = "python -m pip install --no-deps -e /oq-engine"
        version_fence = 'if openquake_version != "3.13.0-git16dd69ecea":'

        for needle in (
            install_git,
            pin_abbrev,
            verify_abbrev,
            install_source,
            version_fence,
        ):
            self.assertIn(needle, text)

        self.assertLess(text.index(install_git), text.index(pin_abbrev))
        self.assertLess(text.index(pin_abbrev), text.index(verify_abbrev))
        self.assertLess(text.index(verify_abbrev), text.index(install_source))

    def test_source_commit_and_historical_version_fingerprint_remain_fixed(self) -> None:
        text = self.text
        self.assertIn(
            "OQ_COMMIT: 16dd69ecea0c6dcaf49c22ca12edc9da3f024889",
            text,
        )
        self.assertIn('"openquake_version": openquake_version', text)
        self.assertNotIn(
            '"openquake_version": "3.13.0-git16dd69ecea"',
            text,
        )


if __name__ == "__main__":
    unittest.main()
