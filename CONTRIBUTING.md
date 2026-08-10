<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Contributing

OpenCatastrophe-data welcomes public contributions to provenance, source admission, scientific clarity, interoperability, tooling, tests and documentation.

Start with `README.md`, `AGENTS.md` and `ARCHITECTURE.md`. Source/admission changes also require `DATA_LICENSING.md`; scientific-semantic changes require `SCIENTIFIC_METHOD.md`.

## Workflow

1. Re-check current `main`, active Pull Requests and public Issues before starting non-trivial work.
2. When Issues are enabled, open or reference the most specific Issue Form **before material edits**. For bounded AI-agent work, use the Agent Task form. One non-trivial task should have one primary Issue that declares its outcome, exact write/shared surfaces, non-goals, dependencies, acceptance criteria and hard stop.
3. Check the declared and actual surfaces of active Issues and Pull Requests for overlap. If another writer owns the same file, canonical/generated pair, schema, manifest/admission rule, CI policy or semantic contract, coordinate on that task or choose independent work rather than creating a competing branch.
4. Create a short-lived branch from current `main`; for agent work prefer `agent/<issue-number>-<slug>`. `main` is the only persistent development branch; do not maintain long-lived agent, development, release or patch branches.
5. Open a draft Pull Request once there is a coherent first change. The draft PR is the visible write claim. Give it one primary Issue (`Closes #N` when merge completes the task, otherwise `Refs #N`) and repeat the exact write/shared surfaces in the PR body.
6. Keep the PR inside the primary Issue's declared scope. If the work reveals an independent improvement, bug, research question or cleanup task, create a new linked Agent Task Issue with `Follow-up to #N`, record any dependency and smallest `next_action`, and continue the current PR without silently absorbing that work.
7. A subsequent agent may claim a ready follow-up by assignment when available and/or by opening its own issue-scoped draft PR after re-checking current `main`, open Issues and open PRs. Chat messages, local notes and comments alone are not durable write claims.
8. Add deterministic offline tests for durable behavior. Use the machine-readable agent-task/run-evidence contracts when formal execution or handoff evidence is useful rather than creating a second task tracker.
9. If a canonical machine-readable source has a committed generated view, change the canonical source first and run `python scripts/render_public_views.py --write`. Commit both together; never hand-edit files marked `GENERATED FILE — DO NOT EDIT DIRECTLY`.
10. Run `python scripts/check_all.py` on the exact candidate and inspect the complete diff.
11. Address CI/review findings without weakening safety, rights, provenance or scientific gates.
12. Before requesting review or stopping, hand off with exact head commit, checks, evidence, assumptions, blockers, external-byte state, changed/shared surfaces and all linked follow-up Issues. If incomplete, make the next independent action explicit in the primary Issue.
13. Delete the head branch after its Pull Request is merged or closed unless it is still the active head of another open Pull Request.

When repository Issues are temporarily disabled, do not create a substitute task database: use a draft Pull Request as the durable public work claim once the change has enough public evidence and a coherent first diff. Record `Issues unavailable` in the PR's primary-task field. The normal issue-first multi-agent protocol is only active after Issues are enabled.

Accepted work is squash-merged so one accepted PR maps to one mainline commit. Topic branches are disposable collaboration state, not durable project records; accepted history lives on `main` and review history lives in Pull Requests plus public Issues when enabled.

## Review quality

`AGENTS.md` is the single detailed authority for the risk-tiered Builder/Reviewer/Challenger protocol. Contributors should choose the smallest justified tier and record the required review evidence in the Pull Request template. Independent roles are quality-control roles rather than competing writers, and shared GitHub accounts use distinct agent/run IDs. If an independent role is unavailable, record that truthfully and follow the exception/maintainer-decision rule in `AGENTS.md`; never fabricate independence to satisfy a checkbox.

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
