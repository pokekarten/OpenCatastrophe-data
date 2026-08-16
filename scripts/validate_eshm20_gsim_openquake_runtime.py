# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed ESHM20 GSIM request compatibility gate for OpenQuake 3.14.

The earlier identity profiler deliberately preserves unresolved GSIM request
terms. This module is the next, narrower source/runtime gate: after the exact
GMM payload and reconstructed OpenQuake reference-runtime observation have both
been validated, it resolves aliases through the exact OpenQuake v3.14.0 source
path and requires every bounded resource-free request to instantiate.

A PASS proves exact-source alias/registry/constructor compatibility for the
frozen OpenQuake commit. It deliberately does not claim that the Python process
performing the constructor probes is the complete Python-3.8 reference runtime
recipe represented by the separately validated observation. It also does not
prove hazard numerical agreement, IMT/site/vulnerability compatibility,
scientific validity, or a reference run.
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
    """Raised when exact GSIM source compatibility cannot be proven safely."""


class _RuntimeAdapter:
    """Small boundary around the exact OpenQuake functions used by this gate."""

    def __init__(
        self,
        *,
        instantiate: Any,
        argument_keys_after_alias: Any,
        aliases: set[str] | frozenset[str],
        registry: dict[str, type],
        engine_source_checkout_verified: bool,
        engine_checkout_commit: str,
    ) -> None:
        self.instantiate = instantiate
        self.argument_keys_after_alias = argument_keys_after_alias
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


def _require_compatible_openquake_version(value: object) -> None:
    """Require the frozen release or its exact commit-bound Git presentation."""

    try:
        runtime_fingerprint._normalize_engine_version(
            value,
            engine_commit=OPENQUAKE_COMMIT,
        )
    except runtime_fingerprint.ReferenceRuntimeError as exc:
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake runtime version does not match the frozen v3.14.0 source"
        ) from exc


def _load_verified_openquake_runtime() -> _RuntimeAdapter:
    try:
        import toml
        from openquake import baselib
        from openquake.hazardlib import valid
        from openquake.hazardlib.gsim.base import gsim_aliases, registry
    except Exception as exc:
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake runtime is unavailable"
        ) from exc

    _require_compatible_openquake_version(getattr(baselib, "__version__", None))

    source_file = inspect.getsourcefile(valid.gsim)
    if source_file is None:
        raise Eshm20GsimRuntimeCompatibilityError(
            "OpenQuake valid.gsim source identity is unavailable"
        )
    _verify_exact_openquake_checkout(source_file)

    def argument_keys_after_alias(model: object) -> list[str]:
        """Return only top-level constructor keys after exact v3.14 to_toml.

        OpenQuake v3.14 expands a bare alias inside ``valid.to_toml`` before
        TOML parsing and before ``valid.gsim`` rewrites ``*_file``/``*_table``
        values. Inspecting this exact post-alias key surface is therefore the
        fail-closed place to reject hidden external-resource dependencies.
        Values are never returned or serialized.
        """

        try:
            expanded = valid.to_toml(model)
            parsed = toml.loads(expanded)
            if type(parsed) is not dict or len(parsed) != 1:
                raise Eshm20GsimRuntimeCompatibilityError(
                    "post-alias GSIM request is not one canonical TOML table"
                )
            [(_, raw_kwargs)] = parsed.items()
            kwargs = valid._fix_toml(raw_kwargs)
            if not hasattr(kwargs, "keys"):
                raise Eshm20GsimRuntimeCompatibilityError(
                    "post-alias GSIM constructor arguments are not an object"
                )
            keys: list[str] = []
            for key in kwargs.keys():
                if type(key) is not str or not key:
                    raise Eshm20GsimRuntimeCompatibilityError(
                        "post-alias GSIM constructor key is not canonical"
                    )
                keys.append(key)
            return sorted(keys)
        except Eshm20GsimRuntimeCompatibilityError:
            raise
        except Exception as exc:
            raise Eshm20GsimRuntimeCompatibilityError(
                "cannot preflight post-alias GSIM constructor keys"
            ) from exc

    return _RuntimeAdapter(
        instantiate=lambda model: valid.gsim(model, basedir=""),
        argument_keys_after_alias=argument_keys_after_alias,
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
            "OpenQuake reference-runtime observation is not validated"
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

        source_external_keys = sorted(
            key for key in argument_keys if key.endswith(_EXTERNAL_RESOURCE_SUFFIXES)
        )
        if source_external_keys:
            raise Eshm20GsimRuntimeCompatibilityError(
                f"GSIM request {branch_set_id}/{branch_id} requires external resources"
            )

        model = models[(branch_set_id, branch_id)]
        try:
            runtime_argument_keys = list(runtime.argument_keys_after_alias(model))
        except Eshm20GsimRuntimeCompatibilityError:
            raise
        except Exception as exc:
            raise Eshm20GsimRuntimeCompatibilityError(
                f"GSIM request {branch_set_id}/{branch_id} post-alias preflight failed"
            ) from exc
        if any(type(key) is not str or not key for key in runtime_argument_keys):
            raise Eshm20GsimRuntimeCompatibilityError(
                f"GSIM request {branch_set_id}/{branch_id} has a noncanonical post-alias key"
            )
        runtime_argument_keys = sorted(runtime_argument_keys)
        runtime_external_keys = sorted(
            key
            for key in runtime_argument_keys
            if key.endswith(_EXTERNAL_RESOURCE_SUFFIXES)
        )
        if runtime_external_keys:
            raise Eshm20GsimRuntimeCompatibilityError(
                f"GSIM request {branch_set_id}/{branch_id} requires external resources after alias expansion"
            )

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
                "runtime_argument_keys_after_alias": runtime_argument_keys,
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
        # The validated observation is useful contextual evidence, but it is not
        # promoted into a claim about the Python process that executes the exact
        # source constructor probes below.
        "reference_runtime_fingerprint": fingerprint,
        "branch_count": len(records),
        "branches": records,
        "unique_resolved_gsim_classes": sorted(resolved_classes),
        "alias_requested_tokens": sorted(alias_tokens),
        "engine_source_commit_verified": True,
        "reference_runtime_observation_validated": True,
        "executing_environment_bound_to_reference_recipe": False,
        "reference_runtime_recipe_verified": False,
        "alias_resolution_verified": True,
        "registry_resolution_verified": True,
        "constructor_compatibility_verified": True,
        "exact_source_constructor_compatibility_verified": True,
        "gsim_request_runtime_compatibility_verified": False,
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
    """Validate exact GMM requests against frozen OpenQuake 3.14 source.

    The public path never accepts caller-supplied registry or alias data. It
    validates the existing reference-runtime observation as contextual evidence
    and imports OpenQuake only from a clean git checkout at the exact v3.14.0
    commit. The validated observation is deliberately not treated as proof that
    this executing Python process matches the complete reference-runtime recipe.
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