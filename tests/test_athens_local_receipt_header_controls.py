# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import acquire_efehr_esrm20_athens_local_receipts as subject


class AthensLocalHeaderControlTests(unittest.TestCase):
    def test_header_values_are_bounded(self):
        self.assertEqual(
            subject._validate_header_value("application/xml", field="content_type"),
            "application/xml",
        )
        self.assertIsNone(subject._validate_header_value(None, field="etag"))
        with self.assertRaisesRegex(subject.AthensLocalReceiptError, "bounded"):
            subject._validate_header_value("x" * 1025, field="etag")

    def test_control_characters_are_rejected(self):
        for value in ("ok\nbad", "ok\rbad", "bad\x7f"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    subject.AthensLocalReceiptError, "control"
                ):
                    subject._validate_header_value(value, field="etag")


if __name__ == "__main__":
    unittest.main()
