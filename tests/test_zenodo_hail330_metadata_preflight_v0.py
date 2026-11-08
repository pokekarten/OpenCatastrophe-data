# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic, offline tests for the exact Zenodo v2 metadata receipt gate."""

from __future__ import annotations

import csv
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_runners"))
from zenodo_hail330_metadata_preflight_v0 import (  # noqa: E402
    COLUMNS, COUNTRIES, HailMetadataError, MAX_METADATA_BYTES,
    audit_metadata_bytes,
)


def make_synthetic_rows() -> list[dict[str, str]]:
    return [
        {
            "file_name": f"hail_{country}_{'ref' if scenario == 'REF' else 'PGW'}.h5",
            "data_source": "model",
            "country_iso3alpha": country,
            "climate_scenario": scenario,
            "res_km": "2.2",
            "climada_datatype": "hail",
            "climada_name": f"hail_{country}_{scenario}",
            "version": "v2",
        }
        for country in COUNTRIES for scenario in ("REF", "PGW")
    ]


def encode_rows(rows: list[dict[str, str]], columns: tuple[str, ...] = COLUMNS) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


class TestZenodoHail330Metadata(unittest.TestCase):
    def test_complete_paired_synthetic_v2(self) -> None:
        receipt = audit_metadata_bytes(encode_rows(make_synthetic_rows()), require_publisher_md5=False)
        self.assertEqual((receipt["country_count"], receipt["file_count"]), (28, 56))
        self.assertFalse(receipt["source_hdf5_bytes_checked"])
        self.assertFalse(receipt["scientific_admitted"])
        self.assertFalse(receipt["rights_reviewed"])

    def test_default_fails_closed_on_unverified_bytes(self) -> None:
        with self.assertRaisesRegex(HailMetadataError, "MD5 mismatch"):
            audit_metadata_bytes(encode_rows(make_synthetic_rows()))

    def test_missing_country_scenario_rejected(self) -> None:
        with self.assertRaises(HailMetadataError):
            audit_metadata_bytes(encode_rows(make_synthetic_rows()[:-1]), require_publisher_md5=False)

    def test_duplicate_country_scenario_rejected(self) -> None:
        rows = make_synthetic_rows()
        rows[-1] = dict(rows[0])
        with self.assertRaisesRegex(HailMetadataError, "duplicate"):
            audit_metadata_bytes(encode_rows(rows), require_publisher_md5=False)

    def test_wrong_file_casing_rejected(self) -> None:
        rows = make_synthetic_rows()
        rows[0]["file_name"] = "hail_ALB_REF.h5"
        with self.assertRaises(HailMetadataError):
            audit_metadata_bytes(encode_rows(rows), require_publisher_md5=False)

    def test_scenario_and_grid_drift_rejected(self) -> None:
        for field, value in (("climate_scenario", "FUT"), ("res_km", "25"), ("version", "v3")):
            with self.subTest(field=field):
                rows = make_synthetic_rows()
                rows[0][field] = value
                with self.assertRaises(HailMetadataError):
                    audit_metadata_bytes(encode_rows(rows), require_publisher_md5=False)

    def test_header_drift_rejected(self) -> None:
        shifted = tuple(reversed(COLUMNS))
        with self.assertRaises(HailMetadataError):
            audit_metadata_bytes(encode_rows(make_synthetic_rows(), shifted), require_publisher_md5=False)

    def test_corrupted_or_oversized_input_rejected(self) -> None:
        for payload in (b"", b"\xff", b"x" * (MAX_METADATA_BYTES + 1)):
            with self.subTest(length=len(payload)):
                with self.assertRaises(HailMetadataError):
                    audit_metadata_bytes(payload, require_publisher_md5=False)


if __name__ == "__main__":
    unittest.main()
