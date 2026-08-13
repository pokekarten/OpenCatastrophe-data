# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import io
import json
import socket
import unittest

from scripts.acquire_efehr_gitlab_receipt import (
    DATASET_ID,
    MAX_CANARY_BYTES,
    OPERATION_ID,
    PROJECT_ID,
    RELEASE_TAG,
    REPOSITORY_PATH,
    SCHEMA_VERSION,
    SOURCE_ISSUE,
    TAG_API_URL,
    EfehrAcquisitionError,
    _classify_public_sockaddrs,
    acquire_canary,
)
from scripts.efehr_gitlab_receipt import raw_file_api_url, validate_target

COMMIT = "a" * 40
RETRIEVED = "2026-08-13T00:45:00Z"
README = b"ESRM20 exposure format companion\n"


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


class FakeResponse(io.BytesIO):
    def __init__(
        self,
        payload: bytes,
        *,
        url: str,
        status: int = 200,
        headers: dict[str, str] | None = None,
        clock: FakeClock | None = None,
        advance_on_read: float = 0.0,
    ) -> None:
        super().__init__(payload)
        self._url = url
        self.status = status
        self.headers = headers if headers is not None else {
            "Content-Length": str(len(payload))
        }
        self.clock = clock
        self.advance_on_read = advance_on_read

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self.clock is not None:
            self.clock.value += self.advance_on_read
        return super().read(size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


class SequenceOpener:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        if not self.responses:
            raise AssertionError("unexpected extra provider request")
        return self.responses.pop(0)


def tag_bytes(
    *,
    name: str = RELEASE_TAG,
    commit_sha: str = COMMIT,
) -> bytes:
    return json.dumps(
        {"name": name, "commit": {"id": commit_sha}},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def expected_file_url() -> str:
    target = validate_target(
        source_issue=SOURCE_ISSUE,
        dataset_id=DATASET_ID,
        project_id=PROJECT_ID,
        commit_sha=COMMIT,
        repository_path=REPOSITORY_PATH,
    )
    return raw_file_api_url(target)


class EfehrTrustedAcquisitionTests(unittest.TestCase):
    def test_happy_path_resolves_tag_then_receipts_only_readme(self) -> None:
        file_url = expected_file_url()
        tag_payload = tag_bytes()
        opener = SequenceOpener(
            [
                FakeResponse(
                    tag_payload,
                    url=TAG_API_URL,
                    headers={
                        "Content-Length": str(len(tag_payload)),
                        "Content-Type": "application/json",
                    },
                ),
                FakeResponse(
                    README,
                    url=file_url,
                    headers={
                        "Content-Length": str(len(README)),
                        "Content-Type": "text/plain; charset=utf-8",
                        "ETag": '"synthetic"',
                    },
                ),
            ]
        )

        receipt = acquire_canary(opener=opener, now=lambda: RETRIEVED)

        self.assertEqual(receipt["schema_version"], SCHEMA_VERSION)
        self.assertEqual(receipt["operation_id"], OPERATION_ID)
        self.assertEqual(receipt["release_tag"], RELEASE_TAG)
        self.assertEqual(receipt["tag_api_url"], TAG_API_URL)
        self.assertEqual(receipt["source_issue"], SOURCE_ISSUE)
        self.assertEqual(receipt["dataset_id"], DATASET_ID)
        self.assertEqual(receipt["project_id"], PROJECT_ID)
        self.assertEqual(receipt["commit_sha"], COMMIT)
        self.assertEqual(receipt["repository_path"], REPOSITORY_PATH)
        self.assertEqual(receipt["requested_url"], file_url)
        self.assertEqual(receipt["final_url"], file_url)
        self.assertEqual(receipt["retrieved_at"], RETRIEVED)
        self.assertEqual(receipt["byte_count"], len(README))
        self.assertEqual(receipt["sha256"], hashlib.sha256(README).hexdigest())
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])
        self.assertEqual(
            [request.full_url for request, _ in opener.requests],
            [TAG_API_URL, file_url],
        )

    def test_tag_identity_and_commit_shape_fail_closed_before_file_fetch(self) -> None:
        for payload in (
            tag_bytes(name="latest"),
            tag_bytes(commit_sha="a" * 39),
            tag_bytes(commit_sha="A" * 40),
            b'{"name":"v1.0","name":"v1.0","commit":{"id":"' + COMMIT.encode() + b'"}}',
            b'{"name":"v1.0","commit":{"id":NaN}}',
        ):
            with self.subTest(payload=payload):
                opener = SequenceOpener([FakeResponse(payload, url=TAG_API_URL)])
                with self.assertRaises(EfehrAcquisitionError):
                    acquire_canary(opener=opener, now=lambda: RETRIEVED)
                self.assertEqual(len(opener.requests), 1)

    def test_tag_redirect_status_length_empty_and_oversize_fail_closed(self) -> None:
        payload = tag_bytes()
        cases = (
            FakeResponse(payload, url=TAG_API_URL + "?drift=1"),
            FakeResponse(payload, url=TAG_API_URL, status=302),
            FakeResponse(
                payload,
                url=TAG_API_URL,
                headers={"Content-Length": str(len(payload) + 1)},
            ),
            FakeResponse(b"", url=TAG_API_URL, headers={}),
            FakeResponse(
                b"x",
                url=TAG_API_URL,
                headers={"Content-Length": "65537"},
            ),
        )
        for response in cases:
            with self.subTest(url=response.geturl(), status=response.status):
                opener = SequenceOpener([response])
                with self.assertRaises(EfehrAcquisitionError):
                    acquire_canary(opener=opener, now=lambda: RETRIEVED)

    def test_artifact_identity_status_headers_and_body_fail_closed(self) -> None:
        file_url = expected_file_url()
        bad_file_responses = (
            FakeResponse(README, url=file_url.replace("https://", "http://", 1)),
            FakeResponse(README, url=file_url, status=404),
            FakeResponse(
                README,
                url=file_url,
                headers={"Content-Length": str(len(README) + 1)},
            ),
            FakeResponse(b"", url=file_url, headers={}),
            FakeResponse(
                b"x",
                url=file_url,
                headers={"Content-Length": str(MAX_CANARY_BYTES + 1)},
            ),
            FakeResponse(
                README,
                url=file_url,
                headers={
                    "Content-Length": str(len(README)),
                    "ETag": "bad\r\nheader",
                },
            ),
        )
        for bad in bad_file_responses:
            with self.subTest(url=bad.geturl(), status=bad.status, headers=bad.headers):
                opener = SequenceOpener(
                    [FakeResponse(tag_bytes(), url=TAG_API_URL), bad]
                )
                with self.assertRaises(EfehrAcquisitionError):
                    acquire_canary(opener=opener, now=lambda: RETRIEVED)

    def test_one_total_deadline_covers_tag_and_file_drip(self) -> None:
        clock = FakeClock()
        file_url = expected_file_url()
        opener = SequenceOpener(
            [
                FakeResponse(
                    tag_bytes(),
                    url=TAG_API_URL,
                    clock=clock,
                    advance_on_read=10.0,
                ),
                FakeResponse(
                    README,
                    url=file_url,
                    clock=clock,
                    advance_on_read=11.0,
                ),
            ]
        )
        with self.assertRaisesRegex(EfehrAcquisitionError, "total deadline"):
            acquire_canary(
                opener=opener,
                now=lambda: RETRIEVED,
                monotonic=clock,
            )

    def test_dns_policy_rejects_any_non_global_answer(self) -> None:
        global_info = (
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
            "",
            ("8.8.8.8", 443),
        )
        private_info = (
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
            "",
            ("10.0.0.1", 443),
        )
        admitted = _classify_public_sockaddrs([global_info])
        self.assertEqual(admitted[0][3][0], "8.8.8.8")
        with self.assertRaises(EfehrAcquisitionError):
            _classify_public_sockaddrs([global_info, private_info])
        with self.assertRaises(EfehrAcquisitionError):
            _classify_public_sockaddrs([])

    def test_canary_has_no_caller_controlled_target_parameters(self) -> None:
        names = set(acquire_canary.__kwdefaults__ or {})
        self.assertEqual(names, {"opener", "now", "monotonic"})


if __name__ == "__main__":
    unittest.main()
