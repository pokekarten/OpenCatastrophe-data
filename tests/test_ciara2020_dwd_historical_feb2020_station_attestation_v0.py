# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline coverage for event-period DWD station attestation."""
from __future__ import annotations

from io import BytesIO
import hashlib
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import ciara2020_dwd_historical_feb2020_station_attestation_v0 as m


GEO = (
    "Stations_id;Stationshoehe;Geogr.Breite;Geogr.Laenge;von_datum;bis_datum;Stationsname\n"
    "603;159.00;50.7350;7.1931;19900101;20200930;Königswinter-Heiderhof\n"
).encode("cp1252")
DEVICE = (
    "Stations_ID;Stationsname;Geo. Laenge [Grad];Geo. Breite [Grad];Stationshoehe [m];"
    "Geberhoehe ueber Grund [m];Von_Datum;Bis_Datum;Geraetetyp Name;Messverfahren;eor\n"
    "603;Königswinter-Heiderhof;7.19;50.74;159;10;20191002;20200930;"
    "Windsensor Classic 4.3303;Windmessung, elektr.;eor\n"
).encode("cp1252")
PARAM = (
    "Stations_ID;Von_Datum;Bis_Datum;Stationsname;Parameter;Parameterbeschreibung;Einheit;"
    "Datenquelle (Strukturversion=SV);Zusatz-Info;Besonderheiten;Literaturhinweis;eor\n"
    "603;20010403;20260418;Königswinter-Heiderhof;FX_911;"
    "hoechste Windspitze der letzten Stunde;m/sec;DWD SYNOP;in UTC;;;eor\n"
).encode("cp1252")


def source_zip(parameter: bytes = PARAM) -> bytes:
    out = BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Metadaten_Geographie_00603.txt", GEO)
        archive.writestr("Metadaten_Geraete_Maxwind_00603.txt", DEVICE)
        archive.writestr("Metadaten_Parameter_fx_stunde_00603.txt", parameter)
    return out.getvalue()


def pinned(raw: bytes) -> dict:
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        members = {
            "geo_member_sha256": hashlib.sha256(archive.read("Metadaten_Geographie_00603.txt")).hexdigest(),
            "device_member_sha256": hashlib.sha256(archive.read("Metadaten_Geraete_Maxwind_00603.txt")).hexdigest(),
            "parameter_member_sha256": hashlib.sha256(archive.read("Metadaten_Parameter_fx_stunde_00603.txt")).hexdigest(),
        }
    return {
        "station_id": "00603",
        "original_zip_sha256": hashlib.sha256(raw).hexdigest(),
        **members,
        "feb2020_latitude": 50.735,
        "feb2020_longitude": 7.1931,
        "feb2020_station_elevation_m": 159.0,
        "feb2020_wind_anemometer_height_above_ground_m": 10.0,
        "feb2020_instrument_type": "Windsensor Classic 4.3303",
        "feb2020_measurement_procedure": "Windmessung, elektr.",
        "feb2020_geo_valid_from": "19900101",
        "feb2020_geo_valid_to": "20200930",
        "feb2020_device_valid_from": "20191002",
        "feb2020_device_valid_to": "20200930",
        "feb2020_parameter_valid_from": "20010403",
        "feb2020_hour_reference": "in UTC",
        "feb2020_gust_reference": "hoechste Windspitze der letzten Stunde",
        "2020_original_era5_comparison_grid_lat": 50.75,
        "2020_original_era5_comparison_grid_lon": 7.25,
        "nearest_original_era5_grid_distance_km": 4.337,
    }


class DWDHistoricalAttestationTests(unittest.TestCase):
    def test_attests_historical_site_instrument_and_utc_hour_semantics(self):
        raw = source_zip()
        result = m.attest_original_zip("00603", raw, pinned(raw))
        self.assertEqual(result["original_DWD_station_latitude_as_of_Feb2020"], 50.735)
        self.assertEqual(result["original_FX911_anemometer_height_above_ground_m_as_of_Feb2020"], 10.0)
        self.assertTrue(result["original_DWD_FX911_hour_label_declared_UTC"])
        self.assertTrue(result["original_DWD_FX911_gust_highest_during_previous_hour"])
        self.assertFalse(result["DWD_FX911_exact_same_postprocess_window_as_ERA5_10fg_verified"])

    def test_rejects_local_time_even_with_current_source_hash_pins(self):
        changed = PARAM.replace(b"in UTC", b"local time")
        raw = source_zip(changed)
        with self.assertRaisesRegex(m.HistoricalDWDNoGo, "UTC"):
            m.attest_original_zip("00603", raw, pinned(raw))

    def test_rejects_metadata_interval_not_covering_all_four_days(self):
        changed_geo = GEO.replace(b"20200930", b"20200209")
        out = BytesIO()
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("Metadaten_Geographie_00603.txt", changed_geo)
            archive.writestr("Metadaten_Geraete_Maxwind_00603.txt", DEVICE)
            archive.writestr("Metadaten_Parameter_fx_stunde_00603.txt", PARAM)
        raw = out.getvalue()
        with self.assertRaisesRegex(m.HistoricalDWDNoGo, "exactly one"):
            m.attest_original_zip("00603", raw, pinned(raw))

    def test_rejects_original_archive_hash_or_station_identity_drift(self):
        raw = source_zip()
        record = pinned(raw)
        with self.assertRaisesRegex(m.HistoricalDWDNoGo, "SHA"):
            m.attest_original_zip("00603", raw + b"x", record)
        with self.assertRaisesRegex(m.HistoricalDWDNoGo, "identity"):
            m.attest_original_zip("02667", raw, record)


if __name__ == "__main__":
    unittest.main()
