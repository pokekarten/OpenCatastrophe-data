# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed ESHM20 GSIM request compatibility gate for OpenQuake 3.14.

The earlier identity profiler deliberately preserves unresolved GSIM request
terms. This module is the next, narrower runtime gate: after the exact GMM
payload and reconstructed OpenQuake runtime fingerprint have both been
validated, it resolves aliases through the exact OpenQuake v3.14.0 code path
and requires every request to instantiate successfully.

A PASS proves only alias/registry/constructor compatibility of the exact GMM
requests with a clean source checkout at the frozen OpenQuake commit plus the
already-defined reference-runtime recipe. It does not prove hazard numerical
agreement, IMT/site/vulnerability compatibility, scientific validity, or a
reference run.
"""

from __future__ import annotations

import inspect
import subprocess
from pathlib import Path
from typing import Any

from scripts import profile_eshm20_gsim_identities as profiler
from scripts import validate_eshm20_openquake_runtime as runtime_fingerprint

SCHEMA_VERSION = "oc-eshm20-gsim-openquake-runtime-compatibility-v1"
SOURCE_ISSUE = 281
HANDOFF_ISSUE = 427
DATASET_ID = profiler.DATASET_ID
OPENQUAKE_REPOSITORY = profiler.OPENQUAKE_REPOSITORY
OPENQUAKE_TAG = profiler.OPENQUAKE_TAG
OPENQUAKE_COMMIT = profiler.OPENQUAKE_COMMIT
OPENQUAKE_VERSION = runtime_fingerprint.ENGINE_VERSION

_GIT_TIMEOUT_SECONDS = 10
_EXTERNAL_RESOURCE_SUFFIXES = ("_file", "_table")


class Eshm20GsimRuntimeCompatibilityError(ValueError):
    """Raised when exact GSIM runtime compatibility cannot be proven safely."""


class _RuntimeAdapter:
    """Small boundary around the exact OpenQuake functions used by this gate."""

    def __init__(
        self,
        *,
        instantiate: Any,
        aliases: set[str] | frozenset[str],
        registry: dict[str, type],
        engine_source_checkout_verified: bool,
        engine_checkout_commit: str,
    ) -> None:
        self.instantiate = instantiate
        self.aliases = frozenset(aliases)
        self.registry = registry
        self.engine_source_checkout_verified = engine_source_checkout_verified
        self.engine_checkout_commit = engine_checkout_commit


def _git_text(root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise Eshm20GsimRuntimeCompatibilityError(
            "cannot verify the OpenQuake source checkout"
        ) from exc
    return completed.stdout.strip()


def _verify_exact_openquake_checkout(source_file: str | Path) -> Path:
    path = Path(source_file).resolve()
    if not path.is_file():
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake runtime source file is not a regular file"
        )

    root: Path | None = None
    for parent in (path.parent, *path.parents):
        if (parent / ".git").exists():
            root = parent
            break
    if root is None:
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake runtime must come from a verifiable git checkout"
        )

    top = Path(_git_text(root, "rev-parse", "--show-toplevel")).resolve()
    if top != root.resolve():
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake git checkout root is ambiguous"
        )
    if _git_text(root, "rev-parse", "HEAD") != OPENQUAKE_COMMIT:
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake checkout is not the frozen v3.14.0 commit"
        )
    if _git_text(root, "status", "--porcelain=v1"):
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake checkout has modifications or untracked files"
        )

    tracked = set(_git_text(root, "ls-files", "--", "openquake").splitlines())
    for candidate in (root / "openquake").rglob("*.py"):
        relative = candidate.relative_to(root).as_posix()
        if relative not in tracked:
            raise Eshm20GsimRuntimeCompatibilityError(
                "OpenQuake checkout contains an untracked Python source file"
            )
    return root


def _load_verified_openquake_runtime() -> _RuntimeAdapter:
    try:
        from openquake import baselib
        from openquake.hazardlib import valid
        from openquake.hazardlib.gsim.base import gsim_aliases, registry
    except Exception as exc:
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake runtime is unavailable"
        ) from exc

    if getattr(baselib, "__version__", None) != OPENQUAKE_VERSION:
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake runtime version is not 3.14.0"
        )

    source_file = inspect.getsourcefile(valid.gsim)
    if source_file is None:
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake valid.gsim source identity is unavailable"
        )
    _verify_exact_openquake_checkout(source_file)

    return _RuntimeAdapter(
        instantiate=lambda model: valid.gsim(model, basedir=""),
        aliases=set(gsim_aliases),
        registry=registry,
        engine_source_checkout_verified=True,
        engine_checkout_commit=OPENQUAKE_COMMIT,
    )


def _model_elements_by_branch(payload: bytes) -> dict[tuple[str, str], Any]:
    try:
        xml_text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Eshm20GsimRuntimeCompatibilityError(
            "verified GMM payload is not strict UTF-8"
        ) from exc

    root = profiler._parse_xml(xml_text)
    models: dict[tuple[str, str], Any] = {}
    for branch_set in root.iter():
        if profiler._local_name(branch_set.tag) != "logicTreeBranchSet":
            continue
        branch_set_id = branch_set.attrib.get("branchSetID")
        for branch in list(branch_set):
            if profiler._local_name(branch.tag) != "logicTreeBranch":
                continue
            branch_id = branch.attrib.get("branchID")
            model_nodes = [
                child
                for child in list(branch)
                if profiler._local_name(child.tag) == "uncertaintyModel"
            ]
            if len(model_nodes) != 1:
                raise Eshm20GsimRuntimeCompatibilityError(
                    "verified GMM branch model structure drifted"
                )
            key = (branch_set_id, branch_id)
            if key in models:
                raise Eshm20GsimRuntimeCompatibilityError(
                    "verified GMM branch identity is duplicated"
                )
            models[key] = model_nodes[0]
    return models


def _safe_class_name(value: object) -> str:
    if type(value) is not str or not value or not value.isidentifier():
        raise Eshm20GsimRuntimeCompatibilityError(
            "resolved GSIM class identity is not canonical"
        )
    return value


def _evaluate_verified_payload(
    payload: bytes,
    fingerprint: dict[str, object],
    runtime: _RuntimeAdapter,
) -> dict[str, object]:
    if (
        type(fingerprint) is not dict
        or fingerprint.get("reference_recipe_match") is not True
    ):
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake reference-runtime fingerprint is not verified"
        )
    if runtime.engine_source_checkout_verified is not True:
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake source checkout identity is not verified"
        )
    if runtime.engine_checkout_commit != OPENQUAKE_COMMIT:
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake source checkout commit drifted"
        )

    try:
        profile = profiler.profile_verified_gsim_identities(payload)
    except profiler.Eshm20GsimIdentityProfileError as exc:
        raise Eshm20GsimRuntimeCompatibilityError(
            "GMM request-token identity gate did not pass"
        ) from exc

    models = _model_elements_by_branch(payload)
    profile_keys = {
        (record["branch_set_id"], record["branch_id"])
        for record in profile["branches"]
    }
    if set(models) != profile_keys:
        raise Eshm20GsimRuntimeCompatibilityError(
            "verified GMM runtime branch set disagrees with identity profile"
        )

    records: list[dict[str, object]] = []
    resolved_classes: set[str] = set()
    alias_tokens: set[str] = set()

    for record in profile["branches"]:
        branch_set_id = record["branch_set_id"]
        branch_id = record["branch_id"]
        requested_token = record["requested_gsim_token"]
        argument_keys = list(record["argument_keys"])

        external_keys = sorted(
            key for key in argument_keys if key.endswith(_EXTERNAL_RESOURCE_SUFFIXES)
        )
        if external_keys:
            raise Eshm20GsimRuntimeCompatibilityError(
                f"GSIM request {branch_set_id}/{branch_id} requires external resources"
            )

        model = models[(branch_set_id, branch_id)]
        try:
            instance = runtime.instantiate(model)
        except Exception:
            raise Eshm20GsimRuntimeCompatibilityError(
                f"GSIM request {branch_set_id}/{branch_id} is incompatible with OpenQuake 3.14"
            ) from None

        resolved_name = _safe_class_name(type(instance).__name__)
        registered_class = runtime.registry.get(resolved_name)
        if registered_class is None or type(instance) is not registered_class:
            raise Eshm20GsimRuntimeCompatibilityError(
                f"GSIM request {branch_set_id}/{branch_id} resolved outside the registry"
            )

        model_text = (model.text or "").strip()
        request_form = "table" if model_text.startswith("[") else "bare"
        alias_definition_present = requested_token in runtime.aliases
        alias_expansion_applied = alias_definition_present and request_form == "bare"
        registry_alias_key_used = alias_definition_present and request_form == "table"
        if (
            registry_alias_key_used
            and runtime.registry.get(requested_token) is not type(instance)
        ):
            raise Eshm20GsimRuntimeCompatibilityError(
                f"GSIM request {branch_set_id}/{branch_id} alias registry identity drifted"
            )
        if (
            not alias_expansion_applied
            and not registry_alias_key_used
            and requested_token != resolved_name
        ):
            raise Eshm20GsimRuntimeCompatibilityError(
                f"GSIM request {branch_set_id}/{branch_id} changed identity without an alias"
            )

        if alias_definition_present:
            alias_tokens.add(requested_token)
        resolved_classes.add(resolved_name)
        records.append(
            {
                "branch_set_id": branch_set_id,
                "branch_id": branch_id,
                "tectonic_region_type": record["tectonic_region_type"],
                "requested_gsim_token": requested_token,
                "resolved_gsim_class": resolved_name,
                "request_form": request_form,
                "alias_definition_present": alias_definition_present,
                "alias_expansion_applied": alias_expansion_applied,
                "registry_alias_key_used": registry_alias_key_used,
                "argument_keys": argument_keys,
                "constructor_accepted": True,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "handoff_issue": HANDOFF_ISSUE,
        "dataset_id": DATASET_ID,
        "gmm_identity": {
            "project_id": profile["project_id"],
            "project_path": profile["project_path"],
            "commit_sha": profile["commit_sha"],
            "repository_path": profile["repository_path"],
            "byte_count": profile["byte_count"],
            "sha256": profile["sha256"],
        },
        "openquake_reference": {
            "repository": OPENQUAKE_REPOSITORY,
            "tag": OPENQUAKE_TAG,
            "commit": OPENQUAKE_COMMIT,
            "version": OPENQUAKE_VERSION,
        },
        "branch_count": len(records),
        "branches": records,
        "unique_resolved_gsim_classes": sorted(resolved_classes),
        "alias_requested_tokens": sorted(alias_tokens),
        "engine_source_commit_verified": True,
        "reference_runtime_recipe_verified": True,
        "alias_resolution_verified": True,
        "registry_resolution_verified": True,
        "constructor_compatibility_verified": True,
        "gsim_request_runtime_compatibility_verified": True,
        "full_hazard_compatibility_verified": False,
        "site_model_compatibility_verified": False,
        "vulnerability_compatibility_verified": False,
        "reference_run_verified": False,
        "scientific_validity_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def validate_verified_gsim_runtime(
    payload: bytes,
    runtime_observation: Any,
) -> dict[str, object]:
    """Validate the exact GMM requests against the frozen OpenQuake runtime.

    The public path never accepts caller-supplied registry or alias data. It
    requires the existing reference-runtime fingerprint and imports OpenQuake
    only from a clean git checkout at the exact v3.14.0 commit.
    """

    try:
        fingerprint = runtime_fingerprint.validate_runtime_observation(
            runtime_observation
        )
    except runtime_fingerprint.ReferenceRuntimeError as exc:
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake reference-runtime fingerprint did not pass"
        ) from exc
    runtime = _load_verified_openquake_runtime()
    return _evaluate_verified_payload(payload, fingerprint, runtime)
