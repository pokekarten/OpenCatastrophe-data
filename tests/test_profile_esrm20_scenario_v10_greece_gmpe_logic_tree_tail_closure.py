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


class GreeceGmpeLogicTreeTailClosureTests(unittest.TestCase):
    def test_rejects_non_whitespace_tail_text_between_valid_leaf_children(self):
        raw = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><logicTree><logicTreeBranchingLevel><logicTreeBranchSet><logicTreeBranch><uncertaintyModel>ExampleGSIM</uncertaintyModel>unexpected-tail<uncertaintyWeight>1.0</uncertaintyWeight></logicTreeBranch></logicTreeBranchSet></logicTreeBranchingLevel></logicTree></nrml>'''

        with self.assertRaisesRegex(subject.GmpeLogicTreeProfileError, "non_whitespace_tail_text_forbidden"):
            _profile(raw)

    def test_allows_whitespace_only_tail_text(self):
        raw = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><logicTree><logicTreeBranchingLevel><logicTreeBranchSet><logicTreeBranch><uncertaintyModel>ExampleGSIM</uncertaintyModel>\n  <uncertaintyWeight>1.0</uncertaintyWeight>\n</logicTreeBranch></logicTreeBranchSet></logicTreeBranchingLevel></logicTree></nrml>'''

        result = _profile(raw)
        self.assertEqual(result["branch_count"], 1)
        self.assertEqual(result["uncertainty_model_count"], 1)
        self.assertEqual(result["uncertainty_weight_count"], 1)


if __name__ == "__main__":
    unittest.main()
