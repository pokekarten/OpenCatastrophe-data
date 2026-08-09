---
name: dataset-admission
description: Review an external source through fail-closed rights, privacy, provenance and exact-scope admission gates.
license: Apache-2.0
---
<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Dataset admission

Use this workflow for a new or changed external-data admission.

1. Re-ground on current public `main`, the relevant Issue/PR, root `AGENTS.md`, `DATA_LICENSING.md`, `SCIENTIFIC_METHOD.md`, and `manifests/AGENTS.md`.
2. Record the exact provider, product, version/release/query, intended modelling role, and authoritative current product/licence/terms evidence.
3. Evaluate access, commercial use, redistribution, attribution/derivative obligations, privacy/confidentiality, and scientific fitness separately. Public availability is not permission.
4. Keep the source-rights ceiling separate from the narrower OpenCatastrophe review scope. Unknown, stale, contradictory, bespoke-uncertain, or restricted rights remain blocked.
5. Start metadata-only. Do not acquire or commit source bytes merely because metadata review succeeds. If bytes are later authorized, acquire them outside Git and record exact retrieval evidence, byte count, SHA-256, and a non-secret logical identity.
6. Update the manifest and durable source review together when an accepted admission changes. Preserve units, CRS, time semantics, quality state, missingness, coverage, uncertainty, and material transformations.
7. Validate the manifest, check deterministic identity when relevant, run `python scripts/check_all.py`, and report admission state before/after, evidence, external-byte state, limitations, and blockers.

An agent may structure evidence and identify inconsistencies; it must not turn legal/scientific ambiguity into approval.