# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.openquake_source_model_logic_tree_dependencies import (
    LogicTreeDependencyOrigin,
    OpenQuakeLogicTreeError,
    SourceModelDependency,
    extract_source_model_logic_tree_dependencies,
)

TREE = "oq/config/source_model_logic_tree.xml"


def wrap(branch_sets: str, *, namespace: str = "http://openquake.org/xmlns/nrml/0.5") -> str:
    return (
        f'<nrml xmlns="{namespace}"><logicTree logicTreeID="lt">'
        f"{branch_sets}</logicTree></nrml>"
    )


def branch_set(
    uncertainty_type: str,
    branches: tuple[tuple[str, str], ...],
    *,
    branch_set_id: str = "bs",
) -> str:
    rendered = "".join(
        f'<logicTreeBranch branchID="{branch_id}">'
        f"<uncertaintyModel>{model}</uncertaintyModel>"
        f"<uncertaintyWeight>1</uncertaintyWeight>"
        f"</logicTreeBranch>"
        for branch_id, model in branches
    )
    return (
        f'<logicTreeBranchSet branchSetID="{branch_set_id}" '
        f'uncertaintyType="{uncertainty_type}">{rendered}</logicTreeBranchSet>'
    )


class OpenQuakeSourceModelLogicTreeDependencyTests(unittest.TestCase):
    def test_source_model_extend_model_and_ignored_types(self) -> None:
        xml = wrap(
            branch_set(
                "sourceModel",
                (("b2", "sources/a.xml sources/b.xml"),),
                branch_set_id="a",
            )
            + branch_set(
                "gmpeModel", (("ignored", "gsim.xml"),), branch_set_id="g"
            )
            + branch_set(
                "extendModel", (("b1", "../shared/c.xml"),), branch_set_id="e"
            )
        )
        result = extract_source_model_logic_tree_dependencies(
            xml, logic_tree_path=TREE
        )
        self.assertEqual(
            result,
            (
                SourceModelDependency(
                    "oq/config/sources/a.xml",
                    (LogicTreeDependencyOrigin("sourceModel", "b2"),),
                ),
                SourceModelDependency(
                    "oq/config/sources/b.xml",
                    (LogicTreeDependencyOrigin("sourceModel", "b2"),),
                ),
                SourceModelDependency(
                    "oq/shared/c.xml",
                    (LogicTreeDependencyOrigin("extendModel", "b1"),),
                ),
            ),
        )

    def test_same_basename_hdf5_is_inventory_dependent(self) -> None:
        xml = wrap(branch_set("sourceModel", (("b1", "sources/a.xml"),)))
        absent = extract_source_model_logic_tree_dependencies(
            xml,
            logic_tree_path=TREE,
            repository_inventory=("oq/config/sources/a.xml",),
        )
        present = extract_source_model_logic_tree_dependencies(
            xml,
            logic_tree_path=TREE,
            repository_inventory=(
                "oq/config/sources/a.hdf5",
                "oq/config/sources/a.xml",
            ),
        )
        self.assertEqual(len(absent), 1)
        self.assertEqual(
            [item.resolved_path for item in present],
            ["oq/config/sources/a.hdf5", "oq/config/sources/a.xml"],
        )
        companion = next(item for item in present if item.is_hdf5_companion)
        self.assertEqual(
            companion.origins,
            (LogicTreeDependencyOrigin("sourceModel", "b1"),),
        )

    def test_extensionless_source_still_emits_inventory_hdf5_companion(self) -> None:
        xml = wrap(branch_set("sourceModel", (("b1", "sources/model"),)))
        result = extract_source_model_logic_tree_dependencies(
            xml,
            logic_tree_path=TREE,
            repository_inventory=("oq/config/sources/model.hdf5",),
        )
        self.assertEqual(
            [item.resolved_path for item in result],
            ["oq/config/sources/model", "oq/config/sources/model.hdf5"],
        )
        companion = next(item for item in result if item.is_hdf5_companion)
        self.assertEqual(
            companion.origins,
            (LogicTreeDependencyOrigin("sourceModel", "b1"),),
        )

    def test_dependency_and_inventory_order_do_not_affect_output(self) -> None:
        first = wrap(
            branch_set(
                "sourceModel",
                (("b2", "b.xml"), ("b1", "a.xml")),
                branch_set_id="one",
            )
        )
        second = wrap(
            branch_set(
                "sourceModel",
                (("b1", "a.xml"), ("b2", "b.xml")),
                branch_set_id="one",
            )
        )
        inv_a = ("oq/config/b.hdf5", "oq/config/a.hdf5")
        inv_b = tuple(reversed(inv_a))
        self.assertEqual(
            extract_source_model_logic_tree_dependencies(
                first, logic_tree_path=TREE, repository_inventory=inv_a
            ),
            extract_source_model_logic_tree_dependencies(
                second, logic_tree_path=TREE, repository_inventory=inv_b
            ),
        )

    def test_legacy_branching_level_shape_is_supported(self) -> None:
        nested = branch_set("sourceModel", (("b1", "a.xml"),))
        xml = wrap(
            '<logicTreeBranchingLevel branchingLevelID="bl1">'
            f"{nested}"
            "</logicTreeBranchingLevel>"
        )
        result = extract_source_model_logic_tree_dependencies(xml, logic_tree_path=TREE)
        self.assertEqual([item.resolved_path for item in result], ["oq/config/a.xml"])

    def test_non_nrml_or_out_of_structure_branch_sets_fail_closed(self) -> None:
        relevant = branch_set("sourceModel", (("b1", "a.xml"),))
        cases = (
            f"<foo><logicTree>{relevant}</logicTree></foo>",
            f"<nrml>{relevant}</nrml>",
            f"<nrml><wrapper><logicTree>{relevant}</logicTree></wrapper></nrml>",
            f"<nrml><logicTree><wrapper>{relevant}</wrapper></logicTree></nrml>",
            f"<nrml><logicTree>{relevant}</logicTree>{relevant}</nrml>",
        )
        for xml in cases:
            with self.subTest(xml=xml):
                with self.assertRaises(OpenQuakeLogicTreeError):
                    extract_source_model_logic_tree_dependencies(
                        xml, logic_tree_path=TREE
                    )

    def test_branch_set_requires_uncertainty_type(self) -> None:
        xml = wrap(
            '<logicTreeBranchSet branchSetID="missing-type">'
            '<logicTreeBranch branchID="b1">'
            '<uncertaintyModel>a.xml</uncertaintyModel>'
            '<uncertaintyWeight>1</uncertaintyWeight>'
            '</logicTreeBranch>'
            '</logicTreeBranchSet>'
        )
        with self.assertRaisesRegex(OpenQuakeLogicTreeError, "uncertaintyType"):
            extract_source_model_logic_tree_dependencies(xml, logic_tree_path=TREE)

    def test_relevant_branch_set_rejects_unexpected_direct_child(self) -> None:
        xml = wrap(
            '<logicTreeBranchSet uncertaintyType="sourceModel">'
            '<logicTreeBranch branchID="b1">'
            '<uncertaintyModel>a.xml</uncertaintyModel>'
            '</logicTreeBranch>'
            '<unexpected />'
            '</logicTreeBranchSet>'
        )
        with self.assertRaisesRegex(OpenQuakeLogicTreeError, "unsupported direct child"):
            extract_source_model_logic_tree_dependencies(xml, logic_tree_path=TREE)

    def test_legacy_branching_level_rejects_multiple_branch_sets(self) -> None:
        first = branch_set("sourceModel", (("b1", "a.xml"),), branch_set_id="one")
        second = branch_set("extendModel", (("b2", "b.xml"),), branch_set_id="two")
        xml = wrap(
            '<logicTreeBranchingLevel branchingLevelID="bl1">'
            f"{first}{second}"
            '</logicTreeBranchingLevel>'
        )
        with self.assertRaisesRegex(OpenQuakeLogicTreeError, "exactly one direct"):
            extract_source_model_logic_tree_dependencies(xml, logic_tree_path=TREE)

    def test_duplicate_raw_and_normalized_dependencies_fail_closed(self) -> None:
        duplicate = wrap(branch_set("sourceModel", (("b1", "a.xml a.xml"),)))
        with self.assertRaisesRegex(OpenQuakeLogicTreeError, "duplicate dependency"):
            extract_source_model_logic_tree_dependencies(
                duplicate, logic_tree_path=TREE
            )

        normalized = wrap(
            branch_set(
                "sourceModel",
                (("b1", "sources/a.xml sources/../sources/a.xml"),),
            )
        )
        with self.assertRaisesRegex(
            OpenQuakeLogicTreeError, "normalize to the same path"
        ):
            extract_source_model_logic_tree_dependencies(
                normalized, logic_tree_path=TREE
            )

    def test_duplicate_branch_ids_fail_closed(self) -> None:
        xml = wrap(
            branch_set("sourceModel", (("dup", "a.xml"),), branch_set_id="one")
            + branch_set("extendModel", (("dup", "b.xml"),), branch_set_id="two")
        )
        with self.assertRaisesRegex(OpenQuakeLogicTreeError, "duplicate branchID"):
            extract_source_model_logic_tree_dependencies(xml, logic_tree_path=TREE)

    def test_unsafe_paths_and_noncanonical_inventory_fail_closed(self) -> None:
        bad_paths = (
            "../../../../../escape.xml",
            "https://example.test/a.xml",
            r"C:\a.xml",
            "a.xml?download=1",
            "a.xml#fragment",
        )
        for raw in bad_paths:
            with self.subTest(raw=raw):
                xml = wrap(branch_set("sourceModel", (("b1", raw),)))
                with self.assertRaises(OpenQuakeLogicTreeError):
                    extract_source_model_logic_tree_dependencies(
                        xml, logic_tree_path=TREE
                    )

        xml = wrap(branch_set("sourceModel", (("b1", "a.xml"),)))
        with self.assertRaisesRegex(OpenQuakeLogicTreeError, "already be canonical"):
            extract_source_model_logic_tree_dependencies(
                xml,
                logic_tree_path=TREE,
                repository_inventory=("oq/config/x/../a.hdf5",),
            )
        with self.assertRaisesRegex(
            OpenQuakeLogicTreeError, "duplicate repository inventory"
        ):
            extract_source_model_logic_tree_dependencies(
                xml,
                logic_tree_path=TREE,
                repository_inventory=("oq/config/a.xml", "oq/config/a.xml"),
            )

    def test_malformed_dtd_entity_and_ambiguous_models_fail_closed(self) -> None:
        with self.assertRaisesRegex(OpenQuakeLogicTreeError, "invalid logic-tree XML"):
            extract_source_model_logic_tree_dependencies(
                "<nrml>", logic_tree_path=TREE
            )
        for xml in (
            '<!DOCTYPE nrml [<!ENTITY x "a.xml">]><nrml/>',
            '<!ENTITY x "a.xml"><nrml/>',
        ):
            with self.assertRaisesRegex(OpenQuakeLogicTreeError, "DTD and entity"):
                extract_source_model_logic_tree_dependencies(
                    xml, logic_tree_path=TREE
                )

        missing = wrap(
            '<logicTreeBranchSet uncertaintyType="sourceModel">'
            '<logicTreeBranch branchID="b1"></logicTreeBranch>'
            "</logicTreeBranchSet>"
        )
        with self.assertRaisesRegex(OpenQuakeLogicTreeError, "exactly one"):
            extract_source_model_logic_tree_dependencies(
                missing, logic_tree_path=TREE
            )

        multiple = wrap(
            '<logicTreeBranchSet uncertaintyType="sourceModel">'
            '<logicTreeBranch branchID="b1">'
            "<uncertaintyModel>a.xml</uncertaintyModel>"
            "<uncertaintyModel>b.xml</uncertaintyModel>"
            "</logicTreeBranch></logicTreeBranchSet>"
        )
        with self.assertRaisesRegex(OpenQuakeLogicTreeError, "exactly one"):
            extract_source_model_logic_tree_dependencies(
                multiple, logic_tree_path=TREE
            )

    def test_namespace_variation_and_shared_dependency_provenance(self) -> None:
        xml = wrap(
            branch_set("sourceModel", (("b1", "a.xml"),), branch_set_id="one")
            + branch_set("extendModel", (("b2", "a.xml"),), branch_set_id="two"),
            namespace="urn:synthetic:nrml",
        )
        result = extract_source_model_logic_tree_dependencies(
            xml, logic_tree_path=TREE
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].resolved_path, "oq/config/a.xml")
        self.assertEqual(
            result[0].origins,
            (
                LogicTreeDependencyOrigin("extendModel", "b2"),
                LogicTreeDependencyOrigin("sourceModel", "b1"),
            ),
        )

    def test_empty_relevant_branch_set_and_bad_branch_id_fail_closed(self) -> None:
        empty = wrap(
            '<logicTreeBranchSet uncertaintyType="sourceModel"></logicTreeBranchSet>'
        )
        with self.assertRaisesRegex(OpenQuakeLogicTreeError, "at least one"):
            extract_source_model_logic_tree_dependencies(empty, logic_tree_path=TREE)

        no_id = wrap(
            '<logicTreeBranchSet uncertaintyType="sourceModel">'
            '<logicTreeBranch><uncertaintyModel>a.xml</uncertaintyModel></logicTreeBranch>'
            "</logicTreeBranchSet>"
        )
        with self.assertRaisesRegex(OpenQuakeLogicTreeError, "branchID"):
            extract_source_model_logic_tree_dependencies(no_id, logic_tree_path=TREE)


if __name__ == "__main__":
    unittest.main()
