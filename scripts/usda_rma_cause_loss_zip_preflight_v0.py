# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed USDA RMA 2025 Cause-of-Loss ZIP structure preflight.

The exact public 2025 ZIP is published by USDA RMA as colsom_2025.zip.
The authoritative 2026-05-28 record layout describes 30 pipe-delimited fields.
No network requests, SQL, third-party raw bytes in Git, or model admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

ZIP_NAME = "colsom_2025.zip"
SOURCE_URL = (
    "https://pubfs-rma.fpac.usda.gov/pub/Web_Data_Files/"
    "Summary_of_Business/cause_of_loss/colsom_2025.zip"
)
LAYOUT_URL = (
    "https://pubfs-rma.fpac.usda.gov/pub/Web_Data_Files/"
    "Summary_of_Business/cause_of_loss/"
    "COL_Summary_of_Business_with_Month_All_Years.pdf"
)
SOURCE_ID = "usda.rma.crop-cause-of-loss-summary.2026"
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_MEMBER_BYTES = 192 * 1024 * 1024
MAX_RECORD_BYTES = 8192
MAX_ROWS = 3_000_000
MAX_MEMBERS = 16
FIELD_COUNT = 30
COVERAGE = frozenset("ACEL")

# One-based official 2026-05-28 layout:
# 1 crop year, 2-5 state/county, 6-7 commodity, 8-9 insurance plan,
# 10 coverage, 11 stage, 12-13 cause, 14-16 loss month/name/year,
# 17-18 policy counts, 19-20 quantity, 21-27 dollar amounts,
# 28 quantity, 29 signed indemnity, 30 loss ratio.
DIGIT_FIELDS = {
    0: 4, 1: 2, 3: 3, 5: 4, 7: 2, 11: 2, 13: 2, 15: 4
}
MONEY_FIELDS = tuple(range(20, 27))
QUANTITY_FIELDS = (18, 19, 27)
COUNT_FIELDS = (16, 17)
# The report's implicit V decimal picture is NOT guaranteed to appear as a
# decimal point in the exported text. Accept both, never rescale or aggregate.
DECIMAL_RE = re.compile(r"[0-9]{1,12}(?:\.[0-9]{1,2})?\Z")
SIGNED_RE = re.compile(r"[+-]?[0-9]{1,12}(?:\.[0-9]{1,2})?\Z")


class Blocked(ValueError):
    """Untrusted source bytes, unsupported layout or unresolved ambiguity."""


def _decimal(raw: str, *, signed: bool = False) -> Decimal:
    if not (SIGNED_RE if signed else DECIMAL_RE).fullmatch(raw):
        raise Blocked("invalid source numeric field")
    try:
        number = Decimal(raw)
    except InvalidOperation as exc:
        raise Blocked("invalid source numeric field") from exc
    if not number.is_finite():
        raise Blocked("non-finite source numeric field")
    return number


def _member_safe(item: zipfile.ZipInfo) -> bool:
    path = PurePosixPath(item.filename)
    return (not item.is_dir() and bool(item.filename)
            and not item.filename.startswith(("/", "\\"))
            and "\\" not in item.filename
            and len(item.filename) <= 220
            and all(p not in {".", "..", ""} for p in item.filename.split("/"))
            and ((item.external_attr >> 16) & stat.S_IFMT(0o170000))
                != stat.S_IFLNK
            and not item.flag_bits & 1)


def _record(raw: bytes, line_no: int, expected_year: int) -> tuple[str, str, str, bool, bool]:
    if len(raw) > MAX_RECORD_BYTES or b"\x00" in raw:
        raise Blocked(f"record {line_no}: oversized/binary data")
    try:
        fields = raw.decode("utf-8-sig").rstrip("\r\n").split("|")
    except UnicodeDecodeError as exc:
        raise Blocked(f"record {line_no}: not UTF-8") from exc
    if len(fields) != FIELD_COUNT:
        raise Blocked(f"record {line_no}: expected 30 pipe-delimited fields")
    cells = [c.strip() for c in fields]
    for index, width in DIGIT_FIELDS.items():
        if not re.fullmatch(r"[0-9]{1," + str(width) + r"}", cells[index], re.ASCII):
            raise Blocked(f"record {line_no}: invalid coded field {index+1}")
    if int(cells[0]) != expected_year:
        raise Blocked(f"record {line_no}: wrong commodity/policy year")
    if int(cells[15]) < 1989 or int(cells[15]) > expected_year + 2:
        raise Blocked(f"record {line_no}: unexpected year of loss")
    if not 1 <= int(cells[13]) <= 12:
        raise Blocked(f"record {line_no}: invalid month of loss")
    if cells[9] not in COVERAGE:
        raise Blocked(f"record {line_no}: invalid coverage category")
    if not re.fullmatch(r"[A-Z]{2}", cells[2], re.ASCII):
        raise Blocked(f"record {line_no}: invalid state abbreviation")
    if not cells[4] or not cells[6] or not cells[12]:
        raise Blocked(f"record {line_no}: missing geography, commodity or cause name")
    # RMA states policy counts are not available for CLIP plans. Preserve
    # blank count as missing rather than incorrectly interpreting as zero.
    missing_policy_count = False
    for idx in COUNT_FIELDS:
        if cells[idx] == "":
            missing_policy_count = True
        elif not re.fullmatch(r"[0-9]{1,9}", cells[idx], re.ASCII):
            raise Blocked(f"record {line_no}: invalid policy count")
    for idx in (*QUANTITY_FIELDS, *MONEY_FIELDS):
        if cells[idx]:
            _decimal(cells[idx])
        # Optional/missing source fields are never converted to zero.
    indemnity = _decimal(cells[28], signed=True)
    if cells[29]:
        _decimal(cells[29])
    return cells[1], cells[11], cells[13], indemnity < 0, missing_policy_count


