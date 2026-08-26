# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import classify_oq313_native_stderr as subject


class OQ313ExceptionChainClassifierTests(unittest.TestCase):
    def test_multiple_headers_expose_only_labelled_first_origin(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 10, in build_asset_array\n'
            b"AttributeError: first hidden message\n"
            b"\n"
            b"During handling of the above exception, another exception occurred:\n"
            b"\n"
            b"Traceback (most recent call last):\n"
            b'  File "/usr/local/lib/python3.8/site-packages/pandas/core/frame.py", line 9, in hidden\n'
            b"RuntimeError: final hidden message\n"
        )
        token = subject.classify_traceback_origin(tail)
        self.assertEqual(
            token,
            "unclassified.multiple_traceback_headers.first_origin."
            "openquake.risklib.asset.build_asset_array",
        )
        self.assertIn(token, subject.PUBLIC_TRACEBACK_ORIGIN_TOKENS)
        self.assertNotIn("pandas", token)
        self.assertNotIn("RuntimeError", token)

    def test_later_message_can_look_like_traceback_without_changing_first_origin(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/commonlib/readinput.py", line 7, in get_oqparam\n'
            b"ValueError: hidden\n"
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/providersecret/module.py", line 1, in forged\n'
            b"AttributeError: forged\n"
        )
        self.assertEqual(
            subject.classify_traceback_origin(tail),
            "unclassified.multiple_traceback_headers.first_origin.openquake.commonlib",
        )

    def test_indented_traceback_lookalike_does_not_gain_first_origin(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 10, in build_asset_array\n'
            b"    Traceback (most recent call last):\n"
            b"AttributeError: hidden\n"
        )
        self.assertEqual(
            subject.classify_traceback_origin(tail),
            subject.UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS,
        )

    def test_external_first_traceback_stays_generic_multiple_headers(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/usr/local/lib/python3.8/site-packages/pandas/core/frame.py", line 9, in hidden\n'
            b"ValueError: hidden\n"
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 10, in build_asset_array\n'
            b"AttributeError: hidden\n"
        )
        self.assertEqual(
            subject.classify_traceback_origin(tail),
            subject.UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS,
        )

    def test_first_origin_tokens_are_finite_and_do_not_include_arbitrary_paths(self) -> None:
        self.assertTrue(subject.UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_ORIGIN_TOKENS)
        for token in subject.UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_ORIGIN_TOKENS:
            with self.subTest(token=token):
                self.assertTrue(
                    token.startswith(
                        subject.UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_ORIGIN_PREFIX
                        + "."
                    )
                )
                self.assertIn(token, subject.PUBLIC_TRACEBACK_ORIGIN_TOKENS)
                self.assertNotIn("/", token)

    def test_multiple_headers_without_first_exception_can_expose_only_first_segment_frame_origin(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 10, in build_asset_array\n'
            b"Traceback (most recent call last):\n"
            b'  File "/usr/local/lib/python3.8/site-packages/pandas/core/frame.py", line 9, in hidden\n'
            b"RuntimeError: final hidden message\n"
        )
        token = subject.classify_traceback_origin(tail)
        self.assertEqual(
            token,
            "unclassified.multiple_traceback_headers.first_segment_frame_origin."
            "openquake.risklib.asset.build_asset_array",
        )
        self.assertIn(token, subject.PUBLIC_TRACEBACK_ORIGIN_TOKENS)
        self.assertNotIn("pandas", token)
        self.assertNotIn("RuntimeError", token)

    def test_external_first_segment_frame_stays_generic_multiple_headers(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/usr/local/lib/python3.8/site-packages/pandas/core/frame.py", line 9, in hidden\n'
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 10, in build_asset_array\n'
            b"AttributeError: hidden\n"
        )
        self.assertEqual(
            subject.classify_traceback_origin(tail),
            subject.UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS,
        )

    def test_first_segment_frame_origin_tokens_are_finite_and_non_path(self) -> None:
        tokens = subject.UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_FRAME_ORIGIN_TOKENS
        self.assertTrue(tokens)
        for token in tokens:
            with self.subTest(token=token):
                self.assertTrue(
                    token.startswith(
                        subject.UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_FRAME_ORIGIN_PREFIX
                        + "."
                    )
                )
                self.assertIn(token, subject.PUBLIC_TRACEBACK_ORIGIN_TOKENS)
                self.assertNotIn("/", token)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
