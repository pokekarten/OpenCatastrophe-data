# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independently synthetic, offline 46-page source receipt safety tests."""
import hashlib
import json
import unittest

from scripts.insurer_directory_source_receipt_v0 import EXPECTED_VERSION, SOURCE_URL
from scripts.insurer_directory_paged_source_receipt_v0 import (
    PageReceiptError, PAGE_COUNT, PAGE_SIZE, PAGE_URL_PREFIX,
    TOTAL_COUNT, audit_pages, inspect_page, page_url,
)

TEST_COUNT, TEST_SIZE, TEST_PAGES = 5, 2, 3


def fixture(page, *, count=TEST_COUNT, page_size=TEST_SIZE,
            page_count=TEST_PAGES):
    rows = []
    for num in range((page - 1) * page_size + 1,
                     min(count, page * page_size) + 1):
        rows.append({"slug": f"synthetic-{num}", "name": f"Synthetic Insurer {num}",
                     "country": "testland", "classCode": "G",
                     "verification": "verified"})
    return {
        "dataset": "Synthetic test register",
        "version": EXPECTED_VERSION,
        "verified": "2026-09-08",
        "licence": "CC BY 4.0 attribute KAFS North America, synthetic test only",
        "count": count, "page": page, "pageSize": page_size,
        "pageCount": page_count, "all": SOURCE_URL,
        "first": page_url(1), "last": page_url(page_count),
        "prev": page_url(page - 1) if page > 1 else None,
        "next": page_url(page + 1) if page < page_count else None,
        "data": rows,
    }


def raw(obj):
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def synthetic_read(mutator=None):
    def read(page):
        obj = fixture(page)
        if mutator:
            mutator(obj, page)
        return raw(obj)
    return read


def audit(reader):
    return audit_pages(reader, total_count=TEST_COUNT,
                       page_size=TEST_SIZE, page_count=TEST_PAGES)


class PageReceiptTests(unittest.TestCase):
    def test_offline_complete_original_page_manifest(self):
        result = audit(synthetic_read())
        self.assertEqual(result["total_source_rows"], 5)
        self.assertEqual(result["unique_source_slugs"], 5)
        self.assertEqual([p["row_count"] for p in result["pages"]], [2, 2, 1])
        self.assertEqual(result["pages"][0]["raw_page_sha256"],
                         hashlib.sha256(raw(fixture(1))).hexdigest())
        self.assertIsNone(result["source_aggregate_original_sha256"])
        source_rows = [r for p in (1, 2, 3) for r in fixture(p)["data"]]
        parts = []
        for r in sorted(source_rows, key=lambda item: item["slug"]):
            parts.append(chr(31).join([
                r["slug"], r["country"], r["name"], r["classCode"], r["verification"]
            ]))
        independent_digest = hashlib.sha256(chr(30).join(parts).encode("utf-8")).hexdigest()
        self.assertEqual(result["canonical_field_digest_sha256"], independent_digest)
        self.assertEqual(result["canonical_record_separator"], "0x1e")
        self.assertEqual(result["canonical_field_separator"], "0x1f")
        for key in ("model_input_approved", "regulator_identity_verified",
                    "neon_database_written", "original_page_bytes_committed_to_git"):
            self.assertFalse(result[key])
        self.assertEqual(PAGE_SIZE, 400)
        self.assertEqual(PAGE_COUNT, 46)
        self.assertEqual(TOTAL_COUNT, 18180)

    def test_duplicate_slug_across_pages_rejected(self):
        def mutate(obj, page):
            if page == 2:
                obj["data"][0]["slug"] = "synthetic-1"
        with self.assertRaisesRegex(PageReceiptError, "cross-page duplicate"):
            audit(synthetic_read(mutate))

    def test_duplicate_slug_within_one_page_rejected(self):
        def mutate(obj, page):
            if page == 1:
                obj["data"][1]["slug"] = obj["data"][0]["slug"]
        with self.assertRaisesRegex(PageReceiptError, "within original page"):
            audit(synthetic_read(mutate))

    def test_page_version_fails_closed(self):
        def mutate(obj, page):
            if page == 2:
                obj["version"] = "unknown"
        with self.assertRaisesRegex(PageReceiptError, "version"):
            audit(synthetic_read(mutate))

    def test_missing_or_short_last_page_rejected(self):
        def mutate(obj, page):
            if page == 3:
                obj["data"] = []
        with self.assertRaisesRegex(PageReceiptError, "incomplete"):
            audit(synthetic_read(mutate))

    def test_bad_navigation_and_page_count_rejected(self):
        for key, value in (("next", "https://example.test/host"),
                           ("pageCount", 200),
                           ("all", "https://example.test/index"),
                           ("page", True)):
            with self.subTest(key=key):
                def mutate(obj, page):
                    if page == 1:
                        obj[key] = value
                with self.assertRaises(PageReceiptError):
                    audit(synthetic_read(mutate))

    def test_unreviewed_verification_and_licence_rejected(self):
        for key, value in (("verification", "licensed-official"),
                           ("licence", "unreviewed")):
            with self.subTest(key=key):
                def mutate(obj, page):
                    if page == 1:
                        if key == "verification":
                            obj["data"][0]["verification"] = value
                        else:
                            obj["licence"] = value
                with self.assertRaises(PageReceiptError):
                    audit(synthetic_read(mutate))

    def test_duplicate_json_keys_and_nan_rejected(self):
        original = raw(fixture(1))
        mutated = original.replace(b'"version":', b'"version":"fake","version":', 1)
        with self.assertRaises(PageReceiptError):
            inspect_page(mutated, 1, total_count=5, page_size=2, page_count=3)
        mutated = original.replace(b'"page": 1', b'"page": NaN', 1)
        with self.assertRaises(PageReceiptError):
            inspect_page(mutated, 1, total_count=5, page_size=2, page_count=3)

    def test_empty_non_utf8_and_oversize_rejected(self):
        for value in (b'', b'\xff', b' ' * 300001):
            with self.subTest(size=len(value)), self.assertRaises(PageReceiptError):
                inspect_page(value, 1, total_count=5, page_size=2, page_count=3)

    def test_source_delimiter_attack_rejected(self):
        for separator in (chr(30), chr(31)):
            with self.subTest(separator=ord(separator)):
                def mutate(obj, page):
                    if page == 2:
                        obj["data"][0]["name"] += separator + "another-row"
                with self.assertRaisesRegex(PageReceiptError, "reserved digest delimiter"):
                    audit(synthetic_read(mutate))

    def test_digest_changes_when_original_name_changes(self):
        before = audit(synthetic_read())["canonical_field_digest_sha256"]
        def mutate(obj, page):
            if page == 2:
                obj["data"][0]["name"] += " A"
        after = audit(synthetic_read(mutate))["canonical_field_digest_sha256"]
        self.assertNotEqual(before, after)

    def test_fixed_page_url_rejects_noninteger_and_out_of_bounds(self):
        for value in (0, -1, PAGE_COUNT + 1, True, 1.0):
            with self.subTest(value=value), self.assertRaises(PageReceiptError):
                page_url(value)
        self.assertEqual(page_url(46), PAGE_URL_PREFIX + "46.json")


if __name__ == "__main__":
    unittest.main()
