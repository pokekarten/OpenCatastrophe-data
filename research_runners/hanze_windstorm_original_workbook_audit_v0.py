# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read every original HANZE windstorm XLSX impact row, fail-closed on source bytes.

Non-admission research preflight only. A country event report is NOT a unique
physical storm, a building claim, an independent observed-loss holdout, or
an annual catastrophe event/frequency sample. All data stay in memory.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from research_runners.hanze_windstorm_original_xlsx_acquisition_v0 import (
    ORIGINAL_SHA256, ORIGINAL_BYTES, ORIGINAL_PUBLISHER_MD5,
    OriginalHanzeError, inspect_source_bytes,
)

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
HEADERS = (
    "ID", "Code", "Year", "Country", "Start", "End", "Type", "Source",
    "Regions affected (NUTS2)", "Regions affected (NUTS3)",
    "Area affected", "Fatalities", "Persons affected",
    "Losses (nominal value)", "Losses (original currency)",
    "Losses (2020 euro) in milions", "Cause", "Notes", "CDS", "Sources",
)
COLS = tuple(chr(65 + n) for n in range(20))
CONTRACT = "OC_HANZE_WINDSTORM_XLSX_ORIGINAL_FULL_ROW_PREFLIGHT_V0"
MAX_XML_MEMBER_BYTES = 9_000_000
MAX_ROWS = 15_000
EXPECTED_SOURCE_ROWS = 1_358
EXPECTED_SOURCE_REFERENCES = 815
EXPECTED_SOURCE_CODES = 33
EXPECTED_SOURCE_MODELLED_CDS = 299
EXPECTED_SOURCE_KYRILL = 12
EXPECTED_SOURCE_KYRILL_CDS = 4
EXPECTED_SOURCE_MISSING_ECONOMIC_LOSS = 638
# Twelve publisher COUNTRY-report IDs of one named windstorm, not event IDs.
EXPECTED_KYRILL_COUNTRY_ID_PAIRS = (
    ("AT", "20034"), ("BE", "20076"), ("CH", "21154"),
    ("CZ", "20104"), ("DE", "20457"), ("DK", "20128"),
    ("FR", "20250"), ("IE", "20576"), ("LU", "20741"),
    ("NL", "20763"), ("PL", "20911"), ("UK", "21290"),
)


def _safe_root(blob: bytes, *, member: str):
    if not 0 < len(blob) <= MAX_XML_MEMBER_BYTES:
        raise OriginalHanzeError(f"XLSX XML source size outside bounded profile: {member}")
    # XML entities / DTD are unnecessary in this source and must never be
    # interpreted as external input instructions.
    if b"<!DOCTYPE" in blob.upper() or b"<!ENTITY" in blob.upper():
        raise OriginalHanzeError("XLSX XML entity or DTD not permitted")
    try:
        return ET.fromstring(blob)
    except ET.ParseError:
        raise OriginalHanzeError(f"invalid source XLSX XML member: {member}") from None


def _read_member(archive: ZipFile, member: str):
    try:
        info = archive.getinfo(member)
    except KeyError:
        raise OriginalHanzeError(f"required original workbook member missing: {member}") from None
    if info.file_size > MAX_XML_MEMBER_BYTES:
        raise OriginalHanzeError("XLSX XML member exceeds safety limit")
    with archive.open(info, "r") as source:
        blob = source.read(MAX_XML_MEMBER_BYTES + 1)
    return _safe_root(blob, member=member)


def _shared_strings(root) -> tuple[str, ...]:
    if root.tag != NS + "sst":
        raise OriginalHanzeError("unexpected XLSX shared string root")
    strings = []
    for si in root.findall(NS + "si"):
        # Includes rich text and runs. Only its original visible <t> content.
        strings.append("".join((t.text or "") for t in si.iter(NS + "t")))
    if len(strings) > 70_000:
        raise OriginalHanzeError("unbounded shared-string catalogue")
    return tuple(strings)


