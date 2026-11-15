# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests of NGI/GA global tsunami PTHA reader; no provider bytes."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from research_runners.ngi_global_ptha_preflight_v0 import audit, InvalidOriginal, RATES, HEIGHTS

class TsunamiPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic.txt"

    def run_sample(self, mutate=None, alias="ari500ZL"):
        hdr = ["FID", *RATES, *HEIGHTS, "ari500P", "ari500M", "ari500LL", alias, "POINT_X", "POINT_Y"]
        vals = ["0", *(str(v) for v in (0.1, 0.08, 0.06, 0.04, 0.03, 0.02, 0.01, 0.005, 0.001)),
                *(str(v) for v in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7)), "0.8", "0.4", "0.5", "0.5", "190.0", "30.0"]
        fields=dict(zip(hdr,vals))
        if mutate:
            fields.update(mutate)
        body=";".join(hdr)+"\n"+";".join(fields[k] for k in hdr)+"\n"
        self.path.write_text(body, encoding="utf-8")
        return hashlib.md5(self.path.read_bytes()).hexdigest()

    def test_good_and_0_360_longitude(self):
        md5=self.run_sample()
        result=audit(self.path,expected_md5=md5)
        self.assertEqual(result["status"],"parsed_with_no_flagged_anomalies")
        self.assertEqual(result["checks"]["longitudes_using_0_to_360"],1)
        self.assertEqual(result["zero_sigma_column"],"ari500ZL")
        self.assertEqual(result["checks"]["left_censored_0p1m"],1)

    def test_both_header_spellings(self):
        md5=self.run_sample(alias="ari500LZ")
        self.assertEqual(audit(self.path,expected_md5=md5)["zero_sigma_column"],"ari500LZ")

    def test_original_checksum_cannot_be_skipped(self):
        self.run_sample()
        with self.assertRaisesRegex(InvalidOriginal,"publisher_md5_mismatch"):
            audit(self.path)

    def test_quality_not_admission(self):
        md5=self.run_sample({"rate_500":"0.2", "ari500M":"0.9"})
        result=audit(self.path,expected_md5=md5)
        self.assertEqual(result["status"],"quality_anomalies")
        self.assertEqual(result["admission"],"none")
        self.assertEqual(result["checks"]["nonmonotonic_exceedance_rates"],1)
        self.assertEqual(result["checks"]["point_outside_95pct_bounds"],1)

    def append_second_site(self, *, longitude="-170.0", rate_25=None):
        """Append a fully synthetic second FID; original-provider bytes are never used."""
        lines = self.path.read_text(encoding="utf-8").splitlines()
        header = lines[0].split(";")
        fields = dict(zip(header, lines[1].split(";")))
        fields["FID"] = "1"
        fields["POINT_X"] = longitude
        if rate_25 is not None:
            fields["rate_25"] = str(rate_25)
        lines.append(";".join(fields[col] for col in header))
        self.path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
        return hashlib.md5(self.path.read_bytes()).hexdigest()

    def test_duplicate_site_across_longitude_conventions_is_an_anomaly(self):
        self.run_sample()  # Original synthetic x=190E, y=30N.
        checksum = self.append_second_site(longitude="-170.0")
        result = audit(self.path, expected_md5=checksum)
        self.assertEqual(result["status"], "quality_anomalies")
        self.assertEqual(result["admission"], "none")
        self.assertEqual(result["checks"]["rows"], 2)
        self.assertEqual(result["checks"]["duplicate_spatial_sites"], 1)
        self.assertEqual(result["checks"]["duplicate_spatial_sites_conflicting_curves"], 0)
        self.assertNotIn("-170.0", str(result))  # Aggregate-only reporting.

    def test_conflicting_duplicate_hazard_curves_are_counted_separately(self):
        self.run_sample()
        checksum = self.append_second_site(rate_25=0.061)
        result = audit(self.path, expected_md5=checksum)
        self.assertEqual(result["status"], "quality_anomalies")
        self.assertEqual(result["checks"]["duplicate_spatial_sites"], 1)
        self.assertEqual(result["checks"]["duplicate_spatial_sites_conflicting_curves"], 1)
        self.assertEqual(result["admission"], "none")

    def test_distinct_sites_do_not_produce_false_duplicate_flags(self):
        self.run_sample()
        checksum = self.append_second_site(longitude="-171.0")
        result = audit(self.path, expected_md5=checksum)
        self.assertEqual(result["status"], "parsed_with_no_flagged_anomalies")
        self.assertEqual(result["checks"]["duplicate_spatial_sites"], 0)
        self.assertEqual(result["checks"]["duplicate_spatial_sites_conflicting_curves"], 0)

    def test_antimeridian_180_and_minus_180_are_the_same_site(self):
        self.run_sample({"POINT_X": "180.0"})
        checksum = self.append_second_site(longitude="-180.0")
        result = audit(self.path, expected_md5=checksum)
        self.assertEqual(result["checks"]["duplicate_spatial_sites"], 1)
        self.assertEqual(result["admission"], "none")

    def test_fail_closed_missing_and_nonfinite(self):
        md5=self.run_sample({"ari100":"nan"})
        with self.assertRaisesRegex(InvalidOriginal,"non_finite_original_field"):
            audit(self.path, expected_md5=md5)
        md5=self.run_sample({"ari100":""})
        with self.assertRaisesRegex(InvalidOriginal,"row_fields_missing"):
            audit(self.path, expected_md5=md5)

if __name__=="__main__":
    unittest.main()
