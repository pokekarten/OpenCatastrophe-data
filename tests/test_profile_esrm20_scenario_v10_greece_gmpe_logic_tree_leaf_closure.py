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


class GreeceGmpeLogicTreeLeafClosureTests(unittest.TestCase):
    def test_rejects_nested_element_inside_uncertainty_model(self):
        raw = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><logicTree><logicTreeBranchingLevel><logicTreeBranchSet><logicTreeBranch><uncertaintyModel>Example<extra/></uncertaintyModel><uncertaintyWeight>1</uncertaintyWeight></logicTreeBranch></logicTreeBranchSet></logicTreeBranchingLevel></logicTree></nrml>'''
        with self.assertRaisesRegex(
            subject.GmpeLogicTreeProfileError,
            "unexpected_leaf_child:uncertaintyModel",
        ):
            _profile(raw)

    def test_rejects_nested_element_inside_uncertainty_weight(self):
        raw = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><logicTree><logicTreeBranchingLevel><logicTreeBranchSet><logicTreeBranch><uncertaintyModel>Example</uncertaintyModel><uncertaintyWeight>1<extra/></uncertaintyWeight></logicTreeBranch></logicTreeBranchSet></logicTreeBranchingLevel></logicTree></nrml>'''
        with self.assertRaisesRegex(
            subject.GmpeLogicTreeProfileError,
            "unexpected_leaf_child:uncertaintyWeight",
        ):
            _profile(raw)


if __name__ == "__main__":
    unittest.main()
