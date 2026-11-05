# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""All tests are synthetic and offline; never download provider original in CI."""
from __future__ import annotations

from contextlib import redirect_stdout
from hashlib import md5, sha256
from io import BytesIO, StringIO
from pathlib import Path
import json
import sys
from tempfile import TemporaryDirectory
import unittest
from urllib.error import URLError
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research_runners import hanze_windstorm_original_xlsx_acquisition_v0 as mod


def toy_xlsx(*, member_name="xl/worksheets/sheet1.xml"):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", "<workbook/>")
        archive.writestr(member_name, "<worksheet><sheetData/></worksheet>")
    return buffer.getvalue()


class FakeResponse(BytesIO):
    def __init__(self, segment, content_range, status=206, *,
                 wrong_length=False, missing_range=False):
        super().__init__(segment)
        self.status = status
        self.headers = {"Content-Length": str(len(segment) + (1 if wrong_length else 0))}
        if not missing_range:
            self.headers["Content-Range"] = content_range


class FakeOpener:
    def __init__(self, content, *, status=206, wrong_length=False,
                 missing_range=False, truncate_last=False, fail=False):
        self.content = content
        self.status = status
        self.wrong_length = wrong_length
        self.missing_range = missing_range
        self.truncate_last = truncate_last
        self.fail = fail
        self.ranges = []

    def __call__(self, request, timeout):
        if self.fail:
            raise URLError("secret-from-untrusted-upstream")
        header = request.get_header("Range")
        if not header or not header.startswith("bytes="):
            raise AssertionError("expected explicit RFC 7233 range")
        a,b = map(int, header[6:].split("-"))
        self.ranges.append((a,b))
        data = self.content[a:b+1]
        if self.truncate_last:
            data = data[:-1]
        return FakeResponse(
            data, f"bytes {a}-{b}/{len(self.content)}",
            self.status,wrong_length=self.wrong_length,
            missing_range=self.missing_range,
        )


