# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict synthetic-only negative tests for optional CDS original acquisition.

Never calls CDS, authenticates, accepts licences or downloads provider data.
"""
from __future__ import annotations

import csv
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research_runners import c3s_ews_annual_original_acquisition_v0 as mod


FIELDS = ("year", "region", "threshold", "storm_number", "mean_wind_gust",
          "ssi", "normalised_ssi", "area_ratio", "wind_gust_ratio", "algorithm")


def toy_csv():
    dest = StringIO(newline="")
    writer = csv.DictWriter(dest, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for year in (1950, 1951, 1952):
        for alg in ("hodges", "tempestextremes"):
            writer.writerow({"year": year, "region": "DE", "threshold": "20",
                             "storm_number": year - 1950, "algorithm": alg})
    return dest.getvalue().encode("utf-8")


def toy_zip(*members):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, payload in members:
            archive.writestr(name, payload)
    return buffer.getvalue()


class FakeClient:
    def __init__(self, body=None, error=None):
        self.body = toy_csv() if body is None else body
        self.error = error
        self.calls = []

    def retrieve(self, name, request, target):
        self.calls.append((name, request))
        if self.error:
            raise ValueError(self.error)
        Path(target).write_bytes(self.body)


class C3SOriginalAcquisitionTests(unittest.TestCase):
    def test_exact_official_form_request_and_tracking_labels(self):
        self.assertEqual(mod.official_request(), {
            "product": "windstorm_summary_indicator", "variable": ["all"],
            "tracking_algorithm": ["hodges", "tempestextremes"]})
        self.assertEqual(mod.official_request(("hodges",))["tracking_algorithm"], ["hodges"])
        for options in ((), ("hodges", "hodges"), ("TRACK",), ("hodges", 1),
                        ("hodges", "tempestextremes", "hodges"), "hodges"):
            with self.subTest(options=options), self.assertRaises(mod.AcquisitionError):
                mod.official_request(options)

    def test_source_hash_and_original_schema_intake_but_no_promotion(self):
        original = toy_csv()
        receipt = mod.inspect_provider_package(original)
        self.assertEqual(receipt["original_response_sha256"], sha256(original).hexdigest())
        self.assertEqual(receipt["original_csv_sha256"], sha256(original).hexdigest())
        self.assertEqual(receipt["official_annual_parser_rows"], 6)
        self.assertEqual(receipt["official_annual_parser_min_year"], 1950)
        self.assertEqual(receipt["official_annual_parser_max_year"], 1952)
        self.assertEqual(receipt["response_representation"], "ORIGINAL_CSV")
        self.assertEqual(receipt["official_annual_parser_algorithms"],
                         ["hodges", "tempestextremes"])
        self.assertTrue(receipt["source_algorithms_match_exact_request"])
        self.assertEqual(receipt["source_canonical_algorithms"],
                         ["hodges", "tempestextremes"])
        self.assertFalse(receipt["rights_admitted"])
        self.assertFalse(receipt["frequency_model_calibrated"])
        self.assertFalse(receipt["original_bytes_independently_publisher_signed"])
        self.assertEqual(receipt, mod.inspect_provider_package(original))

    def test_original_algorithm_names_must_match_exact_request(self):
        raw = toy_csv()
        # A syntactically valid CSV still cannot silently claim an unrelated
        # algorithm, an unrequested second tracker or omit one selected tracker.
        altered = raw.replace(b",hodges\\n", b",TRACK\\n")
        with self.assertRaisesRegex(mod.AcquisitionError, "unknown source tracking"):
            mod.inspect_provider_package(altered)
        only_hodges = mod.official_request(("hodges",))
        with self.assertRaisesRegex(mod.AcquisitionError, "differs from exact"):
            mod.inspect_provider_package(raw, request=only_hodges)
        # Provider documentation uses two different spellings for the same
        # canonical TempestExtremes algorithm; retain the original CSV labels.
        source_case = raw.replace(b",tempestextremes\\n", b",TempestExtremes\\n")
        report = mod.inspect_provider_package(source_case)
        self.assertIn("TempestExtremes", report["official_annual_parser_algorithms"])
        self.assertEqual(report["source_canonical_algorithms"],
                         ["hodges", "tempestextremes"])
        # A forged CSV using two labels for the SAME canonical tracker cannot
        # make the declared single-algorithm request look fully satisfied.
        collided = raw.replace(b",hodges\\n", b",tempest extreme\\n")
        with self.assertRaisesRegex(mod.AcquisitionError, "differs from exact"):
            mod.inspect_provider_package(collided, request=mod.official_request(("tempestextremes",)))
        # Single-tracker request passes when the CSV indeed contains only it.
        lines = raw.decode().splitlines(keepends=True)
        single = "".join([lines[0]] + [line for line in lines[1:]
                                    if line.endswith(",hodges\\n")]).encode()
        found = mod.inspect_provider_package(single, request=only_hodges)
        self.assertEqual(found["source_canonical_algorithms"], ["hodges"])
        self.assertTrue(found["source_algorithms_match_exact_request"])

    def test_original_single_csv_zip_is_extracted_without_normalising_bytes(self):
        original = toy_csv()
        package = toy_zip(("c3s-summary.csv", original))
        receipt = mod.inspect_provider_package(package)
        self.assertEqual(receipt["response_representation"], "ZIP_ONE_ORIGINAL_CSV")
        self.assertEqual(receipt["original_csv_member_name"], "c3s-summary.csv")
        self.assertEqual(receipt["original_response_sha256"], sha256(package).hexdigest())
        self.assertEqual(receipt["original_csv_sha256"], sha256(original).hexdigest())

    def test_fail_closed_on_zip_path_traversal_multi_member_and_invalid_payload(self):
        cases = [
            toy_zip(("../outside.csv", toy_csv())),
            toy_zip((".."+chr(92)+"outside.csv", toy_csv())),
            toy_zip(("C:outside.csv", toy_csv())),
            toy_zip(("a.csv", toy_csv()), ("b.csv", toy_csv())),
            toy_zip(("index.txt", toy_csv())),
            toy_zip(("a.csv", b"not-a-csv")),
            b"<html>Login required</html>",
            b"",
            b"PK\x03\x04bad-archive",
        ]
        for data in cases:
            with self.subTest(first=data[:16]), self.assertRaises(mod.AcquisitionError):
                mod.inspect_provider_package(data)
        with self.assertRaises(mod.AcquisitionError):
            mod.inspect_provider_package(toy_csv(), request={"product": "bad"})
        with self.assertRaises(mod.AcquisitionError):
            mod.inspect_provider_package(toy_csv(), request=[])
        with self.assertRaises(mod.AcquisitionError):
            mod.inspect_provider_package(toy_csv(), request={"product": "windstorm_summary_indicator",
                "variable": ["all"], "tracking_algorithm": ["hodges"], "extra": "ambiguous"})

    def test_injected_local_client_retrieval_is_byte_exact_and_exclusive(self):
        fake = FakeClient()
        with TemporaryDirectory() as directory:
            outdir = Path(directory) / "external"
            receipt = mod.acquire(output_dir=outdir, client=fake)
            self.assertEqual(fake.calls, [(mod.DATASET, mod.official_request())])
            original = outdir / "c3s-ews-original-annual-summary-response.bin"
            recorded = outdir / "c3s-ews-original-annual-summary-receipt.json"
            self.assertEqual(original.read_bytes(), toy_csv())
            self.assertEqual(json.loads(recorded.read_text()), receipt)
            with self.assertRaisesRegex(mod.AcquisitionError, "overwrite"):
                mod.acquire(output_dir=outdir, client=fake)
            self.assertEqual(len(fake.calls), 1)

    def test_download_failure_is_not_silently_admitted_or_logged(self):
        secret = "secret-CDS-token-must-not-appear"
        fake = FakeClient(error=secret)
        with TemporaryDirectory() as directory:
            with self.assertRaises(mod.AcquisitionError) as cm:
                mod.acquire(output_dir=Path(directory), client=fake)
            self.assertNotIn(secret, str(cm.exception))
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_invalid_remote_response_cannot_be_saved_as_original(self):
        fake = FakeClient(body=b"<html>cloud gateway</html>")
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(mod.AcquisitionError, "annual-summary"):
                mod.acquire(output_dir=Path(directory), client=fake)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_git_checkout_is_not_provider_data_storage(self):
        with self.assertRaisesRegex(mod.AcquisitionError, "outside the repository"):
            mod.acquire(output_dir=Path(mod.__file__).resolve().parents[1] / "raw",
                        client=FakeClient())


if __name__ == "__main__":
    unittest.main()
