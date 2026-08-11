# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import json
import socket
import stat
import sys
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.acquire_dwd_extreme_wind_receipt import (  # noqa: E402
    AcquisitionError,
    CHUNK_SIZE,
    FILENAME,
    EXPECTED_HOST,
    MAX_BYTES,
    SOURCE_URL,
    PublicOnlyHTTPSConnection,
    _classify_public_sockaddrs,
    _resolve_with_timeout,
    _validate_member_crc,
    acquire,
)


VALID_HEADER = "STATIONS_ID;MESS_DATUM;QN;FX_10;FNX_10;FMX_10;DX_10;eor\r\n"
VALID_ROWS = (
    "3;201001010000;2;1.0;0.1;0.5;180;eor\r\n"
    "3;201103312350;2;2.0;0.2;1.0;190;eor\r\n"
)
VALID_PRODUCT = (VALID_HEADER + VALID_ROWS).encode()


class FakeResponse(io.BytesIO):
    def __init__(
        self,
        payload: bytes,
        *,
        url: str = SOURCE_URL,
        status: int = 200,
        headers: dict[str, str] | None = None,
        clock: "FakeClock | None" = None,
        advance_on_read: float = 0,
    ):
        super().__init__(payload)
        self._url = url
        self.status = status
        self.headers = headers if headers is not None else {
            "Content-Length": str(len(payload)),
            "Content-Type": "application/zip",
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


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


class SequenceClock:
    def __init__(self, values: list[float]) -> None:
        self._values = iter(values)

    def __call__(self) -> float:
        return next(self._values)


def make_zip(
    *,
    member: str = "produkt_extrema_wind_00003_20100101_20110331_hist.txt",
    payload: bytes = VALID_PRODUCT,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, payload)
    return buffer.getvalue()


class AcquisitionReceiptTests(unittest.TestCase):
    def test_happy_path_emits_metadata_only_receipt(self):
        payload = make_zip()
        receipt = acquire(
            opener=lambda request, timeout: FakeResponse(payload),
            now=lambda: "2026-08-11T12:00:00Z",
        )
        self.assertEqual(receipt["schema_version"], "oc-acquisition-receipt-v1")
        self.assertEqual(receipt["requested_url"], SOURCE_URL)
        self.assertEqual(receipt["final_url"], SOURCE_URL)
        self.assertEqual(receipt["filename"], FILENAME)
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertRegex(receipt["sha256"], r"^[a-f0-9]{64}$")
        self.assertEqual(receipt["archive_member_count"], 1)
        self.assertEqual(receipt["product_station_id"], "00003")
        self.assertEqual(receipt["product_begin_date"], "20100101")
        self.assertEqual(receipt["product_end_date"], "20110331")
        self.assertEqual(receipt["product_row_count"], 2)
        self.assertTrue(receipt["product_structure_validated"])
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])

    def test_rejects_cross_host_redirect(self):
        payload = make_zip()
        with self.assertRaisesRegex(AcquisitionError, "redirected outside"):
            acquire(
                opener=lambda request, timeout: FakeResponse(
                    payload, url="https://example.com/" + FILENAME
                )
            )

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
            acquire(
                opener=lambda request, timeout: FakeResponse(
                    payload,
                    headers={"Content-Length": str(MAX_BYTES + 1)},
                )
            )

    def test_rejects_content_length_mismatch(self):
        payload = make_zip()
        with self.assertRaisesRegex(AcquisitionError, "does not match streamed"):
            acquire(
                opener=lambda request, timeout: FakeResponse(
                    payload,
                    headers={"Content-Length": str(len(payload) + 1)},
                )
            )

    def test_rejects_non_zip_payload(self):
        payload = b"not-a-zip"
        with self.assertRaisesRegex(AcquisitionError, "valid ZIP"):
            acquire(opener=lambda request, timeout: FakeResponse(payload))

    def test_rejects_path_traversal_member(self):
        payload = make_zip(member="../produkt_extrema_wind_bad.txt")
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
        payload = buffer.getvalue()
        with self.assertRaisesRegex(AcquisitionError, "exactly one"):
            acquire(opener=lambda request, timeout: FakeResponse(payload))

    def test_rejects_symlink_member(self):
        buffer = io.BytesIO()
        info = zipfile.ZipInfo("produkt_extrema_wind_bad.txt")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(info, b"target")
        payload = buffer.getvalue()
        with self.assertRaisesRegex(AcquisitionError, "special-file"):
            acquire(opener=lambda request, timeout: FakeResponse(payload))

    def test_rejects_other_unix_special_file_member(self):
        buffer = io.BytesIO()
        info = zipfile.ZipInfo("produkt_extrema_wind_bad.txt")
        info.create_system = 3
        info.external_attr = (stat.S_IFIFO | 0o600) << 16
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(info, VALID_PRODUCT)
        payload = buffer.getvalue()
        with self.assertRaisesRegex(AcquisitionError, "special-file"):
            acquire(opener=lambda request, timeout: FakeResponse(payload))

    def test_rejects_wrong_station_even_with_plausible_member_name(self):
        payload = make_zip(
            payload=(VALID_HEADER + VALID_ROWS.replace("3;", "11;")).encode()
        )
        with self.assertRaisesRegex(AcquisitionError, "frozen station"):
            acquire(opener=lambda request, timeout: FakeResponse(payload))

    def test_rejects_wrong_period(self):
        rows = (
            "3;201001010000;2;1.0;0.1;0.5;180;eor\r\n"
            "3;201104012350;2;2.0;0.2;1.0;190;eor\r\n"
        )
        payload = make_zip(payload=(VALID_HEADER + rows).encode())
        with self.assertRaisesRegex(AcquisitionError, "outside frozen"):
            acquire(opener=lambda request, timeout: FakeResponse(payload))

    def test_rejects_correctly_named_arbitrary_text(self):
        payload = make_zip(payload=b"header\n")
        with self.assertRaisesRegex(AcquisitionError, "header does not match"):
            acquire(opener=lambda request, timeout: FakeResponse(payload))

    def test_rejects_missing_station_identity_column(self):
        header = "MESS_DATUM;QN;FX_10;FNX_10;FMX_10;DX_10;eor\r\n"
        rows = (
            "201001010000;2;1;1;1;180;eor\r\n"
            "201103312350;2;1;1;1;180;eor\r\n"
        )
        payload = make_zip(payload=(header + rows).encode())
        with self.assertRaisesRegex(AcquisitionError, "station identity"):
            acquire(opener=lambda request, timeout: FakeResponse(payload))

    def test_rejects_structurally_incomplete_or_nonnumeric_rows(self):
        incomplete = make_zip(
            payload=(
                VALID_HEADER + "3;201001010000\r\n3;201103312350\r\n"
            ).encode()
        )
        with self.assertRaisesRegex(AcquisitionError, "declared header"):
            acquire(opener=lambda request, timeout: FakeResponse(incomplete))

        bad_numeric_rows = (
            "3;201001010000;2;not-a-number;0.1;0.5;180;eor\r\n"
            "3;201103312350;2;2.0;0.2;1.0;190;eor\r\n"
        )
        bad_numeric = make_zip(
            payload=(VALID_HEADER + bad_numeric_rows).encode()
        )
        with self.assertRaisesRegex(AcquisitionError, "non-numeric"):
            acquire(opener=lambda request, timeout: FakeResponse(bad_numeric))

    def test_total_deadline_blocks_drip_response(self):
        payload = make_zip()
        clock = FakeClock()
        with self.assertRaisesRegex(AcquisitionError, "total deadline"):
            acquire(
                opener=lambda request, timeout: FakeResponse(
                    payload,
                    clock=clock,
                    advance_on_read=61.0,
                ),
                monotonic=clock,
            )

    def test_archive_crc_validation_obeys_total_deadline(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("payload.txt", b"x" * (CHUNK_SIZE * 2))
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            member = archive.infolist()[0]
            clock = SequenceClock([0.0, 61.0])
            with self.assertRaisesRegex(AcquisitionError, "total deadline"):
                _validate_member_crc(
                    archive,
                    member,
                    deadline=60.0,
                    monotonic=clock,
                )

    def test_archive_crc_validation_rejects_unsupported_compression(self):
        member = zipfile.ZipInfo("payload.txt")
        member.compress_type = zipfile.ZIP_BZIP2
        with self.assertRaisesRegex(AcquisitionError, "unsupported compression"):
            _validate_member_crc(
                MagicMock(),
                member,
                deadline=60.0,
                monotonic=lambda: 0.0,
            )

    def test_dns_rejects_loopback_private_and_link_local(self):
        for address in ("127.0.0.1", "10.1.2.3", "169.254.1.2"):
            infos = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))
            ]
            with self.subTest(address=address), self.assertRaisesRegex(
                AcquisitionError, "non-global"
            ):
                _classify_public_sockaddrs(infos)

    def test_dns_accepts_global_address(self):
        infos = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("93.184.216.34", 443),
            )
        ]
        admitted = _classify_public_sockaddrs(infos)
        self.assertEqual(admitted[0][3][0], "93.184.216.34")

    def test_dns_resolution_has_its_own_deadline(self):
        def blocked_resolver(host, port, type):
            time.sleep(0.2)
            return []

        started = time.monotonic()
        with self.assertRaisesRegex(AcquisitionError, "DNS resolution exceeded"):
            _resolve_with_timeout(
                EXPECTED_HOST,
                443,
                0.01,
                resolver=blocked_resolver,
            )
        self.assertLess(time.monotonic() - started, 0.1)

    @patch("scripts.acquire_dwd_extreme_wind_receipt._resolve_with_timeout")
    @patch("scripts.acquire_dwd_extreme_wind_receipt.socket.socket")
    def test_connection_uses_prevalidated_sockaddr_without_second_dns_lookup(
        self, socket_ctor, resolve
    ):
        sockaddr = ("93.184.216.34", 443)
        resolve.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, sockaddr)
        ]
        raw = MagicMock()
        wrapped = MagicMock()
        wrapped.getpeername.return_value = sockaddr
        socket_ctor.return_value = raw
        context = MagicMock()
        context.wrap_socket.return_value = wrapped

        connection = PublicOnlyHTTPSConnection(
            EXPECTED_HOST,
            443,
            timeout=5.0,
            context=context,
        )
        connection.connect()

        resolve.assert_called_once()
        raw.connect.assert_called_once_with(sockaddr)
        context.wrap_socket.assert_called_once_with(
            raw, server_hostname=EXPECTED_HOST
        )

    def test_schema_is_closed_and_pins_non_persistence(self):
        schema = json.loads(
            (ROOT / "schemas" / "acquisition-receipt-v1.schema.json").read_text()
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["external_bytes_persisted"]["const"], False
        )
        self.assertEqual(
            schema["properties"]["publication_authorized"]["const"], False
        )
        self.assertEqual(
            schema["properties"]["requested_url"]["const"], SOURCE_URL
        )
        self.assertEqual(
            schema["properties"]["product_station_id"]["const"], "00003"
        )
        self.assertEqual(
            schema["properties"]["product_structure_validated"]["const"],
            True,
        )


if __name__ == "__main__":
    unittest.main()
