# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Adversarial original-DWD-SHA inventory tests use synthetic ZIP fixtures."""
from __future__ import annotations

from contextlib import redirect_stdout
from io import BytesIO, StringIO
import hashlib
import json
from pathlib import Path
import sys
import tomllib
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import ciara2020_dwd_original_2020_station_metadata_inventory_v0 as m


def source_zip(*, missing=None, extra=None, malicious=None):
    out = BytesIO()
    fields = {
        "Metadaten_Geographie_02667.txt": "Stations-ID 02667; geography; origin; valid_from; valid_to\n2020-02-09; 50.8; 7.1\n",
        "Metadaten_Geraete_02667.txt": "Stations-ID 02667; instrument; height; historical from/to\n2020-02-09; 10m; anemometer\n",
        "Metadaten_Parameter_02667.txt": "Stations-ID 02667; param; source; reference; quality\nFX_911; hourly gust; reference not verified\n",
        "produkt_fx_stunde_02667.txt": "STATIONS_ID;MESS_DATUM;QN_8;FX_911\n02667;2020020800;3;20.2\n",
    }
    if missing:
        fields.pop(missing)
    if extra:
        fields[extra] = "some header\nreal test row\n"
    if malicious:
        fields[malicious] = "some header\nreal test row\n"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, content in fields.items():
            z.writestr(name, content)
    return out.getvalue()


class DWDOriginalMetadataResearchTests(unittest.TestCase):
    def test_three_frozen_real_DWD_sources_2020_station_identity(self):
        with m.dwd.FROZEN_FIRST_REAL_DWD_SOURCE.open("rb") as fd:
            r = tomllib.load(fd)
        self.assertEqual([x["station_id"] for x in r["stations"]],
                         ["02667", "15200", "00603"])
        self.assertTrue(all(len(x["original_unmodified_zip_sha256"]) == 64
                            for x in r["stations"]))
        self.assertFalse(r["DWD_reference_timestamps_UTC_harmonization_verified"])
        self.assertFalse(r["station_2020_vs_current_geography_instrument_metadata_verified"])

    def test_finite_original_source_zip_returns_metadata_sha_not_unverified_dates(self):
        raw = source_zip()
        receipt = m.inspect_original_metadata_zip(raw, "02667")
        self.assertEqual(receipt["original_archive_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(set(receipt["metadata"]), set(m.REQUIRED_CATEGORIES))
        self.assertTrue(all(len(v["original_member_sha256"]) == 64
                            for v in receipt["metadata"].values()))
        self.assertIn("reference not verified",
                      " ".join(receipt["metadata"]["parameter"][
                          "bounded_publisher_original_first_lines_uninterpreted"
                      ]))
        self.assertNotIn("original_2020_geography_valid_from_to_interpreted", receipt)

    def test_official_zip_can_contain_harmless_additional_original_docs(self):
        zip_bytes = source_zip(extra="citation_documentation.pdf")
        proof = m.inspect_original_metadata_zip(zip_bytes, "02667")
        self.assertEqual(set(proof["metadata"]), set(m.REQUIRED_CATEGORIES))
        self.assertEqual(len(proof["original_archive_sha256"]), 64)

    def test_wrong_zip_member_structure_or_metadata_type_fails_closed(self):
        cases = (
            b"fake original publisher ZIP",
            source_zip(missing="Metadaten_Geraete_02667.txt"),
            source_zip(extra="Metadaten_Parameter_additional.txt"),
            source_zip(malicious="../Metadaten_Parameter_outside.txt"),
            source_zip(malicious="a/Metadaten_Geraete_bad.txt"),
        )
        for i, data in enumerate(cases):
            with self.subTest(case=i):
                with self.assertRaises(m.DWDMetadataBlocked):
                    m.inspect_original_metadata_zip(data, "02667")

    def test_invalid_station_identity_and_bounded_bytes_no_go(self):
        blob = source_zip()
        for bad in ("1", "02667;", "../02667", "026670", ""):
            with self.subTest(id=bad):
                with self.assertRaises(m.DWDMetadataBlocked):
                    m.inspect_original_metadata_zip(blob, bad)
        with self.assertRaises(m.DWDMetadataBlocked):
            m.inspect_original_metadata_zip(b"x" * (m.dwd.MAX_ZIP + 1), "02667")

    def test_dry_run_no_external_source_download(self):
        with patch.object(sys, "argv", ["prog", "--dry-run"]), \
             patch.object(m, "inspect_live_original_three_2020_stations",
                          side_effect=AssertionError("network access forbidden")):
            out = StringIO()
            with redirect_stdout(out):
                self.assertEqual(m.main(), 0)
        obj = json.loads(out.getvalue())
        self.assertFalse(obj["publisher_original_station_metadata_read"])
        self.assertFalse(obj["2020_site_instrument_or_UTC_validated"])
        self.assertFalse(obj["calibrated_model_or_insured_losses_admitted"])


if __name__ == "__main__":
    unittest.main()
