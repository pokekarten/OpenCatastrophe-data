# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
import climk_era5_dwd_spatial_station_candidate_screen_v0 as screen
import climk_era5_dwd_50event_station_audit_v0 as audit


def fixture_windows():
    return [{
        "dwd_hourly_gust_qn":[[20.0,3] for _ in range(72)],
        "climk_72h_gust_mps":18.0,
        "era5_grid_node":[50.75,7.25],
        "sensor_height_m":10.0,
        "station_elevation_m":100.0,
        "historical_metadata_verified":True,
    } for _ in range(50)]


class CLIMKDWDSpatialCandidateScreenTests(unittest.TestCase):
    def test_manifest_has_15_unique_hash_pinned_station_archives(self):
        manifest=screen.load_manifest()
        self.assertEqual(len(manifest["candidate_archives"]),15)
        self.assertEqual(len({x["station_id"] for x in manifest["candidate_archives"]}),15)
        self.assertTrue(all(len(x["sha256"])==64 for x in manifest["candidate_archives"]))
        self.assertFalse(manifest["model_skill_admitted"])
        self.assertFalse(manifest["annual_frequency_or_oep_aep_admitted"])

    def test_station_list_and_archive_index_require_exact_frozen_membership(self):
        manifest=screen.load_manifest()
        header="Stations_id von_datum bis_datum Stationshoehe geoBreite geoLaenge Stationsname Bundesland Abgabe"
        lines=[header,"----------- --------- --------- ------------- --------- --------- ----------------------------------------- ---------- ------"]
        for item in manifest["candidate_archives"]:
            match=screen.dwd.ZIP_RE.fullmatch(item["filename"])
            lines.append(f"{item['station_id']} {match.group(2)} {match.group(3)} 100 50.0000 8.0000 Candidate State Frei")
        for offset in range(549):
            station=f"{10000+offset:05d}"
            lines.append(f"{station} 19900101 20251231 100 50.0000 8.0000 Other State Frei")
        station_list=("\n".join(lines)+"\n").encode("cp1252")
        candidate_links=[x["filename"] for x in manifest["candidate_archives"]]
        index_links=candidate_links+[f"stundenwerte_FX_{20000+i:05d}_19900101_20251231_hist.zip" for i in range(433)]
        index=b"synthetic index"
        class Hash:
            def __init__(self,value): self.value=value
            def hexdigest(self): return self.value
        with patch.object(screen.hashlib,"sha256",side_effect=[
            Hash(manifest["dwd_station_list_sha256"]),Hash(manifest["dwd_historical_index_sha256"])
        ]), patch.object(screen.dwd,"LinkIndex") as parser:
            parser.return_value.links=index_links
            roster=screen._listed_sources(station_list,index,manifest)
        self.assertEqual(roster,{"station_list_data_rows":564,
                                 "historical_hourly_FX_zip_archive_links":448})

        # A source listing that no longer matches its frozen digest blocks.
        changed=deepcopy(manifest)
        changed["dwd_station_list_sha256"]="0"*64
        with patch.object(screen.hashlib,"sha256",side_effect=[Hash("1"*64),Hash("2"*64)]), \
             patch.object(screen.dwd,"LinkIndex") as parser:
            parser.return_value.links=index_links
            with self.assertRaises(screen.CandidateScreenBlocked):
                screen._listed_sources(station_list,index,changed)

    def test_audit_emits_station_aggregates_only_and_fails_source_hash_drift(self):
        manifest=deepcopy(screen.load_manifest())
        source=b"synthetic pinned CLIMK bytes"
        manifest["climk_source_sha256"]="a"*64
        station_list=b"station list"
        index=b"directory"
        archives={}
        for item in manifest["candidate_archives"]:
            raw=("archive-"+item["station_id"]).encode()
            item["sha256"]=hashlib.sha256(raw).hexdigest()
            archives[item["station_id"]]=raw
        with patch.object(screen,"verify_source_bytes",return_value={"sha256_observed":"a"*64}), \
             patch.object(screen,"_listed_sources",return_value={"station_list_data_rows":564,
                                                                  "historical_hourly_FX_zip_archive_links":448}), \
             patch.object(audit,"_rows_from_metadata",return_value={}), \
             patch.object(audit,"_parse_original_hourly",return_value={}), \
             patch.object(audit,"_climk_station_windows",return_value=(fixture_windows(),["20000101"]*50)):
            receipt=screen.audit_candidate_sources(source,station_list,index,archives,manifest)
        self.assertEqual(receipt["candidate_count"],15)
        self.assertEqual(receipt["candidate_count_with_verified_historical_metadata_and_hourly_semantics"],15)
        self.assertFalse(receipt["raw_hourly_values_or_event_level_rows_in_receipt"])
        self.assertFalse(receipt["model_skill_or_bias_correction_admitted"])
        self.assertEqual(receipt["unique_nearest_CLIMK_ERA5_grid_nodes_across_audited_candidates"],1)
        self.assertNotIn("dwd_hourly_gust_qn",json.dumps(receipt))

        wrong=dict(archives)
        wrong[manifest["candidate_archives"][0]["station_id"]]=b"tampered"
        with patch.object(screen,"verify_source_bytes",return_value={"sha256_observed":"a"*64}), \
             patch.object(screen,"_listed_sources",return_value={"station_list_data_rows":564,
                                                                  "historical_hourly_FX_zip_archive_links":448}):
            with self.assertRaises(screen.CandidateScreenBlocked):
                screen.audit_candidate_sources(source,station_list,index,wrong,manifest)

    def test_live_cli_stdout_contains_status_only(self):
        sink=StringIO()
        with patch.object(screen,"live_analysis",return_value={"gust":99.0,"hourly":[1,2,3]}), \
             patch("sys.argv",["runner.py","--live-original-sources"]),redirect_stdout(sink):
            self.assertEqual(screen.main(),0)
        self.assertIn("LIVE_CANDIDATE_SCREEN_COMPLETED",sink.getvalue())
        self.assertNotIn("99.0",sink.getvalue())
        self.assertNotIn("hourly",sink.getvalue())

    def test_output_receipt_is_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/"receipt.json"
            with patch.object(screen,"live_analysis",return_value={"aggregate":True}), \
                 patch("sys.argv",["runner.py","--live-original-sources","--output",str(target)]), \
                 redirect_stdout(StringIO()):
                self.assertEqual(screen.main(),0)
            self.assertEqual(json.loads(target.read_text()),{"aggregate":True})
            with patch.object(screen,"live_analysis",return_value={"aggregate":False}), \
                 patch("sys.argv",["runner.py","--live-original-sources","--output",str(target)]), \
                 redirect_stdout(StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    screen.main()
            self.assertEqual(raised.exception.code,2)
            self.assertEqual(json.loads(target.read_text()),{"aggregate":True})


if __name__=="__main__":
    unittest.main()
