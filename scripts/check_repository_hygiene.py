# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed checks for accidentally tracked secrets, private paths and data blobs."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_BYTES = 1 * 1024 * 1024
REGULAR_GIT_MODES = {"100644", "100755"}
SYMLINK_GIT_MODE = "120000"
BLOCKED_SEGMENTS = {
    "artifacts", "data", "downloads", "external", "htmlcov", "outputs", "private", "quarantine",
    "raw", "restricted", "runs", "secrets",
}
BLOCKED_SUFFIXES = {
    ".7z", ".arrow", ".avro", ".bin", ".bz2", ".crt", ".csv", ".dat", ".db",
    ".dbf", ".docx", ".dta", ".duckdb", ".feather", ".geojson", ".gml", ".gpkg",
    ".grib", ".grib2", ".gz", ".h5", ".hdf5", ".ipynb", ".joblib", ".jsonl",
    ".kdbx", ".key", ".kml", ".kmz", ".las", ".laz", ".nc", ".nc4", ".ndjson",
    ".npy", ".npz", ".orc", ".ovpn", ".p12", ".parquet", ".pdf", ".pem", ".pfx",
    ".pickle", ".pkl", ".pptx", ".rda", ".rdata", ".rds", ".rar", ".sas7bdat",
    ".sav", ".shp", ".shx", ".sqlite", ".sqlite3", ".tar", ".tgz", ".tif", ".tiff",
    ".tsv", ".xls", ".xlsx", ".xz", ".zip",
}
BLOCKED_NAMES = {
    ".coverage", ".env", ".git-credentials", ".netrc", ".npmrc", ".pypirc", "coverage.xml", "credentials",
    "credentials.json", "id_ed25519", "id_rsa", "kubeconfig",
}
SECRET_PATTERNS = {
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    "AWS access key": re.compile(rb"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(rb"\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{30,})\b"),
    "Slack token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "Google API key": re.compile(rb"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "OpenAI-style secret": re.compile(rb"\bsk-(?:proj|svcacct)-[A-Za-z0-9_-]{20,}\b"),
    "PyPI token": re.compile(rb"\bpypi-[A-Za-z0-9_-]{20,}\b"),
    "Hugging Face token": re.compile(rb"\bhf_[A-Za-z0-9]{20,}\b"),
    "Stripe live secret": re.compile(rb"\bsk_live_[A-Za-z0-9]{20,}\b"),
}
LOCAL_PATH_PATTERNS = {
    "macOS user path": re.compile(rb"/Users/[A-Za-z0-9._-]+/"),
    "Linux user path": re.compile(rb"/home/[A-Za-z0-9._-]+/"),
    "Windows user path": re.compile(rb"[A-Za-z]:\\Users\\[A-Za-z0-9._ -]+\\"),
    "file URL": re.compile(rb"\bfile://(?:localhost/)?", re.IGNORECASE),
}
PRIVATE_ENDPOINT_PATTERNS = {
    "localhost endpoint": re.compile(rb"https?://" + b"local" + b"host(?::[0-9]+)?(?:/|\b)", re.IGNORECASE),
    "IPv4 loopback endpoint": re.compile(rb"https?://127(?:\.[0-9]{1,3}){3}(?::[0-9]+)?(?:/|\b)", re.IGNORECASE),
    "RFC1918 10/8 endpoint": re.compile(rb"https?://10(?:\.[0-9]{1,3}){3}(?::[0-9]+)?(?:/|\b)", re.IGNORECASE),
    "RFC1918 172.16/12 endpoint": re.compile(rb"https?://172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}(?::[0-9]+)?(?:/|\b)", re.IGNORECASE),
    "RFC1918 192.168/16 endpoint": re.compile(rb"https?://192\.168\.[0-9]{1,3}\.[0-9]{1,3}(?::[0-9]+)?(?:/|\b)", re.IGNORECASE),
    "IPv6 loopback endpoint": re.compile(rb"https?://\[::1\](?::[0-9]+)?(?:/|\b)", re.IGNORECASE),
}
SIGNED_URL_PATTERNS = {
    "AWS signed URL": re.compile(rb"[?&]X-Amz-Signature=[0-9A-Fa-f]{32,}", re.IGNORECASE),
    "Google signed URL": re.compile(rb"[?&]X-Goog-Signature=[0-9A-Fa-f]{32,}", re.IGNORECASE),
    "Azure-style signed URL": re.compile(rb"[?&]sig=[A-Za-z0-9%/+_-]{20,}", re.IGNORECASE),
    "access-token URL": re.compile(rb"[?&]access_token=[A-Za-z0-9._~%+-]{20,}", re.IGNORECASE),
}


