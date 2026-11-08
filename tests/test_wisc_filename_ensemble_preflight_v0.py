# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only independent WISC catalogue claims and original guide controls."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research_runners.wisc_filename_ensemble_preflight_v0 import (
    CatalogueError,
    DATASET,
    inspect_catalogue,
    main,
    parse_wisc_filename,
)


def filename(stamp: str, member: int, *, method: str = "00", track: str = "1708") -> str:
    return f"fp_ga3ups_{stamp}_{track}_{method}{member}_v1.nc"


PUBLISHED_TABLE_EXAMPLE_STEM = "fp_ga3ups_199311201800_1708_002"


def raw_doc(rows: list[str]) -> bytes:
    return (json.dumps(
        {
            "schema_version": "wisc-filename-catalogue-v0",
            "source_dataset_id": DATASET,
            "records": [
                {"filename": item, "original_file_sha256_claim": f"{i + 1:064x}"}
                for i, item in enumerate(rows)
            ],
        }, sort_keys=True, separators=(",", ":")
    ) + "\n").encode("utf-8")


def inspect(*rows: str) -> dict[str, object]:
    payload = raw_doc(list(rows))
    return inspect_catalogue(payload, hashlib.sha256(payload).hexdigest())


class WiscOriginalMetadataContractTests(unittest.TestCase):
    def test_published_table_id_with_documented_v1_extension_is_accepted(self) -> None:
        source = PUBLISHED_TABLE_EXAMPLE_STEM + "_v1.nc"
        o = parse_wisc_filename(source)
        self.assertEqual(o["simulated_median_time"], "1993-11-20T18:00")
        self.assertEqual(o["source_track_id"], "1708")
        self.assertEqual(o["ensemble_member_from_filename"], 2)
        self.assertEqual(o["method_from_code_provisional"], "unresolved_legacy_set")
        self.assertFalse(o["filename_method_and_ensemble_independently_verified_against_original_netcdf"])

    def test_guide_ten_digit_text_does_not_override_twelve_digit_published_table(self) -> None:
        with self.assertRaisesRegex(CatalogueError, "12-digit"):
            parse_wisc_filename("fp_ga3ups_1993112018_1708_002_v1.nc")

    def test_three_methods_same_simulated_track_are_not_three_annual_events(self) -> None:
        o = inspect(
            filename("199311201800", 2, method="12"),
            filename("199311201800", 2, method="20"),
            filename("199311201800", 2, method="30"),
        )
        self.assertEqual(o["file_count_claimed"], 3)
        self.assertEqual(o["distinct_simulated_track_candidates"], 1)
        self.assertEqual(o["same_track_multiple_method_candidates"], 1)
        self.assertEqual(o["method_code_counts"], {"12": 1, "20": 1, "30": 1})
        self.assertFalse(o["same_track_different_method_views_independent_events"])
        self.assertFalse(o["annual_oep_aep_authorized"])

    def test_legacy_zero_zero_method_is_not_silently_renamed_one_point_two(self) -> None:
        o = inspect(PUBLISHED_TABLE_EXAMPLE_STEM + "_v1.nc")
        self.assertTrue(o["unresolved_legacy_method_codes_present"])
        self.assertEqual(o["method_code_counts"], {"00": 1})

    def test_different_ensemble_members_are_separate_candidate_tracks(self) -> None:
        o = inspect(filename("199311201800", 1), filename("199311201800", 2))
        self.assertEqual(o["distinct_simulated_track_candidates"], 2)
        self.assertEqual(o["same_track_multiple_method_candidates"], 0)
        self.assertFalse(o["return_period_weights_verified"])

    def test_different_tracks_at_same_simulation_time_are_separate_candidates(self) -> None:
        o = inspect(filename("199311201800", 2, track="1708"),
                    filename("199311201800", 2, track="1900"))
        self.assertEqual(o["distinct_simulated_track_candidates"], 2)

    def test_first_missing_ensemble_four_interval_oct_1988_to_nov_1998(self) -> None:
        for time in ("198810011200", "199311201800", "199811300600"):
            with self.subTest(time=time), self.assertRaisesRegex(CatalogueError, "missing ensemble"):
                inspect(filename(time, 4))
        self.assertEqual(inspect(filename("198809241200", 4))["file_count_claimed"], 1)
        self.assertEqual(inspect(filename("199812010000", 4))["file_count_claimed"], 1)

    def test_ensemble_three_missing_dec_1988_to_mar_1990(self) -> None:
        for time in ("198812010000", "199001010000", "199003310000"):
            with self.subTest(time=time), self.assertRaisesRegex(CatalogueError, "missing ensemble"):
                inspect(filename(time, 3))
        self.assertEqual(inspect(filename("198811010000", 3))["file_count_claimed"], 1)
        self.assertEqual(inspect(filename("199004010000", 3))["file_count_claimed"], 1)

    def test_ensemble_four_oct_nov_2002_missing(self) -> None:
        for time in ("200210010000", "200211300000"):
            with self.subTest(time=time), self.assertRaisesRegex(CatalogueError, "missing ensemble"):
                inspect(filename(time, 4))
        self.assertEqual(inspect(filename("200212010000", 4))["file_count_claimed"], 1)

    def test_ensemble_five_dec_2008_to_feb_2010_missing(self) -> None:
        for time in ("200812010000", "200909011200", "201002280000"):
            with self.subTest(time=time), self.assertRaisesRegex(CatalogueError, "missing ensemble"):
                inspect(filename(time, 5))
        self.assertEqual(inspect(filename("201003010000", 5))["file_count_claimed"], 1)

    def test_missing_period_of_one_ensemble_does_not_exclude_other_ensembles(self) -> None:
        o = inspect(filename("199311201800", 2), filename("199311201800", 5))
        self.assertEqual(o["file_count_claimed"], 2)

    def test_summer_or_out_of_range_date_is_blocked(self) -> None:
        for time in ("199306150600", "201205160000", "198512151200"):
            with self.subTest(time=time), self.assertRaisesRegex(CatalogueError, "official"):
                inspect(filename(time, 2))

    def test_bad_calendar_date_is_blocked(self) -> None:
        with self.assertRaisesRegex(CatalogueError, "invalid simulated"):
            inspect(filename("199311311200", 2))

    def test_bad_member_method_and_extra_prefix_block(self) -> None:
        for name in (
            filename("199311201800", 0),
            filename("199311201800", 6),
            filename("199311201800", 2, method="99"),
            "untrusted_" + filename("199311201800", 2),
            filename("199311201800", 2).replace("_v1.nc", "_v2.nc"),
        ):
            with self.subTest(name=name), self.assertRaises(CatalogueError):
                inspect(name)

    def test_noncase_sensitive_or_ambiguous_suffix_not_accepted(self) -> None:
        with self.assertRaisesRegex(CatalogueError, "unsupported WISC"):
            parse_wisc_filename(filename("199311201800", 2).replace(".nc", ".NC"))

    def test_duplicate_original_filename_blocks(self) -> None:
        fname = filename("199311201800", 2)
        with self.assertRaisesRegex(CatalogueError, "duplicate original"):
            inspect(fname, fname)

    def test_bad_original_hash_claim_blocks(self) -> None:
        doc = json.loads(raw_doc([filename("199311201800", 2)]))
        doc["records"][0]["original_file_sha256_claim"] = "NOT A HASH"
        raw = json.dumps(doc).encode()
        with self.assertRaisesRegex(CatalogueError, "hash claim malformed"):
            inspect_catalogue(raw, hashlib.sha256(raw).hexdigest())

    def test_manifest_wrong_sha_blocks(self) -> None:
        raw = raw_doc([filename("199311201800", 2)])
        with self.assertRaisesRegex(CatalogueError, "source manifest bytes differ"):
            inspect_catalogue(raw, "f" * 64)

    def test_bad_schema_and_duplicate_json_key_block(self) -> None:
        raw = b'{"schema_version":"a","schema_version":"b"}'
        with self.assertRaisesRegex(CatalogueError, "duplicate JSON"):
            inspect_catalogue(raw, hashlib.sha256(raw).hexdigest())
        doc = json.loads(raw_doc([filename("199311201800", 2)]))
        doc["source_dataset_id"] = "untrusted"
        raw = json.dumps(doc).encode()
        with self.assertRaisesRegex(CatalogueError, "unsupported WISC"):
            inspect_catalogue(raw, hashlib.sha256(raw).hexdigest())

    def test_empty_or_unbounded_catalogue_blocks(self) -> None:
        with self.assertRaisesRegex(CatalogueError, "empty or unbounded"):
            inspect_catalogue(raw_doc([]), hashlib.sha256(raw_doc([])).hexdigest())

    def test_annual_ep_is_never_authorized_even_with_multiple_years(self) -> None:
        a = inspect(filename("199309101200", 2), filename("200709101200", 2))
        self.assertEqual(a["simulated_years_with_at_least_one_filename"], [1993, 2007])
        for field in (
            "complete_source_event_catalogue_verified",
            "complete_ensemble_months_or_zero_event_years_verified",
            "source_events_independent_annual_occurrences_verified",
            "return_period_weights_verified",
            "annual_oep_aep_authorized",
            "oasis_financial_loss_or_calibration_established",
            "source_data_licence_and_admission_verified",
        ):
            with self.subTest(field=field):
                self.assertFalse(a[field])

    def test_cli_synthetic_file_and_exact_hash(self) -> None:
        with TemporaryDirectory() as d:
            p = Path(d) / "imaginary-source-list.json"
            raw = raw_doc([filename("199311201800", 2)])
            p.write_bytes(raw)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = main([str(p), "--manifest-sha256", hashlib.sha256(raw).hexdigest()])
            self.assertEqual(rc, 0)
            self.assertFalse(json.loads(out.getvalue())["annual_oep_aep_authorized"])
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = main([str(p), "--manifest-sha256", "f" * 64])
            self.assertEqual(rc, 2)
            self.assertEqual(json.loads(err.getvalue())["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
