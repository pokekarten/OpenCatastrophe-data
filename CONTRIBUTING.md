<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Contributing

OpenCatastrophe-data welcomes public contributions to provenance, source admission, scientific clarity, interoperability, tooling, tests and documentation.

Start with `README.md`, `AGENTS.md` and `ARCHITECTURE.md`. Source/admission changes also require `DATA_LICENSING.md` and the nearest scoped `AGENTS.md`; scientific-semantic changes require `SCIENTIFIC_METHOD.md`.

## Workflow

1. Re-check current `main`, existing Issues and active Pull Requests before starting non-trivial work.
2. Open or reference the most specific Issue Form. For bounded agent work, use the Agent Task form when useful.
3. Branch from current `main`, declare shared/single-writer surfaces, and keep the change focused.
4. Open a draft Pull Request once there is a coherent first change; it is the visible implementation claim for those shared surfaces.
5. Add deterministic offline tests for durable behavior. Use the machine-readable agent-task/run-evidence contracts when formal execution or handoff evidence is useful rather than creating a second task tracker.
6. Run `python scripts/check_all.py` on the exact candidate and inspect the complete diff.
7. Address CI/review findings without weakening safety, rights, provenance or scientific gates.
8. Handoff with exact commit identity, checks, evidence, assumptions, blockers, external-byte state and the next independent action when relevant.

Accepted work is squash-merged so one accepted PR maps to one mainline commit.

## Boundaries

Never commit secrets/private endpoints, personal/customer/claims/portfolio/confidential data, proprietary model assets, restricted datasets, or material from private repositories/chats/workspaces. Public downloadability is not permission. External bytes require an explicit admission for the exact public asset scope.

Apply SPDX/REUSE metadata to repository-authored files. New direct software dependencies or workflow actions must remain minimal, publicly reviewable and recorded in `THIRD_PARTY.md` plus a GitHub-recognized dependency manifest when practical.

## Source and scientific changes

Record exact provider/product/version/query identity, authoritative rights evidence, reviewed publication scope and scientific semantics. Keep units, coordinate/reference systems, time meaning, quality flags, missingness, uncertainty and material transformations explicit. Unknown or conflicting rights stay blocked.

Use independently synthetic fixtures unless redistribution of an exact external asset has been explicitly reviewed and admitted. The `dataset-admission` and `reproducibility-run` skills under `.github/skills/` provide narrow reusable workflows; they do not grant approval or replace review.

## Security reports

Do not disclose leaked secrets, vulnerabilities or sensitive/restricted data in a public issue or PR. Follow `SECURITY.md` and use GitHub Private Vulnerability Reporting when a report cannot safely be public.
