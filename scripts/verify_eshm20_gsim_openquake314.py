# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Verify exact ESHM20 GSIM constructor compatibility under OpenQuake 3.14.

This probe is deliberately narrower than an EQ1 reference run. It reuses the
merged exact-byte/structural profiler, attests a local OpenQuake source tree to
the frozen v3.14.0 Git tree, and only then asks ``valid.gsim`` to parse and
instantiate every exact uncertainty-model request. Provider model text and
argument values are never returned.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib
import io
import json
import logging
import os
from pathlib import Path
import stat
import sys
import warnings
from typing import Any, Callable

from scripts import profile_eshm20_gsim_identities as profiler

SCHEMA_VERSION = "oc-eshm20-gsim-openquake314-compat-v1"
SOURCE_ISSUE = 281
CONTROL_ISSUE = 431
DATASET_ID = profiler.DATASET_ID

OPENQUAKE_REPOSITORY = "gem/oq-engine"
OPENQUAKE_TAG = "v3.14.0"
OPENQUAKE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
OPENQUAKE_ROOT_TREE_SHA1 = "19c12474bd011c28054fa7660047522681d36356"
OPENQUAKE_SUBTREE_SHA1 = "5a6f64a16da563451fe601bba4bf761d585080e9"
OPENQUAKE_VERSION_PREFIX = "3.14.0"

MAX_TREE_ENTRIES = 20_000
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024


class Eshm20OpenQuake314CompatibilityError(ValueError):
    """Raised when the bounded compatibility probe cannot close safely."""


def _git_object_sha1(kind: str, payload: bytes) -> str:
    if kind not in {"blob", "tree"} or type(payload) is not bytes:
        raise Eshm20OpenQuake314CompatibilityError("invalid Git object input")
    header = f"{kind} {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()  # noqa: S324 - Git identity


def _git_blob_sha1(payload: bytes) -> str:
    return _git_object_sha1("blob", payload)


def _tree_name_bytes(name: str) -> bytes:
    encoded = os.fsencode(name)
    if not encoded or b"\x00" in encoded or b"/" in encoded:
        raise Eshm20OpenQuake314CompatibilityError("unsupported source-tree entry name")
    return encoded


def _read_regular_file(path: Path, size: int, state: dict[str, int]) -> bytes:
    if size > MAX_FILE_BYTES:
        raise Eshm20OpenQuake314CompatibilityError("source-tree file exceeds bound")
    state["total_bytes"] += size
    if state["total_bytes"] > MAX_TOTAL_BYTES:
        raise Eshm20OpenQuake314CompatibilityError("source-tree byte budget exceeded")
    with path.open("rb") as handle:
        payload = handle.read(MAX_FILE_BYTES + 1)
    if len(payload) != size or len(payload) > MAX_FILE_BYTES:
        raise Eshm20OpenQuake314CompatibilityError("source-tree file changed during read")
    return payload


def _git_tree_sha1(path: Path, state: dict[str, int] | None = None) -> str:
    """Recompute a Git tree SHA-1 from a filesystem directory.

    Interpreter-generated ``__pycache__`` directories are ignored. Every
    other entry participates in the identity; additions, deletions, content
    changes, executable-bit changes, and symlink-target changes therefore
    change the computed tree object.
    """

    root = Path(path)
    if state is None:
        state = {"entries": 0, "total_bytes": 0}
    try:
        entries = list(os.scandir(root))
    except OSError as exc:
        raise Eshm20OpenQuake314CompatibilityError(
            "cannot read OpenQuake source tree"
        ) from exc

    records: list[tuple[bytes, bool, bytes]] = []
    for entry in entries:
        if entry.name == "__pycache__" and entry.is_dir(follow_symlinks=False):
            continue
        state["entries"] += 1
        if state["entries"] > MAX_TREE_ENTRIES:
            raise Eshm20OpenQuake314CompatibilityError("source-tree entry budget exceeded")

        name = _tree_name_bytes(entry.name)
        child = root / entry.name
        try:
            metadata = child.lstat()
        except OSError as exc:
            raise Eshm20OpenQuake314CompatibilityError(
                "cannot stat OpenQuake source-tree entry"
            ) from exc

        if stat.S_ISDIR(metadata.st_mode):
            mode = b"40000"
            object_sha = _git_tree_sha1(child, state)
            is_tree = True
        elif stat.S_ISREG(metadata.st_mode):
            mode = b"100755" if metadata.st_mode & 0o111 else b"100644"
            payload = _read_regular_file(child, metadata.st_size, state)
            object_sha = _git_blob_sha1(payload)
            is_tree = False
        elif stat.S_ISLNK(metadata.st_mode):
            mode = b"120000"
            try:
                target = os.readlink(child)
            except OSError as exc:
                raise Eshm20OpenQuake314CompatibilityError(
                    "cannot read OpenQuake source-tree symlink"
                ) from exc
            payload = os.fsencode(target)
            state["total_bytes"] += len(payload)
            if state["total_bytes"] > MAX_TOTAL_BYTES:
                raise Eshm20OpenQuake314CompatibilityError(
                    "source-tree byte budget exceeded"
                )
            object_sha = _git_blob_sha1(payload)
            is_tree = False
        else:
            raise Eshm20OpenQuake314CompatibilityError(
                "unsupported OpenQuake source-tree filesystem object"
            )

        record = mode + b" " + name + b"\x00" + bytes.fromhex(object_sha)
        records.append((name, is_tree, record))

    records.sort(key=lambda item: item[0] + (b"/" if item[1] else b""))
    return _git_object_sha1("tree", b"".join(item[2] for item in records))


