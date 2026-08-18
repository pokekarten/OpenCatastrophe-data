# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import profile_esrm20_exposure_v10_tree as profile


class ExposureV10TreeAuthorityTests(unittest.TestCase):
    def _assert_drift_fails_before_provider(self, mutation) -> None:
        provider_open_attempted = False

        def forbidden_build_opener(*args, **kwargs):
            nonlocal provider_open_attempted
            provider_open_attempted = True
            raise AssertionError("provider I/O must not be reached after authority drift")

        with mock.patch.object(
            profile.transport.urllib.request, "build_opener", forbidden_build_opener
        ):
            with mutation:
                with self.assertRaisesRegex(
                    profile.ExposureTreeProfileError, "authority drifted"
                ):
                    profile.profile_v10_tree()

        self.assertFalse(provider_open_attempted)

    def test_tree_identity_helper_rebinding_fails_before_provider_io(self) -> None:
        self._assert_drift_fails_before_provider(
            mock.patch.object(
                profile, "_tree_identity_sha256", lambda entries: "0" * 64
            )
        )

    def test_canonical_entry_helper_rebinding_fails_before_provider_io(self) -> None:
        self._assert_drift_fails_before_provider(
            mock.patch.object(profile, "_canonical_entry", lambda raw: raw)
        )

    def test_tree_url_helper_rebinding_fails_before_provider_io(self) -> None:
        self._assert_drift_fails_before_provider(
            mock.patch.object(
                profile,
                "_tree_url",
                lambda commit_sha, page: "https://example.invalid/tree",
            )
        )

    def test_entry_bound_mutation_fails_before_provider_io(self) -> None:
        self._assert_drift_fails_before_provider(
            mock.patch.object(profile, "MAX_TREE_ENTRIES", 1)
        )

    def test_hash_implementation_rebinding_fails_before_provider_io(self) -> None:
        self._assert_drift_fails_before_provider(
            mock.patch.object(profile.hashlib, "sha256", lambda payload: object())
        )


if __name__ == "__main__":
    unittest.main()
