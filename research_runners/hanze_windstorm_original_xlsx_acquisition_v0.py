# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-pinned public HANZE windstorm XLSX intake. Research only, NOT CAT.

Default CLI is offline and cannot accept a changed publisher URL/checksum.
Live fetching is explicit and stores source bytes outside this Git checkout.
The published Zenodo file is open but its upstream source rights/science are
not admitted for production, insurer claims, CAT frequency or vulnerability.
"""
from __future__ import annotations

import argparse
from hashlib import md5, sha256
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile

CONTRACT = "OC_HANZE_WINDSTORM_ORIGINAL_XLSX_BYTE_IDENTITY_V0"
RECORD = "https://zenodo.org/records/15266959"
ORIGINAL_URL = (
    "https://zenodo.org/api/records/15266959/files/"
    "HANZE%20European%20Windstorm%20Impact%20Database%201950-2020.xlsx/content"
)
ORIGINAL_FILENAME = "HANZE European Windstorm Impact Database 1950-2020.xlsx"
ORIGINAL_BYTES = 292_136
ORIGINAL_PUBLISHER_MD5 = "0a523543adf76003916186623812ab74"
ORIGINAL_SHA256 = "c2fe636c9e7a1e601d64f00f5bdef8fdf9aaa854060f4d5edcd02e1405140944"
RANGE_BYTES = 40_960
MAX_UNCOMPRESSED_XLSX_BYTES = 25_000_000


class OriginalHanzeError(ValueError):
    """A promised fixed source file cannot be verified or used."""


def _parts(blob: bytes) -> tuple[str, ...]:
    try:
        with ZipFile(BytesIO(blob)) as archive:
            members = archive.infolist()
            names = []
            total_uncompressed = 0
            for info in members:
                name = info.filename
                path = PurePosixPath(name)
                if (not name or name.startswith("/") or "\\" in name or ":" in name or
                        ".." in path.parts or info.flag_bits & 1 or
                        (info.external_attr >> 16) & 0o170000 == 0o120000):
                    raise OriginalHanzeError("unsupported XLSX archive member")
                total_uncompressed += info.file_size
                if total_uncompressed > MAX_UNCOMPRESSED_XLSX_BYTES:
                    raise OriginalHanzeError("XLSX uncompressed content exceeds research safety bound")
                names.append(name)
            if (len(names) != len(set(names)) or
                    "[Content_Types].xml" not in names or
                    "xl/workbook.xml" not in names or
                    not any(name.startswith("xl/worksheets/sheet") and
                            name.endswith(".xml") for name in names)):
                raise OriginalHanzeError("not one valid Office XLSX workbook profile")
            bad = archive.testzip()
            if bad is not None:
                raise OriginalHanzeError("original XLSX member CRC mismatch")
            return tuple(sorted(names))
    except (BadZipFile, OSError, RuntimeError, ValueError) as exc:
        if isinstance(exc, OriginalHanzeError):
            raise
        raise OriginalHanzeError("invalid Office XLSX container") from None


def inspect_source_bytes(
        blob: bytes, *, size: int = ORIGINAL_BYTES,
        publisher_md5: str = ORIGINAL_PUBLISHER_MD5,
        expected_sha256: str = ORIGINAL_SHA256) -> dict:
    """Hash exact raw bytes; metadata never claims observed claim validity.

    Optional expectations exist solely for offline injected synthetic tests.
    Production CLI and acquire() always use immutable module constants.
    """
    if (type(blob) is not bytes or type(size) is not int or size < 1 or
            type(publisher_md5) is not str or len(publisher_md5) != 32 or
            type(expected_sha256) is not str or len(expected_sha256) != 64):
        raise OriginalHanzeError("bounded exact original source and hash expectations required")
    if len(blob) != size or not blob.startswith(b"PK\\x03\\x04"):
        raise OriginalHanzeError("original source size or XLSX magic mismatch")
    md5_actual = md5(blob).hexdigest()
    sha_actual = sha256(blob).hexdigest()
    if md5_actual != publisher_md5 or sha_actual != expected_sha256:
        raise OriginalHanzeError("original publisher-MD5 or exact-SHA256 mismatch")
    members = _parts(blob)
    return {
        "contract": CONTRACT,
        "status": "FULL_ORIGINAL_XLSX_DIGEST_VERIFIED_NOT_SCIENTIFICALLY_ADMITTED",
        "provider_record": RECORD,
        "provider_file_endpoint": ORIGINAL_URL,
        "original_file_name": ORIGINAL_FILENAME,
        "original_file_bytes": len(blob),
        "publisher_md5_recomputed_and_matched": md5_actual,
        "original_sha256": sha_actual,
        "xlsx_members_crc_checked": len(members),
        "source_claims_data_rights_admitted": False,
        "full_original_workbook_rows_semantically_validated": False,
        "observed_insured_claims_confirmed": False,
        "physical_event_country_rows_deduplicated": False,
        "source_modelled_loss_circularity_excluded": False,
        "real_insurer_gross_net_authorized": False,
        "annual_event_frequency": None,
        "annual_AEP": None, "annual_OEP": None,
    }


def fetch_exact_ranges(*, opener=None, chunk_size: int = RANGE_BYTES,
                       size: int = ORIGINAL_BYTES, url: str = ORIGINAL_URL) -> bytes:
    """Never accept silently truncated 200 responses as full source bytes.

    The public URL uses 206 partial responses; Content-Range must match
    every requested offset, byte length and complete source length.
    """
    if (type(size) is not int or not 1 <= size <= 25_000_000 or
            type(chunk_size) is not int or not 1 <= chunk_size <= 65_536 or
            type(url) is not str or not url.startswith("https://")):
        raise OriginalHanzeError("invalid bounded original-source fetch parameters")
    if opener is None:
        opener = urlopen
    result = bytearray()
    for start in range(0, size, chunk_size):
        end = min(start + chunk_size - 1, size - 1)
        expected_len = end - start + 1
        request = Request(url, headers={"Range": f"bytes={start}-{end}"}, method="GET")
        try:
            with opener(request, timeout=30) as response:
                status = response.status
                got_range = response.headers.get("Content-Range")
                got_length = response.headers.get("Content-Length")
                if status != 206 or got_range != f"bytes {start}-{end}/{size}":
                    raise OriginalHanzeError("HTTP byte-range identity not verified")
                if got_length is not None and got_length != str(expected_len):
                    raise OriginalHanzeError("HTTP byte-range content-length mismatch")
                segment = response.read(expected_len + 1)
        except (HTTPError, URLError, TimeoutError, OSError):
            # Never print response bodies, URL query, headers, credentials.
            raise OriginalHanzeError("authorized original Zenodo source fetch failed") from None
        if len(segment) != expected_len:
            raise OriginalHanzeError("short or excessive original source byte range")
        result.extend(segment)
    if len(result) != size:
        raise OriginalHanzeError("original XLSX reconstructed size mismatch")
    return bytes(result)


def acquire(*, output_dir: Path, opener=None) -> dict:
    """Opt-in original public-file download to an external, non-Git directory."""
    out = Path(output_dir).resolve()
    root = Path(__file__).resolve().parents[1]
    if out == root or root in out.parents:
        raise OriginalHanzeError("original HANZE XLSX and receipt must remain outside Git checkout")
    source_path = out / ORIGINAL_FILENAME
    receipt_path = out / "hanze-windstorm-v1-original-xlsx-receipt.json"
    if (source_path.exists() or source_path.is_symlink() or
            receipt_path.exists() or receipt_path.is_symlink()):
        raise OriginalHanzeError("refuse overwrite of original source or receipt")
    blob = fetch_exact_ranges(opener=opener)
    receipt = inspect_source_bytes(blob)
    out.mkdir(parents=True, exist_ok=True)
    with source_path.open("xb") as f:
        f.write(blob)
    with receipt_path.open("x", encoding="utf-8") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, allow_nan=False)
        f.write("\\n")
    return receipt


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute", action="store_true",
                   help="explicitly fetch public original XLSX into an external directory")
    p.add_argument("--out-dir", type=Path)
    a = p.parse_args(argv)
    if not a.execute:
        if a.out_dir is not None:
            p.error("--out-dir requires --execute")
        print(json.dumps({
            "contract": CONTRACT, "mode": "OFFLINE_PREVIEW_NO_NETWORK",
            "record": RECORD, "url": ORIGINAL_URL,
            "expected_bytes": ORIGINAL_BYTES,
            "expected_md5": ORIGINAL_PUBLISHER_MD5,
            "expected_sha256": ORIGINAL_SHA256,
            "scientific_or_insurance_admission": False,
        }, sort_keys=True, indent=2))
        return 0
    if a.out_dir is None:
        p.error("--execute requires --out-dir outside the repository")
    receipt = acquire(output_dir=a.out_dir)
    print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
