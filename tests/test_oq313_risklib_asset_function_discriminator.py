# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import tempfile
import unittest

from scripts import classify_oq313_native_stderr as classifier
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as runner


class OQ313RisklibAssetFunctionDiscriminatorTests(unittest.TestCase):
    def test_exact_asset_function_is_refined_to_finite_public_token(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 900, in build_asset_array\n'
            b"AttributeError: provider-dependent hidden message\n"
        )
        token = classifier.classify_traceback_origin(tail)
        self.assertEqual(token, "openquake.risklib.asset.build_asset_array")
        self.assertIn(token, classifier.PUBLIC_TRACEBACK_ORIGIN_TOKENS)
        self.assertNotIn("900", token)
        self.assertNotIn("provider", token)

    def test_unknown_asset_function_stays_at_existing_module_granularity(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 901, in provider_controlled_name\n'
            b"AttributeError: hidden\n"
        )
        token = classifier.classify_traceback_origin(tail)
        self.assertEqual(token, "openquake.risklib.asset")
        self.assertNotIn("provider_controlled_name", token)

    def test_runner_diagnostic_wires_only_refined_finite_token(self) -> None:
        stderr = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 777, in _get_exposure\n'
            b"AttributeError: hidden taxonomy/value/path\n"
        )
        with tempfile.TemporaryFile(mode="w+b") as handle:
            handle.write(stderr)
            handle.flush()
            diagnostic = runner._stderr_diagnostic_snapshot(handle)

        self.assertEqual(
            diagnostic,
            {
                "byte_count": len(stderr),
                "sha256": hashlib.sha256(stderr).hexdigest(),
                "content_exposed": False,
                "exception_class": "AttributeError",
                "traceback_origin": "openquake.risklib.asset._get_exposure",
            },
        )
        self.assertNotIn("777", repr(diagnostic))
        self.assertNotIn("taxonomy", repr(diagnostic))

    def test_external_final_frame_cannot_forge_asset_function_token(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 1, in _get_exposure\n'
            b'  File "/tmp/provider.py", line 2, in build_asset_array\n'
            b"AttributeError: hidden\n"
        )
        self.assertEqual(
            classifier.classify_traceback_origin(tail),
            classifier.UNCLASSIFIED_TRACEBACK_ORIGIN,
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