def attest_openquake314_source_tree(openquake_dir: str | os.PathLike[str]) -> dict[str, Any]:
    root = Path(openquake_dir)
    if root.name != "openquake" or root.is_symlink() or not root.is_dir():
        raise Eshm20OpenQuake314CompatibilityError(
            "expected the OpenQuake source checkout's openquake directory"
        )
    observed = _git_tree_sha1(root)
    if observed != OPENQUAKE_SUBTREE_SHA1:
        raise Eshm20OpenQuake314CompatibilityError(
            "OpenQuake source tree does not match frozen v3.14.0 commit"
        )
    return {
        "repository": OPENQUAKE_REPOSITORY,
        "tag": OPENQUAKE_TAG,
        "commit": OPENQUAKE_COMMIT,
        "root_tree_sha1": OPENQUAKE_ROOT_TREE_SHA1,
        "openquake_tree_sha1": observed,
        "source_tree_verified": True,
    }


def _module_is_within(module: Any, root: Path) -> bool:
    filename = getattr(module, "__file__", None)
    if not filename:
        return False
    try:
        Path(filename).resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _load_attested_openquake314(
    openquake_dir: Path,
) -> tuple[str, Callable[..., str], Callable[..., Any]]:
    root = openquake_dir.resolve()
    parent = str(root.parent)

    for name, module in tuple(sys.modules.items()):
        if name == "openquake" or name.startswith("openquake."):
            if module is not None and not _module_is_within(module, root):
                raise Eshm20OpenQuake314CompatibilityError(
                    "a different OpenQuake runtime is already imported"
                )

    inserted = False
    if parent not in sys.path:
        sys.path.insert(0, parent)
        inserted = True
    try:
        baselib = importlib.import_module("openquake.baselib")
        valid = importlib.import_module("openquake.hazardlib.valid")
    except Exception:
        raise Eshm20OpenQuake314CompatibilityError(
            "frozen OpenQuake runtime could not be imported"
        ) from None
    finally:
        if inserted:
            try:
                sys.path.remove(parent)
            except ValueError:
                pass

    if not _module_is_within(baselib, root) or not _module_is_within(valid, root):
        raise Eshm20OpenQuake314CompatibilityError(
            "OpenQuake modules were not imported from the attested source tree"
        )
    version = getattr(baselib, "__version__", None)
    if type(version) is not str or not version.startswith(OPENQUAKE_VERSION_PREFIX):
        raise Eshm20OpenQuake314CompatibilityError(
            "attested OpenQuake source reports an unexpected version"
        )
    to_toml_callable = getattr(valid, "to_toml", None)
    gsim_callable = getattr(valid, "gsim", None)
    if not callable(to_toml_callable) or not callable(gsim_callable):
        raise Eshm20OpenQuake314CompatibilityError(
            "attested OpenQuake runtime lacks the exact GSIM parser path"
        )
    return version, to_toml_callable, gsim_callable


