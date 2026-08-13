# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline helpers for inspecting file references in OpenQuake INI configs.

The parser is intentionally narrow: it identifies first-order file references
without fetching provider bytes or interpreting scientific parameter values.
"""

from __future__ import annotations

import configparser
import posixpath
from dataclasses import dataclass


class OpenQuakeConfigError(ValueError):
    """Raised when an OpenQuake configuration is ambiguous or malformed."""


@dataclass(frozen=True)
class OpenQuakeConfigReference:
    """One file dependency declared by an OpenQuake configuration option."""

    section: str
    option: str
    raw_path: str
    resolved_path: str


_EXPLICIT_FILE_OPTIONS = frozenset({"sites_csv"})


def _is_file_option(option: str) -> bool:
    normalized = option.casefold()
    return (
        normalized in _EXPLICIT_FILE_OPTIONS
        or normalized.endswith("_file")
        or normalized.endswith("_files")
    )


def _validate_repository_path(path: str, *, label: str) -> str:
    if not isinstance(path, str):
        raise OpenQuakeConfigError(f"{label} must be a string")
    if not path or path != path.strip():
        raise OpenQuakeConfigError(f"{label} must be non-empty and trimmed")
    if any(ord(char) < 32 for char in path):
        raise OpenQuakeConfigError(f"{label} contains control characters")
    if "\\" in path or ":" in path or "?" in path or "#" in path:
        raise OpenQuakeConfigError(f"{label} is not a plain POSIX repository path")
    if path.startswith("/"):
        raise OpenQuakeConfigError(f"{label} must be repository-relative")

    normalized = posixpath.normpath(path)
    if normalized in {"", ".", ".."} or normalized.startswith("../"):
        raise OpenQuakeConfigError(f"{label} escapes the repository root")
    return normalized


def normalize_repository_reference(config_path: str, raw_path: str) -> str:
    """Resolve a config-relative path and reject references outside the repo."""

    canonical_config_path = _validate_repository_path(config_path, label="config_path")
    if canonical_config_path != config_path:
        raise OpenQuakeConfigError("config_path must already be canonical")

    if not isinstance(raw_path, str):
        raise OpenQuakeConfigError("dependency path must be a string")
    candidate = raw_path.strip()
    if not candidate:
        raise OpenQuakeConfigError("dependency path must be non-empty")
    if any(ord(char) < 32 for char in candidate):
        raise OpenQuakeConfigError("dependency path contains control characters")
    if "\\" in candidate or ":" in candidate or "?" in candidate or "#" in candidate:
        raise OpenQuakeConfigError("dependency path is not a plain POSIX repository path")
    if candidate.startswith("/"):
        raise OpenQuakeConfigError("dependency path must be repository-relative")

    parent = posixpath.dirname(canonical_config_path)
    resolved = posixpath.normpath(posixpath.join(parent, candidate))
    if resolved in {"", ".", ".."} or resolved.startswith("../") or resolved.startswith("/"):
        raise OpenQuakeConfigError("dependency path escapes the repository root")
    return resolved


def extract_openquake_config_references(
    config_text: str,
    *,
    config_path: str,
) -> tuple[OpenQuakeConfigReference, ...]:
    """Return deterministic first-order file references from OpenQuake INI text.

    Options ending in ``_file`` or ``_files`` and the OpenQuake ``sites_csv``
    option are treated as file-valued. Multi-file values use one continuation
    line per path. Empty file options declare no dependency here; whether a
    scientific workflow requires a particular option is a separate contract.
    """

    canonical_config_path = _validate_repository_path(config_path, label="config_path")
    if canonical_config_path != config_path:
        raise OpenQuakeConfigError("config_path must already be canonical")
    if not isinstance(config_text, str):
        raise OpenQuakeConfigError("config_text must be a string")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in config_text):
        raise OpenQuakeConfigError("config_text contains control characters")

    parser = configparser.ConfigParser(
        interpolation=None,
        strict=True,
        empty_lines_in_values=False,
        inline_comment_prefixes=("#", ";"),
    )
    try:
        parser.read_string(config_text)
    except configparser.Error as exc:
        raise OpenQuakeConfigError(f"invalid INI configuration: {exc}") from exc

    if not parser.sections():
        raise OpenQuakeConfigError("configuration must contain at least one section")

    for option, value in parser.defaults().items():
        if _is_file_option(option) and value.strip():
            raise OpenQuakeConfigError("file-valued DEFAULT options are not supported")

    references: list[OpenQuakeConfigReference] = []
    seen: set[tuple[str, str, str]] = set()

    for section in parser.sections():
        for option, value in parser.items(section, raw=True):
            normalized_option = option.casefold()
            if not _is_file_option(normalized_option):
                continue

            for raw_path in (line.strip() for line in value.splitlines() if line.strip()):
                resolved = normalize_repository_reference(canonical_config_path, raw_path)
                identity = (section, normalized_option, resolved)
                if identity in seen:
                    raise OpenQuakeConfigError(
                        f"duplicate dependency in [{section}] {normalized_option}: {resolved}"
                    )
                seen.add(identity)
                references.append(
                    OpenQuakeConfigReference(
                        section=section,
                        option=normalized_option,
                        raw_path=raw_path,
                        resolved_path=resolved,
                    )
                )

    return tuple(
        sorted(
            references,
            key=lambda item: (item.resolved_path, item.section, item.option, item.raw_path),
        )
    )
