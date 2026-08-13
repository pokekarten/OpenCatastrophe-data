# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline helpers for inspecting file references in OpenQuake INI configs.

The parser is intentionally narrow: it identifies first-order file references
without fetching provider bytes or interpreting scientific parameter values.
Input-option recognition follows the OpenQuake Engine 3.14 ``readinput``
contract used by the published ESHM20 reference, while path handling is more
fail-closed for public provenance work.
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


_INPUT_SUFFIXES = ("_file", "_csv", "_hdf5")
_MULTI_FILE_OPTIONS_3_14 = frozenset(
    {"hazard_curves_csv", "site_model_file", "exposure_file"}
)


def _contains_unsupported_placeholder(value: str) -> bool:
    return "%(" in value or "${" in value


def _is_file_option(option: str, value: str) -> bool:
    normalized = option.casefold()
    return normalized.endswith(_INPUT_SUFFIXES) or value.strip().endswith(".hdf5")


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
    if _contains_unsupported_placeholder(candidate):
        raise OpenQuakeConfigError(
            "dependency path contains unsupported interpolation or placeholder syntax"
        )
    if "\\" in candidate or ":" in candidate or "?" in candidate or "#" in candidate:
        raise OpenQuakeConfigError("dependency path is not a plain POSIX repository path")
    if candidate.startswith("/"):
        raise OpenQuakeConfigError("dependency path must be repository-relative")
    if candidate in {".", ".."} or candidate.endswith("/") or "," in candidate:
        raise OpenQuakeConfigError("dependency path is ambiguous or not file-like")

    parent = posixpath.dirname(canonical_config_path)
    resolved = posixpath.normpath(posixpath.join(parent, candidate))
    if resolved in {"", ".", ".."} or resolved.startswith("../") or resolved.startswith("/"):
        raise OpenQuakeConfigError("dependency path escapes the repository root")
    return resolved


def _raw_dependency_paths(option: str, value: str) -> tuple[str, ...]:
    stripped = value.strip()
    if not stripped:
        return ()
    if stripped.startswith("{"):
        raise OpenQuakeConfigError(
            f"mapping-valued file option is not supported yet: {option}"
        )
    if option in _MULTI_FILE_OPTIONS_3_14:
        return tuple(stripped.split())
    return (stripped,)


def extract_openquake_config_references(
    config_text: str,
    *,
    config_path: str,
) -> tuple[OpenQuakeConfigReference, ...]:
    """Return deterministic first-order file references from OpenQuake INI text.

    OpenQuake 3.14 treats options ending in ``_file``, ``_csv`` or ``_hdf5``
    as input paths and also recognizes legacy HDF5-valued parameters. In that
    release, ``hazard_curves_csv``, ``site_model_file`` and ``exposure_file``
    accept whitespace-separated file lists. Other file-valued options are
    single-path inputs. Mapping-valued file options are deliberately rejected
    until a concrete public consumer requires them and tests can freeze their
    semantics. OpenQuake interpolation and special placeholder syntax are also
    deliberately rejected instead of being reimplemented here.

    Empty file options declare no dependency here; whether a scientific
    workflow requires a particular input is a separate contract.
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
    )
    try:
        parser.read_string(config_text)
    except configparser.Error as exc:
        raise OpenQuakeConfigError(f"invalid INI configuration: {exc}") from exc

    if not parser.sections():
        raise OpenQuakeConfigError("configuration must contain at least one section")

    for option, value in parser.defaults().items():
        if _contains_unsupported_placeholder(value):
            raise OpenQuakeConfigError(
                f"unsupported interpolation or placeholder syntax in DEFAULT option {option}"
            )
        if _is_file_option(option, value) and value.strip():
            raise OpenQuakeConfigError("file-valued DEFAULT options are not supported")

    references: list[OpenQuakeConfigReference] = []
    seen_dependencies: set[tuple[str, str, str]] = set()
    option_sections: dict[str, str] = {}

    for section in parser.sections():
        for option, value in parser.items(section, raw=True):
            if _contains_unsupported_placeholder(value):
                raise OpenQuakeConfigError(
                    f"unsupported interpolation or placeholder syntax in [{section}] {option}"
                )
            normalized_option = option.casefold()
            if not _is_file_option(normalized_option, value):
                continue

            previous_section = option_sections.get(normalized_option)
            if previous_section is not None and previous_section != section:
                raise OpenQuakeConfigError(
                    f"file-valued option {normalized_option} is defined in multiple sections"
                )
            option_sections[normalized_option] = section

            for raw_path in _raw_dependency_paths(normalized_option, value):
                resolved = normalize_repository_reference(canonical_config_path, raw_path)
                identity = (section, normalized_option, resolved)
                if identity in seen_dependencies:
                    raise OpenQuakeConfigError(
                        f"duplicate dependency in [{section}] {normalized_option}: {resolved}"
                    )
                seen_dependencies.add(identity)
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
