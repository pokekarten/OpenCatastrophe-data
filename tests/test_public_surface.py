# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode

ROOT = Path(__file__).resolve().parents[1]


class StrictWorkflowLoader(yaml.SafeLoader):
    """Safe workflow loader with fail-closed mapping semantics."""


# PyYAML's SafeLoader follows YAML 1.1 boolean resolution, where keys such as
# `on` can become booleans. GitHub workflow syntax treats those keys as strings.
# We only need structural/string semantics for action-pin validation, so disable
# implicit boolean coercion rather than silently changing workflow keys.
StrictWorkflowLoader.yaml_implicit_resolvers = {
    key: list(resolvers) for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
for resolver_key, resolvers in list(StrictWorkflowLoader.yaml_implicit_resolvers.items()):
    StrictWorkflowLoader.yaml_implicit_resolvers[resolver_key] = [
        (tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:bool"
    ]


def _construct_strict_mapping(
    loader: StrictWorkflowLoader,
    node: MappingNode,
    deep: bool = False,
) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ValueError("workflow mapping keys must be strings")
        if key in mapping:
            raise ValueError(f"workflow contains duplicate mapping key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictWorkflowLoader.construct_mapping = _construct_strict_mapping  # type: ignore[method-assign]


def _workflow_uses(workflow: str) -> list[str]:
    try:
        document = yaml.load(workflow, Loader=StrictWorkflowLoader)
    except (yaml.YAMLError, ValueError) as exc:
        raise ValueError(f"workflow YAML is not safely parseable: {exc}") from exc

    uses: list[str] = []
    visited: set[int] = set()
    active: set[int] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            identity = id(node)
            if identity in active:
                raise ValueError("workflow YAML contains a recursive mapping alias")
            if identity in visited:
                return
            active.add(identity)
            for key, value in node.items():
                if not isinstance(key, str):
                    raise ValueError("workflow mapping keys must be strings")
                if key == "uses":
                    if not isinstance(value, str):
                        raise ValueError("workflow uses value must be a string")
                    uses.append(value)
                walk(value)
            active.remove(identity)
            visited.add(identity)
            return

        if isinstance(node, list):
            identity = id(node)
            if identity in active:
                raise ValueError("workflow YAML contains a recursive sequence alias")
            if identity in visited:
                return
            active.add(identity)
            for item in node:
                walk(item)
            active.remove(identity)
            visited.add(identity)
            return

        if node is None or isinstance(node, (str, int, float, bool)):
            return
        raise ValueError(f"unsupported workflow YAML node type: {type(node).__name__}")

    walk(document)
    return uses


class PublicSurfaceTests(unittest.TestCase):
    def test_no_private_or_retired_project_references_in_tracked_text(self) -> None:
        forbidden = ("private-archive", "FFBK", "Rim-", "OpenCAT-data")
        for path in self._text_files():
            if path == Path(__file__).resolve():
                continue
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                with self.subTest(path=path, token=token):
                    self.assertNotIn(token, text)

    def test_workflow_actions_are_exactly_pinned(self) -> None:
        workflow_files = self._workflow_files()
        self.assertTrue(workflow_files, "at least one tracked GitHub Actions workflow is expected")
        uses = []
        for path in workflow_files:
            workflow = path.read_text(encoding="utf-8")
            for item in _workflow_uses(workflow):
                uses.append((path.relative_to(ROOT).as_posix(), item))

        checkout = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
        setup_python = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
        dependency_review = "actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294"
        allowed = {checkout, setup_python, dependency_review}

        for workflow_path, item in uses:
            with self.subTest(workflow=workflow_path, uses=item):
                self.assertRegex(item, r"^[^@\s]+@[0-9a-f]{40}$")
                self.assertIn(item, allowed)

    def test_workflow_action_scanner_covers_semantic_yaml_forms(self) -> None:
        untrusted = "example/action@main"
        cases = (
            f"      - uses: {untrusted}\n",
            f"      - uses : {untrusted}\n",
            f"      - 'uses': {untrusted}\n",
            f"      - {{name: example, uses: {untrusted}}}\n",
            f"      - &step uses: {untrusted}\n",
            f"      - {{&step uses: {untrusted}}}\n",
            f'      - {{"u\\u0073es": {untrusted}}}\n',
            f"      - {{ ? uses : {untrusted} }}\n",
        )
        for workflow in cases:
            with self.subTest(workflow=workflow):
                self.assertEqual(_workflow_uses(workflow), [untrusted])

    def test_workflow_action_scanner_handles_non_recursive_aliases(self) -> None:
        untrusted = "example/action@main"
        workflow = f"first: &step {{uses: {untrusted}}}\nsecond: *step\n"
        self.assertEqual(_workflow_uses(workflow), [untrusted])

    def test_workflow_action_scanner_rejects_unsafe_or_ambiguous_yaml(self) -> None:
        cases = (
            "uses: example/action@main\nuses: example/action@other\n",
            '"u\\u0073es": example/action@main\nuses: example/action@other\n',
            "1: value\n",
            "uses: !custom example/action@main\n",
            "defaults: &step {uses: example/action@main}\njob:\n  <<: *step\n",
            "recursive: &loop [*loop]\n",
            "uses:\n  nested: example/action@main\n",
        )
        for workflow in cases:
            with self.subTest(workflow=workflow):
                with self.assertRaises(ValueError):
                    _workflow_uses(workflow)

    def test_workflow_is_read_only_and_has_stable_required_job(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("name: Required", workflow)
        self.assertIn(
            "needs: [check, glofas-acquisition, reuse, dependency-review]",
            workflow,
        )
        self.assertIn("GLOFAS_ACQUISITION_RESULT", workflow)
        self.assertNotIn("PR_FILE_COLLISIONS_RESULT", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("GITHUB_TOKEN", workflow)
        self.assertNotIn("check_pr_file_collisions.py", workflow)
        self.assertNotRegex(workflow, r"(?m)^\s*(?:contents|pull-requests|issues|actions):\s*write\s*$")

    def test_pr_collision_workflow_is_metadata_only_base_trusted_and_least_privilege(self) -> None:
        workflow = (ROOT / ".github/workflows/pr-file-collision.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request_target:", workflow)
        self.assertIn("permissions:\n  contents: read\n  pull-requests: read", workflow)
        self.assertIn("name: PR file collision check", workflow)
        trusted_checkout = """      - name: Checkout trusted default branch
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          ref: ${{ github.event.repository.default_branch }}
          fetch-depth: 1
          persist-credentials: false
"""
        self.assertIn(trusted_checkout, workflow)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", workflow)
        self.assertEqual(
            re.findall(r"^\s*run:\s*(.+)$", workflow, flags=re.MULTILINE),
            ["python scripts/check_pr_file_collisions.py"],
        )
        for forbidden in (
            "github.event.pull_request.head",
            "github.head_ref",
            "refs/pull/",
            "allow-unsafe-pr-checkout",
            "github.workflow_sha",
            "secrets.",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, workflow)
        self.assertNotRegex(workflow, r"(?m)^\s*(?:contents|pull-requests|issues|actions):\s*write\s*$")

    def _workflow_files(self) -> list[Path]:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", ".github/workflows"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            check=True,
        )
        paths = []
        for raw in result.stdout.split(b"\0"):
            if not raw:
                continue
            relative = Path(raw.decode("utf-8"))
            if relative.suffix.lower() in {".yml", ".yaml"}:
                paths.append(ROOT / relative)
        return sorted(paths)

    def _text_files(self) -> list[Path]:
        result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, stdout=subprocess.PIPE, check=True)
        paths = []
        for raw in result.stdout.split(b"\0"):
            if not raw:
                continue
            path = ROOT / raw.decode("utf-8")
            if path.suffix.lower() not in {".txt"} and path.name in {"LICENSE"}:
                continue
            try:
                path.read_text(encoding="utf-8")
            except UnicodeError:
                continue
            paths.append(path)
        return paths


if __name__ == "__main__":
    unittest.main()
