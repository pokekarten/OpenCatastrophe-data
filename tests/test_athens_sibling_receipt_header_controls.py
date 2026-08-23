# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import acquire_efehr_esrm20_athens_sibling_receipts as worker


class AthensSiblingReceiptHeaderControlTests(unittest.TestCase):
    def test_receipt_rejects_control_character_content_type(self) -> None:
        role, path = worker.INPUTS[0]
        receipt = {
            "role": role,
            "repository_path": path,
            "retrieved_at": "2026-08-23T19:00:00Z",
            "byte_count": 1,
            "sha256": "0" * 64,
            "content_type": "application/xml\nX-Injected: value",
            "etag": None,
            "provider_file_bytes_read": True,
            "external_bytes_persisted": False,
            "publication_authorized": False,
        }

        with self.assertRaisesRegex(
            worker.AthensSiblingReceiptError, "content_type contains control characters"
        ):
            worker.validate_receipt(receipt, expected=(role, path))


if __name__ == "__main__":
    unittest.main()
