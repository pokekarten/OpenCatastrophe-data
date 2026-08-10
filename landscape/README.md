<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source landscape

`landscape/` is the broad, non-admission discovery registry for public data sources that may be useful to catastrophe-risk research, modelling, validation or interoperability.

A landscape entry means only: **the source exists, an authoritative public source page was checked, and the source looks potentially relevant enough to preserve for future evaluation.**

It does **not** mean that OpenCatastrophe has approved the source's data rights, scientific fitness, redistribution scope, commercial-use conditions, exact version, exact variables, or use in any model.

## Canonical JSON and human-readable Markdown

`landscape/sources*.json` files are the **only canonical source-landscape records**. Each canonical JSON shard has a paired `sources*.md` file generated deterministically by `scripts/render_public_views.py` so the same candidate metadata is easy to inspect on GitHub by people while remaining directly consumable by programs and AI agents.

Generated Markdown is not independently editable and cannot change meaning. Every generated file names its canonical JSON source and carries `GENERATED FILE — DO NOT EDIT DIRECTLY`.

When changing landscape data:

```bash
python scripts/render_public_views.py --write
python scripts/check_all.py
```

CI runs `python scripts/render_public_views.py --check` through the repository definition-of-done gate and fails if a paired Markdown view is missing, stale, manually changed or orphaned. CI checks parity; it never writes or commits a repair.

This pattern is intentionally extensible to future machine/interoperability views, but any additional representation must identify its canonical source and have a deterministic drift check. Do not add an independently maintained JSON/YAML/CSV/Markdown copy of the same landscape facts.

## Two registry levels

- `landscape/sources*.json` — broad discovery layer and canonical machine-readable source. The registry may be split into thematic shards so independent contributors can add bounded source families without turning one large JSON file into a permanent single-writer surface. Entries may exist without a current model consumer and always remain `admission_status: not_admitted` until promoted through the accepted review path. Paired `sources*.md` files are generated human-readable views only.
- `manifests/` plus `docs/source-reviews/` — accepted layer. Manifests are the machine-readable admission records; source reviews are durable human-readable rights/scientific evidence. These are the only accepted admissions/evidence and have a different purpose from the broad landscape.

The landscape must never be interpreted as an allow-list for downloads, redistribution or model use.

## What belongs in the landscape

A candidate should have:

- a canonical provider/product identity as far as currently known;
- at least one authoritative public provider or programme URL;
- a bounded description of spatial/temporal scope and granularity when available;
- one or more plausible catastrophe-risk roles;
- explicit `not_reviewed` rights and scientific states unless those reviews have actually been completed through the accepted process;
- no external dataset bytes.

Useful source families include observations, reanalysis, event catalogues, terrain, bathymetry, hydrology, soils, land cover, population, built environment, infrastructure, vulnerability context, historical impacts and independent validation data.

## Promotion to accepted

Promotion is separate from discovery. A candidate moves into `manifests/` only when there is a bounded current role and the normal admission gates are met: exact source/version/query identity, authoritative rights evidence, scientific semantics, review scope and any required validation design.

A source can therefore be valuable enough to remain in the landscape indefinitely without ever becoming an accepted OpenCatastrophe input.

## Maintenance

Keep canonical JSON entries compact. Prefer updating an existing candidate over adding duplicate records for aliases or mirrors. When a provider replaces a product, preserve the old product when scientifically useful and add the successor separately rather than silently rewriting historical identity.

Use a new thematic `sources-*.json` shard when a bounded source family can be maintained independently. Every shard uses the same registry header and entry shape, and `tests/test_source_landscape.py` enforces globally unique candidate IDs plus the fail-closed non-admission/review state across all shards. The paired Markdown file is generated automatically from that shard; do not hand-maintain a second candidate index or duplicate candidate records merely for navigation.

Candidate research should not duplicate full source reviews. Detailed rights/scientific acceptance evidence belongs in `docs/source-reviews/` only when admission is actually being considered.
