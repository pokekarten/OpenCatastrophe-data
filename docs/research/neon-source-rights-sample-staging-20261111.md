<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Insurance Neon source rights and bounded sample staging — 2026-11-11

## Scope and actual evidence

The public repository is the canonical source for research source identities. Its fixed-commit source-register audit was executed separately on GitHub Actions:
- [All-source and reviewed API workflow](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43070500887), SHA `a40bd05987169aa3594274eff9771a8627276aeb`: **707** source records audited (**692** landscape candidates in **107** JSON shards; **15** existing admitted manifests) and **68** source-access contracts validated.
- **11/11** explicitly reviewed, bounded, anonymous live probe jobs completed successfully. These are provider-specific capabilities, **not** blanket commercial-use, sample-download or model-admission approvals.
- The completed per-record JSON artifact is available in the workflow (artifact `all-source-coverage-audit`).

The separate insurance Neon database `insurance-risk-core` (not the Pokémon database) now includes the following **research-only** objects:

| Neon relation | Purpose |
| --- | --- |
| `research.source_candidate_review_v0` | All **692** canonical candidate records and their original notes, provider, authoritative URL, access hints, source-revision date, and unmodified `rights_review_status=not_reviewed` provenance |
| `research.source_sample_v0` | Narrow, provenance-bound sample rows: source URL, received provider SHA-256, extracted sample SHA-256, license evidence, exact scope, UTC retrieval, no CAT-model admission |
| `research.source_candidate_triage_v0` | Conservative first-pass **signals**, not legal decisions: restrictions/gates, possible open-license citations, or no evidence |
| `research.all_source_inventory_v0` | 692 research candidates + 15 existing manifest records, retaining distinct record types |

These tables **do not** change `registry.source_record`, source manifests, prior legal decisions, or CAT-model input approvals. A DB-level stored sample is not a Git/raw-data release or evidence of a scientifically calibrated hazard/exposure/financial loss.

## Current conservative triage

| Status | Count | Interpretation |
| --- | ---: | --- |
| No clear license signal | 520 | Find original-provider terms, exact version, dataset and API/service rights |
| Possible open-license signal | 126 | Existing source notes mention a license; independently verify original terms and third-party layers |
| Restrictions or access-gate signal | 43 | Treat as blocked for new samples until the exact gate is resolved |
| Source-scoped commercial reuse independently verified | 3 | GFZ Kp, GDW v1.0, USGS 3DEP; attribution/terms and asset scope still apply |

This view gives **692/692** records a queue category, not **692 approved licenses**. Unknown or incompatible rights never default to commercial approval. `commercial_reuse_verdict=allowed_verified` is currently restricted to three exact products.

## Initial six original-provider samples written to Neon (no provider bytes in Git)

| Source / research-only sample | Scoped license and evidence | Original response SHA-256 |
| --- | --- | --- |
| GFZ definitive Kp, 2024-01-01, eight 3-hour values | [GFZ source CC BY 4.0](https://kp.gfz.de/) | `f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a` |
| geoBoundaries **DEU ADM1** metadata, 16 units | [German Data Licence BY 2.0](https://www.govdata.de/dl-de/by-2-0); Germany-specific, **not** blanket worldwide gbOpen clearance | `65af06f80e837028997c396d2c67d74fb1e1752d884e9a0638d5c736ee8c345a` |
| NOAA CO-OPS San Francisco station 9414290, 2026-01-01, first six water-level values, GMT and MLLW metres | [NOAA general reuse caveats](https://www.noaa.gov/office-education/outreach-communication/faq) and [CO-OPS API limits](https://www.tidesandcurrents.noaa.gov/web_services_info.html); no implied official validation | `3ae940b4f9632b1e37fec1009381f85e38fa961a4cea04dc21a1939ca47ae295` |
| STORM IBTrACS v4 **DataCite DOI metadata only** | [DataCite CC0 metadata policy](https://support.datacite.org/docs/datacite-data-file-use-policy) **does not cover linked original storm-track files** | `90bbb620c7e04632e45b5c86c2998b3b023a55d246b56c2c7f09cc1a66c62f66` |
| Global Dam Watch v1.0 Figshare files/version metadata | [GDW original publisher CC BY](https://www.globaldamwatch.org/database); archive GIS bytes not downloaded | `16739c79caa320eb0be27a0486040efb5fdcf02db4416a1493d6f9fac93b77ef` |
| USGS 3DEP Florida S1M catalogue metadata | [USGS public-domain 3DEP](https://www.usgs.gov/3d-elevation-program/); actual elevation raster not downloaded | `a4f2397d06242e702d63ca627379daadeb915d9bdd3c378dbcc761cc7a325c48` |

The original-response hashes above match the prior successful fixed GitHub Actions probes. Any stored subset has its own derived SHA in Neon; all six sample rows are explicitly `model_input_approved=false`. Original raw response retention is permitted only by the source-scoped decision, and no individual building coordinates, insurer records, confidential portfolios, large archives, licensed downstream vendor assets, or provider secrets were added.

## Required next causal steps

1. Process the 126 open-license *signals* via exact provider/version and third-party checks; do not mass-promote labels based on string matches. Resolve the 43 restriction signals separately.
2. For each cleared exact product, select one narrowly bounded download and verify source identity, response byte SHA-256, media/format, units, timestamps, license and attribution. Keep data that is not freely redistributable out of Git and any unauthorized Neon sample table.
3. Cover the remaining 520 entries through original-provider access/terms research, not blind URL crawling. A source with no valid contract remains documentation-only.
4. Add actual hazard/exposure model-admission tests **after** rights and source-specific scientific checks. Public metadata availability is not evidence of usable catastrophe losses.

No provider data, secrets or database credentials are present in this document.
