# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from unittest import mock

from scripts import profile_esrm20_risk_v10_tree as target


_SHA_A = "1" * 40
_SHA_B = "2" * 40
_SHA_C = "3" * 40


class _Response:
    def __init__(
        self,
        url: str,
        payload: bytes,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = 200
        self._url = url
        self._payload = payload
        self._offset = 0
        self.headers = dict(headers or {})
        self.headers.setdefault("Content-Length", str(len(payload)))

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        if size is None or size < 0:
            size = len(self._payload) - self._offset
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


class _Clock:
    def __call__(self) -> float:
        return 1.0


def _entry(
    path: str,
    object_id: str,
    *,
    entry_type: str = "blob",
) -> dict[str, str]:
    mode = "040000" if entry_type == "tree" else "100644"
    return {
        "id": object_id,
        "name": path.rsplit("/", 1)[-1],
        "type": entry_type,
        "path": path,
        "mode": mode,
    }


def _opener_for(
    entries: list[dict[str, str]],
    *,
    tag_commit: str = target.EXPECTED_COMMIT_SHA,
    tree_headers: dict[str, str] | None = None,
):
    tag_url = target._tag_url()
    tree_url = target._tree_url(target.EXPECTED_COMMIT_SHA, 1)
    tag = json.dumps(
        {
            "name": target.RELEASE_TAG,
            "target": tag_commit,
            "commit": {"id": tag_commit},
        },
        separators=(",", ":"),
    ).encode()
    tree = json.dumps(entries, separators=(",", ":")).encode()

    def opener(request, timeout):
        del timeout
        if request.full_url == tag_url:
            return _Response(tag_url, tag)
        if request.full_url == tree_url:
            headers = {
                "X-Page": "1",
                "X-Per-Page": str(target.TREE_PER_PAGE),
                "X-Next-Page": "",
            }
            headers.update(tree_headers or {})
            return _Response(tree_url, tree, headers=headers)
        raise AssertionError(f"unexpected URL: {request.full_url}")

    return opener


class RiskV10TreeProfileTests(unittest.TestCase):
    def test_profile_freezes_sorted_risk_inventory_and_exact_country_candidate(self) -> None:
        entries = [
            _entry("Risk/European_Risk_Country.csv", _SHA_B),
            _entry("Risk/subdir", _SHA_C, entry_type="tree"),
            _entry("Risk/European_Risk_Admin1.csv", _SHA_A),
        ]
        result = target._profile_v10_tree_for_test(
            opener=_opener_for(entries),
            monotonic=_Clock(),
        )

        self.assertEqual(result["commit_sha"], target.EXPECTED_COMMIT_SHA)
        self.assertEqual(result["subtree_path"], "Risk")
        self.assertEqual(
            [item["path"] for item in result["risk_inventory"]],
            [
                "Risk/European_Risk_Admin1.csv",
                "Risk/European_Risk_Country.csv",
                "Risk/subdir",
            ],
        )
        self.assertEqual(result["country_risk_path_status"], "blob")
        self.assertTrue(result["country_risk_blob_candidate_present"])
        self.assertEqual(
            result["country_risk_path_entry"],
            {
                "mode": "100644",
                "object_sha1": _SHA_B,
                "path": "Risk/European_Risk_Country.csv",
                "type": "blob",
            },
        )
        canonical = (
            f"blob\t100644\t{_SHA_A}\tRisk/European_Risk_Admin1.csv\n"
            f"blob\t100644\t{_SHA_B}\tRisk/European_Risk_Country.csv\n"
            f"tree\t040000\t{_SHA_C}\tRisk/subdir\n"
        ).encode()
        self.assertEqual(
            result["tree_identity_sha256"],
            hashlib.sha256(canonical).hexdigest(),
        )
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["country_risk_bytes_verified"])
        self.assertFalse(result["country_risk_schema_verified"])
        self.assertFalse(result["reference_loss_agreement_verified"])

    def test_candidate_absence_is_recorded_without_inventing_a_replacement(self) -> None:
        result = target._profile_v10_tree_for_test(
            opener=_opener_for([_entry("Risk/European_Risk_Admin1.csv", _SHA_A)]),
            monotonic=_Clock(),
        )
        self.assertEqual(result["country_risk_path_status"], "absent")
        self.assertIsNone(result["country_risk_path_entry"])
        self.assertFalse(result["country_risk_blob_candidate_present"])
        self.assertEqual(
            result["risk_inventory"][0]["path"],
            "Risk/European_Risk_Admin1.csv",
        )

    def test_candidate_path_as_tree_is_not_promoted_to_blob(self) -> None:
        result = target._profile_v10_tree_for_test(
            opener=_opener_for(
                [_entry("Risk/European_Risk_Country.csv", _SHA_A, entry_type="tree")]
            ),
            monotonic=_Clock(),
        )
        self.assertEqual(result["country_risk_path_status"], "tree")
        self.assertFalse(result["country_risk_blob_candidate_present"])
        self.assertEqual(result["country_risk_path_entry"]["type"], "tree")

    def test_entry_outside_fixed_risk_subtree_fails_closed(self) -> None:
        with self.assertRaises(target.RiskTreeProfileError) as ctx:
            target._profile_v10_tree_for_test(
                opener=_opener_for([_entry("Exposure/not-risk.xml", _SHA_A)]),
                monotonic=_Clock(),
            )
        self.assertEqual(
            ctx.exception.failure_class,
            "tree_metadata_validation_failure",
        )

    def test_duplicate_path_fails_closed(self) -> None:
        duplicate = _entry("Risk/European_Risk_Country.csv", _SHA_A)
        with self.assertRaises(target.RiskTreeProfileError) as ctx:
            target._profile_v10_tree_for_test(
                opener=_opener_for([duplicate, dict(duplicate)]),
                monotonic=_Clock(),
            )
        self.assertEqual(
            ctx.exception.failure_class,
            "tree_metadata_validation_failure",
        )

    def test_terminal_page_must_reconcile_with_reported_total_pages(self) -> None:
        with self.assertRaises(target.RiskTreeProfileError) as ctx:
            target._profile_v10_tree_for_test(
                opener=_opener_for(
                    [_entry("Risk/European_Risk_Country.csv", _SHA_A)],
                    tree_headers={
                        "X-Total-Pages": "2",
                        "X-Total": "101",
                    },
                ),
                monotonic=_Clock(),
            )
        self.assertEqual(
            ctx.exception.failure_class,
            "tree_metadata_validation_failure",
        )

    def test_reported_total_pages_and_entries_must_agree(self) -> None:
        with self.assertRaises(target.RiskTreeProfileError) as ctx:
            target._profile_v10_tree_for_test(
                opener=_opener_for(
                    [_entry("Risk/European_Risk_Country.csv", _SHA_A)],
                    tree_headers={
                        "X-Total-Pages": "1",
                        "X-Total": "101",
                    },
                ),
                monotonic=_Clock(),
            )
        self.assertEqual(
            ctx.exception.failure_class,
            "tree_metadata_validation_failure",
        )

    def test_inventory_count_must_equal_provider_total_when_reported(self) -> None:
        with self.assertRaises(target.RiskTreeProfileError) as ctx:
            target._profile_v10_tree_for_test(
                opener=_opener_for(
                    [_entry("Risk/European_Risk_Country.csv", _SHA_A)],
                    tree_headers={
                        "X-Total-Pages": "1",
                        "X-Total": "2",
                    },
                ),
                monotonic=_Clock(),
            )
        self.assertEqual(
            ctx.exception.failure_class,
            "tree_metadata_validation_failure",
        )

    def test_tag_commit_drift_fails_closed_before_tree_use(self) -> None:
        wrong = "f" * 40
        with self.assertRaises(target.RiskTreeProfileError) as ctx:
            target._profile_v10_tree_for_test(
                opener=_opener_for(
                    [_entry("Risk/European_Risk_Country.csv", _SHA_A)],
                    tag_commit=wrong,
                ),
                monotonic=_Clock(),
            )
        self.assertEqual(
            ctx.exception.failure_class,
            "tag_metadata_validation_failure",
        )

    def test_production_authority_rejects_target_constant_drift(self) -> None:
        with mock.patch.object(target, "COUNTRY_RISK_PATH", "Risk/other.csv"):
            with self.assertRaisesRegex(
                target.RiskTreeProfileError,
                "trusted risk-tree target authority drifted",
            ):
                target._require_production_authority()


if __name__ == "__main__":
    unittest.main()
