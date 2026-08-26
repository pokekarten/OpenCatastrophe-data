# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import classify_oq313_multiheader_first_segment as subject


class OQ313MultiheaderFirstSegmentStructureTests(unittest.TestCase):
    def test_no_frame_is_bounded(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b"hidden text\n"
            b"Traceback (most recent call last):\n"
            b"RuntimeError: hidden\n"
        )
        self.assertEqual(subject.classify_first_segment_structure(tail), subject.NO_CANONICAL_FRAME)

    def test_malformed_frame_is_bounded(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line zero, in hidden\n'
            b"Traceback (most recent call last):\n"
            b"RuntimeError: hidden\n"
        )
        self.assertEqual(subject.classify_first_segment_structure(tail), subject.MALFORMED_FRAME)

    def test_external_canonical_frame_is_bounded(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/usr/local/lib/python3.8/site-packages/pandas/core/frame.py", line 9, in hidden\n'
            b"Traceback (most recent call last):\n"
            b"RuntimeError: hidden\n"
        )
        self.assertEqual(
            subject.classify_first_segment_structure(tail),
            subject.CANONICAL_FRAME_OUTSIDE_FROZEN_OQ,
        )

    def test_forged_frame_after_exception_line_does_not_override_structure(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b"ValueError: hidden\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 10, in build_asset_array\n'
            b"Traceback (most recent call last):\n"
            b"RuntimeError: hidden\n"
        )
        self.assertEqual(subject.classify_first_segment_structure(tail), subject.NO_CANONICAL_FRAME)

    def test_frozen_oq_frame_is_left_to_stronger_classifier(self) -> None:
        tail = (
            b"Traceback (most recent call last):\n"
            b'  File "/oq-engine/openquake/risklib/asset.py", line 10, in build_asset_array\n'
            b"Traceback (most recent call last):\n"
            b"RuntimeError: hidden\n"
        )
        self.assertEqual(subject.classify_first_segment_structure(tail), subject.UNCLASSIFIED)

    def test_invalid_utf8_and_oversize_fail_closed(self) -> None:
        self.assertEqual(subject.classify_first_segment_structure(b"\xff"), subject.UNCLASSIFIED)
        self.assertEqual(
            subject.classify_first_segment_structure(b"x" * subject.MAX_TAIL_BYTES),
            subject.UNCLASSIFIED,
        )

    def test_public_tokens_are_finite_and_non_path(self) -> None:
        self.assertEqual(len(subject.PUBLIC_TOKENS), 4)
        for token in subject.PUBLIC_TOKENS:
            self.assertNotIn("/", token)
            self.assertNotIn("File", token)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
