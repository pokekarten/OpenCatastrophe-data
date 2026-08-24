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


class GreeceGmpeLogicTreeContainerTextTests(unittest.TestCase):
    def test_rejects_non_whitespace_text_on_structural_container(self):
        raw = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><logicTree>unexpected<logicTreeBranchingLevel><logicTreeBranchSet><logicTreeBranch><uncertaintyModel>X</uncertaintyModel><uncertaintyWeight>1</uncertaintyWeight></logicTreeBranch></logicTreeBranchSet></logicTreeBranchingLevel></logicTree></nrml>'''
        with self.assertRaisesRegex(
            subject.GmpeLogicTreeProfileError,
            "non_whitespace_container_text_forbidden:logicTree",
        ):
            _profile(raw)

    def test_allows_formatting_whitespace_on_structural_containers(self):
        raw = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">\n  <logicTree>\n    <logicTreeBranchingLevel>\n      <logicTreeBranchSet>\n        <logicTreeBranch>\n          <uncertaintyModel>X</uncertaintyModel>\n          <uncertaintyWeight>1</uncertaintyWeight>\n        </logicTreeBranch>\n      </logicTreeBranchSet>\n    </logicTreeBranchingLevel>\n  </logicTree>\n</nrml>'''
        result = _profile(raw)
        self.assertEqual(result["branch_count"], 1)
        self.assertEqual(result["non_whitespace_text_element_count"], 2)
        self.assertFalse(result["gmpe_semantics_verified"])
        self.assertFalse(result["model_use_authorized"])


if __name__ == "__main__":
    unittest.main()
