# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests: same country and dates NEVER prove the same CAT event."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.dfo_floodrecords_csv_preflight_v0 import HEADER as DFO_HEADER
from research_runners.historical_cat_benchmark_csv_preflight_v0 import HANZE_COLUMNS
from research_runners.flood_event_link_candidates_v0 import LinkageError, link_candidates

ROOT = Path(__file__).resolve().parents[1]


def csv_blob(header, rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def dfo_row(**kwargs):
    row = {field: "" for field in DFO_HEADER}
    row.update({
        "﹟": "5510", "Glide ﹟": "",
        "Start Date": "12/30/23", "End Date": "1/4/24", "Country": "Germany",
        "Area (km²)": "100", "Main Cause": "Heavy rain", "Source": "News",
        "Fatalities": "0", "Displaced": "", "Severity": "1", "Flood impact index ": "2.5",
    })
    row.update(kwargs)
    return row


def hanze_row(**kwargs):
    row = {field: "" for field in HANZE_COLUMNS}
    row.update({
        "id": "1001", "country_code": "DE", "event_start_date_year": "2023",
        "country_name": "Germany", "start_date": "2023-12-29", "end_date": "2024-01-05",
        "event_type": "River", "cause": "Heavy rainfall", "admin_unit_year": "2024",
    })
    row.update(kwargs)
    return row


def crosswalk(rows=None):
    if rows is None:
        rows = [{
            "dfo_country": "Germany", "hanze_iso2": "DE",
            "mapping_evidence_url": "https://example.org/pinned-country-codes",
        }]
    return json.dumps({"schema_version": "dfo-country-hanze-v0", "mappings": rows},
                      separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(value):
    return hashlib.sha256(value).hexdigest()


def link(dfo=None, hanze=None, mapping=None):
    dfo = dfo if dfo is not None else csv_blob(DFO_HEADER, [dfo_row()])
    hanze = hanze if hanze is not None else csv_blob(HANZE_COLUMNS, [hanze_row()])
    mapping = mapping if mapping is not None else crosswalk()
    return link_candidates(dfo, sha(dfo), hanze, sha(hanze), mapping, sha(mapping))


class FloodCandidateLinkTests(unittest.TestCase):
    def test_verified_bytes_temporal_candidates_not_event_identity(self):
        output = link()
        self.assertEqual(output["dfo_event_count"], 1)
        self.assertEqual(output["hanze_event_count"], 1)
        self.assertEqual(output["candidate_pair_count"], 1)
        self.assertTrue(output["dfo_release_date_anomaly"])
        match = output["candidate_pairs"][0]
        self.assertEqual(match["country_iso2_from_supplied_crosswalk"], "DE")
        self.assertEqual(match["dfo_interval"], ["2023-12-30", "2024-01-04"])
        self.assertEqual(match["relationship"], "SAME_COUNTRY_AND_OVERLAPPING_DATES_ONLY")
        for field in ("same_event_confirmed", "independent_reports_confirmed", "losses_joined"):
            self.assertFalse(match[field])
        for field in ("common_event_identity_proven", "source_independence_proven",
                      "geographic_footprint_aligned", "economic_or_insured_loss_joined",
                      "model_input_admitted", "missing_candidate_is_evidence_of_no_disaster"):
            self.assertFalse(output[field])

    def test_nonoverlapping_intervals_are_not_misrepresented_as_zero_disasters(self):
        hanze = csv_blob(HANZE_COLUMNS, [hanze_row(start_date="2023-01-01", end_date="2023-01-03")])
        output = link(hanze=hanze)
        self.assertEqual(output["candidate_pair_count"], 0)
        self.assertEqual(output["mapped_dfo_events_without_overlapping_hanze_dates"], 1)
        self.assertFalse(output["missing_candidate_is_evidence_of_no_disaster"])

    def test_multicountry_unmapped_and_nonmatching_country(self):
        multi = csv_blob(DFO_HEADER, [dfo_row(**{"Country": "Germany • Poland"})])
        output = link(dfo=multi)
        self.assertEqual(output["unmapped_dfo_events"], 1)
        self.assertEqual(output["candidate_pair_count"], 0)
        with self.assertRaisesRegex(LinkageError, "ambiguous"):
            link(dfo=multi, mapping=crosswalk([{
                "dfo_country": "Germany • Poland", "hanze_iso2": "DE",
                "mapping_evidence_url": "https://example.org/countries",
            }]))
        mapping = crosswalk([{
            "dfo_country": "Germany", "hanze_iso2": "FR",
            "mapping_evidence_url": "https://example.org/countries",
        }])
        output = link(mapping=mapping)
        self.assertEqual(output["mapped_dfo_events_with_no_hanze_country"], 1)

    def test_multiple_candidates_are_all_marked_ambiguous(self):
        hanze = csv_blob(HANZE_COLUMNS, [
            hanze_row(id="1001"),
            hanze_row(id="1002", start_date="2024-01-01",
                      end_date="2024-01-02", event_start_date_year="2024"),
        ])
        out = link(hanze=hanze)
        self.assertEqual(out["candidate_pair_count"], 2)
        self.assertEqual([x["hanze_event_id"] for x in out["candidate_pairs"]], ["1001", "1002"])
        self.assertFalse(any(x["same_event_confirmed"] for x in out["candidate_pairs"]))

    def test_checksums_country_schema_and_csv_errors_fail_closed(self):
        dfo = csv_blob(DFO_HEADER, [dfo_row()])
        hanze = csv_blob(HANZE_COLUMNS, [hanze_row()])
        mapping = crosswalk()
        with self.assertRaisesRegex(LinkageError, "DFO.*SHA256"):
            link_candidates(dfo, "0" * 64, hanze, sha(hanze), mapping, sha(mapping))
        with self.assertRaisesRegex(LinkageError, "crosswalk.*SHA256"):
            link_candidates(dfo, sha(dfo), hanze, sha(hanze), mapping, "0" * 64)
        dup = crosswalk([
            {"dfo_country": "Germany", "hanze_iso2": "DE", "mapping_evidence_url": "https://example.org/1"},
            {"dfo_country": "Germany", "hanze_iso2": "DE", "mapping_evidence_url": "https://example.org/2"},
        ])
        with self.assertRaisesRegex(LinkageError, "duplicate DFO country"):
            link(dfo=dfo, hanze=hanze, mapping=dup)
        bad_hanze = csv_blob(HANZE_COLUMNS, [
            hanze_row(start_date="2023-13-01"),
        ])
        with self.assertRaises(ValueError):
            link(hanze=bad_hanze)

    def test_cli_writes_report_without_overwriting_sources(self):
        dfo, hanze, mapping = csv_blob(DFO_HEADER, [dfo_row()]), csv_blob(HANZE_COLUMNS, [hanze_row()]), crosswalk()
        with tempfile.TemporaryDirectory() as path:
            paths = [Path(path) / x for x in ("dfo.csv", "hanze.csv", "country.json")]
            for f, blob in zip(paths, (dfo, hanze, mapping)):
                f.write_bytes(blob)
            output = Path(path) / "report.json"
            base = [sys.executable, str(ROOT / "research_runners/flood_event_link_candidates_v0.py"),
                    "--dfo-csv", str(paths[0]), "--dfo-csv-sha256", sha(dfo),
                    "--hanze-csv", str(paths[1]), "--hanze-csv-sha256", sha(hanze),
                    "--country-crosswalk", str(paths[2]), "--country-crosswalk-sha256", sha(mapping)]
            run = subprocess.run(base + ["--out", str(output)], cwd=ROOT, capture_output=True, text=True, timeout=25)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["candidate_pair_count"], 1)
            fail = subprocess.run(base + ["--out", str(paths[0])], cwd=ROOT, capture_output=True, text=True, timeout=25)
            self.assertNotEqual(fail.returncode, 0)
            self.assertEqual(paths[0].read_bytes(), dfo)


if __name__ == "__main__":
    unittest.main()
