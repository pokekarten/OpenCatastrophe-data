<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source landscape

`landscape/` is the broad, non-admission discovery registry for public data sources that may be useful to catastrophe-risk research, modelling, validation or interoperability.

A landscape entry means only: **the source exists, an authoritative public source page was checked, and the source looks potentially relevant enough to preserve for future evaluation.**

It does **not** mean that OpenCatastrophe has approved the source's data rights, scientific fitness, redistribution scope, commercial-use conditions, exact version, exact variables, or use in any model.

## Two registry levels

- `landscape/sources.json` — broad discovery layer. Entries may exist without a current model consumer. Every entry remains `admission_status: not_admitted` until promoted through the accepted review path.
- `manifests/` plus `docs/source-reviews/` — accepted layer. These are the only machine-readable admissions and durable source-specific acceptance evidence.

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

Keep entries compact. Prefer updating an existing candidate over adding duplicate records for aliases or mirrors. When a provider replaces a product, preserve the old product when scientifically useful and add the successor separately rather than silently rewriting historical identity.

Candidate research should not duplicate full source reviews. Detailed rights/scientific acceptance evidence belongs in `docs/source-reviews/` only when admission is actually being considered.
