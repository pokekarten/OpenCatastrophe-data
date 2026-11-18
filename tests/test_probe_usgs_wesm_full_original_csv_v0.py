# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic original WESM complete CSV: hash, identity, quality, privacy tests."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from unittest.mock import patch
import unittest

from scripts import probe_usgs_wesm_full_original_csv_v0 as s


FIELDS = [
    "workunit_id", "project_id", "lpc_category",
    "sourcedem_category", "seamless_category", "seamless_reason",
] + [f"field_{i}" for i in range(22)]


def mock_source(rows=None):
    if rows is None:
        rows = [
            ["synthetic-WU-001", "synthetic-project", "Meets",
             "Meets", "Meets", "Meets 3DEP seamless requirements"],
            ["synthetic-WU-002", "synthetic-project", "Meets",
             "Meets", "Pending publication", "Awaiting final absolute vertical accuracy assessment"],
            ["synthetic-WU-002", "synthetic-project", "Meets",
             "Meets", "Meets with variance", "LPC meets v.1.0 or earlier draft specification"],
            ["synthetic-WU-004", "synthetic-project", "Meets",
             "Meets", "UNVERIFIED CUSTOM LABEL", "unexpected"],
        ]
    a = [",".join(FIELDS)]
    for r in rows:
        a.append(",".join(r + [""] * 22))
    return ("\n".join(a) + "\n").encode("utf-8")


class Response:
    def __init__(self, body, status=200, url=s.URL,
                 mime="application/octet-stream", length=None, encoding="identity"):
        self.body = body
        self.status = status
        self.url = url
        self.headers = {"Content-Type":mime,"Content-Encoding":encoding}
        if length is not None:
            self.headers["Content-Length"] = str(length)
        self.reads=0
    def geturl(self): return self.url
    def read(self, n):
        self.reads += 1
        return self.body[:n]
    def __enter__(self): return self
    def __exit__(self, *_): return False


class FullOriginalWESMTests(unittest.TestCase):
    def test_reviews_exact_provider_and_is_not_model_admission(self):
        self.assertEqual(len(s.validate_contract()),64)
        self.assertEqual(s.EXPECTED_BYTES,2267051)
        self.assertEqual(s.PREFIX_SHA,
            "19e025e68687bbb2b61d7f58a5eeedfa6d59b29a9ba98aa159556cc801e6eb8d")
        self.assertEqual(s.URL,"https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/WESM.csv")

    def test_known_unknown_and_repeated_workunit_source_counts_not_approvals(self):
        data = mock_source()
        expected_header_sha = hashlib.sha256("\n".join(FIELDS).encode()).hexdigest()
        with patch.object(s, "HEADER_NAMES_SHA", expected_header_sha):
            out = s.summarize_original_csv(data)
        self.assertEqual(out["original_wesm_data_row_count"],4)
        self.assertEqual(out["original_wesm_header_columns"],28)
        self.assertEqual(out["duplicate_workunit_id_occurrences"],1)
        self.assertEqual(out["duplicate_workunit_project_row_occurrences"],1)
        self.assertEqual(out["reused_workunit_id_other_project_occurrences"],0)
        self.assertEqual(out["reused_workunit_id_conflicting_seamless_category_occurrences"],1)
        self.assertFalse(out["workunit_duplicate_structure_scientifically_resolved"])
        self.assertTrue(out["has_unrecognized_seamless_quality_status"])
        self.assertEqual(out["original_wesm_seamless_quality_category_counts"]["Meets"],1)
        self.assertEqual(out["original_wesm_seamless_quality_category_counts"]["unknown_or_blank"],1)
        self.assertFalse(out["all_original_quality_rows_scientifically_approved"])
        self.assertNotIn("synthetic-WU",str(out))

    def test_full_fake_source_request_only_reports_sha_aggregate_and_utc(self):
        data = mock_source()
        reply = Response(data,length=len(data))
        requests=[]
        def opener(req, timeout):
            requests.append((req.full_url,req.get_method(),timeout))
            return reply
        with patch.object(s,"validate_contract",return_value="f"*64), \
             patch.object(s,"HEADER_NAMES_SHA",hashlib.sha256("\n".join(FIELDS).encode()).hexdigest()), \
             patch.object(s,"EXPECTED_BYTES",len(data)), \
             patch.object(s,"PREFIX_BYTES",64), \
             patch.object(s,"PREFIX_SHA",hashlib.sha256(data[:64]).hexdigest()), \
             patch.object(s,"EXPECTED_FULL_SHA",hashlib.sha256(data).hexdigest()):
            output=s.observe(opener=opener,clock=lambda:datetime(2026,11,16,tzinfo=timezone.utc))
        self.assertEqual(requests,[(s.URL,"GET",s.TIMEOUT)])
        self.assertEqual(output["original_complete_csv_sha256"],hashlib.sha256(data).hexdigest())
        self.assertEqual(reply.reads,1)
        self.assertEqual(output["original_wesm_data_row_count"],4)
        for field in ("original_geopackage_spatial_geometry_verified",
                      "source_workunit_to_exact_florida_s1m_tile_verified",
                      "original_s1m_pixel_lidar_quality_verified",
                      "original_raw_provider_csv_bytes_persisted","neon_write_performed",
                      "cat_model_input_approved"):
            self.assertFalse(output[field])
        self.assertNotIn("synthetic-WU",str(output))

    def test_original_full_csv_mismatch_blocks_before_parsing(self):
        data=mock_source()
        with patch.object(s,"validate_contract",return_value="f"*64), \
             patch.object(s,"EXPECTED_BYTES",len(data)), \
             patch.object(s,"PREFIX_BYTES",64):
            with self.assertRaisesRegex(s.Blocked,"previously verified"):
                s.observe(opener=lambda req,timeout:Response(data,length=len(data)))
            with patch.object(s,"PREFIX_SHA",hashlib.sha256(data[:64]).hexdigest()):
                with self.assertRaisesRegex(s.Blocked,"complete original WESM CSV SHA256 changed"):
                    s.observe(opener=lambda req,timeout:Response(data,length=len(data)))
            with self.assertRaisesRegex(s.Blocked,"Content-Length"):
                s.observe(opener=lambda req,timeout:Response(data,length=len(data)+1))
            with self.assertRaisesRegex(s.Blocked,"complete byte length"):
                s.observe(opener=lambda req,timeout:Response(data[:-1],length=None))
            bad=Response(data,status=206)
            with self.assertRaisesRegex(s.Blocked,"HTTP 200"):
                s.observe(opener=lambda req,timeout:bad)
            self.assertEqual(bad.reads,0)

    def test_malformed_csv_and_header_fail_closed(self):
        source=mock_source()
        for raw in (b"",b"\xff"*100,source.replace(b"workunit_id",b"workunit_x",1),
                    mock_source([["tiny"]]),source.replace(b"seamless_category",b"other_column",1)):
            with self.subTest(raw=raw[:40]),self.assertRaises(s.Blocked):
                s.summarize_original_csv(raw)
        with patch.object(s,"HEADER_NAMES_SHA",hashlib.sha256("\n".join(FIELDS).encode()).hexdigest()):
            with self.assertRaisesRegex(s.Blocked,"row count or column shape"):
                s.summarize_original_csv(mock_source([["bad"]]))

    def test_cli_never_runs_network_without_explicit_opt_in(self):
        with patch("sys.argv",["probe-usgs-wesm"]):
            with self.assertRaises(SystemExit) as err:
                s.main()
        self.assertEqual(err.exception.code,2)


if __name__=="__main__":
    unittest.main()