class OriginalHanzeWindstormIntakeTests(unittest.TestCase):
    def test_offline_default_prints_exact_provider_manifest(self):
        stream = StringIO()
        with redirect_stdout(stream):
            self.assertEqual(mod.main([]), 0)
        info=json.loads(stream.getvalue())
        self.assertEqual(info["mode"],"OFFLINE_PREVIEW_NO_NETWORK")
        self.assertEqual(info["expected_bytes"],292136)
        self.assertEqual(info["expected_md5"],"0a523543adf76003916186623812ab74")
        self.assertEqual(info["expected_sha256"],
                         "c2fe636c9e7a1e601d64f00f5bdef8fdf9aaa854060f4d5edcd02e1405140944")
        self.assertFalse(info["scientific_or_insurance_admission"])

    def test_injected_xlsx_uses_exact_206_ranges_without_skips(self):
        original=toy_xlsx()
        fake=FakeOpener(original)
        actual=mod.fetch_exact_ranges(opener=fake,chunk_size=64,size=len(original))
        self.assertEqual(actual,original)
        self.assertGreater(len(fake.ranges),1)
        self.assertEqual(fake.ranges[0],(0,63))
        self.assertEqual(fake.ranges[-1][1],len(original)-1)
        self.assertEqual(sum(b-a+1 for a,b in fake.ranges),len(original))
        self.assertTrue(all(fake.ranges[i][1]+1==fake.ranges[i+1][0]
                            for i in range(len(fake.ranges)-1)))

    def test_synthetic_zip_digest_attestation_is_not_scientific_admission(self):
        raw=toy_xlsx()
        receipt=mod.inspect_source_bytes(raw,size=len(raw),
            publisher_md5=md5(raw).hexdigest(),
            expected_sha256=sha256(raw).hexdigest())
        self.assertEqual(receipt["status"],"FULL_ORIGINAL_XLSX_DIGEST_VERIFIED_NOT_SCIENTIFICALLY_ADMITTED")
        self.assertEqual(receipt["original_file_bytes"],len(raw))
        self.assertEqual(receipt["xlsx_members_crc_checked"],3)
        self.assertFalse(receipt["source_claims_data_rights_admitted"])
        self.assertFalse(receipt["full_original_workbook_rows_semantically_validated"])
        self.assertFalse(receipt["source_modelled_loss_circularity_excluded"])
        self.assertIsNone(receipt["annual_AEP"])
        self.assertIsNone(receipt["annual_OEP"])

    def test_synthetic_bytes_cannot_claim_pinned_actual_hanze(self):
        raw=toy_xlsx()
        with self.assertRaises(mod.OriginalHanzeError):
            mod.inspect_source_bytes(raw)
        with self.assertRaisesRegex(mod.OriginalHanzeError,"mismatch"):
            mod.inspect_source_bytes(raw,size=len(raw),
               publisher_md5=md5(raw).hexdigest(),expected_sha256="0"*64)
        with self.assertRaisesRegex(mod.OriginalHanzeError,"mismatch"):
            mod.inspect_source_bytes(raw,size=len(raw),
               publisher_md5="0"*32,expected_sha256=sha256(raw).hexdigest())

    def test_missing_malformed_wrong_size_or_non_xlsx_fail_closed(self):
        for raw in (b"",b"arbitrary text",b"PK\\x03\\x04fake",b"%PDF-1.7"):
            with self.subTest(prefix=raw[:4]),self.assertRaises(mod.OriginalHanzeError):
                mod.inspect_source_bytes(raw,size=max(1,len(raw)),
                   publisher_md5=md5(raw).hexdigest(),expected_sha256=sha256(raw).hexdigest())
        bad=toy_xlsx(member_name="../evil.xml")
        with self.assertRaisesRegex(mod.OriginalHanzeError,"unsupported"):
            mod.inspect_source_bytes(bad,size=len(bad),
                publisher_md5=md5(bad).hexdigest(),expected_sha256=sha256(bad).hexdigest())

    def test_http_full_200_truncated_and_header_drift_rejected(self):
        raw=toy_xlsx()
        variants=[
            FakeOpener(raw,status=200),
            FakeOpener(raw,missing_range=True),
            FakeOpener(raw,wrong_length=True),
            FakeOpener(raw,truncate_last=True),
        ]
        for fake in variants:
            with self.subTest(case=fake.__dict__),self.assertRaises(mod.OriginalHanzeError):
                mod.fetch_exact_ranges(opener=fake,size=len(raw),chunk_size=64)

    def test_upstream_http_errors_do_not_echo_secret(self):
        fake=FakeOpener(toy_xlsx(),fail=True)
        with self.assertRaises(mod.OriginalHanzeError) as ctx:
            mod.fetch_exact_ranges(opener=fake,size=len(fake.content),chunk_size=64)
        self.assertNotIn("secret-from-untrusted-upstream",str(ctx.exception))

    def test_invalid_range_parameters_are_blocked_before_network(self):
        fake=FakeOpener(toy_xlsx())
        for kw in ({"size":True},{"size":0},{"size":-1},{"chunk_size":False},
                   {"chunk_size":65537},{"url":"http://not-https.local/x"}):
            with self.subTest(kw=kw),self.assertRaises(mod.OriginalHanzeError):
                mod.fetch_exact_ranges(opener=fake,**kw)
        self.assertEqual(fake.ranges,[])

    def test_local_checkout_and_existing_file_cannot_be_overwritten(self):
        checkout=Path(mod.__file__).resolve().parents[1]
        with self.assertRaisesRegex(mod.OriginalHanzeError,"outside Git checkout"):
            mod.acquire(output_dir=checkout/"raw",opener=FakeOpener(toy_xlsx()))
        with TemporaryDirectory() as directory:
            outdir=Path(directory)
            target=outdir/mod.ORIGINAL_FILENAME
            target.write_bytes(b"do-not-overwrite")
            with self.assertRaisesRegex(mod.OriginalHanzeError,"overwrite"):
                mod.acquire(output_dir=outdir,opener=FakeOpener(toy_xlsx()))
            self.assertEqual(target.read_bytes(),b"do-not-overwrite")

    def test_unauthorized_reproducible_fake_download_never_written(self):
        original=toy_xlsx()
        with TemporaryDirectory() as directory:
            outdir=Path(directory)/"separate"
            with self.assertRaises(mod.OriginalHanzeError):
                mod.acquire(output_dir=outdir,opener=FakeOpener(original))
            self.assertFalse(outdir.exists())


if __name__ == "__main__":
    unittest.main()
