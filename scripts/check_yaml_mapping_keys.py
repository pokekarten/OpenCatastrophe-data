# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Reject ambiguous GitHub configuration YAML before the hosted runner reads it.

Use BaseLoader only to build the YAML syntax tree: it never constructs objects
and preserves GitHub Actions' literal ``on`` key (YAML 1.1 resolves it as bool).
This is a syntax/structural check, not a claim that workflows have run.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def check_file(path: Path) -> list[str]:
    """Return deterministic, actionable errors for a single YAML file."""

    try:
        document = yaml.compose(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"{path}: invalid YAML: {exc}"]

    errors: list[str] = []
    # Aliases form a graph, not a tree. Visiting a shared subtree repeatedly can
    # take exponential time even for a very small, otherwise valid YAML file.
    finished: set[int] = set()
    allowed_tags = {
        yaml.ScalarNode: "tag:yaml.org,2002:str",
        yaml.MappingNode: "tag:yaml.org,2002:map",
        yaml.SequenceNode: "tag:yaml.org,2002:seq",
    }

    def visit(node: yaml.Node, location: str, ancestors: frozenset[int]) -> None:
        identity = id(node)
        if identity in ancestors:
            errors.append(f"{path}: recursive YAML alias at {location}")
            return
        if identity in finished:
            return
        # Reject custom/typed tags that GitHub's configuration parser may not
        # interpret like PyYAML's BaseLoader; never treat a parse as approval.
        expected_tag = allowed_tags.get(type(node))
        if expected_tag is None or node.tag != expected_tag:
            errors.append(f"{path}:{node.start_mark.line + 1}: unsupported YAML tag at {location}")
            return
        parents = ancestors | {identity}
        if isinstance(node, yaml.MappingNode):
            seen: dict[str, int] = {}
            for key, value in node.value:
                if not isinstance(key, yaml.ScalarNode):
                    errors.append(f"{path}:{key.start_mark.line + 1}: non-scalar YAML mapping key at {location}")
                    continue
                name = key.value
                line = key.start_mark.line + 1
                if key.tag != allowed_tags[yaml.ScalarNode]:
                    errors.append(f"{path}:{line}: unsupported YAML key tag at {location}")
                if name == "<<":
                    errors.append(f"{path}:{line}: YAML merge key is ambiguous at {location}")
                elif name in seen:
                    errors.append(
                        f"{path}:{line}: duplicate key {name!r} at {location} "
                        f"(first defined at line {seen[name]})"
                    )
                else:
                    seen[name] = line
                visit(value, f"{location}/{name}", parents)
        elif isinstance(node, yaml.SequenceNode):
            for index, value in enumerate(node.value):
                visit(value, f"{location}/{index}", parents)
        finished.add(identity)

    if document is not None:
        if not isinstance(document, yaml.MappingNode):
            errors.append(f"{path}: expected a YAML mapping as document root")
        else:
            visit(document, "$", frozenset())
    else:
        errors.append(f"{path}: empty YAML document")
    return errors


def check_all(root: Path = ROOT) -> tuple[list[str], int]:
    """Inspect every GitHub configuration YAML file, including issue templates."""

    github = root / ".github"
    if not github.is_dir():
        return [f"{github}: required GitHub configuration directory is missing"], 0
    paths = sorted((*github.rglob("*.yml"), *github.rglob("*.yaml")))
    if not paths:
        return [f"{github}: no YAML files were found"], 0
    errors: list[str] = []
    for path in paths:
        if path.is_symlink():
            errors.append(f"{path}: symlink is not a safe configuration source")
        elif path.is_file():
            errors.extend(check_file(path))
        else:
            errors.append(f"{path}: expected a regular YAML file")
    return errors, len(paths)


def main() -> int:
    errors, count = check_all()
    if errors:
        for message in errors:
            print(f"FAIL: {message}", file=sys.stderr)
        return 1
    print(f"PASS: GitHub YAML syntax and unique mapping keys ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
