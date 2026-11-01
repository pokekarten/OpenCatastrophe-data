# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for FEMA NFIP v1 penetration exact-byte preflight."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from research_runners.nfip_residential_penetration_v1_preflight import (
    NFIPPenetrationError, validate_original,
)

ROOT = Path(__file__).resolve().parents[1]


def row(i, **overrides):
    value = {
        "id": "EPHEMERAL-" + str(i),
        "fipsCode": f"{1000 + i:05d}",
        "state": "Synthetic State",
        "county": "Synthetic County",
        "asOfDate": "2026-08-04",
        "resContractsInForce": 110,
        "totalResStructures": 100,
        "resPenetrationRate": 1.1,
        "resContractsInForceSfha": 20,
        "totalResStructuresSfha": 40,
        "resPenetrationRateSfha": 0.5,
        "latitude": 30.1,
        "longitude": -89.1,
    }
    value.update(overrides)
    return value


def payload(rows, **meta):
    metadata = {"entityname": "NfipResidentialPenetrationRates",
                "version": "v1", "top": 100}
    metadata.update(meta)
    return json.dumps({"metadata": metadata,
                       "NfipResidentialPenetrationRates": rows}).encode("utf-8")


def check(raw):
    return validate_original(raw, hashlib.sha256(raw).hexdigest())


class NFIPPenetrationTests(unittest.TestCase):
    def test_source_fields_and_over_100pct_rate_are_preserved_as_warning(self):
        actual = check(payload([row(1), row(2)]))
        self.assertEqual(actual["source_record_count"], 2)
        self.assertEqual(actual["record_counts_by_as_of_date"]["2026-08-04"], 2)
        self.assertEqual(actual["ratio_over_100pct_counts"]["total"], 2)
        self.assertFalse(actual["model_input_admitted"])
        self.assertFalse(actual["source_completeness_proven"])
        serialized = json.dumps(actual)
        self.assertNotIn("EPHEMERAL-", serialized)
        self.assertNotIn("Synthetic County", serialized)
        self.assertNotIn("latitude", serialized)

    def test_missing_denominator_and_rate_are_not_zero(self):
        actual = check(payload([row(1, totalResStructures=None,
                                    resPenetrationRate=None)]))
        self.assertEqual(actual["missing_structure_denominator_counts"]["total"], 1)
        self.assertEqual(actual["missing_ratio_counts"]["total"], 1)
        self.assertNotIn("total", actual["zero_structure_denominator_counts"])

    def test_zero_denominator_is_distinct(self):
        actual = check(payload([row(1, totalResStructures=0,
                                    resPenetrationRate=2.8)]))
        self.assertEqual(actual["zero_structure_denominator_counts"]["total"], 1)

    def test_wrong_field_types_bad_fips_negative_rate_and_duplicate_county(self):
        variants = [
            row(1, fipsCode=1001),
            row(1, fipsCode="0101"),
            row(1, resContractsInForce=True),
            row(1, totalResStructures=-1),
            row(1, resPenetrationRate="-Infinity"),
            row(1, resPenetrationRate=-0.1),
            row(1, asOfDate="2026-02-30"),
        ]
        for v in variants:
            with self.subTest(v=v):
                with self.assertRaises(NFIPPenetrationError):
                    check(payload([v]))
        with self.assertRaisesRegex(NFIPPenetrationError, "duplicate county"):
            check(payload([row(1), row(2, fipsCode="01001")], top=2))

    def test_wrong_dataset_version_and_duplicate_ids_fail(self):
        with self.assertRaisesRegex(NFIPPenetrationError, "wrong FEMA"):
            check(payload([row(1)], version="v2"))
        with self.assertRaisesRegex(NFIPPenetrationError, "duplicate ephemeral"):
            check(payload([row(1), row(2, id="EPHEMERAL-1")]))
        with self.assertRaisesRegex(NFIPPenetrationError, "invalid provider metadata top"):
            check(payload([row(1), row(2)], top=1))
        with self.assertRaisesRegex(NFIPPenetrationError, "sha256 mismatch"):
            validate_original(payload([row(1)]), "0" * 64)

    def test_unknown_source_fields_remain_unexported(self):
        actual = check(payload([row(1, unknownPrivateNote="PRIVATE")]))
        self.assertNotIn("PRIVATE", json.dumps(actual))

    def test_cli_with_synthetic_original_json(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.json"
            original = payload([row(1)])
            path.write_bytes(original)
            proc = subprocess.run(
                [sys.executable,
                 "research_runners/nfip_residential_penetration_v1_preflight.py",
                 "--source-json", str(path),
                 "--sha256", hashlib.sha256(original).hexdigest()],
                cwd=ROOT, capture_output=True, text=True, check=True, timeout=30)
            out = json.loads(proc.stdout)
            self.assertEqual(out["source_record_count"], 1)
            self.assertFalse(out["original_geographic_rows_exported"])


if __name__ == "__main__":
    unittest.main()
