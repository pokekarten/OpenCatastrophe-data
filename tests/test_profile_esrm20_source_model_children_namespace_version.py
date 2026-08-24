# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from scripts import profile_esrm20_source_model_children as subject

PATH = next(iter(subject.RECEIPTS))


def _profile(payload: bytes) -> dict:
    receipt = (len(payload), hashlib.sha256(payload).hexdigest())
    with patch.dict(subject.RECEIPTS, {PATH: receipt}, clear=True):
        return subject.profile_source_model(PATH, payload)


class SourceModelNamespaceVersionStructureTests(unittest.TestCase):
    def test_nrml_04_rejects_source_group_children(self) -> None:
        payload = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"><sourceModel><sourceGroup tectonicRegion="Shallow Default"><pointSource id="p1"/></sourceGroup></sourceModel></nrml>'''
        with self.assertRaisesRegex(
            subject.SourceModelContentProfileError,
            "NRML 0.4 sourceModel must contain direct source children",
        ):
            _profile(payload)

    def test_nrml_05_rejects_direct_source_children(self) -> None:
        payload = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><sourceModel><pointSource id="p1" tectonicRegion="Shallow Default"/></sourceModel></nrml>'''
        with self.assertRaisesRegex(
            subject.SourceModelContentProfileError,
            "NRML 0.5 sourceModel must contain sourceGroup children",
        ):
            _profile(payload)


if __name__ == "__main__":
    unittest.main()
