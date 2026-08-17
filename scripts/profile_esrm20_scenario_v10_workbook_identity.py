# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded identity-only profile of ESRM20 v1.0 ``testing_scenarios.xlsx``.

The workbook is read only from the immutable project-273 v1.0 commit after its
Git blob identity is re-derived from the hardened repository-tree collector.
XLSX bytes are transient. Durable output contains receipts and redacted
occurrence/binding counts only; it never returns workbook cells/rows, selects a
scenario, or promotes a city inference to model authority.
"""

from __future__ import annotations

import hashlib
import io
import re
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

from scripts import acquire_efehr_esrm20_scenario_tree_metadata as tree
from scripts import acquire_efehr_gitlab_receipt as transport
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT

SCHEMA_VERSION = "oc-esrm20-scenario-v10-workbook-identity-profile-v1"
SOURCE_ISSUE = 285
PROJECT_ID = 273
PROJECT_PATH = "efehr/esrm20_scenario_tests"
RELEASE_TAG = "v1.0"
COMMIT_SHA = "041f90d950d6ff84180b2faa11319a42c66c74cc"
WORKBOOK_PATH = "testing_scenarios.xlsx"
TARGET_EVENT_ID = "Greece_07-9-1999"
NAME_LITERALS = ("athens", "thessaloniki")

MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_ZIP_MEMBERS = 256
MAX_MEMBER_BYTES = 8 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
MAX_SHARED_STRINGS = 100_000
MAX_WORKSHEETS = 64
MAX_ROWS = 100_000
MAX_CELLS = 500_000
MAX_CELL_UTF8_BYTES = 8 * 1024
MAX_TREE_PATH_UTF8_BYTES = 2048
TOTAL_DEADLINE_SECONDS = 90.0
_ALLOWED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
_ALLOWED_BLOB_MODES = {"100644", "100755", "120000"}
_CELL_REF_RE = re.compile(r"^[A-Z]{1,4}[1-9][0-9]{0,6}$")
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_WORD_PATTERNS = {
    name: re.compile(rf"(?<![a-z]){re.escape(name)}(?![a-z])", re.IGNORECASE)
    for name in NAME_LITERALS
}
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_WORKSHEET_REL_TYPE = f"{_REL_NS}/worksheet"

_TREE_ACQUIRE = tree.acquire_esrm20_scenario_tree_metadata
_OPEN_FIXED = transport._open_fixed
_READ_BOUNDED = transport._read_bounded
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_MONOTONIC = time.monotonic
_NOW = transport.utc_now


class ScenarioWorkbookIdentityError(RuntimeError):
    """Raised when the fixed workbook identity profile cannot be proven safely."""


def _bounded_text(value: object, *, field: str) -> str:
    if type(value) is not str:
        raise ScenarioWorkbookIdentityError(f"{field} is not text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ScenarioWorkbookIdentityError(f"{field} is not UTF-8 encodable") from exc
    if len(encoded) > MAX_CELL_UTF8_BYTES:
        raise ScenarioWorkbookIdentityError(f"{field} exceeds bounded policy")
    if any(ord(ch) < 32 and ch not in "\t\n" for ch in value) or any(
        ord(ch) == 127 for ch in value
    ):
        raise ScenarioWorkbookIdentityError(f"{field} contains control characters")
    return value


def _canonical_tree_path(value: object) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise ScenarioWorkbookIdentityError("scenario tree path is invalid")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ScenarioWorkbookIdentityError("scenario tree path is not UTF-8 encodable") from exc
    if len(encoded) > MAX_TREE_PATH_UTF8_BYTES:
        raise ScenarioWorkbookIdentityError("scenario tree path exceeds bounded policy")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ScenarioWorkbookIdentityError("scenario tree path contains control characters")
    pure = PurePosixPath(value)
    if pure.is_absolute() or str(pure) != value or any(
        part in ("", ".", "..") for part in pure.parts
    ):
        raise ScenarioWorkbookIdentityError("scenario tree path is noncanonical")
    return value


def _validate_tree_entry(raw: object) -> dict[str, str]:
    if type(raw) is not dict or set(raw) != {"path", "type", "id", "mode"}:
        raise ScenarioWorkbookIdentityError("scenario tree entry shape drifted")
    path = _canonical_tree_path(raw["path"])
    entry_type = raw["type"]
    object_id = raw["id"]
    mode = raw["mode"]
    if type(entry_type) is not str or entry_type not in {"blob", "tree"}:
        raise ScenarioWorkbookIdentityError("scenario tree entry type is invalid")
    if type(object_id) is not str or _SHA1_RE.fullmatch(object_id) is None:
        raise ScenarioWorkbookIdentityError("scenario tree object id is invalid")
    if type(mode) is not str:
        raise ScenarioWorkbookIdentityError("scenario tree mode is invalid")
    if entry_type == "tree":
        if mode != "040000":
            raise ScenarioWorkbookIdentityError("scenario tree type/mode pair is invalid")
    elif mode not in _ALLOWED_BLOB_MODES:
        raise ScenarioWorkbookIdentityError("scenario tree type/mode pair is invalid")
    return {"path": path, "type": entry_type, "id": object_id, "mode": mode}


def _tree_identity(entries: list[dict[str, str]]) -> str:
    canonical = "".join(
        f"{item['type']}\t{item['mode']}\t{item['id']}\t{item['path']}\n"
        for item in sorted(
            entries,
            key=lambda item: (item["path"], item["type"], item["id"]),
        )
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _workbook_blob_from_tree(receipt: object) -> tuple[str, str]:
    if type(receipt) is not dict:
        raise ScenarioWorkbookIdentityError("scenario tree receipt is not an object")
    fixed = (
        ("schema_version", tree.SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("release_tag", RELEASE_TAG),
        ("resolved_commit_sha", COMMIT_SHA),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in fixed:
        observed = receipt.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise ScenarioWorkbookIdentityError(f"scenario tree receipt drifted at {field}")

    raw_entries = receipt.get("entries")
    count = receipt.get("tree_entry_count")
    if (
        type(raw_entries) is not list
        or not raw_entries
        or type(count) is not int
        or isinstance(count, bool)
        or count != len(raw_entries)
    ):
        raise ScenarioWorkbookIdentityError("scenario tree inventory is incomplete")

    entries: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for raw in raw_entries:
        entry = _validate_tree_entry(raw)
        if entry["path"] in seen_paths:
            raise ScenarioWorkbookIdentityError("scenario tree paths are duplicated")
        seen_paths.add(entry["path"])
        entries.append(entry)

    matches = [item for item in entries if item["path"] == WORKBOOK_PATH]
    if len(matches) != 1:
        raise ScenarioWorkbookIdentityError("fixed workbook is not unique in immutable tree")
    match = matches[0]
    if match["type"] != "blob" or match["mode"] != "100644":
        raise ScenarioWorkbookIdentityError("fixed workbook is not a canonical regular blob")
    return match["id"], _tree_identity(entries)


def _raw_url() -> str:
    path = urllib.parse.quote(WORKBOOK_PATH, safe="")
    ref = urllib.parse.quote(COMMIT_SHA, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/files/"
        f"{path}/raw?ref={ref}"
    )


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _canonical_zip_name(name: object) -> str:
    if type(name) is not str or not name or "\\" in name:
        raise ScenarioWorkbookIdentityError("XLSX member name is invalid")
    candidate = name[:-1] if name.endswith("/") else name
    pure = PurePosixPath(candidate)
    if (
        not candidate
        or pure.is_absolute()
        or str(pure) != candidate
        or any(part in ("", ".", "..") for part in pure.parts)
    ):
        raise ScenarioWorkbookIdentityError("XLSX member path is noncanonical")
    return name


def _canonical_relationship_target(value: object) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise ScenarioWorkbookIdentityError("worksheet relationship target is invalid")
    if "?" in value or "#" in value:
        raise ScenarioWorkbookIdentityError("worksheet relationship target is invalid")
    pure = PurePosixPath(value)
    if pure.is_absolute() or str(pure) != value or any(
        part in ("", ".", "..") for part in pure.parts
    ):
        raise ScenarioWorkbookIdentityError("worksheet relationship target is noncanonical")
    resolved = f"xl/{value}"
    resolved_pure = PurePosixPath(resolved)
    if (
        str(resolved_pure) != resolved
        or not resolved.startswith("xl/worksheets/")
        or not resolved.endswith(".xml")
    ):
        raise ScenarioWorkbookIdentityError("worksheet relationship target escapes worksheet root")
    return resolved


def _read_zip_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    if info.is_dir():
        raise ScenarioWorkbookIdentityError("XLSX required XML member is a directory")
    if info.flag_bits & 0x1:
        raise ScenarioWorkbookIdentityError("encrypted XLSX members are forbidden")
    if info.compress_type not in _ALLOWED_COMPRESSION:
        raise ScenarioWorkbookIdentityError("XLSX compression method is outside policy")
    if not (0 <= info.file_size <= MAX_MEMBER_BYTES):
        raise ScenarioWorkbookIdentityError("XLSX member size exceeds bounded policy")
    try:
        data = archive.read(info)
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise ScenarioWorkbookIdentityError("XLSX member read failed closed") from exc
    if len(data) != info.file_size:
        raise ScenarioWorkbookIdentityError("XLSX member size disagrees with ZIP metadata")
    upper = data.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ScenarioWorkbookIdentityError("DTD/entity declarations are forbidden in XLSX XML")
    return data


def _parse_xml(payload: bytes, *, label: str) -> ET.Element:
    try:
        return ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ScenarioWorkbookIdentityError(f"{label} XML is malformed") from exc


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _element_text(element: ET.Element) -> str:
    parts: list[str] = []
    for node in element.iter():
        if _local(node.tag) == "t" and node.text is not None:
            parts.append(node.text)
    return _bounded_text("".join(parts), field="XLSX cell text")


def _shared_strings(archive: zipfile.ZipFile, infos: dict[str, zipfile.ZipInfo]) -> list[str]:
    info = infos.get("xl/sharedStrings.xml")
    if info is None:
        return []
    root = _parse_xml(_read_zip_member(archive, info), label="sharedStrings")
    strings: list[str] = []
    for node in root.iter():
        if _local(node.tag) != "si":
            continue
        strings.append(_element_text(node))
        if len(strings) > MAX_SHARED_STRINGS:
            raise ScenarioWorkbookIdentityError("shared string count exceeds bounded policy")
    return strings


def _referenced_worksheets(
    archive: zipfile.ZipFile, infos: dict[str, zipfile.ZipInfo]
) -> list[str]:
    workbook_name = "xl/workbook.xml"
    rels_name = "xl/_rels/workbook.xml.rels"
    if workbook_name not in infos or rels_name not in infos:
        raise ScenarioWorkbookIdentityError("workbook relationship metadata is incomplete")
    workbook = _parse_xml(
        _read_zip_member(archive, infos[workbook_name]), label="workbook"
    )
    rels = _parse_xml(
        _read_zip_member(archive, infos[rels_name]), label="workbook relationships"
    )

    relationship_map: dict[str, tuple[str, str, str | None]] = {}
    for node in rels.iter():
        if _local(node.tag) != "Relationship":
            continue
        rel_id = node.attrib.get("Id")
        rel_type = node.attrib.get("Type")
        target = node.attrib.get("Target")
        target_mode = node.attrib.get("TargetMode")
        if (
            type(rel_id) is not str
            or not rel_id
            or rel_id in relationship_map
            or type(rel_type) is not str
            or type(target) is not str
        ):
            raise ScenarioWorkbookIdentityError("workbook relationship metadata is invalid")
        relationship_map[rel_id] = (rel_type, target, target_mode)

    sheet_ids: list[str] = []
    for node in workbook.iter():
        if _local(node.tag) != "sheet":
            continue
        rel_id = node.attrib.get(f"{{{_REL_NS}}}id")
        if type(rel_id) is not str or not rel_id or rel_id in sheet_ids:
            raise ScenarioWorkbookIdentityError("workbook sheet relationship id is invalid")
        sheet_ids.append(rel_id)
        if len(sheet_ids) > MAX_WORKSHEETS:
            raise ScenarioWorkbookIdentityError("worksheet count exceeds bounded policy")
    if not sheet_ids:
        raise ScenarioWorkbookIdentityError("workbook contains no referenced worksheets")

    worksheet_names: list[str] = []
    seen_targets: set[str] = set()
    for rel_id in sheet_ids:
        relationship = relationship_map.get(rel_id)
        if relationship is None:
            raise ScenarioWorkbookIdentityError("workbook sheet relationship is unresolved")
        rel_type, target, target_mode = relationship
        if target_mode not in (None, "Internal"):
            raise ScenarioWorkbookIdentityError("external worksheet relationships are forbidden")
        if rel_type != _WORKSHEET_REL_TYPE:
            raise ScenarioWorkbookIdentityError("workbook sheet relationship type is invalid")
        resolved = _canonical_relationship_target(target)
        if resolved in seen_targets:
            raise ScenarioWorkbookIdentityError("workbook worksheet targets are duplicated")
        if resolved not in infos or infos[resolved].is_dir():
            raise ScenarioWorkbookIdentityError("referenced worksheet member is missing")
        seen_targets.add(resolved)
        worksheet_names.append(resolved)

    archive_worksheets = {
        name
        for name, info in infos.items()
        if name.startswith("xl/worksheets/")
        and name.endswith(".xml")
        and not info.is_dir()
    }
    if archive_worksheets != set(worksheet_names):
        raise ScenarioWorkbookIdentityError("XLSX contains orphan or unreferenced worksheets")
    return worksheet_names


def _cell_text(cell: ET.Element, shared: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    allowed_types = {None, "n", "s", "str", "inlineStr", "b", "e", "d"}
    if cell_type not in allowed_types:
        raise ScenarioWorkbookIdentityError("XLSX cell type is outside closed set")
    if cell_type == "inlineStr":
        inline = next((node for node in cell if _local(node.tag) == "is"), None)
        return "" if inline is None else _element_text(inline)
    value_node = next((node for node in cell if _local(node.tag) == "v"), None)
    raw = "" if value_node is None or value_node.text is None else value_node.text
    raw = _bounded_text(raw, field="XLSX cell value")
    if cell_type == "s":
        if not raw.isdigit():
            raise ScenarioWorkbookIdentityError("shared-string cell index is invalid")
        index = int(raw)
        if not (0 <= index < len(shared)):
            raise ScenarioWorkbookIdentityError("shared-string cell index is out of range")
        return shared[index]
    return raw


def _scan_workbook(payload: bytes) -> dict[str, Any]:
    if type(payload) is not bytes or not (1 <= len(payload) <= MAX_FILE_BYTES):
        raise ScenarioWorkbookIdentityError("workbook byte size is outside bounded policy")
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload), mode="r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise ScenarioWorkbookIdentityError("workbook is not a valid ZIP package") from exc

    with archive:
        members = archive.infolist()
        if not (1 <= len(members) <= MAX_ZIP_MEMBERS):
            raise ScenarioWorkbookIdentityError("XLSX member count exceeds bounded policy")
        infos: dict[str, zipfile.ZipInfo] = {}
        total_uncompressed = 0
        for info in members:
            name = _canonical_zip_name(info.filename)
            if name in infos:
                raise ScenarioWorkbookIdentityError("XLSX contains duplicate member names")
            infos[name] = info
            if info.is_dir():
                continue
            if info.flag_bits & 0x1:
                raise ScenarioWorkbookIdentityError("encrypted XLSX members are forbidden")
            if info.compress_type not in _ALLOWED_COMPRESSION:
                raise ScenarioWorkbookIdentityError("XLSX compression method is outside policy")
            if not (0 <= info.file_size <= MAX_MEMBER_BYTES):
                raise ScenarioWorkbookIdentityError("XLSX member size exceeds bounded policy")
            total_uncompressed += info.file_size
            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
                raise ScenarioWorkbookIdentityError("XLSX uncompressed size exceeds bounded policy")

        content_types_name = "[Content_Types].xml"
        if content_types_name not in infos:
            raise ScenarioWorkbookIdentityError(
                f"XLSX required member missing: {content_types_name}"
            )
        _parse_xml(
            _read_zip_member(archive, infos[content_types_name]),
            label=content_types_name,
        )
        worksheet_names = _referenced_worksheets(archive, infos)
        if not (1 <= len(worksheet_names) <= MAX_WORKSHEETS):
            raise ScenarioWorkbookIdentityError("worksheet count is outside bounded policy")
        shared = _shared_strings(archive, infos)

        row_count = 0
        cell_count = 0
        target_cell_count = 0
        target_row_count = 0
        name_cell_counts = {name: 0 for name in NAME_LITERALS}
        name_row_counts = {name: 0 for name in NAME_LITERALS}
        target_same_row_counts = {name: 0 for name in NAME_LITERALS}

        for worksheet_name in worksheet_names:
            root = _parse_xml(
                _read_zip_member(archive, infos[worksheet_name]),
                label="worksheet",
            )
            seen_refs: set[str] = set()
            for row in root.iter():
                if _local(row.tag) != "row":
                    continue
                row_count += 1
                if row_count > MAX_ROWS:
                    raise ScenarioWorkbookIdentityError("worksheet row count exceeds bounded policy")
                row_has_target = False
                row_names: set[str] = set()
                row_cell_count = 0
                for cell in row:
                    if _local(cell.tag) != "c":
                        continue
                    row_cell_count += 1
                    cell_count += 1
                    if row_cell_count > 1024 or cell_count > MAX_CELLS:
                        raise ScenarioWorkbookIdentityError("worksheet cell count exceeds bounded policy")
                    ref = cell.attrib.get("r")
                    if type(ref) is not str or _CELL_REF_RE.fullmatch(ref) is None:
                        raise ScenarioWorkbookIdentityError("worksheet cell reference is invalid")
                    scoped_ref = f"{worksheet_name}:{ref}"
                    if scoped_ref in seen_refs:
                        raise ScenarioWorkbookIdentityError("worksheet contains duplicate cell reference")
                    seen_refs.add(scoped_ref)
                    value = _cell_text(cell, shared)
                    if value == TARGET_EVENT_ID:
                        target_cell_count += 1
                        row_has_target = True
                    for name, pattern in _WORD_PATTERNS.items():
                        if pattern.search(value):
                            name_cell_counts[name] += 1
                            row_names.add(name)
                if row_has_target:
                    target_row_count += 1
                    for name in row_names:
                        target_same_row_counts[name] += 1
                for name in row_names:
                    name_row_counts[name] += 1

        bindings = [name for name, count in target_same_row_counts.items() if count > 0]
        if len(bindings) > 1:
            raise ScenarioWorkbookIdentityError(
                "target event identifier has contradictory same-row name literals"
            )
        return {
            "zip_member_count": len(members),
            "total_uncompressed_bytes": total_uncompressed,
            "worksheet_count": len(worksheet_names),
            "shared_string_count": len(shared),
            "scanned_row_count": row_count,
            "scanned_cell_count": cell_count,
            "target_event_id_exact_cell_count": target_cell_count,
            "target_event_id_row_count": target_row_count,
            "name_literal_cell_counts": name_cell_counts,
            "name_literal_row_counts": name_row_counts,
            "target_same_row_name_literal_counts": target_same_row_counts,
            "same_row_name_literal_binding": bindings[0] if bindings else None,
        }


def acquire_and_profile_workbook_identity(
    *,
    tree_acquire: Any | None = None,
    opener: Any | None = None,
    now: Any | None = None,
    monotonic: Any | None = None,
) -> dict[str, Any]:
    """Read the one fixed workbook and return redacted identity evidence."""
    if (
        tree.acquire_esrm20_scenario_tree_metadata is not _TREE_ACQUIRE
        or transport._open_fixed is not _OPEN_FIXED
        or transport._read_bounded is not _READ_BOUNDED
        or transport._validate_exact_response is not _VALIDATE_RESPONSE
        or transport._remaining is not _REMAINING
        or transport.utc_now is not _NOW
        or time.monotonic is not _MONOTONIC
    ):
        raise ScenarioWorkbookIdentityError("trusted workbook acquisition authority drifted")

    acquire_tree = tree_acquire or _TREE_ACQUIRE
    try:
        tree_receipt = acquire_tree()
    except tree.EfehrAcquisitionError as exc:
        raise ScenarioWorkbookIdentityError("immutable scenario tree acquisition failed") from exc
    expected_blob_sha1, tree_identity_sha256 = _workbook_blob_from_tree(tree_receipt)

    clock = monotonic or _MONOTONIC
    open_response = opener or _OPEN_FIXED
    now_utc = now or _NOW
    deadline = clock() + TOTAL_DEADLINE_SECONDS
    url = _raw_url()
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*;q=0.1",
            "User-Agent": "OpenCatastrophe-ESRM20-scenario-v10-workbook-identity-v1",
        },
        method="GET",
    )
    try:
        with open_response(request, timeout=_REMAINING(deadline, clock)) as response:
            _VALIDATE_RESPONSE(response, url)
            payload = _READ_BOUNDED(
                response,
                deadline=deadline,
                maximum=MAX_FILE_BYTES,
                monotonic=clock,
            )
    except ScenarioWorkbookIdentityError:
        raise
    except (OSError, TimeoutError, transport.EfehrAcquisitionError) as exc:
        raise ScenarioWorkbookIdentityError("workbook acquisition failed closed") from exc

    observed_blob_sha1 = _git_blob_sha1(payload)
    if observed_blob_sha1 != expected_blob_sha1:
        raise ScenarioWorkbookIdentityError("workbook bytes do not match immutable tree Git blob")
    retrieved_at = now_utc()
    if type(retrieved_at) is not str or not retrieved_at.endswith("Z"):
        raise ScenarioWorkbookIdentityError("workbook retrieval timestamp is invalid")
    scan = _scan_workbook(payload)

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": COMMIT_SHA,
        "workbook_path": WORKBOOK_PATH,
        "tree_identity_sha256": tree_identity_sha256,
        "workbook_git_blob_sha1": observed_blob_sha1,
        "retrieved_at": retrieved_at,
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "target_event_id": TARGET_EVENT_ID,
        **scan,
        "raw_workbook_cells_returned": False,
        "raw_workbook_rows_returned": False,
        "provider_file_bytes_read": True,
        "external_bytes_persisted": False,
        "rupture_or_shakemap_payload_bytes_read": False,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
