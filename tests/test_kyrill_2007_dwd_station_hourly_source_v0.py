# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
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
import kyrill_2007_dwd_station_hourly_source_v0 as m


class Kyrill2007DWDSourceAuditTests(unittest.TestCase):
    def test_pinned_event_window_station_archives_and_historic_sensor_heights(self):
        source=m._manifest()
        self.assertEqual(source["publisher_event_time_utc"],"2007-01-18T15:00:00Z")
        self.assertEqual(source["study_window_hours"],96)
        self.assertEqual([s["station_id"] for s in source["stations"]],["02667","00603"])
        self.assertEqual([s["historical_anemometer_height_m_agl"] for s in source["stations"]],[10.0,12.0])
        self.assertEqual([s["expected_qn8_3_hours"] for s in source["stations"]],[96,96])

    def test_dry_run_does_not_claim_original_source_replay(self):
        with patch.object(sys,"argv",["kyrill","--dry-run"]),\
             patch.object(m,"replay",side_effect=AssertionError("network not allowed in dry run")):
            out=StringIO()
            with redirect_stdout(out):
                self.assertEqual(m.main(),0)
        receipt=json.loads(out.getvalue())
        self.assertFalse(receipt["source_bytes_retrieved"])
        self.assertFalse(receipt["loss_or_vulnerability_calibrated"])

    def test_wrong_original_station_list_bytes_fail_before_archive_reads(self):
        calls=[]
        def fake_get(url,max_bytes,opener=None):
            calls.append(url)
            return b"not the pinned original station list"
        with patch.object(m.dwd,"_get_publisher_bytes",side_effect=fake_get):
            with self.assertRaises(m.KyrillDWDSourceBlocked):
                m._sources()
        self.assertEqual(calls,[m.dwd.STATION_LIST,m.dwd.INDEX])


if __name__=="__main__":
    unittest.main()
