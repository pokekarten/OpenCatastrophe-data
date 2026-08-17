# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import contextlib
import hashlib
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_site_openquake_runtime as subject


class SiteRuntimeGmmHelperRegressionTests(unittest.TestCase):
    def test_adapter_delegates_to_reviewed_exact_gmm_helper(self) -> None:
        payload = b"exact-gmm-regression-bytes"
        digest = hashlib.sha256(payload).hexdigest()

        @contextlib.contextmanager
        def binding():
            yield

        with (
            mock.patch.object(subject, "_require_contract"),
            mock.patch.object(subject._esrm_runtime, "esrm20_binding", binding),
            mock.patch.object(
                subject._base_runtime,
                "_acquire_exact_gmm",
                return_value=payload,
            ) as acquire,
            mock.patch.object(subject, "GMM_EXPECTED_BYTE_COUNT", len(payload)),
            mock.patch.object(subject, "GMM_EXPECTED_SHA256", digest),
        ):
            self.assertEqual(subject._acquire_verified_gmm_bytes(), payload)

        acquire.assert_called_once_with()

    def test_adapter_does_not_depend_on_removed_helper_name(self) -> None:
        self.assertFalse(hasattr(subject._base_runtime, "_acquire_gmm_bytes"))
        self.assertTrue(hasattr(subject._base_runtime, "_acquire_exact_gmm"))


if __name__ == "__main__":
    unittest.main()
