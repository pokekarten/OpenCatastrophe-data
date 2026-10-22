# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only tests for exact OpenQuake 3.13 threshold dataflow evidence."""

from __future__ import annotations

import unittest
from unittest import mock

from research_runners import oq313_minimum_asset_loss_provenance as subject


RISKMODELS = b"""
    def event_based_risk(self, loss_type, assets, gmf_df, col, rndgen):
        vf = self.risk_functions[loss_type, 'vulnerability']
        return vf(asset_df, gmf_df, col, rndgen,
                  self.minimum_asset_loss[loss_type]).set_index(['eid', 'aid'])

    scenario = ebrisk = scenario_risk = event_based_risk
"""
SCIENTIFIC = b"""
    def get_losses(self, df, covs):
        vals = df['val'].to_numpy()
        losses = vals * df['mean'].to_numpy()
        return losses

    def sampleLN(self, df):
        return None

    def __call__(self, asset_df, gmf_df, col, rng=None, minloss=0):
        losses = sampler.get_losses(df, covs)
        ok = losses > minloss
        return pandas.DataFrame(dict(eid=df.eid[ok], loss=losses[ok]))

    def strictly_increasing(self):
        return None
"""
CALCULATOR = b"""
def aggreg(outputs, crmodel, ARKD, kids, rlz_id, monitor):
    alt = out[ln].reset_index()
    coo = average_losses(
        ln, alt, rlz_id, (A, R), oq.collect_rlzs)
    fast_agg(eids + U64(K), values, correl, li, acc)

def event_based_risk(df, oqparam, monitor):
    return None

    def agg_dicts(self, dummy, dic):
        for ln, ls in dic['avg'].items():
            self.avg_losses[coo.row, coo.col, lti[ln]] += coo.data

    def post_execute(self, dummy):
        self.avg_losses[:, r] *= self.avg_ratio[r]
        self.datastore['avg_losses-rlzs'] = self.avg_losses
"""


class MinimumAssetLossProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.blobs = {
            "openquake/risklib/riskmodels.py": RISKMODELS,
            "openquake/risklib/scientific.py": SCIENTIFIC,
            "openquake/calculators/event_based_risk.py": CALCULATOR,
        }
        digest_map = {
            k: subject.git_blob_id(v) for k, v in self.blobs.items()
        }
        pin = mock.patch.dict(subject.EXPECTED_GIT_BLOBS, digest_map, clear=True)
        pin.start()
        self.addCleanup(pin.stop)

    def test_exact_pinned_source_proves_threshold_before_annual_average(self):
        result = subject.probe_source_bytes(self.blobs)
        self.assertEqual(result["status"], "PINNED_SOURCE_SEMANTICS_VERIFIED")
        self.assertEqual(result["source_declared_minimum_asset_loss_structural_eur"], 2000)
        self.assertTrue(result["loss_equal_to_threshold_is_excluded"])
        self.assertTrue(result["filter_applied_before_avg_losses_aggregation"])
        self.assertTrue(result["filter_applied_before_risk_by_event_aggregation"])
        self.assertTrue(result["can_affect_reconstructed_average_annual_loss"])
        for flag in (
            "published_esrm20_same_threshold_verified",
            "threshold_compatibility_verified",
            "denominator_semantics_verified",
            "annualization_semantics_verified",
            "reference_loss_agreement_verified",
            "model_use_authorized",
            "publication_authorized",
            "external_bytes_persisted",
        ):
            self.assertIs(result[flag], False, flag)
        self.assertEqual(set(result["source_file_git_blob_ids"]), set(self.blobs))

    def test_changed_source_byte_blocks_even_if_known_anchor_still_exists(self):
        changed = dict(self.blobs)
        changed["openquake/risklib/scientific.py"] += b"\n# drift\n"
        with self.assertRaisesRegex(subject.ThresholdProvenanceError, "blob identity"):
            subject.probe_source_bytes(changed)

    def test_wrong_threshold_comparator_blocked_with_new_pin(self):
        changed = dict(self.blobs)
        changed["openquake/risklib/scientific.py"] = SCIENTIFIC.replace(
            b"ok = losses > minloss", b"ok = losses >= minloss"
        )
        with mock.patch.dict(subject.EXPECTED_GIT_BLOBS, {
            k: subject.git_blob_id(v) for k, v in changed.items()
        }, clear=True):
            with self.assertRaisesRegex(subject.ThresholdProvenanceError, "dataflow"):
                subject.probe_source_bytes(changed)

    def test_threshold_only_after_averaging_is_not_accepted(self):
        changed = dict(self.blobs)
        changed["openquake/calculators/event_based_risk.py"] = CALCULATOR.replace(
            b"    coo = average_losses(\n", b"    # coo = average_losses(\n"
        ).replace(
            b"    fast_agg(eids + U64(K), values, correl, li, acc)",
            b"    fast_agg(eids + U64(K), values, correl, li, acc)\n"
            b"    coo = average_losses(\n",
        )
        with mock.patch.dict(subject.EXPECTED_GIT_BLOBS, {
            k: subject.git_blob_id(v) for k, v in changed.items()
        }, clear=True):
            with self.assertRaisesRegex(subject.ThresholdProvenanceError, "dataflow"):
                subject.probe_source_bytes(changed)

    def test_missing_file_or_oversized_source_fails_closed(self):
        with self.assertRaisesRegex(subject.ThresholdProvenanceError, "file set"):
            subject.probe_source_bytes({"unexpected": b"x"})
        changed = dict(self.blobs)
        changed["openquake/risklib/riskmodels.py"] = b"x" * (
            subject.MAX_BYTES_PER_SOURCE + 1
        )
        with self.assertRaisesRegex(subject.ThresholdProvenanceError, "size"):
            subject.probe_source_bytes(changed)

    def test_git_blob_hash_matches_standard_git_encoding(self):
        self.assertEqual(
            subject.git_blob_id(b""),
            "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
        )


if __name__ == "__main__":
    unittest.main()
