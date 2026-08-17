# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_site_openquake_runtime as subject


class _ExpectedDigest:
    def hexdigest(self) -> str:
        return subject.GMM_EXPECTED_SHA256


class SiteRuntimeGmmHelperRegressionTests(unittest.TestCase):
    def test_gmm_acquisition_delegates_to_reviewed_exact_helper(self) -> None:
        payload = b"g" * subject.GMM_EXPECTED_BYTE_COUNT
        with (
            mock.patch.object(
                subject._base_runtime,
                "_acquire_exact_gmm",
                return_value=payload,
            ) as acquire,
            mock.patch.object(
                subject.hashlib,
                "sha256",
                return_value=_ExpectedDigest(),
            ),
        ):
            observed = subject._acquire_verified_gmm_bytes()

        self.assertEqual(observed, payload)
        acquire.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
