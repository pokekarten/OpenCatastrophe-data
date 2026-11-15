# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only NOAA NCEI tsunami source-event (not runup) preflight tests."""
import copy
import hashlib
import json
import unittest
from scripts.noaa_tsunami_event_preflight_v0 import (
    FIELD_TYPES, TsunamiEventPreflightError, screen_noaa_tsunami_event_json,
    MAX_RESPONSE_BYTES,
)


def fixture(validities=(4, 2)):
    fields = [{"name": name, "type": typ} for name, typ in FIELD_TYPES.items()]
    features = []
    for i, v in enumerate(validities, start=1):
        attrs = {"OBJECTID": i, "ID": float(100 + i), "YEAR": 2020,
                 "MONTH": 2, "DAY": 29, "LATITUDE": 36.7, "LONGITUDE": 141.2,
                 "EVENT_VALIDITY_CODE": v, "CAUSE_CODE": 1,
                 "NUM_RUNUP": 8, "MAX_EVENT_RUNUP": 1.7}
        features.append({"attributes": attrs})
    return {"objectIdFieldName": "OBJECTID", "fields": fields,
            "geometryType": "esriGeometryPoint", "features": features,
            "exceededTransferLimit": False}


def encoded(obj):
    return json.dumps(obj, separators=(",", ":"), allow_nan=False).encode("utf-8")


class TsunamiEventPreflightTests(unittest.TestCase):
    def test_distinguishes_confirmed_and_unconfirmed_historical_events(self):
        original = encoded(fixture((4, 2)))
        r = screen_noaa_tsunami_event_json(original)
        self.assertEqual(r["input_response_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(r["historically_probable_or_definite_event_count"], 1)
        self.assertEqual(r["unconfirmed_or_non_tsunami_event_count"], 1)
        self.assertEqual(r["event_validity_counts"]["4"], 1)
        self.assertFalse(r["commercial_cat_model_use_approved"])
        self.assertFalse(r["original_provider_provenance_verified"])
        self.assertFalse(r["runup_record_geometry_or_inundation_verified"])

    def test_pre_modern_bce_partially_dated_and_erroneous_codes_not_admitted(self):
        r = fixture((-1, 0, 3))
        r["features"][0]["attributes"].update(YEAR=-1900, MONTH=None, DAY=None)
        r["features"][1]["attributes"].update(YEAR=1550, MONTH=2, DAY=29)
        out = screen_noaa_tsunami_event_json(encoded(r))
        self.assertEqual(out["partially_dated_events"], 1)
        self.assertEqual(out["historically_probable_or_definite_event_count"], 1)
        self.assertEqual(out["unconfirmed_or_non_tsunami_event_count"], 2)
        self.assertFalse(out["historical_calendar_and_source_deduplication_verified"])

    def test_fail_closes_bad_geometry_dates_validity_schema_and_json(self):
        rejects = []
        def add(change):
            r = fixture((4,))
            change(r)
            rejects.append(encoded(r))
        add(lambda r: r.update(objectIdFieldName="TSEVENT_ID"))
        add(lambda r: r.update(error={"code": 403}))
        add(lambda r: r.update(exceededTransferLimit=True))
        add(lambda r: r.update(geometryType="esriGeometryPolyline"))
        add(lambda r: r["fields"].append({"name": "TSEVENT_ID", "type": "esriFieldTypeDouble"}))
        add(lambda r: r["fields"][1].update(type="esriFieldTypeString"))
        add(lambda r: r["features"][0].update(geometry={"x": 1, "y": 2}))
        add(lambda r: r["features"][0]["attributes"].update(TSEVENT_ID=100))
        add(lambda r: r["features"][0]["attributes"].update(YEAR=0))
        add(lambda r: r["features"][0]["attributes"].update(YEAR=2027))
        add(lambda r: r["features"][0]["attributes"].update(DAY=30))
        add(lambda r: r["features"][0]["attributes"].update(MONTH=None, DAY=5))
        add(lambda r: r["features"][0]["attributes"].update(LATITUDE=100))
        add(lambda r: r["features"][0]["attributes"].update(LONGITUDE=-181))
        add(lambda r: r["features"][0]["attributes"].update(EVENT_VALIDITY_CODE=5))
        add(lambda r: r["features"][0]["attributes"].update(EVENT_VALIDITY_CODE=None))
        add(lambda r: r["features"][0]["attributes"].update(CAUSE_CODE=19))
        add(lambda r: r["features"][0]["attributes"].update(NUM_RUNUP=-1))
        add(lambda r: r["features"][0]["attributes"].update(MAX_EVENT_RUNUP=-9999))
        add(lambda r: r["features"][0]["attributes"].update(ID=True))
        add(lambda r: r["features"][0]["attributes"].update(ID=101.5))
        add(lambda r: r["features"][0]["attributes"].update(OBJECTID=0))
        add(lambda r: r.update(features=[]))
        add(lambda r: r.update(features=r["features"]*4))
        add(lambda r: r.update(spatialReference={"wkid": 4326}))
        add(lambda r: r["fields"].append(copy.deepcopy(r["fields"][0])))
        rejects += [b"", b"Not JSON", b"{\"a\":1,\"a\":2}", b"{\"x\":NaN}",
                    b" "+b"x"*MAX_RESPONSE_BYTES,
                    encoded({"error":{"message":"Unauthorized"}})]
        duplicate = fixture((4, 3))
        duplicate["features"][1]["attributes"]["ID"] = duplicate["features"][0]["attributes"]["ID"]
        rejects.append(encoded(duplicate))
        for raw in rejects:
            with self.subTest(raw=raw[:90]):
                with self.assertRaises(TsunamiEventPreflightError):
                    screen_noaa_tsunami_event_json(raw)


if __name__ == "__main__":
    unittest.main()
