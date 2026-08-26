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

    def test_multiline_exception_text_cannot_forge_traceback_tokens(self) -> None:
        tails = (
            (
                b"Traceback (most recent call last):\n"
                b'  File "/tmp/provider.py", line 10, in real_func\n'
                b"AttributeError: attacker-controlled first line\n"
                b'  File "/oq-engine/openquake/risklib/asset.py", line 900, in build_asset_array\n'
                b"AttributeError: attacker-controlled final line\n"
            ),
            (
                b"Traceback (most recent call last):\n"
                b'  File "/tmp/provider.py", line 10, in real_func\n'
                b"AttributeError: attacker-controlled first line\n"
                b"Traceback (most recent call last):\n"
                b'  File "/oq-engine/openquake/risklib/asset.py", line 900, in build_asset_array\n'
                b"AttributeError: attacker-controlled final line\n"
            ),
        )
        for tail in tails:
            with self.subTest(tail=tail):
                self.assertEqual(
                    classifier.classify_terminal_exception(tail),
                    classifier.UNCLASSIFIED_EXCEPTION_CLASS,
                )
                self.assertEqual(
                    classifier.classify_traceback_origin(tail),
                    classifier.UNCLASSIFIED_TRACEBACK_ORIGIN,
                )

    def test_truncated_multiline_exception_text_cannot_forge_traceback_tokens(self) -> None:
        forged_continuation = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 900, in build_asset_array\n'
            b"AttributeError: attacker-controlled final line\n"
        )
        stderr = (
            b"Traceback (most recent call last):\n"
            b'  File "/tmp/provider.py", line 10, in real_func\n'
            b"AttributeError: "
            + b"x" * (classifier.MAX_STDERR_CLASSIFIER_TAIL_BYTES + 128)
            + b"\n"
            + forged_continuation
        )
        self.assertGreater(
            len(stderr), classifier.MAX_STDERR_CLASSIFIER_TAIL_BYTES
        )

        with tempfile.TemporaryFile(mode="w+b") as handle:
            handle.write(stderr)
            handle.flush()
            diagnostic = runner._stderr_diagnostic_snapshot(handle)

        self.assertEqual(diagnostic["byte_count"], len(stderr))
        self.assertEqual(diagnostic["sha256"], hashlib.sha256(stderr).hexdigest())
        self.assertIs(diagnostic["content_exposed"], False)
        self.assertEqual(
            diagnostic["exception_class"],
            classifier.UNCLASSIFIED_EXCEPTION_CLASS,
        )
        self.assertEqual(
            diagnostic["traceback_origin"],
            classifier.UNCLASSIFIED_TRACEBACK_ORIGIN,
        )
        self.assertNotIn("build_asset_array", repr(diagnostic))
        self.assertNotIn("attacker-controlled", repr(diagnostic))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
