# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/oq313-kosovo-reconstructed-run.yml")


class OQ313KosovoReconstructedWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_only_owner_issue_comment_can_reach_trusted_request_lane(self) -> None:
        text = self.text
        self.assertIn("issue_comment:", text)
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("pull_request_target:", text)
        self.assertNotIn("workflow_dispatch:", text)
        self.assertIn("github.event.issue.number == 609", text)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            text,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", text)
        self.assertIn(
            "<!-- oc-eq1-esrm20-kosovo-oq313-run-request-v1 -->",
            text,
        )

    def test_execution_is_bound_to_trusted_default_branch_sha(self) -> None:
        text = self.text
        self.assertGreaterEqual(
            text.count("ref: ${{ github.event.repository.default_branch }}"),
            2,
        )
        self.assertIn('EXECUTION_SHA="$(git rev-parse HEAD)"', text)
        self.assertIn("--execution-sha \"$EXECUTION_SHA\"", text)
        self.assertNotIn("ref: ${{ needs.validate-request.outputs.execution_sha }}", text)
        self.assertIn('test "$(git rev-parse HEAD)" = "$EXECUTION_SHA"', text)
        self.assertLess(
            text.index("Re-fence privileged checkout to validated main SHA"),
            text.index("Deduplicate trusted terminal result before external access"),
        )
        self.assertLess(
            text.index("Deduplicate trusted terminal result before external access"),
            text.index("Fetch exact ESRM20 v1.0 provider snapshot"),
        )

    def test_action_is_always_invoked_as_repository_package_module(self) -> None:
        text = self.text
        module = "-m scripts.run_esrm20_kosovo_residential_ebrisk_openquake313_action"
        self.assertEqual(text.count(module), 2)
        self.assertNotIn(
            "python scripts/run_esrm20_kosovo_residential_ebrisk_openquake313_action.py",
            text,
        )
        self.assertNotIn(
            "/repo/scripts/run_esrm20_kosovo_residential_ebrisk_openquake313_action.py",
            text,
        )

    def test_provider_and_runtime_refs_are_immutable_and_not_request_selectable(self) -> None:
        text = self.text
        self.assertIn(
            "ESRM20_COMMIT: 05f83bbc9df81d02ee8ddb1801d9d781355ce783",
            text,
        )
        self.assertIn("refs/tags/v1.0:refs/tags/v1.0", text)
        self.assertIn(
            "OQ_COMMIT: 16dd69ecea0c6dcaf49c22ca12edc9da3f024889",
            text,
        )
        self.assertIn(
            'git -C "$OQ_ROOT" fetch --depth=1 origin "$OQ_COMMIT"',
            text,
        )
        self.assertIn(
            'OBSERVED="$(git -C "$OQ_ROOT" rev-parse \'FETCH_HEAD^{commit}\')"',
            text,
        )
        self.assertIn(
            'git -C "$OQ_ROOT" checkout --detach "$OQ_COMMIT"',
            text,
        )
        self.assertIn(
            'test "$(git -C "$OQ_ROOT" rev-parse \'HEAD^{commit}\')" = "$OQ_COMMIT"',
            text,
        )
        self.assertNotIn("refs/tags/v3.13.0", text)
        self.assertNotIn("github.event.inputs", text)
        self.assertNotIn("repository_path:", text)

    def test_fixed_source_identities_are_reverified_before_derivation(self) -> None:
        text = self.text
        self.assertIn("wrapper.SOURCE_BYTE_COUNT", text)
        self.assertIn("wrapper.SOURCE_SHA256", text)
        self.assertIn("wrapper.SELECTED_BYTE_COUNT", text)
        self.assertIn("wrapper.SELECTED_SHA256", text)
        self.assertIn("cfg.GROUP1_BYTE_COUNT", text)
        self.assertIn("cfg.GROUP1_SHA256", text)
        self.assertIn("build_kosovo_residential_exposure_wrapper", text)
        self.assertIn("build_kosovo_residential_ebrisk_config", text)

    def test_exact_oq313_envelope_is_invoked_and_raw_results_are_not_uploaded(self) -> None:
        text = self.text
        self.assertIn(
            "-m scripts.run_esrm20_kosovo_residential_ebrisk_openquake313_action",
            text,
        )
        self.assertIn("--expected-issue 609", text)
        self.assertIn("--source-group1-config", text)
        self.assertIn("--runtime-identity", text)
        self.assertIn("--resolved-runtime", text)
        self.assertNotIn("actions/upload-artifact", text)
        self.assertNotIn("artifact upload", text.casefold())
        self.assertIn('"external_provider_bytes_persisted": False', text)
        self.assertIn('"publication_authorized": False', text)
        self.assertIn('"model_use_authorized": False', text)

    def test_runtime_probe_pins_dependencies_observes_oqparam_and_binds_source(self) -> None:
        text = self.text
        for name, version in {
            "h5py": "3.1.0",
            "numpy": "1.20.0",
            "pandas": "1.1.5",
            "psutil": "5.6.7",
            "pyzmq": "19.0.0",
            "scipy": "1.4.1",
            "shapely": "1.7.1",
        }.items():
            self.assertIn(f'"{name}": "{version}"', text)
        self.assertIn('sys.version_info[:2] != (3, 8)', text)
        self.assertIn("-e OQ_DISTRIBUTE=no -e OPENBLAS_NUM_THREADS=1", text)
        self.assertIn("-e PYTHONPATH=/oq-engine", text)
        self.assertIn('os.environ.get("PYTHONPATH") != "/oq-engine"', text)
        self.assertIn("import openquake.baselib as openquake_baselib", text)
        self.assertIn("from openquake.commonlib import readinput", text)
        self.assertIn('source_root = Path("/oq-engine").resolve()', text)
        self.assertIn(
            'package_root = (source_root / "openquake").resolve()',
            text,
        )
        self.assertIn('getattr(module, "__file__", None)', text)
        self.assertIn("Path(module_file).resolve().relative_to(package_root)", text)
        self.assertIn("openquake_version = openquake_baselib.__version__", text)
        self.assertIn(
            'if openquake_version != "3.13.0-git16dd69ecea":',
            text,
        )
        self.assertIn('"openquake_version": openquake_version', text)
        self.assertNotIn(
            '"openquake_version": "3.13.0-git16dd69ecea"',
            text,
        )
        self.assertIn("params = readinput.get_params(config_path)", text)
        self.assertIn("oqparam = readinput.get_oqparam(params)", text)
        self.assertIn('if "ses_seed" in params:', text)
        self.assertIn('"ses_seed": oqparam.ses_seed', text)
        self.assertIn('"concurrent_tasks": oqparam.concurrent_tasks', text)
        self.assertNotIn('"concurrent_tasks": 0', text)
        self.assertIn("multiprocessing.cpu_count() * 2", text)
        self.assertIn("docker run --rm -i --entrypoint python", text)
        self.assertLess(
            text.index("-e PYTHONPATH=/oq-engine"),
            text.index("import openquake.baselib as openquake_baselib"),
        )

    def test_exact_source_ownership_forces_single_user_mode_before_execution(self) -> None:
        text = self.text
        editable_install = "python -m pip install --no-deps -e /oq-engine"
        ownership = "chown -R openquake:openquake /oq-engine"
        owner_probe = 'if source_owner != "openquake":'
        single_user_probe = "if openquake_baselib.config.multi_user is not False:"

        self.assertIn(ownership, text)
        self.assertEqual(text.count(ownership), 1)
        self.assertIn("import pwd", text)
        self.assertIn(
            "source_owner = pwd.getpwuid(baselib_file.stat().st_uid).pw_name",
            text,
        )
        self.assertIn(owner_probe, text)
        self.assertIn(single_user_probe, text)
        self.assertLess(text.index(editable_install), text.index(ownership))
        self.assertLess(
            text.index(ownership),
            text.index("Probe pinned runtime and write OqParam-observed runtime receipts"),
        )
        self.assertLess(text.index(owner_probe), text.index(single_user_probe))
        self.assertLess(
            text.index(single_user_probe),
            text.index("openquake_version = openquake_baselib.__version__"),
        )

    def test_runtime_probe_rejects_namespace_contamination_before_submodule_imports(self) -> None:
        text = self.text
        preload_guard = 'if any(name.startswith("openquake.") for name in sys.modules):'
        top_level_import = "import openquake\n"
        pin = "openquake.__path__ = [str(package_root)]"
        submodule_import = "import openquake.baselib as openquake_baselib"

        self.assertIn(preload_guard, text)
        self.assertIn(
            'raise SystemExit("OQ3.13 OpenQuake submodule loaded before source pin")',
            text,
        )
        self.assertIn(top_level_import, text)
        self.assertIn("if not package_root.is_dir():", text)
        self.assertIn('namespace_path = getattr(openquake, "__path__", None)', text)
        self.assertIn(pin, text)
        self.assertIn(
            "[Path(path).resolve() for path in openquake.__path__] != [package_root]",
            text,
        )
        self.assertLess(text.index(preload_guard), text.index(top_level_import))
        self.assertLess(text.index(top_level_import), text.index(pin))
        self.assertLess(text.index(pin), text.index(submodule_import))

    def test_execute_job_uses_explicit_bounded_budget_above_observed_limit(self) -> None:
        text = self.text
        _, execute_section = text.split("  execute-and-publish:", 1)
        execute_header, _ = execute_section.split("    steps:", 1)

        self.assertIn("    timeout-minutes: 90", execute_header)
        self.assertNotIn("    timeout-minutes: 45", execute_header)
        self.assertEqual(execute_header.count("timeout-minutes:"), 1)
        self.assertIn("    timeout-minutes: 5", text)
        self.assertEqual(text.count("timeout-minutes:"), 2)


if __name__ == "__main__":
    unittest.main()
