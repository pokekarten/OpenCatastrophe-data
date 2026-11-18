# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import json
import unittest
from research_runners.ciara_missing_day_acquisition import validate_metadata, VARIABLE

class MetadataTest(unittest.TestCase):
    def test_time_origin_drift_rejected(self):
        with self.assertRaises(ValueError):
            validate_metadata('time/.zattrs',json.dumps({'units':'hours since 1970-01-01','calendar':'gregorian'}))
    def test_raster_drift_rejected(self):
        with self.assertRaises(ValueError):
            validate_metadata(VARIABLE+'/.zarray',json.dumps({'chunks':[24,721,1440],'shape':[100,721,1440],'dtype':'<f4'}))
    def test_expected_time_axis(self):
        validate_metadata('time/.zattrs',json.dumps({'units':'hours since 1900-01-01','calendar':'proleptic_gregorian'}))