def _runtime_toml_argument_keys(
    model: Any, to_toml_callable: Callable[..., str]
) -> tuple[str, ...]:
    try:
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
            warnings.catch_warnings(),
        ):
            warnings.simplefilter("ignore")
            rendered = to_toml_callable(model)
    except Exception:
        raise Eshm20OpenQuake314CompatibilityError(
            "OpenQuake 3.14 rejected verified GSIM request during TOML preflight"
        ) from None
    if type(rendered) is not str:
        raise Eshm20OpenQuake314CompatibilityError(
            "OpenQuake TOML preflight returned an invalid type"
        )
    lines = [line.strip() for line in rendered.splitlines() if line.strip()]
    if not lines or not lines[0].startswith("[") or not lines[0].endswith("]"):
        raise Eshm20OpenQuake314CompatibilityError(
            "OpenQuake TOML preflight returned an unsupported shape"
        )
    keys: set[str] = set()
    for line in lines[1:]:
        if line.startswith("#"):
            continue
        if line.startswith("[") or "=" not in line:
            raise Eshm20OpenQuake314CompatibilityError(
                "OpenQuake TOML preflight returned an unsupported shape"
            )
        key = line.split("=", 1)[0].strip()
        if not key or not key.replace("_", "a").isalnum() or not (
            key[0].isalpha() or key[0] == "_"
        ):
            raise Eshm20OpenQuake314CompatibilityError(
                "OpenQuake TOML preflight returned an unsupported argument key"
            )
        if key in keys:
            raise Eshm20OpenQuake314CompatibilityError(
                "OpenQuake TOML preflight duplicated an argument key"
            )
        keys.add(key)
    return tuple(sorted(keys))


def _local_name(tag: object) -> str:
    if type(tag) is not str:
        raise Eshm20OpenQuake314CompatibilityError("invalid verified XML tag")
    return tag.rsplit("}", 1)[-1]


def _verified_model_nodes(payload: bytes, profile: dict[str, Any]) -> dict[tuple[str, str], Any]:
    try:
        xml_text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Eshm20OpenQuake314CompatibilityError(
            "verified GMM payload is not strict UTF-8"
        ) from exc
    root = profiler._parse_xml(xml_text)
    nodes: dict[tuple[str, str], Any] = {}
    for branch_set in root.iter():
        if _local_name(branch_set.tag) != "logicTreeBranchSet":
            continue
        set_id = branch_set.attrib.get("branchSetID")
        for branch in list(branch_set):
            if _local_name(branch.tag) != "logicTreeBranch":
                continue
            branch_id = branch.attrib.get("branchID")
            models = [
                child
                for child in list(branch)
                if _local_name(child.tag) == "uncertaintyModel"
            ]
            if len(models) != 1 or type(set_id) is not str or type(branch_id) is not str:
                raise Eshm20OpenQuake314CompatibilityError(
                    "verified GMM structure cannot be rebound to runtime nodes"
                )
            key = (set_id, branch_id)
            if key in nodes:
                raise Eshm20OpenQuake314CompatibilityError(
                    "verified GMM runtime node identity is duplicated"
                )
            nodes[key] = models[0]

    expected = {
        (record["branch_set_id"], record["branch_id"])
        for record in profile["branches"]
    }
    if set(nodes) != expected:
        raise Eshm20OpenQuake314CompatibilityError(
            "verified GMM runtime nodes drifted from the structural profile"
        )
    return nodes


