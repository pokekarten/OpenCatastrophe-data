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


class GreeceGmpeLogicTreeProfileTests(unittest.TestCase):
    def test_profiles_structure_without_returning_models(self):
        raw = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><logicTree logicTreeID="lt1"><logicTreeBranchingLevel branchingLevelID="bl1"><logicTreeBranchSet branchSetID="bs1" uncertaintyType="gmpeModel"><logicTreeBranch branchID="b1"><uncertaintyModel>ExampleGSIM</uncertaintyModel><uncertaintyWeight>0.6</uncertaintyWeight></logicTreeBranch><logicTreeBranch branchID="b2"><uncertaintyModel>OtherGSIM</uncertaintyModel><uncertaintyWeight>0.4</uncertaintyWeight></logicTreeBranch></logicTreeBranchSet></logicTreeBranchingLevel></logicTree></nrml>'''
        result = _profile(raw)
        self.assertEqual(result["branch_set_count"], 1)
        self.assertEqual(result["branch_count"], 2)
        self.assertEqual(result["uncertainty_model_count"], 2)
        self.assertEqual(result["uncertainty_weight_count"], 2)
        self.assertEqual(result["attribute_name_counts"]["uncertaintyType"], 1)
        self.assertFalse(result["raw_model_values_returned"])
        self.assertNotIn("ExampleGSIM", repr(result))
        self.assertFalse(result["gmpe_semantics_verified"])
        self.assertFalse(result["model_use_authorized"])

    def test_identity_precedes_xml_parse(self):
        raw = b"<broken"
        with self.assertRaisesRegex(subject.GmpeLogicTreeProfileError, "sha256"):
            subject._profile_verified(raw, expected_byte_count=len(raw), expected_sha256="0" * 64)

    def test_rejects_dtd_and_entities(self):
        raw = b'<!DOCTYPE nrml [<!ENTITY x "y">]><nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><logicTree>&x;</logicTree></nrml>'
        with self.assertRaisesRegex(subject.GmpeLogicTreeProfileError, "dtd_or_entity"):
            _profile(raw)

    def test_requires_nrml05_logic_tree_root(self):
        raw = b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"><logicTree/></nrml>'
        with self.assertRaisesRegex(subject.GmpeLogicTreeProfileError, "unexpected_nrml_root"):
            _profile(raw)

    def test_rejects_branch_without_weight(self):
        raw = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><logicTree><logicTreeBranchingLevel><logicTreeBranchSet><logicTreeBranch><uncertaintyModel>X</uncertaintyModel></logicTreeBranch></logicTreeBranchSet></logicTreeBranchingLevel></logicTree></nrml>'''
        with self.assertRaisesRegex(subject.GmpeLogicTreeProfileError, "branch_direct_child_cardinality"):
            _profile(raw)

    def test_rejects_aggregate_balanced_but_per_branch_invalid_shape(self):
        raw = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><logicTree><logicTreeBranchingLevel><logicTreeBranchSet><logicTreeBranch branchID="b1"><uncertaintyModel>A</uncertaintyModel><uncertaintyModel>B</uncertaintyModel><uncertaintyWeight>0.5</uncertaintyWeight><uncertaintyWeight>0.5</uncertaintyWeight></logicTreeBranch><logicTreeBranch branchID="b2"/></logicTreeBranchSet></logicTreeBranchingLevel></logicTree></nrml>'''
        with self.assertRaisesRegex(subject.GmpeLogicTreeProfileError, "branch_direct_child_cardinality"):
            _profile(raw)

    def test_rejects_unexpected_direct_branch_child(self):
        raw = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><logicTree><logicTreeBranchingLevel><logicTreeBranchSet><logicTreeBranch><uncertaintyModel>X</uncertaintyModel><uncertaintyWeight>1</uncertaintyWeight><extra/></logicTreeBranch></logicTreeBranchSet></logicTreeBranchingLevel></logicTree></nrml>'''
        with self.assertRaisesRegex(subject.GmpeLogicTreeProfileError, "branch_direct_child_cardinality"):
            _profile(raw)

    def test_rejects_foreign_namespace(self):
        raw = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><logicTree><logicTreeBranchingLevel><logicTreeBranchSet><logicTreeBranch><uncertaintyModel>X</uncertaintyModel><uncertaintyWeight>1</uncertaintyWeight><x xmlns="urn:other"/></logicTreeBranch></logicTreeBranchSet></logicTreeBranchingLevel></logicTree></nrml>'''
        with self.assertRaisesRegex(subject.GmpeLogicTreeProfileError, "foreign_xml_namespace"):
            _profile(raw)

    def test_fixed_wrapper_rejects_synthetic_bytes(self):
        with self.assertRaisesRegex(subject.GmpeLogicTreeProfileError, "byte_count"):
            subject.profile_fixed_greece_gmpe_logic_tree(b"<nrml/>")


if __name__ == "__main__":
    unittest.main()
