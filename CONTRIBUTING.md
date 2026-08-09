<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Contributing

OpenCatastrophe-data welcomes public contributions to provenance, source admission, scientific clarity, interoperability, tooling, tests and documentation.

Start with `README.md`, `AGENTS.md` and `ARCHITECTURE.md`. Source/admission changes also require `DATA_LICENSING.md`; scientific-semantic changes require `SCIENTIFIC_METHOD.md`.

## Workflow

1. Search existing Issues and Pull Requests.
2. For non-trivial work, open or reference the most specific Issue Form.
3. Branch from current `main` and keep the change focused.
4. Add deterministic offline tests for durable behavior.
5. Run `python scripts/check_all.py` and inspect the complete diff.
6. Open a Pull Request using the template and link the relevant issue when applicable.
7. Address CI/review findings without weakening safety, rights, provenance or scientific gates.

Accepted work is squash-merged so one accepted PR maps to one mainline commit.

## Boundaries

Never commit secrets/private endpoints, personal/customer/claims/portfolio/confidential data, proprietary model assets, restricted datasets, or material from private repositories/chats/workspaces. Public downloadability is not permission. External bytes require an explicit admission for the exact public asset scope.

Apply SPDX/REUSE metadata to repository-authored files. New direct software dependencies or workflow actions must remain minimal, publicly reviewable and recorded in `THIRD_PARTY.md` plus a GitHub-recognized dependency manifest when practical.

## Source and scientific changes

Record exact provider/product/version/query identity, authoritative rights evidence, reviewed publication scope and scientific semantics. Keep units, coordinate/reference systems, time meaning, quality flags, missingness, uncertainty and material transformations explicit. Unknown or conflicting rights stay blocked.

Use independently synthetic fixtures unless redistribution of an exact external asset has been explicitly reviewed and admitted.

## Security reports

Do not disclose leaked secrets, vulnerabilities or sensitive/restricted data in a public issue or PR. Follow `SECURITY.md` and use GitHub Private Vulnerability Reporting when a report cannot safely be public.
