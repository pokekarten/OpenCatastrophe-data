# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json
import math
import unittest

from scripts.select_oq313_risk_by_event_rows import (
    OQ313DatastoreSelectionError,
    select_oq313_risk_by_event_receipt,
)


class Series:
    def __init__(self, dtype):
        self.dtype = dtype


class Frame:
    columns = ("event_id", "agg_id", "loss_id", "variance", "loss")

    def __init__(self, rows, dtypes=None, columns=None):
        self.rows = list(rows)
        self.dtypes = dtypes or {
            "event_id": "uint32",
            "agg_id": "uint32",
            "loss_id": "uint8",
            "variance": "float32",
            "loss": "float32",
        }
        if columns is not None:
            self.columns = tuple(columns)

    def __getitem__(self, name):
        return Series(self.dtypes[name])

    def to_records(self, index=False):
        if index:
            raise AssertionError("index must be false")
        return list(self.rows)


class Group:
    def __init__(self, attrs):
        self.attrs = attrs


class StructuredDtype:
    def __init__(self, fields, dtypes):
        self.names = tuple(fields)
        self.fields = {
            name: (dtypes[name], index)
            for index, name in enumerate(self.names)
        }


class EventArray(list):
    def __init__(self, rows, *, fields=None, dtypes=None):
        super().__init__(rows)
        fields = fields or ("id", "rup_id", "rlz_id")
        dtypes = dtypes or {
            "id": "uint32",
            "rup_id": "uint32",
            "rlz_id": "uint16",
        }
        self.dtype = StructuredDtype(fields, dtypes)


class Events:
    def __init__(self, rows, *, fields=None, dtypes=None):
        self.rows = list(rows)
        self.fields = fields
        self.dtypes = dtypes

    def __getitem__(self, key):
        if isinstance(key, slice):
            return EventArray(
                self.rows[key],
                fields=self.fields,
                dtypes=self.dtypes,
            )
        return self.rows[key]


class Store:
    def __init__(
        self,
        rows,
        events,
        attrs=None,
        frame=None,
        event_fields=None,
        event_dtypes=None,
    ):
        self.group = Group(attrs or {"K": 2, "L": 2})
        self.frame = frame or Frame(rows)
        self.events = Events(
            events,
            fields=event_fields,
            dtypes=event_dtypes,
        )

    def __getitem__(self, key):
        if key == "risk_by_event":
            return self.group
        if key == "events":
            return self.events
        raise KeyError(key)

    def read_df(self, key):
        if key != "risk_by_event":
            raise KeyError(key)
        return self.frame


class Oq:
    def __init__(self):
        self.loss_types = ["contents", "structural"]
        self.lti = {"contents": 0, "structural": 1}
        self.inputs = {
            "job_ini": "fixed/job.ini",
            "structural_vulnerability": "fixed/v.xml",
        }
        self.concurrent_tasks = 2


def rows():
    return [
        {"event_id": 9, "agg_id": 2, "loss_id": 1, "variance": -0.0, "loss": 1.5},
        {"event_id": 3, "agg_id": 0, "loss_id": 1, "variance": 0.25, "loss": 7.0},
        {"event_id": 4, "agg_id": 2, "loss_id": 0, "variance": 0.5, "loss": 8.0},
        {"event_id": 1, "agg_id": 2, "loss_id": 1, "variance": 2.0, "loss": 3.25},
    ]


def events():
    return [
        {"id": 1, "rup_id": 101, "rlz_id": 0},
        {"id": 3, "rup_id": 103, "rlz_id": 0},
        {"id": 4, "rup_id": 104, "rlz_id": 0},
        {"id": 9, "rup_id": 109, "rlz_id": 1},
    ]