@dataclass(frozen=True, slots=True)
class TrackedEntry:
    path: Path
    git_mode: str


def tracked_entries() -> list[TrackedEntry]:
    """Enumerate tracked paths with Git index modes without following symlinks."""

    process = subprocess.run(
        ["git", "ls-files", "--stage", "-z"], cwd=ROOT, check=True, stdout=subprocess.PIPE
    )
    entries: list[TrackedEntry] = []
    for item in process.stdout.split(b"\0"):
        if not item:
            continue
        try:
            metadata, raw_path = item.split(b"\t", 1)
            mode_raw, object_id_raw, stage_raw = metadata.split(b" ")
            mode = mode_raw.decode("ascii", errors="strict")
            object_id = object_id_raw.decode("ascii", errors="strict")
            stage = stage_raw.decode("ascii", errors="strict")
            relative_text = raw_path.decode("utf-8", errors="strict")
        except (ValueError, UnicodeError) as exc:
            raise ValueError("unable to interpret git ls-files --stage output") from exc
        if stage != "0":
            raise ValueError("tracked file inventory contains unresolved index stages")
        if not object_id or re.fullmatch(r"[0-9a-f]+", object_id) is None:
            raise ValueError("tracked file inventory contains an invalid object id")
        if not mode or re.fullmatch(r"[0-7]{6}", mode) is None:
            raise ValueError("tracked file inventory contains an invalid Git mode")
        relative = Path(relative_text)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("tracked file inventory contains an unsafe path")
        entries.append(TrackedEntry(ROOT / relative, mode))
    return entries


def check_relative_path(relative: Path) -> list[str]:
    problems: list[str] = []
    if any(part.lower() in BLOCKED_SEGMENTS for part in relative.parts[:-1]):
        problems.append("tracked file is inside a blocked private/data/output directory")
    lowered_name = relative.name.lower()
    if lowered_name in BLOCKED_NAMES or lowered_name.startswith((".env.", ".coverage.")):
        problems.append("tracked filename is reserved for local credentials/configuration")
    if relative.suffix.lower() in BLOCKED_SUFFIXES:
        problems.append(f"tracked high-risk binary/data suffix: {relative.suffix.lower()}")
    return problems


def check_file(path: Path, *, git_mode: str | None = None) -> list[str]:
    relative = path.relative_to(ROOT)
    problems = check_relative_path(relative)

    # Git index mode is authoritative across platforms. The local filesystem
    # check also catches direct helper calls on a symlink without a supplied mode.
    if git_mode == SYMLINK_GIT_MODE or path.is_symlink():
        problems.append("tracked symlink is not allowed")
        return problems
    if git_mode is not None and git_mode not in REGULAR_GIT_MODES:
        problems.append("tracked path uses an unsupported non-regular Git mode")
        return problems
    if not path.is_file():
        problems.append("tracked entry is not a regular file")
        return problems

    size = path.stat().st_size
    if size > MAX_TRACKED_BYTES:
        problems.append(f"tracked file exceeds {MAX_TRACKED_BYTES} bytes")
        return problems
    content = path.read_bytes()
    for label, pattern in {
        **SECRET_PATTERNS,
        **LOCAL_PATH_PATTERNS,
        **PRIVATE_ENDPOINT_PATTERNS,
        **SIGNED_URL_PATTERNS,
    }.items():
        if pattern.search(content):
            problems.append(f"possible {label}")
    return problems


def main() -> int:
    failures: list[str] = []
    try:
        entries = tracked_entries()
    except (OSError, subprocess.CalledProcessError, UnicodeError, ValueError) as exc:
        print(f"BLOCKED: unable to enumerate tracked files: {exc}")
        return 2
    for entry in entries:
        try:
            problems = check_file(entry.path, git_mode=entry.git_mode)
        except OSError as exc:
            failures.append(f"{entry.path.relative_to(ROOT)}: unreadable: {exc}")
            continue
        failures.extend(
            f"{entry.path.relative_to(ROOT)}: {problem}" for problem in problems
        )
    if failures:
        print("BLOCKED: repository hygiene violations found")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"PASS: checked {len(entries)} tracked files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
