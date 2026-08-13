# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail closed on broken repository-local links in tracked Markdown files."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

INLINE_LINK_RE = re.compile(
    r"\[[^\]\n]*\]\(\s*(?P<destination><[^>\n]+>|[^)\s]+)"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
REFERENCE_DESTINATION_RE = re.compile(
    r"(?m)^[ \t]{0,3}\[[^\]\n]+\]:[ \t]*(?P<destination><[^>\n]+>|\S+)"
)
FENCE_START_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def tracked_markdown_paths(root: Path = ROOT) -> list[Path]:
    """Return tracked Markdown paths from the Git index."""

    process = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.md"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )
    paths: list[Path] = []
    for raw_path in process.stdout.split(b"\0"):
        if not raw_path:
            continue
        text = raw_path.decode("utf-8", errors="strict")
        relative = Path(text)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Git returned an unsafe Markdown path")
        paths.append(root / relative)
    return paths


def strip_code_and_comments(text: str) -> str:
    """Remove regions where Markdown-looking links are literal examples."""

    text = HTML_COMMENT_RE.sub("", text)
    output: list[str] = []
    fence_char: str | None = None
    fence_length = 0

    for line in text.splitlines(keepends=True):
        match = FENCE_START_RE.match(line)
        if fence_char is not None:
            if match:
                fence = match.group("fence")
                trailing = line[match.end() :]
                if (
                    fence[0] == fence_char
                    and len(fence) >= fence_length
                    and not trailing.strip(" \t\r\n")
                ):
                    fence_char = None
                    fence_length = 0
            output.append("\n" if line.endswith("\n") else "")
            continue

        if match:
            fence = match.group("fence")
            fence_char = fence[0]
            fence_length = len(fence)
            output.append("\n" if line.endswith("\n") else "")
            continue

        output.append(INLINE_CODE_RE.sub("", line))

    return "".join(output)


def link_destinations(text: str) -> list[str]:
    """Extract inline and reference-definition destinations from Markdown text."""

    cleaned = strip_code_and_comments(text)
    destinations = [
        match.group("destination") for match in INLINE_LINK_RE.finditer(cleaned)
    ]
    destinations.extend(
        match.group("destination")
        for match in REFERENCE_DESTINATION_RE.finditer(cleaned)
    )
    return destinations


def local_target_problem(
    source_path: Path, destination: str, *, root: Path = ROOT
) -> str | None:
    """Return a deterministic problem for a repository-local destination."""

    raw = destination.strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()
    if not raw:
        return None

    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc:
        return None
    if not parsed.path:
        return None

    decoded_path = unquote(parsed.path)
    if "\x00" in decoded_path:
        return f"invalid repository-local target: {destination}"

    root_resolved = root.resolve()
    if decoded_path.startswith("/"):
        target = root_resolved / decoded_path.lstrip("/")
    else:
        target = source_path.parent / decoded_path
    target_resolved = target.resolve(strict=False)

    if not target_resolved.is_relative_to(root_resolved):
        return f"repository-local target escapes repository root: {destination}"
    if not target_resolved.exists():
        return f"missing repository-local target: {destination}"
    return None


def check_markdown_file(path: Path, *, root: Path = ROOT) -> list[str]:
    """Check one Markdown file for broken repository-local destinations."""

    try:
        text = path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        return [f"unable to read UTF-8 Markdown: {exc}"]

    problems: list[str] = []
    for destination in link_destinations(text):
        problem = local_target_problem(path, destination, root=root)
        if problem is not None:
            problems.append(problem)
    return problems


def main() -> int:
    failures: list[str] = []
    try:
        paths = tracked_markdown_paths()
    except (OSError, subprocess.CalledProcessError, UnicodeError, ValueError) as exc:
        print(f"BLOCKED: unable to enumerate tracked Markdown files: {exc}")
        return 2

    for path in paths:
        relative = path.relative_to(ROOT)
        for problem in check_markdown_file(path):
            failures.append(f"{relative}: {problem}")

    if failures:
        print("BLOCKED: broken repository-local Markdown links found")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"PASS: checked repository-local links in {len(paths)} tracked Markdown files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
