# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline adversarial gates for ACTUAL Feb 2020 DWD source geography/UTC."""
from __future__ import annotations
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tomllib
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
import ciara2020_dwd_historical_feb2020_station_attestation_v0 as m


def test_geo():
    return (
        "Stations_id;Stationshoehe;Geogr.Breite;Geogr.Laenge;von_datum;bis_datum;Stationsname\n"
        "603; 159.00; 50.7350;7.1931;19900101;20200930;Koenigswinter-Heiderhof\n"
        "603; 147.17; 50.7293;7.2040;20201001;        ;Koenigswinter-Heiderhof\n"
    ).encode("cp1252")


def test_device():
    return (
        "Stations_ID;Stationsname;Geo. Laenge [Grad];Geo. Breite [Grad];Stationshoehe [m];Geberhoehe ueber Grund [m];Von_Datum;Bis_Datum;Geraetetyp Name;Messverfahren;eor;\n"
        "603;Koenigswinter-Heiderhof;7.19;50.74;159;10;20191002;20200930;Windsensor Classic 4.3303;Windmessung, elektr.;eor;\n"
        "603;Koenigswinter-Heiderhof;7.2;50.73;147.17;12;20201001;20260419;Ultrasonic Anemometer 2D compact;Windmessung, elektr.;eor;\n"
        "generiert: 24.04.2026 --  Deutscher Wetterdienst  --\n"
    ).encode("cp1252")


def test_parameter():
    return (
        "Stations_ID;Von_Datum;Bis_Datum;Stationsname;Parameter;Parameterbeschreibung;Einheit;Datenquelle (Strukturversion=SV);Zusatz-Info;Besonderheiten;Literaturhinweis;eor;\n"
        "603;20010403;20260418;Koenigswinter-Heiderhof;FX_911;hoechste Windspitze der letzten Stunde;m/sec;SYNOP source;in UTC;;;eor;\n"
        "Legende: FT=Folgetag\n"
    ).encode("cp1252")


class DWDHistoricalFeb2020TrueSiteAttestationTests(unittest.TestCase):
    def test_real_nine_historical_source_member_shas_and_no_loss_flags(self):
        with m.ORIGINAL_RESEARCH.open("rb") as f:
            r=tomllib.load(f)
        self.assertEqual(r["schema"],m.SCHEMA)
        self.assertEqual(r["first_original_metadata_github_run_id"],43605892890)
        self.assertEqual([x["station_id"] for x in r["stations"]],list(m.SUPPORTED_IDS))
        self.assertTrue(r["source_original_DWD_FX911_UTC_reference_hour_label_attested"])
        self.assertFalse(r["ERA5_10fg_time_support_aggregation_equal_to_DWD_FX911_verified"])
        self.assertFalse(r["native_catastrophe_GUL_IL_RI_OEP_AEP_or_SCR_admitted"])
        self.assertEqual([x["feb2020_wind_anemometer_height_above_ground_m"]
                          for x in r["stations"]],[10,12,10])
        self.assertEqual([x["feb2020_latitude"] for x in r["stations"]],[50.8645,51.2531,50.735])
        self.assertEqual(r["stations"][2]["after_event_station_move_effective"],"20201001")
        self.assertEqual(r["stations"][2]["nearest_original_era5_grid_distance_km"],4.337)
        self.assertTrue(all(len(s[k])==64 for s in r["stations"]
                            for k in ("original_zip_sha256","geo_member_sha256",
                                      "device_member_sha256","parameter_member_sha256")))

    def test_original_historical_geography_selects_feb_2020_not_oct_move(self):
        rows=m._metadata_rows(test_geo(),"geographie","00603")
        self.assertEqual(len(rows),2)
        active=m._active_unique(rows,"von_datum","bis_datum")
        self.assertEqual(active["Geogr.Breite"],"50.7350")
        self.assertEqual(active["Geogr.Laenge"],"7.1931")
        self.assertEqual(active["Stationshoehe"],"159.00")
        self.assertEqual(active["bis_datum"],"20200930")

    def test_original_device_selects_10m_windsensor_not_post_event_12m(self):
        rows=m._metadata_rows(test_device(),"geraete","00603")
        active=m._active_unique(rows,"Von_Datum","Bis_Datum")
        self.assertEqual(active["Geberhoehe ueber Grund [m]"],"10")
        self.assertEqual(active["Geraetetyp Name"],"Windsensor Classic 4.3303")
        self.assertEqual(active["Bis_Datum"],"20200930")
        self.assertNotEqual(active["Geraetetyp Name"],"Ultrasonic Anemometer 2D compact")

    def test_original_parameter_source_states_UTC_previous_hour_not_ERA5_identity(self):
        rows=m._metadata_rows(test_parameter(),"parameter","00603")
        active=m._active_unique(rows,"Von_Datum","Bis_Datum")
        self.assertEqual(active["Zusatz-Info"],"in UTC")
        self.assertEqual(active["Parameterbeschreibung"],
                         "hoechste Windspitze der letzten Stunde")
        self.assertEqual(active["Parameter"],"FX_911")
        self.assertNotIn("ERA5",str(active))

    def test_overlaps_gaps_wrong_station_UTC_and_numeric_nonfinite_rejected(self):
        g=m._metadata_rows(test_geo(),"geographie","00603")
        duplicate=[g[0],dict(g[0])]
        with self.assertRaises(m.HistoricalDWDNoGo):
            m._active_unique(duplicate,"von_datum","bis_datum")
        gap=[{**g[0],"bis_datum":"20200209"},g[1]]
        with self.assertRaises(m.HistoricalDWDNoGo):
            m._active_unique(gap,"von_datum","bis_datum")
        with self.assertRaises(m.HistoricalDWDNoGo):
            m._metadata_rows(test_geo().replace(b"603;",b"777;"),"geographie","00603")
        bad=test_parameter().replace(b"in UTC",b"in GZ ")
        self.assertNotEqual(m._active_unique(
            m._metadata_rows(bad,"parameter","00603"),"Von_Datum","Bis_Datum"
        )["Zusatz-Info"],"in UTC")
        for num in ("NaN","Infinity","not-a-number"):
            with self.subTest(value=num):
                with self.assertRaises(m.HistoricalDWDNoGo):
                    m._safe_decimal(num)

    def test_dry_run_never_treats_original_metadata_as_loaded(self):
        with patch.object(sys,"argv",["attest","--dry-run"]),\
             patch.object(m,"live_feb2020_attestation",
                          side_effect=AssertionError("NO ORIGINAL SOURCE READ")):
            buf=StringIO()
            with redirect_stdout(buf):
                self.assertEqual(m.main(),0)
        receipt=json.loads(buf.getvalue())
        self.assertFalse(receipt["historical_site_sensor_hour_UTC_attested_by_this_run"])
        self.assertFalse(receipt["insurer_loss_model_approved"])


if __name__=="__main__":
    unittest.main()
