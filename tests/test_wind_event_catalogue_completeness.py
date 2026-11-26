# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import copy
import json
import unittest

from research_runners.wind_event_catalogue_completeness import INPUT_SCHEMA, audit, parse_manifest_json


def fixture():
    return {
        "schema": INPUT_SCHEMA,
        "first_month": "2020-01",
        "last_month": "2020-02",
        "tracking_algorithm": "TRACK",
        "product_version": "1.0",
        "months": [
            {
                "month": "2020-01",
                "tracking_algorithm": "TRACK",
                "product_version": "1.0",
                "delivery_complete": True,
                "source_sha256": "a" * 64,
                "events": [],
            }
        ],
    }


class CompletenessTest(unittest.TestCase):
    def test_missing_month_is_not_inferred_zero(self):
        result = audit(fixture())
        self.assertEqual(result["missing_months"], ["2020-02"])
        self.assertEqual(result["explicit_zero_event_months"], ["2020-01"])
        self.assertFalse(result["manifest_month_coverage_complete"])
        self.assertFalse(result["declared_catalogue_structure_complete"])

    def test_duplicate_month_event_and_mixed_tracker_are_rejected(self):
        data = fixture()
        second = copy.deepcopy(data["months"][0])
        second["month"] = "2020-02"
        data["months"].append(second)
        data["months"][0]["events"] = [{"event_id": "same", "footprint_verified": True}]
        data["months"][1]["events"] = [{"event_id": "same", "footprint_verified": True}]
        with self.assertRaisesRegex(ValueError, "duplicate physical event"):
            audit(data)
        data["months"][1]["month"] = "2020-01"
        with self.assertRaisesRegex(ValueError, "duplicate month"):
            audit(data)
        data["months"][1]["month"] = "2020-02"
        data["months"][1]["events"] = []
        data["months"][1]["tracking_algorithm"] = "OTHER"
        with self.assertRaisesRegex(ValueError, "mixed tracking algorithms"):
            audit(data)

    def test_product_version_must_be_constant(self):
        data = fixture()
        data["last_month"] = "2020-01"
        data["months"][0]["product_version"] = "2.0"
        with self.assertRaisesRegex(ValueError, "mixed product versions"):
            audit(data)

    def test_complete_declaration_does_not_authorize_annual_risk(self):
        data = fixture()
        data["last_month"] = "2020-01"
        result = audit(data)
        self.assertTrue(result["declared_catalogue_structure_complete"])
        self.assertFalse(result["source_bytes_independently_verified"])
        self.assertFalse(result["frequency_weights_verified"])
        self.assertFalse(result["annual_risk_authorized"])

    def test_missing_footprint_blocks_declared_catalogue_structure(self):
        data = fixture()
        data["last_month"] = "2020-01"
        data["months"][0]["events"] = [
            {"event_id": "event-1", "footprint_verified": False}
        ]
        result = audit(data)
        self.assertFalse(result["manifest_event_footprints_complete"])
        self.assertFalse(result["declared_catalogue_structure_complete"])
        self.assertEqual(result["events_without_verified_footprint"], ["event-1"])

    def test_malformed_month_and_reversed_range_are_rejected(self):
        for value in ("2020-1", "2020-13", "2020/01", 202001):
            data = fixture()
            data["first_month"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                audit(data)
        data = fixture()
        data["first_month"], data["last_month"] = "2020-02", "2020-01"
        with self.assertRaisesRegex(ValueError, "Reversed coverage"):
            audit(data)

    def test_bad_hash_incomplete_delivery_and_malformed_event_are_rejected(self):
        data = fixture()
        data["months"][0]["source_sha256"] = "A" * 64
        with self.assertRaisesRegex(ValueError, "invalid source_sha256"):
            audit(data)
        data = fixture()
        data["months"][0]["delivery_complete"] = 1
        with self.assertRaisesRegex(ValueError, "incomplete source delivery"):
            audit(data)
        data = fixture()
        data["months"][0]["events"] = [{"event_id": "e", "footprint_verified": 1}]
        with self.assertRaisesRegex(ValueError, "must be boolean"):
            audit(data)

    def test_raw_json_duplicate_keys_are_rejected_at_every_level(self):
        # json.loads alone silently keeps the last value. A reported source
        # receipt cannot safely have competing event, month or schema claims.
        cases = (
            '{"schema":"WIND_EVENT_CATALOGUE_MONTHLY_INPUT_V1","schema":"invalid"}',
            '{"months":[{"month":"2020-01","month":"2020-02"}]}',
            '{"months":[{"events":[{"event_id":"a","event_id":"b"}]}]}',
        )
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaisesRegex(
                ValueError, "duplicate JSON key"
            ):
                parse_manifest_json(raw)
        # Existing valid manifests retain their exact public audit behavior.
        self.assertEqual(audit(parse_manifest_json(json.dumps(fixture()))),
                         audit(fixture()))

    def test_wrong_manifest_shape_is_rejected_without_uncaught_type_error(self):
        for data in ([], None, {"schema": "other"}, {"schema": INPUT_SCHEMA, "months": {}}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                audit(data)


if __name__ == "__main__":
    unittest.main()
