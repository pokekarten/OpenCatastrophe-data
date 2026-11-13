# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Adversarial offline challenges for original DWD measured gusts, no losses."""
from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
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
import ciara2020_dwd_hourly_fx_original_station_observations_v0 as m


def station_description() -> bytes:
    data = [
        "Stations_id von_datum bis_datum Stationshoehe geoBreite geoLaenge Stationsname Bundesland",
        "00001 20000101 20251231 100 51.0000 7.0000 Mockstadt Eins NRW",
        "00002 20100101 20251231 200 51.1000 7.1000 Mockstadt Zwei NRW",
        "00003 19900101 20251231 300 51.2000 7.2000 Mockstadt Drei NRW",
        "00004 20210101 20251231 400 51.0100 7.0100 Future NRW",
        "00005 20100101 20251231 50 48.0000 11.0000 Far away",
    ]
    return ("\n".join(data)+"\n").encode()


def product_zip(station: str, *, badfield: str | None = None,
                invalid_hour: int | None = None, duplicate_hour: int | None = None,
                quality: int = 10) -> bytes:
    name = f"produkt_fx_stunde_{station}_20200101_20201231.txt"
    column = badfield or "FX_911"
    rows = [f"STATIONS_ID;MESS_DATUM;QN_8;{column};eor"]
    for i in range(96):
        date = (m.EVENT_START + m.timedelta(hours=i)).strftime("%Y%m%d%H")
        wind = "-999" if invalid_hour == i else f"{22.0+i*0.01:.2f}"
        rows.append(f"{int(station)};{date};{quality};{wind};eor")
        if duplicate_hour == i:
            rows.append(rows[-1])
    b = BytesIO()
    with zipfile.ZipFile(b,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(name, "\n".join(rows)+"\n")
        z.writestr("Metadaten_Parameter.txt", "Original DWD fictional mock sensor data")
    return b.getvalue()


def index_html() -> bytes:
    entries = [
        f'<a href="stundenwerte_FX_{i:05d}_20000101_20251231_hist.zip">original</a>'
        for i in range(1, 6)
    ]
    return ("<html><body>"+"".join(entries)+"</body></html>").encode()


class FakeResponse(BytesIO):
    status=200
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self.close()


class FakeOpener:
    def __init__(self, data=None):
        self.data = data or {}
        self.called=[]
    def open(self, req, timeout):
        self.called.append((req.full_url, timeout))
        if req.full_url not in self.data:
            raise m.error.URLError("test unexpected origin")
        return FakeResponse(self.data[req.full_url])


class DWDOriginalFX911Station2020Tests(unittest.TestCase):
    def test_official_dwd_source_and_cc_by_license_preflight_dryrun(self):
        receipt=m.dry_run()
        self.assertEqual(receipt["requested_stations"],3)
        self.assertEqual(receipt["requested_2020_study_hours"],96)
        self.assertTrue(receipt["station_metadata_url"].startswith("https://opendata.dwd.de/"))
        self.assertFalse(receipt["DWD_original_stations_fetched"])
        self.assertFalse(receipt["native_GUL_IL_RI_OEP_AEP_admitted"])

    def test_real_date_gated_station_selection_and_radius(self):
        sites=m.station_candidates(station_description())
        self.assertEqual([x["station_id"] for x in sites],["00001","00002","00003"])
        self.assertEqual(sites[0]["latitude_as_publisher_lists_today"],51.0)
        self.assertEqual(sites[0]["distance_to_original_era5_51N_7E_km"],0)
        self.assertLess(sites[2]["distance_to_original_era5_51N_7E_km"], 120)

    def test_historical_link_parser_blocks_nonoriginal_non2020_and_malicious_urls(self):
        source=m.historical_zip_links(index_html())
        self.assertEqual(len(source),5)
        for name in ("https://evil.invalid/a.zip",
                     m.INDEX+"../token",
                     m.INDEX+"stundenwerte_FX_00001_20210101_20251231_hist.zip",
                     m.INDEX+"stundenwerte_FX_00001_20000101_20251231_hist.zip?delete=1"):
            with self.subTest(url=name):
                with self.assertRaises(m.OriginalDWDRejected):
                    m._get_publisher_bytes(name,m.MAX_ZIP,FakeOpener())
        self.assertEqual(m.ZIP_RE.fullmatch("stundenwerte_FX_00001_20000101_20251231_hist.zip") is not None,True)

    def test_original_product_fx911_2020_full96h_and_missing_marker(self):
        good=m.measured_2020_gust_from_original_zip(product_zip("00001"),"00001")
        self.assertEqual(good["original_station_fx911_hourly_valid_count"],96)
        self.assertEqual(good["DWD_QN8_quality_level_hour_counts"],{"10":96})
        self.assertEqual(good["original_station_fx911_missing_marker_count"],0)
        self.assertAlmostEqual(good["measured_2020_02_08_through_11_max_hourly_gust_mps"],22.95)
        self.assertEqual(good["measured_2020_Ciara_window_peak_hour_as_publisher_reports"],"2020021123")
        self.assertTrue(good["observed_station_max_gust_hours_full_96h"])
        partial=m.measured_2020_gust_from_original_zip(product_zip("00001", invalid_hour=6),"00001")
        self.assertEqual(partial["original_station_fx911_hourly_valid_count"],95)
        self.assertEqual(partial["original_station_fx911_missing_marker_count"],1)
        self.assertFalse(partial["observed_station_max_gust_hours_full_96h"])

    def test_duplicate_wrong_station_wrong_variable_bad_zip_rejected(self):
        for bad in (
            (product_zip("00001", badfield="FF"),"00001"),
            (product_zip("00001",duplicate_hour=4),"00001"),
            (product_zip("00001"),"00002"),
            (b"not-zip","00001"),
            (product_zip("00001",quality=12),"00001"),
        ):
            with self.subTest(bad=hashlib.sha256(bad[0]).hexdigest()[:8]):
                with self.assertRaises(m.OriginalDWDRejected):
                    m.measured_2020_gust_from_original_zip(*bad)

    def test_genuine_bounded_original_source_mock_three_station_end_to_end_no_loss(self):
        docs={
            m.STATION_LIST:station_description(),
            m.INDEX:index_html(),
        }
        for i in range(1,4):
            docs[m.INDEX+f"stundenwerte_FX_{i:05d}_20000101_20251231_hist.zip"]=product_zip(f"{i:05d}")
        fake=FakeOpener(docs)
        receipt=m.live_dwd_2020_original_three_stations(opener=fake)
        self.assertEqual(len(fake.called),5)
        self.assertEqual(receipt["station_count"],3)
        self.assertEqual([x["station_id"] for x in receipt["stations"]],["00001","00002","00003"])
        self.assertTrue(receipt["original_DWD_station_winds_measured_not_ERA5_grid_reanalysis"])
        self.assertFalse(receipt["same_station_temporal_spatial_methods_as_ERA5_verified"])
        self.assertFalse(receipt["actual_2020_insurer_losses_or_building_vulnerability_calibrated"])
        self.assertFalse(receipt["native_NextGen_Oasis_GUL_IL_RI_OEP_AEP_admitted"])
        self.assertIn("CC BY 4.0",receipt["source_rights"])
        for station in receipt["stations"]:
            self.assertEqual(len(station["provider_original_zip_sha256"]),64)

    def test_real_original_archive_having_missing_2020_hours_is_skipped_not_approved(self):
        docs={m.STATION_LIST:station_description(), m.INDEX:index_html()}
        for i in range(1,5):
            docs[m.INDEX+f"stundenwerte_FX_{i:05d}_20000101_20251231_hist.zip"]=(
                product_zip(f"{i:05d}", invalid_hour=3) if i == 1 else product_zip(f"{i:05d}")
            )
        # Missing just one (95 valid) is still scientifically usable.
        okay=m.live_dwd_2020_original_three_stations(opener=FakeOpener(docs))
        self.assertEqual(okay["station_count"],3)
        self.assertEqual(okay["historical_station_archive_candidates_checked"],3)
        self.assertEqual(okay["stations"][0]["original_station_fx911_hourly_valid_count"],95)
        # Truly sparse: publisher archive has a 2020 date span, but all
        # 96 FX_911 values are -999. Our code must not claim observations.
        low=product_zip("00001")
        lines=[]
        with zipfile.ZipFile(BytesIO(low)) as z:
            product=[n for n in z.namelist() if n.startswith("produkt_")][0]
            rows=z.read(product).decode().splitlines()
        rows=[rows[0]]+[r.replace(r.split(";")[3], "-999") for r in rows[1:]]
        b=BytesIO()
        with zipfile.ZipFile(b,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(product,"\n".join(rows)+"\n")
        docs[m.INDEX+"stundenwerte_FX_00001_20000101_20251231_hist.zip"]=b.getvalue()
        # Station 00004 is future-only in the *station metadata*, so it
        # cannot substitute just because ZIP index happens to list it.
        with self.assertRaisesRegex(m.OriginalDWDRejected, "too few sufficiently complete"):
            m.live_dwd_2020_original_three_stations(opener=FakeOpener(docs))

    def test_original_dwd_three_real_station_sha_2020_QN3_replay_receipt(self):
        with m.FROZEN_FIRST_REAL_DWD_SOURCE.open("rb") as f:
            original=tomllib.load(f)
        self.assertEqual(original["first_original_live_github_run_id"],43499602678)
        self.assertEqual(original["source_archives_inspected"],4)
        self.assertEqual(original["source_archives_rejected_for_insufficient_2020_hours"],1)
        self.assertEqual(original["rejected_station_id"],"03623")
        self.assertFalse(original["station_QN8_10_highest_quality_met"])
        self.assertFalse(original["DWD_reference_timestamps_UTC_harmonization_verified"])
        self.assertFalse(original["native_Oasis_NextGen_GUL_IL_RI_OEP_AEP_admitted"])
        self.assertEqual([s["station_id"] for s in original["stations"]],
                         ["02667","15200","00603"])
        self.assertEqual([s["observed_2020_96h_peak_gust_mps"]
                          for s in original["stations"]],[26.4,31.1,25.5])
        self.assertTrue(all(s["source_quality_QN8_3_hour_count"] == 96
                            and s["valid_2020_hour_count"] == 96
                            and len(s["original_unmodified_zip_sha256"]) == 64
                            for s in original["stations"]))
        live={
            "status":original["status"],
            "source_variable":"FX_911",
            "units":"m/s",
            "station_count":3,
            "historic_reference_time_interpretation_verified_as_UTC":False,
            "actual_2020_insurer_losses_or_building_vulnerability_calibrated":False,
            "native_NextGen_Oasis_GUL_IL_RI_OEP_AEP_admitted":False,
            "historical_station_archive_candidates_checked":4,
            "skipped_original_archives_due_to_insufficient_2020_gust_coverage":[{
                "original_station_id":original["rejected_station_id"],
                "original_station_zip_sha256":original["rejected_original_zip_sha256"],
            }],
            "stations":[{
                "station_id":site["station_id"],
                "original_DWD_historical_FX_zip_url":site["original_archive_url"],
                "provider_original_zip_sha256":site["original_unmodified_zip_sha256"],
                "latitude_as_publisher_lists_today":site["current_publisher_latitude"],
                "longitude_as_publisher_lists_today":site["current_publisher_longitude"],
                "distance_to_original_era5_51N_7E_km":site["distance_to_51N_7E_km"],
                "measured_2020_Ciara_window_peak_hour_as_publisher_reports":site["published_2020_peak_hour_label"],
                "measured_2020_02_08_through_11_max_hourly_gust_mps":site["observed_2020_96h_peak_gust_mps"],
                "original_station_fx911_hourly_valid_count":site["valid_2020_hour_count"],
                "original_station_fx911_missing_marker_count":site["missing_original_value_count"],
                "DWD_QN8_quality_level_hour_counts":{"3":96},
                "observed_station_max_gust_hours_full_96h":True,
            } for site in original["stations"]],
        }
        self.assertIsNone(m.verify_first_original_2020_station_receipt_against_live(live))
        for name,field,new_value in (
            ("gust","measured_2020_02_08_through_11_max_hourly_gust_mps",99.0),
            ("zip","provider_original_zip_sha256","0"*64),
            ("2020qc","DWD_QN8_quality_level_hour_counts",{"10":96}),
            ("hours","original_station_fx911_hourly_valid_count",95),
        ):
            with self.subTest(name=name):
                altered=deepcopy(live)
                altered["stations"][1][field]=new_value
                with self.assertRaises(m.OriginalDWDRejected):
                    m.verify_first_original_2020_station_receipt_against_live(altered)
        altered=deepcopy(live)
        altered["actual_2020_insurer_losses_or_building_vulnerability_calibrated"]=True
        with self.assertRaises(m.OriginalDWDRejected):
            m.verify_first_original_2020_station_receipt_against_live(altered)

    def test_source_dry_run_never_accesses_network(self):
        with patch.object(sys,"argv",["prog","--dry-run"]),\
             patch.object(m,"live_dwd_2020_original_three_stations",
                          side_effect=AssertionError("DWD NETWORK FORBIDDEN")):
            out=StringIO()
            with redirect_stdout(out):
                self.assertEqual(m.main(),0)
            result=json.loads(out.getvalue())
            self.assertFalse(result["DWD_original_stations_fetched"])


if __name__=="__main__":
    unittest.main()
