# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline tests for immutable CAT publisher-byte receipt checks."""
import csv
import hashlib
import io
import unittest

from research_runners.historical_cat_benchmark_csv_preflight_v0 import (
    HANZE_COLUMNS, EXPOSURE_COLUMNS, SourcePreflightError,
)
from scripts.verify_historical_cat_csv_provider_receipts import (
    read_receipt, verify_one, verify_pair,
)


def csv_bytes(columns, row):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def hanze():
    row = {k: "" for k in HANZE_COLUMNS}
    row.update(id="2000", country_code="DE", event_start_date_year="2025",
               start_date="2025-01-02", end_date="2025-01-04",
               reference_year_eur="2025", admin_unit_year="2024")
    return csv_bytes(HANZE_COLUMNS, row)


def residential():
    row = {k: "" for k in EXPOSURE_COLUMNS}
    row.update(IndicatorCode="A1", Indicator="Building", Unit="EUR_per_m2",
               CountryCode="DE", Country="Germany", **{"2024": "0"})
    return csv_bytes(EXPOSURE_COLUMNS, row)


def pin(raw, profile):
    return {
        "bytes": len(raw), "observed_sha256": hashlib.sha256(raw).hexdigest(),
        "publisher_md5": hashlib.md5(raw, usedforsecurity=False).hexdigest(),
        "required_profile": profile,
    }


class ProviderByteReceiptTests(unittest.TestCase):
    def test_committed_receipt_is_nonadmitted_and_pinned(self):
        records = read_receipt()
        self.assertEqual(set(records["sources"]), {"hanze_v3_0_2_beta", "residential_v2025"})
        for source in records["sources"].values():
            self.assertEqual(source["admission_status"], "not_admitted")
            self.assertEqual(len(source["observed_sha256"]), 64)
            self.assertTrue(source["api_url"].startswith("https://zenodo.org/api/records/"))

    def test_synthetic_hanze(self):
        raw = hanze()
        result = verify_one("hanze_v3_0_2_beta", raw, pin(raw, {"event_count": 1}))
        self.assertFalse(result["model_admission"])

    def test_synthetic_residential(self):
        raw = residential()
        result = verify_one("residential_v2025", raw, pin(raw, {"numeric_cells_present": 1}))
        self.assertFalse(result["profile"]["insured_tiv_calculated"])

    def test_refuse_tampered_same_length(self):
        raw = residential()
        with self.assertRaises(SourcePreflightError):
            verify_one("residential_v2025", raw.replace(b"Germany", b"GermaNy"), pin(raw, {}))

    def test_refuse_wrong_length(self):
        raw = hanze()
        with self.assertRaises(SourcePreflightError):
            verify_one("hanze_v3_0_2_beta", raw + b"x", pin(raw, {}))

    def test_refuse_bad_publisher_md5(self):
        raw = hanze()
        bad = pin(raw, {"event_count": 1})
        bad["publisher_md5"] = "0" * 32
        with self.assertRaises(SourcePreflightError):
            verify_one("hanze_v3_0_2_beta", raw, bad)

    def test_refuse_profile_drift(self):
        raw = hanze()
        with self.assertRaises(SourcePreflightError):
            verify_one("hanze_v3_0_2_beta", raw, pin(raw, {"event_count": 2780}))

    def test_pair_never_admits_sources(self):
        a, b = hanze(), residential()
        records = {"sources": {
            "hanze_v3_0_2_beta": pin(a, {"event_count": 1}),
            "residential_v2025": pin(b, {"indicator_country_row_count": 1}),
        }}
        result = verify_pair(a, b, records)
        self.assertFalse(result["source_admitted"])
        self.assertFalse(result["insured_loss_or_asset_tiv_created"])
        self.assertEqual(result["historical_country_year_availability"]["event_count_with_exact_country_prior_year_indicator"], 1)
        self.assertFalse(result["historical_country_year_availability"]["insured_loss_created"])


if __name__ == "__main__":
    unittest.main()
