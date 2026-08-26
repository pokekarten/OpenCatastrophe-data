# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import classify_oq313_native_stderr as subject


class OQ313NativeStderrClassifierTests(unittest.TestCase):
    def test_allowlisted_builtin_class_is_returned_without_message(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/provider/private/path.py", line 9, in <module>\n'
            b"    raise ValueError('secret-value')\n"
            b"ValueError: secret-value /provider/private/path\n"
        )

        self.assertEqual(subject.classify_terminal_exception(tail), "ValueError")

    def test_pinned_openquake_invalidfile_class_is_allowlisted(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b"  File \"/oq-engine/openquake/commonlib/readinput.py\", line 1\n"
            b"openquake.baselib.InvalidFile: hidden provider value\n"
        )

        self.assertEqual(subject.classify_terminal_exception(tail), "InvalidFile")

    def test_message_without_canonical_traceback_is_unclassified(self) -> None:
        tail = b"ValueError: forged-looking terminal text\n"

        self.assertEqual(
            subject.classify_terminal_exception(tail),
            subject.UNCLASSIFIED_EXCEPTION_CLASS,
        )
        self.assertEqual(
            subject.classify_traceback_origin(tail),
            subject.UNCLASSIFIED_TRACEBACK_ORIGIN,
        )

    def test_unallowlisted_class_is_unclassified(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b"  File \"x\", line 1, in <module>\n"
            b"ProviderSecretException: hidden-value\n"
        )

        self.assertEqual(
            subject.classify_terminal_exception(tail),
            subject.UNCLASSIFIED_EXCEPTION_CLASS,
        )

    def test_non_utf8_terminal_is_unclassified(self) -> None:
        tail = b"Traceback (most recent call last):\n\xff\xfe\x00\n"

        self.assertEqual(
            subject.classify_terminal_exception(tail),
            subject.UNCLASSIFIED_EXCEPTION_CLASS,
        )
        self.assertEqual(
            subject.classify_traceback_origin(tail),
            subject.UNCLASSIFIED_TRACEBACK_ORIGIN,
        )

    def test_non_utf8_interior_with_valid_terminal_is_unclassified(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "x", line 1, in <module>\n'
            b"\xff\xfe invalid frame detail\n"
            b"ValueError: hidden\n"
        )

        self.assertEqual(
            subject.classify_terminal_exception(tail),
            subject.UNCLASSIFIED_EXCEPTION_CLASS,
        )
        self.assertEqual(
            subject.classify_traceback_origin(tail),
            subject.UNCLASSIFIED_TRACEBACK_ORIGIN,
        )

    def test_oversized_tail_fails_closed(self) -> None:
        tail = (
            b"x" * subject.MAX_STDERR_CLASSIFIER_TAIL_BYTES
            + b"Traceback (most recent call last):\nValueError: hidden\n"
        )

        self.assertGreater(len(tail), subject.MAX_STDERR_CLASSIFIER_TAIL_BYTES)
        self.assertEqual(
            subject.classify_terminal_exception(tail),
            subject.UNCLASSIFIED_EXCEPTION_CLASS,
        )
        self.assertEqual(
            subject.classify_traceback_origin(tail),
            subject.UNCLASSIFIED_TRACEBACK_ORIGIN,
        )

    def test_traceback_origin_returns_only_final_allowlisted_oq_package(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/commonlib/readinput.py", line 10, in get_oqparam\n'
            b'  File "/oq-engine/openquake/risklib/riskmodels.py", line 20, in get_risk_functions\n'
            b"AttributeError: hidden provider-dependent message\n"
        )

        self.assertEqual(
            subject.classify_traceback_origin(tail),
            "openquake.risklib",
        )

    def test_traceback_origin_external_final_frame_is_unclassified(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/riskmodels.py", line 20, in get_risk_functions\n'
            b'  File "/usr/local/lib/python3.8/site-packages/pandas/core/frame.py", line 9, in hidden\n'
            b"AttributeError: hidden provider-dependent message\n"
        )

        self.assertEqual(
            subject.classify_traceback_origin(tail),
            subject.UNCLASSIFIED_TRACEBACK_ORIGIN,
        )

    def test_traceback_origin_does_not_expose_filename_function_or_line(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/calculators/event_based_risk.py", line 123, in secret_func\n'
            b"AttributeError: hidden\n"
        )

        origin = subject.classify_traceback_origin(tail)
        self.assertEqual(origin, "openquake.calculators")
        self.assertNotIn("event_based_risk", origin)
        self.assertNotIn("secret_func", origin)
        self.assertNotIn("123", origin)

    def test_traceback_origin_outside_frozen_oq_tree_is_unclassified(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/usr/local/lib/python3.8/site-packages/pandas/core/frame.py", line 9, in hidden\n'
            b"AttributeError: hidden\n"
        )

        self.assertEqual(
            subject.classify_traceback_origin(tail),
            subject.UNCLASSIFIED_TRACEBACK_ORIGIN,
        )

    def test_unknown_openquake_package_is_unclassified(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/providersecret/module.py", line 9, in hidden\n'
            b"AttributeError: hidden\n"
        )

        self.assertEqual(
            subject.classify_traceback_origin(tail),
            subject.UNCLASSIFIED_TRACEBACK_ORIGIN,
        )

    def test_public_token_sets_are_closed(self) -> None:
        self.assertIn("ValueError", subject.PUBLIC_EXCEPTION_CLASS_TOKENS)
        self.assertIn("InvalidFile", subject.PUBLIC_EXCEPTION_CLASS_TOKENS)
        self.assertIn(subject.UNCLASSIFIED_EXCEPTION_CLASS, subject.PUBLIC_EXCEPTION_CLASS_TOKENS)
        self.assertNotIn("ProviderSecretException", subject.PUBLIC_EXCEPTION_CLASS_TOKENS)

        self.assertIn("openquake.risklib", subject.PUBLIC_TRACEBACK_ORIGIN_TOKENS)
        self.assertIn("openquake.calculators", subject.PUBLIC_TRACEBACK_ORIGIN_TOKENS)
        self.assertIn(subject.UNCLASSIFIED_TRACEBACK_ORIGIN, subject.PUBLIC_TRACEBACK_ORIGIN_TOKENS)
        self.assertNotIn("openquake.providersecret", subject.PUBLIC_TRACEBACK_ORIGIN_TOKENS)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
