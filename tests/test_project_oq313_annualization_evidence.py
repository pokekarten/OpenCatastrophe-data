# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import struct
import unittest

from scripts import project_oq313_annualization_evidence as subject


class StructuredDtype:
    def __init__(self) -> None:
        self.names = ("id", "rup_id", "rlz_id")
        self.fields = {
            "id": ("uint32", 0),
            "rup_id": ("uint32", 1),
            "rlz_id": ("uint16", 2),
        }


class Array(list):
    def __init__(self, values, *, dtype: str, shape=None):
        super().__init__(values)
        self.dtype = dtype
        self.shape = shape if shape is not None else (len(values),)


class EventArray(list):
    def __init__(self, values):
        super().__init__(values)
        self.dtype = StructuredDtype()
        self.shape = (len(values),)


class Dataset:
    def __init__(self, array):
        self.array = array

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.array
        return self.array[key]


class Store:
    def __init__(self, *, events=None, weights=None, avg=None):
        self.datasets = {
            "events": Dataset(EventArray(events or _events())),
            "weights": Dataset(
                Array(
                    weights if weights is not None else [0.25, 0.75],
                    dtype="float64",
                )
            ),
            "avg_losses-rlzs/structural": Dataset(
                avg
                if avg is not None
                else Array(
                    [[1.0, 2.0], [3.0, 4.0]],
                    dtype="float32",
                    shape=(2, 2),
                )
            ),
        }

    def __getitem__(self, key):
        return self.datasets[key]


class Oq:
    def __init__(self, *, collect_rlzs=False):
        self.loss_types = ["contents", "structural"]
        self.lti = {"contents": 0, "structural": 1}
        self.inputs = {
            "job_ini": "fixed/job.ini",
            "structural_vulnerability": "fixed/v.xml",
        }
        self.investigation_time = 50.0
        self.risk_investigation_time = None
        self.ses_per_logic_tree_path = 2
        self.collect_rlzs = collect_rlzs
        self.number_of_logic_tree_samples = 0


def _events():
    return [
        {"id": 1, "rup_id": 101, "rlz_id": 0},
        {"id": 2, "rup_id": 102, "rlz_id": 1},
        {"id": 3, "rup_id": 103, "rlz_id": 1},
    ]


