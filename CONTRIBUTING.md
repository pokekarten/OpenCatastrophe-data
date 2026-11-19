<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Contributing

OpenCatastrophe-data welcomes public contributions to provenance, source admission, scientific clarity, interoperability, tooling, tests and documentation.

Start with `README.md`, `AGENTS.md` and `ARCHITECTURE.md`. Source/admission changes also require `DATA_LICENSING.md`; scientific-semantic changes require `SCIENTIFIC_METHOD.md`.

## Workflow

The proportional-risk and source-safety rules in `AGENTS.md` are authoritative. **A routine, bounded, reversible fix does not need a new Issue, Draft PR, separate agent roles or a handoff artifact merely to satisfy a process checklist.**

1. Check the current `main`, relevant open Issues and Pull Requests, and changed-file/semantic overlap before starting. If another PR owns the same source contract or file, collaborate or take an independent task.
2. For small non-colliding fixes, work directly on a short-lived topic branch with a clear PR description and executable evidence. Create/reference an Issue for material scientific, rights, security or shared-contract decisions, long-running collaboration, or a genuine multi-writer collision. Use the Agent Task Issue form **when it helps coordinate such a task**, not by default.
3. Keep implementation changes bounded. A Draft PR is useful for unfinished scientific/source work or coordination, but is **not** obligatory for a reversible, fully tested routine change. Only claim work that is actually done; no reviewer/agent identity may be invented.
4. Update the **canonical** JSON/manifest source first, regenerate paired Markdown views with `python scripts/render_public_views.py --write`, and never edit generated projections as a second authority.
5. Add synthetic, offline and negative tests for durable behavior. Check the exact diff, run focused tests and `python scripts/check_all.py` where repository-wide contracts or scientific guards are affected. Retain exact-head CI evidence when it runs.
6. For source/admission/scientific work, keep the exact provider/product/version, current rights, source-byte state, scientific assumptions, uncertainty and remaining blockers explicit. Incomplete original-source verification never becomes model admission merely because synthetic CI passes.
7. Request independent review/challenge **when the risk warrants it** (scientific conclusions, rights, security, data admission, high-impact architecture). Document pending or unavailable reviews truthfully; do not treat self-review as independent. Maintain explicit blocking decisions for unresolved material risk.
8. Squash-merge completed, reviewed changes and retire their disposable branches. Keep unfinished work on the relevant PR/Issue with the smallest concrete next action rather than creating extra tracking systems.

When Issues are disabled, use an ordinary PR; do not create a substitute task database. Existing Issues and historical source receipts remain valuable records even when a newer, smaller PR replaces implementation code.

## Review quality

Use the smallest justified review tier from `AGENTS.md`: routine fixes rely on transparent diff and real CI/test evidence; high-impact rights, science, security and admission decisions require independently challenged claims where material. **No role, approval or exception may be represented as completed unless it really occurred.** A GitHub-green synthetic test does not establish real original-source truth, licence permission or scientific model admission.

## Canonical and generated representations

Use one independently editable source for one set of facts. Structured facts should normally live in a versioned machine-readable contract; human or interoperability views should be deterministic projections from that contract when they repeat the same semantics.

For the source landscape, `landscape/sources*.json` is canonical and the paired `landscape/sources*.md` files are generated human views. `python scripts/render_public_views.py --check` verifies byte-for-byte parity and rejects missing, stale or orphaned generated views. Narrative documents such as scientific/source-review reasoning remain human-authored; do not force narrative evidence into JSON merely to create symmetry.

Before adding YAML, JSONL, CSV, STAC, RDLS, Oasis or another representation, state which existing contract is canonical, whether the projection is lossless or intentionally scoped, and how CI proves it cannot silently drift. Do not introduce two independently editable files that claim authority over the same fields.

## Boundaries

Never commit secrets/private endpoints, personal/customer/claims/portfolio/confidential data, proprietary model assets, restricted datasets, or material from private repositories/chats/workspaces. Public downloadability is not permission. External bytes require an explicit admission for the exact public asset scope.

Apply SPDX/REUSE metadata to repository-authored files. New direct software dependencies or workflow actions must remain minimal, publicly reviewable and recorded in `THIRD_PARTY.md` plus a GitHub-recognized dependency manifest when practical.

## Source and scientific changes

Record exact provider/product/version/query identity, authoritative rights evidence, reviewed publication scope and scientific semantics. Keep units, coordinate/reference systems, time meaning, quality flags, missingness, uncertainty and material transformations explicit. Unknown or conflicting rights stay blocked.

Use independently synthetic fixtures unless redistribution of an exact external asset has been explicitly reviewed and admitted.

## Security reports

Do not disclose leaked secrets, vulnerabilities or sensitive/restricted data in a public issue or PR. Follow `SECURITY.md` and use GitHub Private Vulnerability Reporting when a report cannot safely be public.
