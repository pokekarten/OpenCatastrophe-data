# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline dependency discovery for OpenQuake source-model logic trees.

The helper intentionally implements only the source-file discovery semantics needed
by OpenCatastrophe's ESHM20 provenance work. It never opens referenced files, fetches
provider content, or evaluates a hazard model.
"""

from __future__ import annotations

import posixpath
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable

try:
    from scripts.openquake_config_dependencies import (
        OpenQuakeConfigError,
        normalize_repository_reference,
    )
except ModuleNotFoundError:  # direct script execution
    from openquake_config_dependencies import (  # type: ignore[no-redef]
        OpenQuakeConfigError,
        normalize_repository_reference,
    )


class OpenQuakeLogicTreeError(ValueError):
    """Raised when source-model dependency discovery is ambiguous or unsafe."""


@dataclass(frozen=True, order=True)
class LogicTreeDependencyOrigin:
    """One branch that declares a source-model dependency."""

    uncertainty_type: str
    branch_id: str


@dataclass(frozen=True)
class SourceModelDependency:
    """One canonical source-model file dependency and its declaring branches."""

    resolved_path: str
    origins: tuple[LogicTreeDependencyOrigin, ...]
    is_hdf5_companion: bool = False


_RELEVANT_UNCERTAINTY_TYPES = frozenset({"sourceModel", "extendModel"})
_FORBIDDEN_DECLARATION_RE = re.compile(r"<\s*!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _nonblank_identifier(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise OpenQuakeLogicTreeError(f"{label} must be a non-empty trimmed string")
    if any(ord(char) < 32 for char in value):
        raise OpenQuakeLogicTreeError(f"{label} contains control characters")
    return value


def _canonical_repository_path(path: object, *, label: str) -> str:
    if not isinstance(path, str):
        raise OpenQuakeLogicTreeError(f"{label} must be a string")
    try:
        normalized = normalize_repository_reference("inventory-anchor.xml", path)
    except OpenQuakeConfigError as exc:
        raise OpenQuakeLogicTreeError(f"invalid {label}: {exc}") from exc
    if normalized != path:
        raise OpenQuakeLogicTreeError(f"{label} must already be canonical")
    return path


def _canonical_inventory(paths: Iterable[str]) -> frozenset[str]:
    if isinstance(paths, (str, bytes)):
        raise OpenQuakeLogicTreeError("repository_inventory must be an iterable of paths")
    result: set[str] = set()
    try:
        iterator = iter(paths)
    except TypeError as exc:
        raise OpenQuakeLogicTreeError("repository_inventory must be iterable") from exc
    for index, path in enumerate(iterator):
        canonical = _canonical_repository_path(path, label=f"repository_inventory[{index}]")
        if canonical in result:
            raise OpenQuakeLogicTreeError(f"duplicate repository inventory path: {canonical}")
        result.add(canonical)
    return frozenset(result)


def _parse_xml(xml_text: str) -> ET.Element:
    if not isinstance(xml_text, str):
        raise OpenQuakeLogicTreeError("xml_text must be a string")
    if _FORBIDDEN_DECLARATION_RE.search(xml_text):
        raise OpenQuakeLogicTreeError("DTD and entity declarations are not supported")
    try:
        root = ET.fromstring(xml_text)
    except (ET.ParseError, ValueError) as exc:
        raise OpenQuakeLogicTreeError(f"invalid logic-tree XML: {exc}") from exc
    return root


def _logic_tree_branch_sets(root: ET.Element) -> tuple[ET.Element, ...]:
    """Return branch sets from OpenQuake's accepted source-logic-tree shapes."""

    if _local_name(root.tag) != "nrml":
        raise OpenQuakeLogicTreeError("logic-tree XML root must be nrml")

    root_children = list(root)
    logic_trees = [child for child in root_children if _local_name(child.tag) == "logicTree"]
    if len(logic_trees) != 1:
        raise OpenQuakeLogicTreeError("nrml must contain exactly one direct logicTree")
    if len(root_children) != 1:
        raise OpenQuakeLogicTreeError("nrml must not contain direct children outside logicTree")

    branch_sets: list[ET.Element] = []
    for child in list(logic_trees[0]):
        local = _local_name(child.tag)
        if local == "logicTreeBranchSet":
            branch_sets.append(child)
            continue
        if local == "logicTreeBranchingLevel":
            nested = [
                branch_set
                for branch_set in list(child)
                if _local_name(branch_set.tag) == "logicTreeBranchSet"
            ]
            if len(nested) != 1 or len(list(child)) != 1:
                raise OpenQuakeLogicTreeError(
                    "logicTreeBranchingLevel must contain exactly one direct logicTreeBranchSet"
                )
            branch_sets.extend(nested)
            continue
        raise OpenQuakeLogicTreeError(
            f"unsupported direct logicTree child: {local or '<non-element>'}"
        )

    if not branch_sets:
        raise OpenQuakeLogicTreeError("logicTree must contain at least one branch set")
    return tuple(branch_sets)


