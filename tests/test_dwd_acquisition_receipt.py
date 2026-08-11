# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import json
import stat
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.acquire_dwd_extreme_wind_receipt import (  # noqa: E402
    AcquisitionError,
    FILENAME,
    MAX_BYTES,
    SOURCE_URL,
    acquire,
)


class FakeResponse(io.BytesIO):
    def __init__(self, payload: bytes, *, url: str = SOURCE_URL, status: int = 200, headers: dict[str, str] | None = None):
        super().__init__(payload)
        self._url = url
        self.status = status
        self.headers = headers or {"Content-Length": str(len(payload)), "Content-Type": "application/zip"}

    def geturl(self) -> str:
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


def make_zip(*, member: str = "produkt_extrema_wind_00003_20100101_20110331_hist.txt", payload: bytes = b"header\n") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, payload)
    return buffer.getvalue()


class AcquisitionReceiptTests(unittest.TestCase):
    def test_happy_path_emits_metadata_only_receipt(self):
        payload = make_zip()
        receipt = acquire(opener=lambda request, timeout: FakeResponse(payload), now=lambda: "2026-08-11T12:00:00Z")
        self.assertEqual(receipt["schema_version"], "oc-acquisition-receipt-v1")
        self.assertEqual(receipt["requested_url"], SOURCE_URL)
        self.assertEqual(receipt["final_url"], SOURCE_URL)
        self.assertEqual(receipt["filename"], FILENAME)
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertRegex(receipt["sha256"], r"^[a-f0-9]{64}$")
        self.assertEqual(receipt["archive_member_count"], 1)
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])

    def test_rejects_cross_host_redirect(self):
        payload = make_zip()
        with self.assertRaisesRegex(AcquisitionError, "redirected outside"):
            acquire(opener=lambda request, timeout: FakeResponse(payload, url="https://example.com/" + FILENAME))

    def test_rejects_same_host_different_path_redirect(self):
        payload = make_zip()
        with self.assertRaisesRegex(AcquisitionError, "redirected outside"):
            acquire(
                opener=lambda request, timeout: FakeResponse(
                    payload,
                    url="https://opendata.dwd.de/other/" + FILENAME,
                )
            )

    def test_rejects_declared_oversize(self):
        payload = make_zip()
        with self.assertRaisesRegex(AcquisitionError, "Content-Length"):
            acquire(opener=lambda request, timeout: FakeResponse(payload, headers={"Content-Length": str(MAX_BYTES + 1)}))

    def test_rejects_non_zip_payload(self):
        payload = b"not-a-zip"
        with self.assertRaisesRegex(AcquisitionError, "valid ZIP"):
            acquire(opener=lambda request, timeout: FakeResponse(payload))

    def test_rejects_path_traversal_member(self):
        payload = make_zip(member="../produkt_extrema_wind_00003_bad.txt")
        with self.assertRaisesRegex(AcquisitionError, "unsafe member path"):
            acquire(opener=lambda request, timeout: FakeResponse(payload))

    def test_rejects_overlong_member_name(self):
        payload = make_zip(member=("a" * 513))
        with self.assertRaisesRegex(AcquisitionError, "unsafe member name"):
            acquire(opener=lambda request, timeout: FakeResponse(payload))

    def test_requires_exactly_one_product_member(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("readme.txt", b"x")
        with self.assertRaisesRegex(AcquisitionError, "exactly one"):
            acquire(opener=lambda request, timeout: FakeResponse(buffer.getvalue()))

    def test_rejects_symlink_member(self):
        buffer = io.BytesIO()
        info = zipfile.ZipInfo("produkt_extrema_wind_00003_bad.txt")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(info, b"target")
        with self.assertRaisesRegex(AcquisitionError, "symlinks"):
            acquire(opener=lambda request, timeout: FakeResponse(buffer.getvalue()))

    def test_schema_is_closed_and_pins_non_persistence(self):
        schema = json.loads((ROOT / "schemas" / "acquisition-receipt-v1.schema.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["external_bytes_persisted"]["const"], False)
        self.assertEqual(schema["properties"]["publication_authorized"]["const"], False)
        self.assertEqual(schema["properties"]["requested_url"]["const"], SOURCE_URL)


if __name__ == "__main__":
    unittest.main()
