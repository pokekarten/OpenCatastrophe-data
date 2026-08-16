# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate an observed OpenQuake 3.14 ESHM20 reference-runtime fingerprint.

This module binds a small, public, reconstructed reference recipe from the
official GEM OpenQuake v3.14.0 source tree.  A PASS means only that the
observed runtime matches the fields checked here.  It does not establish a
historically byte-identical ESHM20 production environment, numerical
agreement, benchmark success, admission, publication, or model-use authority.
"""

from __future__ import annotations

import re
from typing import Any


SCHEMA_VERSION = "oc-eshm20-openquake-reference-runtime-fingerprint-v1"
SOURCE_ISSUE = 281
DATASET_ID = "efehr.eshm20"

ENGINE_REPOSITORY = "gem/oq-engine"
ENGINE_TAG = "v3.14.0"
ENGINE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
ENGINE_VERSION = "3.14.0"

DOCKERFILE_PATH = "docker/Dockerfile.engine"
DOCKERFILE_GIT_BLOB_SHA1 = "3f2966d212286e033e38ccd7111c554c7bfa77ce"
DOCKER_BASE_IMAGE_TAG = "python:3.8-slim"

REQUIREMENTS_PATH = "requirements-py38-linux64.txt"
REQUIREMENTS_GIT_BLOB_SHA1 = "0ebb7e5042cce16005603a3961824797ef72397f"

BASELIB_PATH = "openquake/baselib/__init__.py"
BASELIB_GIT_BLOB_SHA1 = "a2432f3dacea07537f8b8c851f76a63c1de870c1"

EXPECTED_PYTHON_MAJOR_MINOR = "3.8"
EXPECTED_PLATFORM_SYSTEM = "Linux"
EXPECTED_PLATFORM_MACHINE = "x86_64"
EXPECTED_OPENBLAS_NUM_THREADS = "1"

# Exact package versions named by the official v3.14.0 Linux/Python-3.8
# requirements recipe.  These are recipe-version identities only; the source
# recipe does not provide wheel SHA-256 values.
_REFERENCE_PACKAGES: tuple[tuple[str, str], ...] = (
    ("asgiref", "3.4.1"),
    ("certifi", "2019.3.9"),
    ("chardet", "3.0.4"),
    ("cycler", "0.10.0"),
    ("decorator", "4.4.2"),
    ("django", "3.2.12"),
    ("django-pam", "2.0.1"),
    ("docutils", "0.14"),
    ("gdal", "3.2.2"),
    ("h5py", "3.1.0"),
    ("idna", "2.8"),
    ("kiwisolver", "1.1.0"),
    ("matplotlib", "3.1.2"),
    ("numpy", "1.20.0"),
    ("pandas", "1.1.5"),
    ("pbr", "5.2.0"),
    ("psutil", "5.6.7"),
    ("pyparsing", "2.4.0"),
    ("pyproj", "2.5.0"),
    ("python-dateutil", "2.8.0"),
    ("python-pam", "1.8.4"),
    ("pytz", "2019.1"),
    ("pyzmq", "19.0.0"),
    ("requests", "2.22.0"),
    ("scipy", "1.7.3"),
    ("setproctitle", "1.2.2"),
    ("setuptools", "56.0.0"),
    ("shapely", "1.8.0"),
    ("six", "1.12.0"),
    ("sqlparse", "0.3.0"),
    ("toml", "0.10.0"),
    ("urllib3", "1.25.3"),
)

_OBSERVATION_FIELDS = {
    "engine_commit",
    "engine_version",
    "python_version",
    "platform_system",
    "platform_machine",
    "openblas_num_threads",
    "packages",
    "container_image_digest",
}

_PYTHON_VERSION_RE = re.compile(r"^3\.8(?:\.\d+)?$")
_SHA256_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_CANONICAL_PACKAGE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ENGINE_GIT_VERSION_RE = re.compile(
    rf"^{re.escape(ENGINE_VERSION)}-git([0-9a-f]{{7,40}})$"
)


class ReferenceRuntimeError(ValueError):
    """Raised when an observed runtime drifts from the reference contract."""


def _exact(value: object, expected: object, field: str) -> None:
    if type(value) is not type(expected) or value != expected:
        raise ReferenceRuntimeError(f"{field} does not match the OpenQuake 3.14 reference recipe")


def _normalize_engine_version(value: object, *, engine_commit: str) -> str:
    """Normalize only the exact release or its commit-bound Git checkout form."""

    if type(value) is not str:
        raise ReferenceRuntimeError(
            "engine_version does not match the OpenQuake 3.14 reference recipe"
        )
    if value == ENGINE_VERSION:
        return ENGINE_VERSION

    match = _ENGINE_GIT_VERSION_RE.fullmatch(value)
    if match is None or not engine_commit.startswith(match.group(1)):
        raise ReferenceRuntimeError(
            "engine_version does not match the OpenQuake 3.14 reference recipe"
        )
    return ENGINE_VERSION


def _normalize_package_name(name: str) -> str:
    if not name or name != name.strip():
        raise ReferenceRuntimeError("package names must be non-empty and already trimmed")
    normalized = re.sub(r"[-_.]+", "-", name).lower()
    if not _CANONICAL_PACKAGE_RE.fullmatch(normalized):
        raise ReferenceRuntimeError("package name is not canonicalizable")
    return normalized


def _validate_packages(raw: object) -> dict[str, str]:
    if type(raw) is not dict:
        raise ReferenceRuntimeError("packages must be an object")

    normalized: dict[str, str] = {}
    for key, value in raw.items():
        if type(key) is not str or type(value) is not str:
            raise ReferenceRuntimeError("package names and versions must be strings")
        name = _normalize_package_name(key)
        if name in normalized:
            raise ReferenceRuntimeError("duplicate package identity after normalization")
        if key != name:
            raise ReferenceRuntimeError("package names must use canonical lowercase-hyphen form")
        normalized[name] = value

    expected = dict(_REFERENCE_PACKAGES)
    if set(normalized) != set(expected):
        raise ReferenceRuntimeError("package set does not match the OpenQuake 3.14 recipe")
    for name, version in expected.items():
        _exact(normalized[name], version, f"packages.{name}")
    return normalized


def reference_runtime_contract() -> dict[str, object]:
    """Return the immutable public source-recipe identity for this validator."""

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "engine": {
            "repository": ENGINE_REPOSITORY,
            "tag": ENGINE_TAG,
            "commit": ENGINE_COMMIT,
            "version": ENGINE_VERSION,
        },
        "docker_recipe": {
            "path": DOCKERFILE_PATH,
            "git_blob_sha1": DOCKERFILE_GIT_BLOB_SHA1,
            "base_image_tag": DOCKER_BASE_IMAGE_TAG,
            "base_image_digest_pinned": False,
        },
        "requirements_recipe": {
            "path": REQUIREMENTS_PATH,
            "git_blob_sha1": REQUIREMENTS_GIT_BLOB_SHA1,
            "wheel_sha256_pinned": False,
            "packages": [
                {"name": name, "version": version}
                for name, version in _REFERENCE_PACKAGES
            ],
        },
        "baselib_reference": {
            "path": BASELIB_PATH,
            "git_blob_sha1": BASELIB_GIT_BLOB_SHA1,
            "openblas_num_threads": EXPECTED_OPENBLAS_NUM_THREADS,
        },
    }


def validate_runtime_observation(observation: Any) -> dict[str, object]:
    """Validate one observed runtime and return bounded reproducibility evidence."""

    if type(observation) is not dict:
        raise ReferenceRuntimeError("runtime observation must be an object")
    if set(observation) != _OBSERVATION_FIELDS:
        raise ReferenceRuntimeError("runtime observation has missing or extra fields")

    _exact(observation["engine_commit"], ENGINE_COMMIT, "engine_commit")
    engine_version = _normalize_engine_version(
        observation["engine_version"], engine_commit=ENGINE_COMMIT
    )

    python_version = observation["python_version"]
    if type(python_version) is not str or not _PYTHON_VERSION_RE.fullmatch(python_version):
        raise ReferenceRuntimeError("python_version must be Python 3.8 with optional patch component")

    _exact(observation["platform_system"], EXPECTED_PLATFORM_SYSTEM, "platform_system")
    _exact(observation["platform_machine"], EXPECTED_PLATFORM_MACHINE, "platform_machine")
    _exact(
        observation["openblas_num_threads"],
        EXPECTED_OPENBLAS_NUM_THREADS,
        "openblas_num_threads",
    )

    packages = _validate_packages(observation["packages"])

    image_digest = observation["container_image_digest"]
    if image_digest is not None:
        if type(image_digest) is not str or not _SHA256_DIGEST_RE.fullmatch(image_digest):
            raise ReferenceRuntimeError("container_image_digest must be null or sha256:<64 lowercase hex>")

    return {
        "schema_version": SCHEMA_VERSION,
        "reference": reference_runtime_contract(),
        "observation": {
            "engine_commit": ENGINE_COMMIT,
            "engine_version": engine_version,
            "python_version": python_version,
            "platform_system": EXPECTED_PLATFORM_SYSTEM,
            "platform_machine": EXPECTED_PLATFORM_MACHINE,
            "openblas_num_threads": EXPECTED_OPENBLAS_NUM_THREADS,
            "packages": [
                {"name": name, "version": packages[name]}
                for name, _ in _REFERENCE_PACKAGES
            ],
            "container_image_digest": image_digest,
        },
        "reference_recipe_match": True,
        "observed_container_digest_recorded": image_digest is not None,
        "historical_environment_verified": False,
        "reference_base_image_byte_identity_verified": False,
        "wheel_byte_identity_verified": False,
        "benchmark_execution_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
    }
