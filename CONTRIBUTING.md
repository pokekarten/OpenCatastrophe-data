<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Contributing

OpenCatastrophe-data welcomes public contributions to provenance, source admission, scientific clarity, interoperability, tooling, tests and documentation.

Start with `README.md`, `AGENTS.md` and `ARCHITECTURE.md`. Source/admission changes also require `DATA_LICENSING.md`; scientific-semantic changes require `SCIENTIFIC_METHOD.md`.

## Workflow

1. Re-check current `main`, active Pull Requests and any enabled public Issues before starting non-trivial work.
2. When Issues are enabled, open or reference the most specific Issue Form; for bounded agent work, use the Agent Task form when useful. When Issues are disabled, do not create a substitute task tracker: use a draft Pull Request as the durable public work claim once the change has enough public evidence and a coherent first diff.
3. Create a short-lived branch from current `main`, declare shared/single-writer surfaces, and keep the change focused. `main` is the only persistent development branch; do not maintain long-lived agent, development, release or patch branches.
4. Open a draft Pull Request once there is a coherent first change; it is the visible implementation claim for those shared surfaces.
5. Add deterministic offline tests for durable behavior. Use the machine-readable agent-task/run-evidence contracts when formal execution or handoff evidence is useful rather than creating a second task tracker.
6. If a canonical machine-readable source has a committed generated view, change the canonical source first and run `python scripts/render_public_views.py --write`. Commit both together; never hand-edit files marked `GENERATED FILE — DO NOT EDIT DIRECTLY`.
7. Run `python scripts/check_all.py` on the exact candidate and inspect the complete diff.
8. Address CI/review findings without weakening safety, rights, provenance or scientific gates.
9. Handoff with exact commit identity, checks, evidence, assumptions, blockers, external-byte state and the next independent action when relevant.
10. Delete the head branch after its Pull Request is merged or closed unless it is still the active head of another open Pull Request.

Accepted work is squash-merged so one accepted PR maps to one mainline commit. Topic branches are disposable collaboration state, not durable project records; accepted history lives on `main` and review history lives in Pull Requests plus public Issues when enabled.

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