class SelectionTests(unittest.TestCase):
    def test_selects_runtime_k_structural_lti_and_binds_ruptures(self):
        payload, receipt = select_oq313_risk_by_event_receipt(
            Store(rows(), events()), Oq()
        )
        doc = json.loads(payload)
        self.assertEqual(
            doc["selection"],
            {"portfolio_agg_id": 2, "structural_loss_id": 1},
        )
        self.assertEqual(doc["runtime"], {"concurrent_tasks": 2})
        self.assertEqual([row["event_id"] for row in doc["rows"]], [1, 9])
        self.assertEqual([row["rup_id"] for row in doc["rows"]], [101, 109])
        self.assertEqual([row["rlz_id"] for row in doc["rows"]], [0, 1])
        self.assertEqual(doc["rows"][0]["loss_f32_be_hex"], "40500000")
        self.assertEqual(doc["rows"][1]["variance_f32_be_hex"], "80000000")
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertEqual(len(receipt["sha256"]), 64)

    def test_input_permutation_is_byte_deterministic(self):
        a = select_oq313_risk_by_event_receipt(Store(rows(), events()), Oq())
        b = select_oq313_risk_by_event_receipt(
            Store(list(reversed(rows())), list(reversed(events()))), Oq()
        )
        self.assertEqual(a, b)

    def test_events_native_uint32_ids_are_required(self):
        for name in ("id", "rup_id"):
            with self.subTest(name=name):
                dtypes = {
                    "id": "uint32",
                    "rup_id": "uint32",
                    "rlz_id": "uint16",
                }
                dtypes[name] = "uint64"
                with self.assertRaisesRegex(
                    OQ313DatastoreSelectionError,
                    rf"events {name} dtype must be uint32",
                ):
                    select_oq313_risk_by_event_receipt(
                        Store(rows(), events(), event_dtypes=dtypes), Oq()
                    )

    def test_events_native_uint16_rlz_id_is_required(self):
        with self.assertRaisesRegex(
            OQ313DatastoreSelectionError,
            "events rlz_id dtype must be uint16",
        ):
            select_oq313_risk_by_event_receipt(
                Store(
                    rows(),
                    events(),
                    event_dtypes={
                        "id": "uint32",
                        "rup_id": "uint32",
                        "rlz_id": "uint32",
                    },
                ),
                Oq(),
            )

    def test_events_rlz_id_value_is_strict_uint16(self):
        for value in (True, -1, 1 << 16):
            evs = events()
            evs[0] = dict(evs[0], rlz_id=value)
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    OQ313DatastoreSelectionError,
                    "events\\[0\\]\\.rlz_id",
                ):
                    select_oq313_risk_by_event_receipt(Store(rows(), evs), Oq())

    def test_events_native_field_order_and_shape_are_required(self):
        for fields in (
            ("rup_id", "id", "rlz_id"),
            ("id", "rup_id", "rlz_id", "extra"),
            ("id", "rup_id"),
        ):
            with self.subTest(fields=fields):
                dtypes = {
                    "id": "uint32",
                    "rup_id": "uint32",
                    "rlz_id": "uint16",
                    "extra": "uint8",
                }
                with self.assertRaisesRegex(
                    OQ313DatastoreSelectionError,
                    "events fields must be exactly",
                ):
                    select_oq313_risk_by_event_receipt(
                        Store(
                            rows(),
                            events(),
                            event_fields=fields,
                            event_dtypes=dtypes,
                        ),
                        Oq(),
                    )

    def test_missing_k_fails_closed(self):
        with self.assertRaisesRegex(OQ313DatastoreSelectionError, "contain K and L"):
            select_oq313_risk_by_event_receipt(
                Store(rows(), events(), attrs={"L": 2}), Oq()
            )

    def test_lti_order_mismatch_fails_closed(self):
        oq = Oq()
        oq.lti = {"contents": 1, "structural": 0}
        with self.assertRaisesRegex(OQ313DatastoreSelectionError, "disagrees"):
            select_oq313_risk_by_event_receipt(Store(rows(), events()), oq)

    def test_l_mismatch_fails_closed(self):
        with self.assertRaisesRegex(OQ313DatastoreSelectionError, "L disagrees"):
            select_oq313_risk_by_event_receipt(
                Store(rows(), events(), attrs={"K": 2, "L": 3}), Oq()
            )

    def test_insured_loss_column_fails_closed(self):
        cols = Frame.columns + ("ins_loss",)
        frame = Frame(rows(), columns=cols)
        with self.assertRaisesRegex(
            OQ313DatastoreSelectionError, "columns must be exactly"
        ):
            select_oq313_risk_by_event_receipt(
                Store(rows(), events(), frame=frame), Oq()
            )

    def test_policy_input_fails_closed(self):
        oq = Oq()
        oq.inputs["policy_file"] = "policies.csv"
        with self.assertRaisesRegex(OQ313DatastoreSelectionError, "policy/insurance"):
            select_oq313_risk_by_event_receipt(Store(rows(), events()), oq)

    def test_float64_source_column_fails_closed(self):
        frame = Frame(rows())
        frame.dtypes["loss"] = "float64"
        with self.assertRaisesRegex(
            OQ313DatastoreSelectionError, "loss dtype must be float32"
        ):
            select_oq313_risk_by_event_receipt(
                Store(rows(), events(), frame=frame), Oq()
            )

    def test_missing_event_link_fails_closed(self):
        evs = [event for event in events() if event["id"] != 9]
        with self.assertRaisesRegex(OQ313DatastoreSelectionError, "no events linkage"):
            select_oq313_risk_by_event_receipt(Store(rows(), evs), Oq())

    def test_duplicate_event_link_fails_closed(self):
        evs = events() + [
            {"id": 9, "rup_id": 999, "rlz_id": 1}
        ]
        with self.assertRaisesRegex(
            OQ313DatastoreSelectionError, "events ids must be unique"
        ):
            select_oq313_risk_by_event_receipt(Store(rows(), evs), Oq())

    def test_duplicate_selected_event_fails_closed(self):
        selected_rows = rows() + [
            {
                "event_id": 9,
                "agg_id": 2,
                "loss_id": 1,
                "variance": 1.0,
                "loss": 2.0,
            }
        ]
        with self.assertRaisesRegex(
            OQ313DatastoreSelectionError, "selected event ids must be unique"
        ):
            select_oq313_risk_by_event_receipt(
                Store(selected_rows, events()), Oq()
            )

    def test_empty_selection_fails_closed(self):
        candidate_rows = [
            {
                "event_id": 1,
                "agg_id": 0,
                "loss_id": 0,
                "variance": 1.0,
                "loss": 2.0,
            }
        ]
        with self.assertRaisesRegex(
            OQ313DatastoreSelectionError, "no portfolio structural rows"
        ):
            select_oq313_risk_by_event_receipt(
                Store(candidate_rows, events()), Oq()
            )

    def test_nonfinite_binary32_fails_closed(self):
        candidate_rows = rows()
        candidate_rows[0] = dict(candidate_rows[0], loss=math.inf)
        with self.assertRaisesRegex(
            OQ313DatastoreSelectionError, "failed receipt projection"
        ):
            select_oq313_risk_by_event_receipt(
                Store(candidate_rows, events()), Oq()
            )

    def test_bool_ids_fail_closed(self):
        candidate_rows = rows()
        candidate_rows[0] = dict(candidate_rows[0], event_id=True)
        with self.assertRaisesRegex(OQ313DatastoreSelectionError, "must be an integer"):
            select_oq313_risk_by_event_receipt(
                Store(candidate_rows, events()), Oq()
            )

    def test_empty_dataframe_read_fails_closed(self):
        store = Store(rows(), events())

        def fail_read(_key):
            raise ValueError("empty dataset")

        store.read_df = fail_read
        with self.assertRaisesRegex(
            OQ313DatastoreSelectionError, "cannot read risk_by_event"
        ):
            select_oq313_risk_by_event_receipt(store, Oq())

    def test_zero_concurrency_is_preserved(self):
        oq = Oq()
        oq.concurrent_tasks = 0
        payload, _ = select_oq313_risk_by_event_receipt(Store(rows(), events()), oq)
        self.assertEqual(json.loads(payload)["runtime"], {"concurrent_tasks": 0})

    def test_invalid_concurrency_fails_closed(self):
        for value in (-1, True):
            with self.subTest(value=value):
                oq = Oq()
                oq.concurrent_tasks = value
                with self.assertRaisesRegex(
                    OQ313DatastoreSelectionError,
                    "outside|must be an integer",
                ):
                    select_oq313_risk_by_event_receipt(Store(rows(), events()), oq)


if __name__ == "__main__":
    unittest.main()