def _resolution_fingerprint(records: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        records,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_with_runtime(
    payload: bytes,
    *,
    openquake_version: str,
    to_toml_callable: Callable[..., str],
    gsim_callable: Callable[..., Any],
    source_tree_sha1: str,
) -> dict[str, Any]:
    if source_tree_sha1 != OPENQUAKE_SUBTREE_SHA1:
        raise Eshm20OpenQuake314CompatibilityError(
            "OpenQuake source-tree attestation is not the frozen v3.14.0 tree"
        )
    if type(openquake_version) is not str or not openquake_version.startswith(
        OPENQUAKE_VERSION_PREFIX
    ):
        raise Eshm20OpenQuake314CompatibilityError(
            "OpenQuake runtime version is not v3.14.0"
        )
    if not callable(to_toml_callable) or not callable(gsim_callable):
        raise Eshm20OpenQuake314CompatibilityError(
            "OpenQuake GSIM runtime is unavailable"
        )

    try:
        profile = profiler.profile_verified_gsim_identities(payload)
    except Exception as exc:
        if isinstance(exc, profiler.Eshm20GsimIdentityProfileError):
            raise
        raise Eshm20OpenQuake314CompatibilityError(
            "verified GMM profile could not be established"
        ) from None

    resource_keys = sorted(
        {
            key
            for branch in profile["branches"]
            for key in branch["argument_keys"]
            if key.endswith(("_file", "_table"))
        }
    )
    if resource_keys:
        raise Eshm20OpenQuake314CompatibilityError(
            "verified GMM requests external GSIM resources outside this slice"
        )

    nodes = _verified_model_nodes(payload, profile)
    resolutions: list[dict[str, Any]] = []
    resolved_classes: set[str] = set()

    for index, branch in enumerate(profile["branches"]):
        key = (branch["branch_set_id"], branch["branch_id"])
        model = nodes[key]
        try:
            requested_token, argument_keys = profiler._structural_model_identity(model)
        except Exception:
            raise Eshm20OpenQuake314CompatibilityError(
                "verified GMM runtime node failed structural revalidation"
            ) from None
        if (
            requested_token != branch["requested_gsim_token"]
            or list(argument_keys) != branch["argument_keys"]
        ):
            raise Eshm20OpenQuake314CompatibilityError(
                "verified GMM runtime node drifted from structural identity"
            )

        runtime_argument_keys = _runtime_toml_argument_keys(model, to_toml_callable)
        if any(key.endswith(("_file", "_table")) for key in runtime_argument_keys):
            raise Eshm20OpenQuake314CompatibilityError(
                "OpenQuake alias/TOML expansion requests external GSIM resources"
            )

        previous_logging_disable = logging.root.manager.disable
        try:
            logging.disable(logging.CRITICAL)
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
                warnings.catch_warnings(),
            ):
                warnings.simplefilter("ignore")
                instance = gsim_callable(model, basedir="")
        except Exception:
            raise Eshm20OpenQuake314CompatibilityError(
                f"OpenQuake 3.14 rejected verified GSIM request at branch index {index}"
            ) from None
        finally:
            logging.disable(previous_logging_disable)

        cls = instance.__class__
        module_name = getattr(cls, "__module__", None)
        class_name = getattr(cls, "__name__", None)
        if (
            type(module_name) is not str
            or type(class_name) is not str
            or not module_name
            or not class_name
        ):
            raise Eshm20OpenQuake314CompatibilityError(
                "OpenQuake returned a GSIM with invalid class identity"
            )
        resolved = f"{module_name}.{class_name}"
        resolved_classes.add(resolved)
        resolutions.append(
            {
                "branch_set_id": branch["branch_set_id"],
                "branch_id": branch["branch_id"],
                "requested_gsim_token": requested_token,
                "argument_keys": list(argument_keys),
                "resolved_gsim_class": resolved,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "control_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "provider_commit": profiler.COMMIT_SHA,
        "provider_repository_path": profiler.REPOSITORY_PATH,
        "provider_byte_count": profiler.EXPECTED_BYTE_COUNT,
        "provider_sha256": profiler.EXPECTED_SHA256,
        "openquake_repository": OPENQUAKE_REPOSITORY,
        "openquake_tag": OPENQUAKE_TAG,
        "openquake_commit": OPENQUAKE_COMMIT,
        "openquake_tree_sha1": source_tree_sha1,
        "openquake_version": openquake_version,
        "branch_set_count": profile["branch_set_count"],
        "branch_count": profile["branch_count"],
        "requested_gsim_token_count": len(profile["unique_requested_gsim_tokens"]),
        "resolved_gsim_class_count": len(resolved_classes),
        "resolution_fingerprint_sha256": _resolution_fingerprint(resolutions),
        "openquake_source_tree_verified": True,
        "alias_expansion_resource_preflight_verified": True,
        "alias_registry_constructor_path_verified": True,
        "constructor_compatibility_verified": True,
        "reference_environment_identity_closed": False,
        "provider_model_text_returned": False,
        "provider_argument_values_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def verify_verified_gsim_runtime(
    payload: bytes,
    *,
    openquake_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Verify exact GMM bytes against an exact OpenQuake-v3.14.0 source tree."""

    if type(payload) is not bytes:
        raise Eshm20OpenQuake314CompatibilityError("GMM payload must be immutable bytes")
    attestation = attest_openquake314_source_tree(openquake_dir)
    version, to_toml_callable, gsim_callable = _load_attested_openquake314(
        Path(openquake_dir)
    )
    return _verify_with_runtime(
        payload,
        openquake_version=version,
        to_toml_callable=to_toml_callable,
        gsim_callable=gsim_callable,
        source_tree_sha1=attestation["openquake_tree_sha1"],
    )
