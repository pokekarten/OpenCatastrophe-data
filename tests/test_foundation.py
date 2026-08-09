# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class FoundationTests(unittest.TestCase):
    def test_required_public_surfaces_exist(self):
        required = [
            'README.md','AGENTS.md','ARCHITECTURE.md','DATA_LICENSING.md','SCIENTIFIC_METHOD.md',
            'SECURITY.md','SUPPORT.md','CONTRIBUTING.md','CITATION.cff','LICENSE',
            '.github/workflows/ci.yml','.github/CODEOWNERS','.github/copilot-instructions.md',
            '.github/dependabot.yml','.github/pull_request_template.md',
            '.github/agents/data-rights-reviewer.agent.md',
            '.github/skills/dataset-admission/SKILL.md','.github/skills/reproducibility-run/SKILL.md',
        ]
        for rel in required:
            self.assertTrue((ROOT/rel).is_file(), rel)

    def test_ci_is_read_only_and_fail_closed(self):
        text=(ROOT/'.github/workflows/ci.yml').read_text()
        self.assertIn('permissions:\n  contents: read', text)
        self.assertIn('persist-credentials: false', text)
        self.assertNotIn('pull_request_target', text)
        self.assertRegex(text, r'actions/checkout@[0-9a-f]{40}')
        self.assertRegex(text, r'actions/setup-python@[0-9a-f]{40}')
        self.assertIn('name: Required', text)

    def test_issue_forms_disable_blank_and_warn_about_sensitive_data(self):
        config=(ROOT/'.github/ISSUE_TEMPLATE/config.yml').read_text()
        self.assertIn('blank_issues_enabled: false', config)
        forms=list((ROOT/'.github/ISSUE_TEMPLATE').glob('*.yml'))
        self.assertGreaterEqual(len(forms), 5)
        for form in forms:
            if form.name == 'config.yml':
                continue
            text=form.read_text().lower()
            self.assertIn('public', text)
            self.assertIn('claims', text)
            self.assertIn('restricted dataset', text)

    def test_agent_boundary_is_provider_neutral(self):
        agents=(ROOT/'AGENTS.md').read_text().lower()
        self.assertIn('public repository state', agents)
        self.assertIn('not agent-ready', agents)
        readme=(ROOT/'README.md').read_text().lower()
        self.assertIn('ai agents', readme)
        self.assertIn('scientists', readme)
        self.assertIn('insurers', readme)

if __name__ == '__main__':
    unittest.main()