def _rows(sheet, strings: tuple[str, ...]) -> tuple[tuple[int, dict[str, str]], ...]:
    if sheet.tag != NS + "worksheet":
        raise OriginalHanzeError("unexpected XLSX worksheet root")
    sd = sheet.find(NS + "sheetData")
    if sd is None:
        raise OriginalHanzeError("XLSX worksheet has no sheetData")
    result = []
    for row in sd.findall(NS + "row"):
        raw_row = row.get("r")
        if raw_row is None or not raw_row.isdigit():
            raise OriginalHanzeError("row number missing")
        index = int(raw_row)
        if not 1 <= index <= MAX_ROWS or (result and index <= result[-1][0]):
            raise OriginalHanzeError("nonmonotone or excessive XLSX row indices")
        values: dict[str, str] = {}
        for cell in row.findall(NS + "c"):
            address = cell.get("r", "")
            match = re.fullmatch(r"([A-Z]+)([0-9]+)", address)
            if not match or int(match.group(2)) != index:
                raise OriginalHanzeError("invalid XLSX cell coordinate")
            col = match.group(1)
            if col in values:
                raise OriginalHanzeError("duplicate XLSX cell column")
            if cell.find(NS + "f") is not None:
                raise OriginalHanzeError("formulas prohibited in original evidence table")
            dtype = cell.get("t", "n")
            v = cell.find(NS + "v")
            if v is not None and v.text is not None:
                raw = v.text
                if dtype == "s":
                    if not raw.isdigit() or int(raw) >= len(strings):
                        raise OriginalHanzeError("invalid shared string index")
                    value = strings[int(raw)]
                elif dtype in ("n", "str"):
                    value = raw
                else:
                    raise OriginalHanzeError("unapproved original XLSX cell type")
                values[col] = value
            elif dtype == "inlineStr":
                node = cell.find(NS + "is")
                if node is not None:
                    values[col] = "".join(t.text or "" for t in node.iter(NS + "t"))
            # Blank/self-closing cells are deliberately OMITTED. They must
            # never inherit the following cell's economic-loss value.
        result.append((index, values))
    return tuple(result)


def _excel_date(raw: str | None) -> str | None:
    """Preserve empty vs exact ISO vs Excel 1900-date serial safely."""
    if raw is None or raw == "":
        return None
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", raw):
        try:
            return date.fromisoformat(raw).isoformat()
        except ValueError:
            return None
    if re.fullmatch(r"[0-9]{4,5}", raw):
        serial = int(raw)
        # 1900 leap-bug serials 0..60 are deliberately not interpreted.
        if not 61 <= serial <= 73050:
            return None
        try:
            return (date(1899, 12, 30) + timedelta(days=serial)).isoformat()
        except OverflowError:
            return None
    return None



def kyrill_country_source_candidate(rows: list[dict]) -> dict:
    """One *country-report review grouping*, never a physical cyclone ID.

    For named Kyrill reports only, use an exact 2007 shared calendar-day
    intersection and original distinct per-country report identities. A
    common date is necessary here but does NOT prove common meteorology,
    geographic footprint, independence or insurer coverage. The result
    cannot represent a dated annual event in NextGen or Oasis.
    """
    if type(rows) is not list or not rows or len(rows) > 33:
        raise OriginalHanzeError("bounded Kyrill source-country review requires rows")
    seen_ids = set()
    seen_countries = set()
    starts = []
    ends = []
    modelled = []
    without_loss = []
    indexed = []
    for row in rows:
        if type(row) is not dict:
            raise OriginalHanzeError("invalid Kyrill source row type")
        sid, code = row.get("source_id"), row.get("country_code")
        start, end = row.get("date_start"), row.get("date_end")
        model = row.get("publisher_modelled_cds_loss")
        value_present = row.get("economic_loss_value_present")
        if (type(sid) is not str or not re.fullmatch(r"[0-9]{1,10}", sid) or
                type(code) is not str or not re.fullmatch(r"[A-Z]{2}", code) or
                sid in seen_ids or code in seen_countries or
                type(model) is not bool or type(value_present) is not bool or
                type(start) is not str or type(end) is not str):
            raise OriginalHanzeError("Kyrill candidate contains invalid or duplicate report identity")
        try:
            start_day, end_day = date.fromisoformat(start), date.fromisoformat(end)
        except ValueError:
            raise OriginalHanzeError("invalid Kyrill calendar day") from None
        if (start_day.year != 2007 or end_day.year != 2007 or start_day > end_day or
                start_day < date(2007, 1, 16) or end_day > date(2007, 1, 21)):
            raise OriginalHanzeError("Kyrill dates outside bounded publisher review window")
        seen_ids.add(sid)
        seen_countries.add(code)
        starts.append(start_day)
        ends.append(end_day)
        indexed.append((code, sid))
        if model:
            modelled.append(code)
        if not value_present:
            without_loss.append(code)
    if max(starts) > min(ends):
        raise OriginalHanzeError("Kyrill countries have no common review-window date intersection")
    return {
        "contract": "OC_HANZE_KYRILL_2007_COUNTRY_REPORT_REVIEW_CANDIDATE_V0",
        "status": "SOURCE_COUNTRY_ROWS_CANDIDATE_ONLY_NOT_VERIFIED_STORM_PARENT",
        "source_storm_label": "Kyrill",
        "review_day_intersection_start": max(starts).isoformat(),
        "review_day_intersection_end": min(ends).isoformat(),
        "country_report_rows": len(rows),
        "country_codes": sorted(seen_countries),
        "source_country_id_pairs": [
            {"country_code": code, "publisher_row_id": sid}
            for code, sid in sorted(indexed)
        ],
        "country_codes_explicitly_modelled_cds": sorted(modelled),
        "country_codes_without_economic_loss_value": sorted(without_loss),
        "country_codes_not_explicitly_modelled_cds": sorted(seen_countries - set(modelled)),
        "other_country_rows_independently_observed": False,
        "source_impact_is_insured_loss": False,
        "published_cross_country_parent_storm_id": None,
        "native_c3s_climk_oasis_parent_id": None,
        "independent_physical_hazard_occurrences": None,
        "annual_event_frequency": None, "annual_AAL": None,
        "annual_AEP": None, "annual_OEP": None,
        "insurer_gross_net_validated": False,
        "scientific_or_rights_admitted": False,
    }