class AnnualizationEvidenceTests(unittest.TestCase):
    def test_noncollected_projects_runtime_events_weights_and_native_mean(self):
        payload, receipt = subject.project_oq313_annualization_evidence(
            Store(), Oq()
        )
        doc = json.loads(payload)

        self.assertEqual(doc["loss_type"], "structural")
        self.assertEqual(doc["structural_loss_id"], 1)
        self.assertEqual(
            doc["runtime"]["time_ratio_f64_be_hex"],
            struct.pack("!d", 0.5).hex(),
        )
        self.assertFalse(doc["runtime"]["collect_rlzs"])
        self.assertEqual(doc["runtime"]["sampling_mode"], "enumerated")
        self.assertEqual(
            doc["events"]["event_count_by_realization"],
            [
                {"rlz_id": 0, "event_count": 1},
                {"rlz_id": 1, "event_count": 2},
            ],
        )
        self.assertEqual(doc["weights"]["count"], 2)
        self.assertFalse(doc["weights"]["values_returned"])
        self.assertEqual(
            doc["avg_losses"]["shape"],
            [2, 2],
        )
        self.assertEqual(
            doc["avg_losses"]["engine_mean_method"],
            "weighted_native_portfolio_totals",
        )
        self.assertEqual(
            doc["avg_losses"]["engine_mean_f64_be_hex"],
            struct.pack("!d", 5.5).hex(),
        )
        self.assertFalse(doc["avg_losses"]["portfolio_totals_returned"])
        self.assertFalse(doc["reference_loss_comparison_performed"])
        self.assertFalse(doc["reference_loss_agreement_verified"])
        self.assertFalse(doc["publication_authorized"])
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertEqual(len(receipt["sha256"]), 64)

    def test_collected_realizations_require_one_native_avg_output(self):
        avg = Array(
            [[2.0], [4.0]],
            dtype="float32",
            shape=(2, 1),
        )
        payload, _ = subject.project_oq313_annualization_evidence(
            Store(avg=avg), Oq(collect_rlzs=True)
        )
        doc = json.loads(payload)
        self.assertTrue(doc["runtime"]["collect_rlzs"])
        self.assertEqual(doc["weights"]["count"], 2)
        self.assertEqual(doc["avg_losses"]["shape"], [2, 1])
        self.assertEqual(
            doc["avg_losses"]["engine_mean_method"],
            "collected_realization_native_portfolio_total",
        )
        self.assertEqual(
            doc["avg_losses"]["engine_mean_f64_be_hex"],
            struct.pack("!d", 6.0).hex(),
        )

    def test_risk_investigation_time_overrides_investigation_time_in_ratio(self):
        oq = Oq()
        oq.risk_investigation_time = 20.0
        payload, _ = subject.project_oq313_annualization_evidence(Store(), oq)
        doc = json.loads(payload)
        self.assertTrue(doc["runtime"]["risk_investigation_time_present"])
        self.assertEqual(
            doc["runtime"]["time_ratio_f64_be_hex"],
            struct.pack("!d", 0.2).hex(),
        )

    def test_sampled_mode_is_explicit(self):
        oq = Oq()
        oq.number_of_logic_tree_samples = 100
        payload, _ = subject.project_oq313_annualization_evidence(Store(), oq)
        self.assertEqual(json.loads(payload)["runtime"]["sampling_mode"], "sampled")

    def test_weights_are_bound_but_not_returned(self):
        payload, _ = subject.project_oq313_annualization_evidence(Store(), Oq())
        doc = json.loads(payload)
        self.assertIn("values_f64_sha256", doc["weights"])
        self.assertNotIn("values", doc["weights"])
        self.assertNotIn("portfolio_total_by_output_realization", doc["avg_losses"])

    def test_weights_must_sum_to_one(self):
        with self.assertRaisesRegex(
            subject.OQ313AnnualizationEvidenceError,
            "sum to one",
        ):
            subject.project_oq313_annualization_evidence(
                Store(weights=[0.2, 0.7]), Oq()
            )

    def test_noncollected_avg_outputs_must_match_weight_count(self):
        avg = Array(
            [[1.0], [2.0]],
            dtype="float32",
            shape=(2, 1),
        )
        with self.assertRaisesRegex(
            subject.OQ313AnnualizationEvidenceError,
            "output realization count",
        ):
            subject.project_oq313_annualization_evidence(Store(avg=avg), Oq())

    def test_avg_losses_dtype_is_exact_float32(self):
        avg = Array(
            [[1.0, 2.0]],
            dtype="float64",
            shape=(1, 2),
        )
        with self.assertRaisesRegex(
            subject.OQ313AnnualizationEvidenceError,
            "dtype must be float32",
        ):
            subject.project_oq313_annualization_evidence(Store(avg=avg), Oq())

    def test_event_realization_outside_weight_dimension_fails_closed(self):
        events = [
            {"id": 1, "rup_id": 101, "rlz_id": 0},
            {"id": 2, "rup_id": 102, "rlz_id": 2},
        ]
        with self.assertRaisesRegex(
            subject.OQ313AnnualizationEvidenceError,
            "outside the weights dimension",
        ):
            subject.project_oq313_annualization_evidence(
                Store(events=events), Oq()
            )

    def test_zero_event_realization_is_preserved_explicitly(self):
        events = [
            {"id": 1, "rup_id": 101, "rlz_id": 0},
        ]
        payload, _ = subject.project_oq313_annualization_evidence(
            Store(events=events), Oq()
        )
        self.assertEqual(
            json.loads(payload)["events"]["event_count_by_realization"],
            [
                {"rlz_id": 0, "event_count": 1},
                {"rlz_id": 1, "event_count": 0},
            ],
        )

    def test_policy_input_remains_forbidden(self):
        oq = Oq()
        oq.inputs["policy_file"] = "policy.csv"
        with self.assertRaisesRegex(
            subject.OQ313AnnualizationEvidenceError,
            "insurance-scope",
        ):
            subject.project_oq313_annualization_evidence(Store(), oq)

    def test_zero_ses_per_logic_tree_path_fails_closed(self):
        oq = Oq()
        oq.ses_per_logic_tree_path = 0
        with self.assertRaisesRegex(
            subject.OQ313AnnualizationEvidenceError,
            "must be positive",
        ):
            subject.project_oq313_annualization_evidence(Store(), oq)

    def test_payload_is_deterministic_under_event_permutation(self):
        a = subject.project_oq313_annualization_evidence(Store(), Oq())
        b = subject.project_oq313_annualization_evidence(
            Store(events=list(reversed(_events()))), Oq()
        )
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
