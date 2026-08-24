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


class SourceModelGmlGeometryTests(unittest.TestCase):
    def test_accepts_standard_gml_geometry_descendants(self) -> None:
        payload = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.4" xmlns:gml="http://www.opengis.net/gml"><sourceModel><pointSource id="p1" tectonicRegion="Shallow Default"><pointGeometry><gml:Point><gml:pos>20.0 42.0</gml:pos></gml:Point></pointGeometry></pointSource></sourceModel></nrml>'''
        profile = _profile(payload)

        self.assertEqual(
            profile["tectonic_region_type_counts"], {"Shallow Default": 1}
        )
        self.assertEqual(profile["trt_provenance_counts"], {"direct_source": 1})
        self.assertEqual(profile["element_type_counts"]["Point"], 1)
        self.assertEqual(profile["element_type_counts"]["pos"], 1)

    def test_rejects_unknown_foreign_geometry_namespace(self) -> None:
        payload = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.4" xmlns:foreign="urn:not-gml"><sourceModel><pointSource id="p1" tectonicRegion="Shallow Default"><pointGeometry><foreign:Point/></pointGeometry></pointSource></sourceModel></nrml>'''
        with self.assertRaisesRegex(
            subject.SourceModelContentProfileError, "unsupported descendant namespace"
        ):
            _profile(payload)


if __name__ == "__main__":
    unittest.main()
