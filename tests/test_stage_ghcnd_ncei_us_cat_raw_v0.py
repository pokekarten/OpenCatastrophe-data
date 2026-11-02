# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only: signed private Neon original-object transfer boundaries."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import gzip
import hashlib
import io
import json
from urllib import error
import unittest

from scripts import stage_ghcnd_ncei_us_cat_raw_v0 as staging
from tests.test_probe_ghcnd_ncei_us_station_gzip_v0 import fixture


def presigned_url():
    return (
        "https://" + staging.S3_HOST + staging.TARGET_PATH
        + "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
        + "&X-Amz-Credential=FAKE%2F20261102%2Feu-central-1%2Fs3%2Faws4_request"
        + "&X-Amz-Date=20261102T190000Z&X-Amz-Expires=90"
        + "&X-Amz-SignedHeaders=content-type%3Bhost"
        + "&X-Amz-Signature=FAKESIGNATURE"
    )


class Response:
    def __init__(self, data: bytes, *, url: str, status: int = 200,
                 media="application/gzip", content_range=None):
        self.status = status
        self.url = url
        self.body = io.BytesIO(data)
        self.headers = {
            "Content-Type": media,
            "Content-Length": str(len(data)),
            "Content-Encoding": "identity",
        }
        if content_range is not None:
            self.headers["Content-Range"] = content_range

    def geturl(self):
        return self.url

    def read(self, n):
        return self.body.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.body.close()


class StageUSStationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_csv = fixture().split(b"\n", 1)[1]
        cls.raw_gzip = gzip.compress(cls.raw_csv, mtime=0)
        cls.expected = staging.OriginalIdentity(
            compressed_sha256=hashlib.sha256(cls.raw_gzip).hexdigest(),
            inflated_sha256=hashlib.sha256(cls.raw_csv).hexdigest(),
            compressed_bytes=len(cls.raw_gzip),
            inflated_bytes=len(cls.raw_csv),
            rows=41000,
            last_day=(date(1869, 1, 1) + timedelta(days=40999)).strftime("%Y%m%d"),
            gzip_members=1,
        )

    def test_signed_exact_private_bucket_and_key(self):
        staging._check_presigned_target(presigned_url())
        self.assertEqual(staging.BUCKET, "cat-raw")
        self.assertIn(staging.SOURCE_SHA, staging.OBJECT_KEY)

    def test_unapproved_destination_rejected_before_download(self):
        urls = [
            "",
            "https://example.org" + staging.TARGET_PATH + presigned_url().split("?")[1],
            presigned_url().replace(staging.S3_HOST, "attacker.example.org"),
            presigned_url().replace(staging.SOURCE_SHA, "a" * 64),
            presigned_url().replace("https://", "http://"),
            presigned_url().split("?")[0],
            presigned_url() + "#unreviewed",
            presigned_url().replace("cat-raw", "cat-model-results"),
            presigned_url().replace("X-Amz-Signature", "Other-Signature"),
        ]
        for url in urls:
            calls = []
            with self.subTest(url_kind=url[:20]), self.assertRaises(staging.TransferBlocked):
                staging.transfer(
                    authorization=url, expected=self.expected,
                    get=lambda *args: calls.append("GET"),
                    put=lambda *args: calls.append("PUT"),
                )
            self.assertEqual(calls, [])

    def test_original_checked_before_one_private_put(self):
        requests = []
        url = presigned_url()
        def get(req, timeout):
            requests.append(("get", req.get_method(), req.full_url, timeout))
            return Response(self.raw_gzip, url=staging.SOURCE_URL)
        def put(req, timeout):
            requests.append(("put", req.get_method(), req.full_url, timeout))
            self.assertEqual(req.data, self.raw_gzip)
            self.assertEqual(req.get_header("Content-type"), "application/gzip")
            return Response(b"", url=url, status=200)
        receipt = staging.transfer(
            authorization=url, get=get, put=put, expected=self.expected,
            clock=lambda: datetime(2026, 11, 2, 19, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0], ("get", "GET", staging.SOURCE_URL, 60))
        self.assertEqual(requests[1], ("put", "PUT", url, 60))
        self.assertEqual(receipt["original_rows_checked"], 41000)
        self.assertTrue(receipt["upload_acknowledged"])
        self.assertFalse(receipt["independent_download_hash_verified"])
        self.assertFalse(receipt["registry_artifact_row_created"])
        self.assertFalse(receipt["scientific_model_admitted"])
        self.assertFalse(receipt["insured_exposure_derived"])
        self.assertNotIn("X-Amz", json.dumps(receipt))
        self.assertNotIn("FAKESIGNATURE", json.dumps(receipt))
        self.assertNotIn("DATA_VALUE", json.dumps(receipt))

    def test_wrong_original_bytes_do_not_put(self):
        seen = []
        corrupted = self.raw_gzip[:-1] + b"x"
        with self.assertRaises(staging.TransferBlocked):
            staging.transfer(
                authorization=presigned_url(),
                get=lambda req, timeout: Response(corrupted, url=staging.SOURCE_URL),
                put=lambda *args: seen.append("put"),
                expected=self.expected,
            )
        self.assertEqual(seen, [])

    def test_original_synthetic_not_mistaken_for_pinned_real_hash(self):
        with self.assertRaises(staging.TransferBlocked):
            staging.verify_bytes(self.raw_gzip)

    def test_bad_source_status_or_content_type_rejected(self):
        for options in [{"status": 206}, {"media": "text/html"}, {"content_range": "bytes 0-3/99"}]:
            with self.subTest(options=options), self.assertRaises(staging.TransferBlocked):
                staging.transfer(
                    authorization=presigned_url(),
                    get=lambda req, timeout: Response(
                        self.raw_gzip, url=staging.SOURCE_URL, **options),
                    put=lambda *args: self.fail("must not upload"),
                    expected=self.expected,
                )

    def test_storage_http_error_does_not_expose_signed_query(self):
        with self.assertRaisesRegex(staging.TransferBlocked, "upload failed") as ctx:
            staging.transfer(
                authorization=presigned_url(),
                get=lambda req, timeout: Response(self.raw_gzip, url=staging.SOURCE_URL),
                put=lambda req, timeout: (_ for _ in ()).throw(
                    error.HTTPError(req.full_url, 403, "fake", {}, None)
                ),
                expected=self.expected,
            )
        self.assertNotIn("X-Amz", str(ctx.exception))
        self.assertNotIn("FAKESIGNATURE", str(ctx.exception))

    def test_storage_500_does_not_claim_object(self):
        with self.assertRaises(staging.TransferBlocked):
            staging.transfer(
                authorization=presigned_url(),
                get=lambda req, timeout: Response(self.raw_gzip, url=staging.SOURCE_URL),
                put=lambda req, timeout: Response(b"", url=presigned_url(), status=500),
                expected=self.expected,
            )

    def test_timestamp_without_tz_must_not_upload(self):
        with self.assertRaises(staging.TransferBlocked):
            staging.transfer(
                authorization=presigned_url(),
                get=lambda req, timeout: Response(self.raw_gzip, url=staging.SOURCE_URL),
                put=lambda *args: self.fail("must not upload"),
                clock=lambda: datetime(2026, 11, 2),
                expected=self.expected,
            )


if __name__ == "__main__":
    unittest.main()