def _branch_model_tokens(branch: ET.Element, *, branch_id: str) -> tuple[str, ...]:
    models = [child for child in list(branch) if _local_name(child.tag) == "uncertaintyModel"]
    if len(models) != 1:
        raise OpenQuakeLogicTreeError(
            f"branch {branch_id!r} must contain exactly one direct uncertaintyModel"
        )
    model = models[0]
    if list(model):
        raise OpenQuakeLogicTreeError(
            f"branch {branch_id!r} uncertaintyModel must contain text only"
        )
    text = model.text
    if not isinstance(text, str) or not text.strip():
        raise OpenQuakeLogicTreeError(
            f"branch {branch_id!r} uncertaintyModel must be non-empty"
        )
    tokens = tuple(text.split())
    if not tokens:
        raise OpenQuakeLogicTreeError(
            f"branch {branch_id!r} uncertaintyModel must declare a dependency"
        )
    if len(tokens) != len(set(tokens)):
        raise OpenQuakeLogicTreeError(
            f"branch {branch_id!r} contains a duplicate dependency name"
        )
    return tokens


def extract_source_model_logic_tree_dependencies(
    xml_text: str,
    *,
    logic_tree_path: str,
    repository_inventory: Iterable[str] = (),
) -> tuple[SourceModelDependency, ...]:
    """Return deterministic source-model dependencies declared by one logic tree.

    Only branch sets with OpenQuake 3.14 ``uncertaintyType`` values
    ``sourceModel`` and ``extendModel`` contribute references. Same-basename
    HDF5 companions are emitted only when present in the explicit repository
    inventory supplied by the caller.
    """

    logic_tree_path = _canonical_repository_path(
        logic_tree_path, label="logic_tree_path"
    )
    inventory = _canonical_inventory(repository_inventory)
    root = _parse_xml(xml_text)

    relevant_sets: list[ET.Element] = []
    for element in _logic_tree_branch_sets(root):
        uncertainty_type = _nonblank_identifier(
            element.attrib.get("uncertaintyType"), label="uncertaintyType"
        )
        if uncertainty_type in _RELEVANT_UNCERTAINTY_TYPES:
            relevant_sets.append(element)

    path_origins: dict[str, set[LogicTreeDependencyOrigin]] = {}
    seen_branch_ids: set[str] = set()

    for branch_set in relevant_sets:
        uncertainty_type = branch_set.attrib["uncertaintyType"]
        branch_set_children = list(branch_set)
        branches = [
            child
            for child in branch_set_children
            if _local_name(child.tag) == "logicTreeBranch"
        ]
        if len(branches) != len(branch_set_children):
            raise OpenQuakeLogicTreeError(
                f"{uncertainty_type} branch set contains an unsupported direct child"
            )
        if not branches:
            raise OpenQuakeLogicTreeError(
                f"{uncertainty_type} branch set must contain at least one direct logicTreeBranch"
            )

        for branch in branches:
            branch_id = _nonblank_identifier(
                branch.attrib.get("branchID"), label="branchID"
            )
            if branch_id in seen_branch_ids:
                raise OpenQuakeLogicTreeError(f"duplicate branchID: {branch_id}")
            seen_branch_ids.add(branch_id)

            tokens = _branch_model_tokens(branch, branch_id=branch_id)
            origin = LogicTreeDependencyOrigin(uncertainty_type, branch_id)
            normalized_in_branch: set[str] = set()
            for raw_path in tokens:
                try:
                    resolved = normalize_repository_reference(
                        logic_tree_path, raw_path
                    )
                except OpenQuakeConfigError as exc:
                    raise OpenQuakeLogicTreeError(
                        f"invalid dependency in branch {branch_id!r}: {exc}"
                    ) from exc
                if resolved in normalized_in_branch:
                    raise OpenQuakeLogicTreeError(
                        f"branch {branch_id!r} contains dependencies that normalize to the same path: {resolved}"
                    )
                normalized_in_branch.add(resolved)
                path_origins.setdefault(resolved, set()).add(origin)

    result: list[SourceModelDependency] = []
    for path in sorted(path_origins):
        origins = tuple(sorted(path_origins[path]))
        result.append(SourceModelDependency(path, origins, False))
        stem = posixpath.splitext(path)[0]
        companion = f"{stem}.hdf5"
        if companion in inventory and companion != path:
            result.append(SourceModelDependency(companion, origins, True))

    return tuple(
        sorted(
            result,
            key=lambda item: (
                item.resolved_path,
                item.is_hdf5_companion,
                item.origins,
            ),
        )
    )
