# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline regression: urllib opener timeout must be a keyword, never POST data.

This specifically guards against an earlier incorrect
opener.open(request, timeout) positional call, which silently passes the
integer as an HTTP message body and makes live public direct GETs fail.
No provider network or GitHub secrets are used.
"""
from __future__ import annotations

import unittest
from unittest.mock import patch
from urllib import request

from scripts.probe_nl_cbs_83673ned_2025_original_three_v0 import direct_open


class CBSOriginalGETTimeoutKeywordTests(unittest.TestCase):
    def test_urllib_timeout_is_not_treated_as_request_body(self):
        calls = []
        marker = object()

        class FakeOpener:
            def open(self, req, *args, **kwargs):
                calls.append((req, args, kwargs))
                return marker

        req = request.Request("https://opendata.cbs.nl/ODataApi/OData/83673NED/TableInfos?$top=1", method="GET")
        with patch("scripts.probe_nl_cbs_83673ned_2025_original_three_v0.request.build_opener", return_value=FakeOpener()):
            observed = direct_open(req, 25)
        self.assertIs(observed, marker)
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][0], req)
        self.assertEqual(calls[0][0].get_method(), "GET")
        self.assertEqual(calls[0][1], ())
        self.assertEqual(calls[0][2], {"timeout": 25})


if __name__ == "__main__":
    unittest.main()
