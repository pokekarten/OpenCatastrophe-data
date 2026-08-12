# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from scripts.validate_agent_action_result import ResultError, validate_acquisition_receipt

ROOT = Path(__file__).resolve().parents[1]
ACQUISITION_SCHEMA = ROOT / "schemas/acquisition-receipt-v1.schema.json"
ACTION_RESULT_SCHEMA = ROOT / "schemas/agent-action-result-v1.schema.json"

BASE_RECEIPT = {
    "schema_version": "oc-acquisition-receipt-v1",
    "dataset_id": "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03",
    "source_issue": 162,
    "requested_url": (
        "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
        "10_minutes/extreme_wind/historical/"
        "10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip"
    ),
    "final_url": (
        "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
        "10_minutes/extreme_wind/historical/"
        "10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip"
    ),
    "filename": "10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip",
    "retrieved_at": "2026-08-12T00:11:50Z",
    "byte_count": 488338,
    "sha256": "c" * 64,
    "content_type": "application/zip",
    "last_modified": "Tue, 30 Nov 2021 10:59:16 GMT",
    "etag": None,
    "archive_member_count": 2,
    "archive_uncompressed_bytes": 1000000,
    "product_member": "produkt_zehn_min_ff_00003_20100101_20110331_hist.txt",
    "product_station_id": "00003",
    "product_begin_date": "20100101",
    "product_end_date": "20110331",
    "product_row_count": 65000,
    "product_structure_validated": True,
    "external_bytes_persisted": False,
    "publication_authorized": False,
}


class DwdActionReceiptMemberContractTests(unittest.TestCase):
    def test_accepts_safe_text_member_without_legacy_prefix(self) -> None:
        receipt = dict(BASE_RECEIPT)
        validated = validate_acquisition_receipt(receipt)
        self.assertEqual(validated["product_member"], BASE_RECEIPT["product_member"])

        nested_uppercase = dict(
            BASE_RECEIPT,
            product_member="nested/provider-product-00003.TXT",
        )
        self.assertEqual(
            validate_acquisition_receipt(nested_uppercase)["product_member"],
            "nested/provider-product-00003.TXT",
        )

    def test_rejects_unsafe_or_non_text_member_paths(self) -> None:
        unsafe_members = (
            "",
            "/absolute.txt",
            "../escape.txt",
            "dir/../escape.txt",
            "./product.txt",
            "dir//product.txt",
            "dir\\product.txt",
            "product.csv",
            "product\n.txt",
            "product\x00.txt",
        )
        for member in unsafe_members:
            with self.subTest(member=repr(member)):
                with self.assertRaisesRegex(ResultError, "product_member"):
                    validate_acquisition_receipt(dict(BASE_RECEIPT, product_member=member))

    def test_portable_schemas_drop_legacy_prefix_and_keep_text_shape(self) -> None:
        acquisition = json.loads(ACQUISITION_SCHEMA.read_text(encoding="utf-8"))
        action_result = json.loads(ACTION_RESULT_SCHEMA.read_text(encoding="utf-8"))
        patterns = (
            acquisition["properties"]["product_member"]["pattern"],
            action_result["$defs"]["acquisitionReceipt"]["properties"]["product_member"]["pattern"],
        )
        for pattern in patterns:
            with self.subTest(pattern=pattern):
                self.assertNotIn("produkt_extrema_wind_", pattern)
                self.assertIsNotNone(re.search(pattern, "provider-product.txt"))
                self.assertIsNotNone(re.search(pattern, "provider-product.TXT"))
                self.assertIsNone(re.search(pattern, "provider-product.csv"))


if __name__ == "__main__":
    unittest.main()
