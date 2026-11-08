# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only original FPA FOD archive release and ZIP security tests."""
import hashlib
import sqlite3
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from research_runners import us_fpa_v7_original_archive_receipt_v0 as gate

NAME_INDEX = "_fileindex_RDS-2013-0009.7.html"
NAME_HTML = "_metadata_RDS-2013-0009.7.html"
NAME_XML = "_metadata_RDS-2013-0009.7.xml"


def make_metadata(*, idx=None, html=None, xml=None, extras=None):
    if idx is None:
        idx = "Spatial wildfire 1992-2024 FPA_FOD_20260615.gpkg seventh edition"
    if html is None:
        html = "FPA_FOD_20260615 1992-2024 10.2737/RDS-2013-0009.7 without additional permissions or fees"
    if xml is None:
        xml = "<root><title>FPA_FOD_20260615</title><doi>10.2737/RDS-2013-0009.7</doi><end>2024</end><rights>without additional permissions or fees</rights></root>"
    b = BytesIO()
    with ZipFile(b, "w", ZIP_DEFLATED) as z:
        for name, text in ((NAME_INDEX, idx), (NAME_HTML, html), (NAME_XML, xml)):
            z.writestr(name, text)
        for name, text in extras or ():
            z.writestr(name, text)
    return b.getvalue()


def verify_meta(blob):
    return gate.verify_original_metadata_zip(
        blob, expected_bytes=len(blob), expected_sha256=hashlib.sha256(blob).hexdigest()
    )


def zip_gpkg(contents=None, member=None, extras=None):
    if contents is None:
        contents = gate.SQLITE_HEADER + b"\x00" * 100_100
    if member is None:
        member = gate.GPKG_MEMBER
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as z:
        z.writestr(member, contents)
        z.writestr(gate.VARIABLES_MEMBER, b"synthetic-only-variable-metadata" + b"0" * (gate.VARIABLES_MEMBER_BYTES - len(b"synthetic-only-variable-metadata")))
        for name, text in extras or ():
            z.writestr(name, text)
    return stream.getvalue()


def verify_gpkg(data):
    with tempfile.TemporaryDirectory() as folder:
        p = Path(folder) / gate.DATA_NAME
        p.write_bytes(data)
        return gate.verify_original_gpkg_zip(
            p, expected_bytes=len(data), expected_sha256=hashlib.sha256(data).hexdigest()
        )