def inspect_zip(original: bytes, *, member: str | None = None,
                year: int = 2025) -> dict[str, object]:
    if type(original) is not bytes or not 0 < len(original) <= MAX_ARCHIVE_BYTES:
        raise Blocked("archive byte limit or empty source")
    if year != 2025:
        raise Blocked("only the exact 2025 ZIP profile has been researched")
    try:
        archive = zipfile.ZipFile(io.BytesIO(original))
    except (zipfile.BadZipFile, OSError) as exc:
        raise Blocked("invalid original ZIP container") from exc
    with archive:
        all_files = archive.infolist()
        if not 0 < len(all_files) <= MAX_MEMBERS:
            raise Blocked("ZIP member count exceeds bounded profile")
        files = [info for info in all_files if not info.is_dir()]
        if not files or not all(_member_safe(info) for info in files):
            raise Blocked("unsafe ZIP member path/type/encryption")
        if len({info.filename for info in files}) != len(files):
            raise Blocked("duplicate ZIP member name")
        if member is None:
            candidates = [
                item for item in files
                if item.filename.lower().endswith((".txt", ".dat"))
            ]
            if len(candidates) != 1:
                raise Blocked("ambiguous ZIP data member; choose --member explicitly")
            chosen = candidates[0]
        else:
            candidates = [i for i in files if i.filename == member]
            if len(candidates) != 1 or not member.lower().endswith((".txt", ".dat")):
                raise Blocked("exact named ZIP data member unavailable/unsupported")
            chosen = candidates[0]
        if chosen.file_size > MAX_MEMBER_BYTES or chosen.compress_size == 0:
            raise Blocked("unbounded source member")
        if chosen.file_size > chosen.compress_size * 300:
            raise Blocked("ZIP compression ratio exceeds bounded limit")
        rows = 0
        states: Counter[str] = Counter()
        causes: set[str] = set()
        months: set[str] = set()
        negative_indemnity_rows = 0
        missing_policy_counts = 0
        h = hashlib.sha256()
        try:
            with archive.open(chosen) as stream:
                for raw_line in stream:
                    rows += 1
                    if rows > MAX_ROWS:
                        raise Blocked("too many source records")
                    h.update(raw_line)
                    state, cause, month, is_negative, missing_count = _record(
                        raw_line, rows, year,
                    )
                    states[state] += 1
                    causes.add(cause)
                    months.add(month)
                    negative_indemnity_rows += int(is_negative)
                    missing_policy_counts += int(missing_count)
        except (zipfile.BadZipFile, RuntimeError, OSError, EOFError) as exc:
            raise Blocked("corrupt or unsupported ZIP member") from exc
        if rows == 0:
            raise Blocked("data member has no source records")
        return {
            "schema_version": "rma-2025-colsom-zip-offline-preflight-v0",
            "source_id": SOURCE_ID,
            "source_product_url": SOURCE_URL,
            "publisher_record_layout_url": LAYOUT_URL,
            "commodity_year": year,
            "original_local_archive_sha256": hashlib.sha256(original).hexdigest(),
            "original_local_archive_byte_count": len(original),
            "local_decompressed_member_sha256": h.hexdigest(),
            "local_decompressed_member_byte_count": chosen.file_size,
            "rows": rows,
            "distinct_states": len(states),
            "distinct_causes": len(causes),
            "distinct_loss_months": len(months),
            "negative_indemnity_rows": negative_indemnity_rows,
            "rows_with_missing_policy_counts": missing_policy_counts,
            "source_original_http_response_authenticated": False,
            "source_rights_and_automation_reviewed": False,
            "data_fully_scientifically_validated": False,
            "cat_model_input_approved": False,
            "derived_elt_or_insured_portfolio_approved": False,
            "external_database_import_performed": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True,
                        help="Already-acquired source ZIP outside Git")
    parser.add_argument("--member", type=str, default=None,
                        help="Exact internal text member if multiple candidates exist")
    args = parser.parse_args(argv)
    try:
        path = args.zip
        if path.is_symlink() or not path.is_file() or path.name != ZIP_NAME:
            raise Blocked("expected a regular exact-named 2025 source ZIP")
        if path.stat().st_size > MAX_ARCHIVE_BYTES:
            raise Blocked("source ZIP too large")
        with path.open("rb") as f:
            data = f.read(MAX_ARCHIVE_BYTES + 1)
        result = inspect_zip(data, member=args.member)
    except (OSError, Blocked) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
