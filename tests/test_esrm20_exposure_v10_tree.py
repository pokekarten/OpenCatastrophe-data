# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from unittest import mock

from scripts import profile_esrm20_exposure_v10_tree as profile

COMMIT = profile.EXPECTED_COMMIT_SHA
ANNOTATED_TAG_OBJECT = "f" * 40


class FakeHeaders(dict):
    def get(self, key, default=None):
        for observed, value in self.items():
            if observed.casefold() == key.casefold():
                return value
        return default


class FakeResponse:
    def __init__(self, payload: bytes, url: str, *, headers=None, status: int = 200) -> None:
        self._payload = payload
        self._offset = 0
        self._url = url
        self.status = status
        self.headers = FakeHeaders(headers or {})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        end = len(self._payload) if size is None or size < 0 else min(
            len(self._payload), self._offset + size
        )
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk


def _json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _entry(path: str, entry_type: str, object_id: str, *, mode: str | None = None):
    return {
        "id": object_id,
        "name": path.rsplit("/", 1)[-1],
        "type": entry_type,
        "path": path,
        "mode": mode or ("040000" if entry_type == "tree" else "100644"),
    }


class ExposureV10TreeProfileTests(unittest.TestCase):
    def _opener(self, pages: list[list[dict[str, str]]]):
        calls: list[str] = []

        def opener(request, timeout):
            calls.append(request.full_url)
            if len(calls) == 1:
                self.assertEqual(request.full_url, profile._tag_url())
                return FakeResponse(
                    _json_bytes(
                        {
                            "name": "v1.0",
                            "target": ANNOTATED_TAG_OBJECT,
                            "commit": {"id": COMMIT},
                        }
                    ),
                    request.full_url,
                )
            page = len(calls) - 1
            self.assertEqual(request.full_url, profile._tree_url(COMMIT, page))
            next_page = "" if page == len(pages) else str(page + 1)
            return FakeResponse(
                _json_bytes(pages[page - 1]),
                request.full_url,
                headers={
                    "X-Page": str(page),
                    "X-Per-Page": str(profile.TREE_PER_PAGE),
                    "X-Next-Page": next_page,
                },
            )

        return opener, calls

    def test_fixed_subtree_profile_is_metadata_only_and_deterministic(self) -> None:
        pages = [
            [
                _entry(
                    "Exposure_30arcsec/Exposure_Model_Andorra.xml",
                    "blob",
                    "1" * 40,
                ),
                _entry("Exposure_30arcsec/nested", "tree", "2" * 40),
            ],
            [
                _entry(
                    "Exposure_30arcsec/Exposure_Model_Kosovo.xml",
                    "blob",
                    "3" * 40,
                )
            ],
        ]
        opener, calls = self._opener(pages)
        result = profile._profile_v10_tree_for_test(
            opener=opener, monotonic=lambda: 0.0
        )
        self.assertEqual(len(calls), 3)
        self.assertTrue(all("path=Exposure_30arcsec" in url for url in calls[1:]))
        self.assertTrue(all("recursive=true" in url for url in calls[1:]))
        self.assertNotIn("/repository/files/", "\n".join(calls))
        self.assertEqual(result["project_id"], 269)
        self.assertEqual(result["commit_sha"], COMMIT)
        self.assertEqual(result["subtree_path"], "Exposure_30arcsec")
        self.assertEqual(result["pages_read"], 2)
        self.assertEqual(result["entry_count"], 3)
        self.assertEqual(
            result["kosovo_named_xml_candidates"],
            [
                {
                    "mode": "100644",
                    "object_sha1": "3" * 40,
                    "path": "Exposure_30arcsec/Exposure_Model_Kosovo.xml",
                    "type": "blob",
                }
            ],
        )
        entries = sorted(
            [item for page in pages for item in page], key=lambda item: item["path"]
        )
        canonical = "".join(
            f"{item['type']}\t{item['mode']}\t{item['id']}\t{item['path']}\n"
            for item in entries
        ).encode("utf-8")
        self.assertEqual(
            result["tree_identity_sha256"], hashlib.sha256(canonical).hexdigest()
        )
        for field in (
            "provider_file_bytes_read",
            "external_bytes_persisted",
            "exact_kosovo_exposure_selected",
            "value_structural_wiring_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertFalse(result[field])

    def test_pagination_header_is_read_from_response_and_gap_fails_closed(self) -> None:
        entries = [
            _entry(
                "Exposure_30arcsec/Exposure_Model_Kosovo.xml",
                "blob",
                "3" * 40,
            )
        ]
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse(
                    _json_bytes(
                        {
                            "name": "v1.0",
                            "target": COMMIT,
                            "commit": {"id": COMMIT},
                        }
                    ),
                    request.full_url,
                )
            return FakeResponse(
                _json_bytes(entries),
                request.full_url,
                headers={"X-Page": "1", "X-Per-Page": "100", "X-Next-Page": "3"},
            )

        with self.assertRaisesRegex(profile.ExposureTreeProfileError, "not contiguous"):
            profile._profile_v10_tree_for_test(opener=opener, monotonic=lambda: 0.0)

    def test_invalid_tag_target_object_fails_before_tree_request(self) -> None:
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            return FakeResponse(
                _json_bytes(
                    {
                        "name": "v1.0",
                        "target": "not-a-git-object",
                        "commit": {"id": COMMIT},
                    }
                ),
                request.full_url,
            )

        with self.assertRaisesRegex(profile.ExposureTreeProfileError, "target object id"):
            profile._profile_v10_tree_for_test(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(calls, 1)

    def test_repointed_tag_fails_before_tree_request(self) -> None:
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            return FakeResponse(
                _json_bytes(
                    {
                        "name": "v1.0",
                        "target": "a" * 40,
                        "commit": {"id": "a" * 40},
                    }
                ),
                request.full_url,
            )

        with self.assertRaisesRegex(profile.ExposureTreeProfileError, "frozen commit"):
            profile._profile_v10_tree_for_test(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(calls, 1)

    def test_path_mode_duplicate_and_candidate_cardinality_fail_closed(self) -> None:
        cases = {
            "escape": [
                _entry("Exposure_30arcsec/../Kosovo.xml", "blob", "4" * 40)
            ],
            "mode": [
                _entry(
                    "Exposure_30arcsec/Kosovo.xml", "blob", "4" * 40, mode="120000"
                )
            ],
            "no-kosovo": [
                _entry("Exposure_30arcsec/Andorra.xml", "blob", "4" * 40)
            ],
            "duplicate": [
                _entry("Exposure_30arcsec/Kosovo.xml", "blob", "4" * 40),
                _entry("Exposure_30arcsec/Kosovo.xml", "blob", "5" * 40),
            ],
        }
        for label, entries in cases.items():
            with self.subTest(label=label):
                opener, _ = self._opener([entries])
                with self.assertRaises(profile.ExposureTreeProfileError):
                    profile._profile_v10_tree_for_test(
                        opener=opener, monotonic=lambda: 0.0
                    )

    def test_production_authority_drift_fails_before_provider_io(self) -> None:
        called = False

        def forged(request, timeout):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        with mock.patch.object(profile.transport, "_open_fixed", forged):
            with self.assertRaisesRegex(
                profile.ExposureTreeProfileError, "execution authority drifted"
            ):
                profile.profile_v10_tree()
        self.assertFalse(called)


if __name__ == "__main__":
    unittest.main()