class PublisherArchiveReceiptTests(unittest.TestCase):
    def test_metadata_archive_identity_and_rights_are_not_cat_admission(self):
        result = verify_meta(make_metadata())
        self.assertTrue(result["metadata_original_zip_crc_valid"])
        self.assertEqual(result["original_member_count"], 3)
        self.assertEqual(result["publisher_doi"], "10.2737/RDS-2013-0009.7")
        self.assertTrue(result["publisher_general_use_without_additional_permissions_stated"])
        self.assertFalse(result["GPKG_original_data_file_sha256_verified"])
        self.assertFalse(result["CAT_source_scientific_or_insurance_loss_admission_granted"])

    def test_genuine_publisher_metadata_zip_is_pinned_not_just_zip_magic(self):
        raw = make_metadata()
        with self.assertRaisesRegex(gate.ArchiveBlocked, "wrong exact size"):
            gate.verify_original_metadata_zip(raw)
        with self.assertRaisesRegex(gate.ArchiveBlocked, "SHA256 mismatch"):
            gate.verify_original_metadata_zip(
                raw, expected_bytes=len(raw), expected_sha256="0"*64
            )

    def test_missing_or_misnamed_member_fail_closed(self):
        raw = make_metadata(extras=[("unexpected.txt", "some text")])
        with self.assertRaisesRegex(gate.ArchiveBlocked, "members drifted"):
            verify_meta(raw)

    def test_invalid_filename_relative_path_or_symlink_blocks(self):
        for name in ("../unsafe.txt", "/absolute", "C:\\windows\\escape"):
            raw = make_metadata(extras=[(name, "bad")])
            with self.subTest(name=name), self.assertRaises(gate.ArchiveBlocked):
                verify_meta(raw)

    def test_edition_or_doi_or_rights_changes_are_not_silently_accepted(self):
        tests = (
            {"idx": "FPA_FOD_20221014.gpkg spatial 1992-2020"},
            {"html": "FPA_FOD_20260615 2024 10.2737/RDS-2013-0009.6 without additional permissions or fees"},
            {"xml": "<root>FPA_FOD_20260615 2024 10.2737/RDS-2013-0009.7 restrictive license</root>"},
        )
        for change in tests:
            with self.subTest(change=change), self.assertRaises(gate.ArchiveBlocked):
                verify_meta(make_metadata(**change))

    def test_corrupted_checksum_or_not_a_zip_rejected(self):
        for b in (b"not a ZIP", b"bad", b""):
            with self.assertRaises(gate.ArchiveBlocked):
                verify_meta(b)

    def test_original_gpkg_full_archive_hash_plus_sqlite_header_without_event_reads(self):
        result = verify_gpkg(zip_gpkg())
        self.assertTrue(result["source_gpkg_member_exists"])
        self.assertTrue(result["member_sqlite_header_checked"])
        self.assertFalse(result["full_member_sqlite_table_or_spatial_integrity_checked"])
        self.assertFalse(result["source_event_rows_extracted_or_published"])

    def test_wrong_gpkg_signature_and_extra_member_block(self):
        with self.assertRaisesRegex(gate.ArchiveBlocked, "SQLite header"):
            verify_gpkg(zip_gpkg(contents=b"not a SQLite source" + b"\x00"*100_100))
        with self.assertRaisesRegex(gate.ArchiveBlocked, "membership drift"):
            verify_gpkg(zip_gpkg(extras=[("Data/another.gpkg", "other")]))

    def test_full_gpkg_archive_declared_sha_and_length_required(self):
        raw = zip_gpkg()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / gate.DATA_NAME
            path.write_bytes(raw)
            with self.assertRaisesRegex(gate.ArchiveBlocked, "wrong exact|incorrect full"):
                gate.verify_original_gpkg_zip(path)
            with self.assertRaisesRegex(gate.ArchiveBlocked, "SHA256 mismatch"):
                gate.verify_original_gpkg_zip(
                    path, expected_bytes=len(raw), expected_sha256="0"*64
                )

    def test_private_sqlite_2024_exact_grouped_source_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = Path(folder) / "synthetic-fires.gpkg"
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "CREATE TABLE Fires (FIRE_YEAR INTEGER, STATE TEXT, "
                    "FIRE_SIZE_CLASS TEXT, MTBS_ID TEXT)"
                )
                rows = [(2024, "CA", cls, "linked" if cls in ("A", "F") else None)
                        for cls in "ABCDEFG"]
                rows += [(2024, "OR", "F", None), (2024, "OR", "G", "linked"),
                         (2023, "CA", "A", "historical")]
                conn.executemany("INSERT INTO Fires VALUES (?,?,?,?)", rows)
            expected_all = dict(A=1, B=1, C=1, D=1, E=1, F=2, G=2)
            expected_linked = dict(A=1, B=0, C=0, D=0, E=0, F=1, G=1)
            result = gate.audit_extracted_fires_2024_sqlite(
                db_path,
                expected_records=9,
                expected_mtbs_id_present=3,
                expected_state_codes=2,
                expected_state_size_cells=9,
                expected_size_counts=expected_all,
                expected_link_counts=expected_linked,
            )
            self.assertEqual(result["original_2024_fpa_report_count"], 9)
            self.assertEqual(result["original_2024_mtbs_id_nonnull_count"], 3)
            self.assertTrue(result["archived_2024_counts_match_independently_read_original_arcgis"])
            self.assertFalse(result["source_identity_join_or_insurance_loss_model_admitted"])
            with self.assertRaisesRegex(gate.ArchiveBlocked, "A-G totals differ"):
                gate.audit_extracted_fires_2024_sqlite(
                    db_path, expected_records=9, expected_mtbs_id_present=3,
                    expected_state_codes=2, expected_state_size_cells=9,
                    expected_size_counts={**expected_all, "F": 3},
                    expected_link_counts=expected_linked,
                )

    def test_unrecognized_sqlite_schema_never_indicates_valid_source(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = Path(folder) / "unknown.gpkg"
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE Other (x INTEGER)")
            with self.assertRaisesRegex(gate.ArchiveBlocked, "Fires feature table"):
                gate.audit_extracted_fires_2024_sqlite(db_path)

    def test_optional_full_sqlite_audit_requires_exact_original_gpkg_length(self):
        raw = zip_gpkg()
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / gate.DATA_NAME
            p.write_bytes(raw)
            with self.assertRaisesRegex(gate.ArchiveBlocked, "expanded byte length drift"):
                gate.verify_original_gpkg_zip(
                    p, expected_bytes=len(raw),
                    expected_sha256=hashlib.sha256(raw).hexdigest(), audit_2024=True
                )
