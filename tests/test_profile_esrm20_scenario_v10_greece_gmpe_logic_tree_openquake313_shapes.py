# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest

from scripts import profile_esrm20_scenario_v10_greece_gmpe_logic_tree as subject


def _profile(raw: bytes):
    return subject._profile_verified(
        raw,
        expected_byte_count=len(raw),
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )


def _branch(branch_id: str = "b1") -> str:
    return (
        f'<logicTreeBranch branchID="{branch_id}">'
        "<uncertaintyModel>ExampleGSIM</uncertaintyModel>"
        "<uncertaintyWeight>1.0</uncertaintyWeight>"
        "</logicTreeBranch>"
    )


def _nrml(logic_tree_body: str) -> bytes:
    return (
        '<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">'
        '<logicTree logicTreeID="lt1">'
        f"{logic_tree_body}"
        "</logicTree>"
        "</nrml>"
    ).encode("utf-8")


class GreeceGmpeOpenQuake313ShapeTests(unittest.TestCase):
    def test_accepts_direct_branch_set_shape_used_by_openquake313(self):
        raw = _nrml(
            '<logicTreeBranchSet branchSetID="bs1" uncertaintyType="gmpeModel">'
            f"{_branch()}"
            "</logicTreeBranchSet>"
        )

        result = _profile(raw)

        self.assertEqual(result["branching_level_count"], 0)
        self.assertEqual(result["branch_set_count"], 1)
        self.assertEqual(result["branch_count"], 1)
        self.assertFalse(result["raw_model_values_returned"])
        self.assertFalse(result["gmpe_semantics_verified"])
        self.assertFalse(result["model_use_authorized"])

    def test_preserves_legacy_branching_level_shape(self):
        raw = _nrml(
            '<logicTreeBranchingLevel branchingLevelID="bl1">'
            '<logicTreeBranchSet branchSetID="bs1" uncertaintyType="gmpeModel">'
            f"{_branch()}"
            "</logicTreeBranchSet>"
            "</logicTreeBranchingLevel>"
        )

        result = _profile(raw)

        self.assertEqual(result["branching_level_count"], 1)
        self.assertEqual(result["branch_set_count"], 1)
        self.assertEqual(result["branch_count"], 1)

    def test_accepts_mixed_direct_and_legacy_top_level_nodes_like_openquake313(self):
        raw = _nrml(
            '<logicTreeBranchSet branchSetID="direct" uncertaintyType="gmpeModel">'
            f"{_branch('direct-branch')}"
            "</logicTreeBranchSet>"
            '<logicTreeBranchingLevel branchingLevelID="legacy">'
            '<logicTreeBranchSet branchSetID="wrapped" uncertaintyType="gmpeModel">'
            f"{_branch('wrapped-branch')}"
            "</logicTreeBranchSet>"
            "</logicTreeBranchingLevel>"
        )

        result = _profile(raw)

        self.assertEqual(result["branching_level_count"], 1)
        self.assertEqual(result["branch_set_count"], 2)
        self.assertEqual(result["branch_count"], 2)

    def test_rejects_unknown_direct_child_of_logic_tree(self):
        raw = _nrml("<wrapper/>")

        with self.assertRaisesRegex(
            subject.GmpeLogicTreeProfileError,
            "unexpected_direct_child:logicTree:wrapper",
        ):
            _profile(raw)

    def test_rejects_nested_branch_set_instead_of_branch(self):
        raw = _nrml(
            '<logicTreeBranchSet branchSetID="outer" uncertaintyType="gmpeModel">'
            '<logicTreeBranchSet branchSetID="inner" uncertaintyType="gmpeModel">'
            f"{_branch()}"
            "</logicTreeBranchSet>"
            "</logicTreeBranchSet>"
        )

        with self.assertRaisesRegex(
            subject.GmpeLogicTreeProfileError,
            "unexpected_direct_child:logicTreeBranchSet:logicTreeBranchSet",
        ):
            _profile(raw)


if __name__ == "__main__":
    unittest.main()
