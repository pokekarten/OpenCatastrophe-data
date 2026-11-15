# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline Nord source identity and exact original-byte negative checks."""
from __future__ import annotations
import gzip
import json
import unittest

from research_runners.meteofrance_nord_original_gust_v0 import (
    audit_original, verify_resource, SOURCE_ID, SOURCE_URL, SOURCE_BYTES, SOURCE_SHA256, Blocked,
)
from research_runners.meteofrance_north_hourly_catalogue_v0 import DEPARTMENTS, PERIOD, BASE

FIELD_DICTIONARY = (
    "FF: force du vent moyenné sur 10 mn\n"
    "FXI: force maximale du vent instantané\n"
    "FXI3S: force maximale du vent moyenné sur 3 secondes\n"
    "STATUS_FXI3S: code fonction de transfert\n"
).encode()
HEADER = "NUM_POSTE;AAAAMMJJHH;FF;FXI;FXI3S;QFXI3S;STATUS_FXI3S;LAT\n"
ROWS = "59101001;2020020915;7.1;18.5;19.4;1;0;50.1\n"


def example_resources():
    records=[]
    for dep in DEPARTMENTS:
        records.append({
            "title":f"HOR_departement_{dep}_periode_{PERIOD}",
            "id": SOURCE_ID if dep=="59" else
                  "aaaaaaaa-bbbb-cccc-dddd-" + str(int(dep)).zfill(12),
            "url": SOURCE_URL if dep=="59" else
                   f"{BASE}H_{dep}_previous-{PERIOD}.csv.gz",
            "filesize": SOURCE_BYTES if dep=="59" else 100_000,
        })
    return records


def sample_resource():
    return {
        "department":"59","resource_id":SOURCE_ID,
        "original_url":SOURCE_URL,"declared_compressed_bytes":SOURCE_BYTES,
        "period":"2020-2024", "source_admitted":False,"original_bytes_fetched":False,
    }


class TestNordOriginal(unittest.TestCase):
    def test_metadata_identity(self):
        verify_resource(sample_resource())

    def test_source_sha256_is_pinned_to_true_original_receipt(self):
        self.assertEqual(SOURCE_SHA256, "ee2b7254856875b5445aeaa67ea461f7e68145243bbeb2aa6cf4e5c1b36eb5e8")
        self.assertEqual(len(SOURCE_SHA256), 64)

    def test_admission_or_wrong_byte_size_block(self):
        for change in [{"declared_compressed_bytes":SOURCE_BYTES+1},
                       {"source_admitted":True},
                       {"original_bytes_fetched":True},
                       {"original_url":"https://unapproved.example/Nord.csv.gz"},
                       {"resource_id":"not-nord"}]:
            with self.subTest(change=change),self.assertRaises(Blocked):
                verify_resource({**sample_resource(), **change})

    def test_full_original_digest_requires_exact_declared_file_size(self):
        catalogue=json.dumps({"resources":example_resources()}).encode()
        fake=gzip.compress((HEADER+ROWS).encode(),mtime=0)
        with self.assertRaisesRegex(Blocked,"compressed bytes changed"):
            audit_original(catalogue,FIELD_DICTIONARY,fake)

    def test_provider_catalogue_tampering_blocks(self):
        resources=example_resources()
        resources[1]["id"]="aaaaaaaa-bbbb-cccc-dddd-000000000059"
        source=gzip.compress((HEADER+ROWS).encode(),mtime=0)
        with self.assertRaises(Blocked):
            audit_original(json.dumps({"resources":resources}).encode(),FIELD_DICTIONARY,source)

    def test_no_sensitive_rows_or_insurer_data_in_metadata(self):
        resource=sample_resource()
        self.assertNotIn("59101001",json.dumps(resource))
        self.assertNotIn("insured_tiv",json.dumps(resource))


if __name__ == "__main__":
    unittest.main()
