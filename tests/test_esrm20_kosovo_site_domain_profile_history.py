# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_site_domain_profile_action as subject
from tests.test_esrm20_kosovo_site_domain_profile_action import _payload

CURRENT_SHA = "a" * 40
OLD_SHA = "b" * 40


def _body(sha: str) -> str:
    result = subject._run_site_domain(execution_sha=sha, acquirer=_payload)
    return subject.RESULT_MARKER + "\n" + json.dumps(
        result, sort_keys=True, separators=(",", ":")
    )


class KosovoSiteDomainHistoryTests(unittest.TestCase):
    def test_valid_historical_result_does_not_deduplicate_new_exact_head(self) -> None:
        comments = [
            {
                "id": 1,
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": _body(OLD_SHA),
            }
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            self.assertFalse(
                subject.has_terminal_site_domain_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=CURRENT_SHA,
                )
            )

    def test_current_result_deduplicates_even_after_valid_historical_result(self) -> None:
        comments = [
            {
                "id": 1,
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": _body(OLD_SHA),
            },
            {
                "id": 2,
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": _body(CURRENT_SHA),
            },
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            self.assertTrue(
                subject.has_terminal_site_domain_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=CURRENT_SHA,
                )
            )

    def test_internally_inconsistent_historical_sha_fails_closed(self) -> None:
        result = subject._run_site_domain(execution_sha=OLD_SHA, acquirer=_payload)
        result["target_sha"] = "c" * 40
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        comments = [
            {
                "id": 1,
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": body,
            }
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            with self.assertRaisesRegex(
                subject.SiteDomainActionError, "historical SHA identity is inconsistent"
            ):
                subject.has_terminal_site_domain_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=CURRENT_SHA,
                )


if __name__ == "__main__":
    unittest.main()
