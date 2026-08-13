# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline helpers for inspecting file references in OpenQuake INI configs."""

from __future__ import annotations

from dataclasses import dataclass


class OpenQuakeConfigError(ValueError):
    """Raised when an OpenQuake configuration is ambiguous or malformed."""


@dataclass(frozen=True)
class OpenQuakeConfigReference:
    section: str
    option: str
    raw_path: str
    resolved_path: str