def audit_workbook(
    original: bytes, *, expected_size: int = ORIGINAL_BYTES,
    expected_md5: str = ORIGINAL_PUBLISHER_MD5,
    expected_sha256: str = ORIGINAL_SHA256,
) -> dict:
    """Inspect all sheet rows, emit no original rows and never admit claims.

    Pinned original bytes are enforced in the production CLI; test overrides
    are for synthetic workbook fixtures and do not create source admission.
    """
    original_receipt = inspect_source_bytes(
        original, size=expected_size, publisher_md5=expected_md5,
        expected_sha256=expected_sha256,
    )
    with ZipFile(__import__("io").BytesIO(original)) as archive:
        workbook = _read_member(archive, "xl/workbook.xml")
        props = workbook.find(NS + "workbookPr")
        if props is not None and props.get("date1904", "0") in ("1", "true"):
            raise OriginalHanzeError("unsupported workbook 1904 date system")
        strings = _shared_strings(_read_member(archive, "xl/sharedStrings.xml"))
        sheet1 = _rows(_read_member(archive, "xl/worksheets/sheet1.xml"), strings)
        references = _rows(_read_member(archive, "xl/worksheets/sheet2.xml"), strings)
    if not sheet1 or sheet1[0][0] != 1 or tuple(
        sheet1[0][1].get(col) for col in COLS
    ) != HEADERS:
        raise OriginalHanzeError("original 20-column windstorm impact schema drift")
    if not references or references[0][0] != 1 or tuple(
        references[0][1].get(col) for col in ("A", "B", "C", "D")
    ) != ("No.", "Name", "URL", "Type"):
        raise OriginalHanzeError("original source-reference worksheet schema drift")
    data = sheet1[1:]
    if not data or len(data) > MAX_ROWS - 1:
        raise OriginalHanzeError("no valid bounded windstorm impact rows")
    ids = set()
    countries = set()
    years = []
    has_econ = 0
    has_nominal = 0
    modelled = 0
    kyrill = []
    date_serials = 0
    bad_dates = []
    mismatched_year = 0
    for row_number, cells in data:
        key = cells.get("A")
        code = cells.get("B")
        country = cells.get("D")
        year_raw = cells.get("C")
        if (key is None or not re.fullmatch(r"[0-9]{1,10}", key) or
                key in ids or code is None or not re.fullmatch(r"[A-Z]{2}", code) or
                not country or not year_raw or not re.fullmatch(r"[0-9]{4}", year_raw)):
            raise OriginalHanzeError("invalid/duplicate source ID, country or year")
        ids.add(key)
        countries.add(code)
        year = int(year_raw)
        years.append(year)
        start, end = _excel_date(cells.get("E")), _excel_date(cells.get("F"))
        if start is None or end is None:
            bad_dates.append({"source_id": key, "problem": "UNPARSEABLE_DATE"})
        elif start > end:
            bad_dates.append({
                "source_id": key, "problem": "END_BEFORE_START",
                "normalized_start": start, "normalized_end": end,
            })
        if start and year != int(start[:4]):
            mismatched_year += 1
        if (cells.get("E") and str(cells["E"]).isdigit() or
                cells.get("F") and str(cells["F"]).isdigit()):
            date_serials += 1
        if cells.get("P") not in (None, ""):
            raw = cells["P"]
            try:
                from decimal import Decimal, InvalidOperation
                val = Decimal(raw)
            except (InvalidOperation, ValueError):
                raise OriginalHanzeError("invalid economic loss amount") from None
            if not val.is_finite() or val < 0:
                raise OriginalHanzeError("invalid economic loss units/value")
            has_econ += 1
        if cells.get("N") not in (None, ""):
            has_nominal += 1
        source_modelled_cds = bool(re.search(
            r"modelled economic loss from cds",
            " ".join((cells.get("S", ""), cells.get("R", ""))), re.IGNORECASE))
        if source_modelled_cds:
            modelled += 1
        if (cells.get("H") or "").casefold().strip() == "kyrill":
            kyrill.append({
                "source_id": key, "country_code": code, "date_start": start,
                "date_end": end, "publisher_modelled_cds_loss": source_modelled_cds,
                "economic_loss_value_present": cells.get("P") not in (None, ""),
            })
    # Original exact-hash facts are a regression gate, not a quality score.
    is_original = expected_sha256 == ORIGINAL_SHA256 and expected_size == ORIGINAL_BYTES
    if is_original and (
        len(data) != EXPECTED_SOURCE_ROWS or len(countries) != EXPECTED_SOURCE_CODES or
        len(references) - 1 != EXPECTED_SOURCE_REFERENCES or
        modelled != EXPECTED_SOURCE_MODELLED_CDS or
        len(kyrill) != EXPECTED_SOURCE_KYRILL or
        sum(item["publisher_modelled_cds_loss"] for item in kyrill) != EXPECTED_SOURCE_KYRILL_CDS or
        tuple(sorted((item["country_code"], item["source_id"]) for item in kyrill)) !=
        EXPECTED_KYRILL_COUNTRY_ID_PAIRS or
        len(data) - has_econ != EXPECTED_SOURCE_MISSING_ECONOMIC_LOSS
    ):
        raise OriginalHanzeError("pinned original XLSX fails independently reviewed row profile")
    return {
        "contract": CONTRACT,
        "status": "ORIGINAL_COMPLETE_XLSX_ROWS_READ_RESEARCH_UNADMITTED",
        "original_sha256": original_receipt["original_sha256"],
        "source_year_min": min(years),
        "source_year_max": max(years),
        "original_impact_country_rows": len(data),
        "unique_publisher_country_row_ids": len(ids),
        "country_code_count": len(countries),
        "original_reference_worksheet_rows": len(references) - 1,
        "economic_loss_2020_eur_million_present": has_econ,
        "economic_loss_2020_eur_million_missing": len(data) - has_econ,
        "nominal_economic_loss_value_present": has_nominal,
        "explicit_publisher_modelled_cds_loss_rows": modelled,
        "rows_with_excel_date_serials": date_serials,
        "year_differs_from_normalized_start_year": mismatched_year,
        "unresolved_date_rows": bad_dates,
        "named_kyrill_country_rows": len(kyrill),
        "kyrill_candidates": sorted(kyrill, key=lambda x: x["country_code"]),
        "kyrill_source_country_review_candidate": (
            kyrill_country_source_candidate(kyrill) if kyrill else None
        ),
        "published_loss_equals_observed_claim": False,
        "modelled_loss_eligible_for_independent_empirical_holdout": False,
        "other_loss_rows_independently_verified": False,
        "yearly_country_rows_are_independent_physical_storms": False,
        "c3s_climk_native_event_ids_joined": False,
        "original_data_rights_admitted": False,
        "source_rows_promoted_to_cat": False,
        "annual_event_frequency": None,
        "annual_AAL": None, "annual_AEP": None, "annual_OEP": None,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-xlsx", type=Path, required=True,
                   help="exact SHA-pinned source workbook already downloaded outside Git")
    args = p.parse_args(argv)
    path = args.original_xlsx.absolute()
    root = Path(__file__).resolve().parents[1]
    if path.is_symlink() or root == path or root in path.parents:
        p.error("original source must be a regular file outside the Git checkout")
    if not path.is_file() or path.stat().st_size != ORIGINAL_BYTES:
        p.error("original XLSX missing or not exactly published size")
    receipt = audit_workbook(path.read_bytes())
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
