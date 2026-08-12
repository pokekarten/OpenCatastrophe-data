<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ec-jrc.ai-disaster-health-storylines.zenodo-v1.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ec-jrc.ai-disaster-health-storylines.zenodo-v1.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ec-jrc.ai-disaster-health-storylines.zenodo-v1

## Source ids

- ec-jrc.ai-disaster-health-storylines

**Provider:** European Commission Joint Research Centre / Zenodo

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://zenodo.org/records/18598183>

**Service root:** <https://zenodo.org>

**Api version:** crisesStorylinesRAG Zenodo v1; DOI 10.5281/zenodo.18598183; JRC dataset DOI 10.2905/JRC.CJDXGM8

## Access scope

- metadata
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- fetch_disasterstory_v1_csv

### Path templates

- /records/18598183/files/DisasterStory.csv

**Parameter rules:** Documentation-only exact-snapshot contract. No HTTP request is authorized yet. The scientific/archival identity is fixed to Zenodo record 18598183, version v1, file DisasterStory.csv. Zenodo's current download link advertises a provider-controlled \`download=1\` query parameter; before execution, a reviewed worker must freeze the exact final transport URL and redirect/query behavior rather than accepting any caller-supplied query. Callers must never supply a record ID, filename, host, query string, alternate file, mutable JRC latest path, redirect target or arbitrary header. No Zenodo record crawl, 'download all', GitHub checkout, Hugging Face access or substitution of input_emdat_1424.xlsx is authorized by this contract.

## Response contract

### Expected media types

- text/csv
- application/octet-stream

**Format:** Single CSV snapshot named DisasterStory.csv from Zenodo record 18598183 v1. Zenodo currently reports a file size of approximately 5.2 MiB and provider MD5 \`bd47fdf75d7c7264c8aabea097dbc530\`; a future acquisition must independently compute SHA-256 before any scientific use.

**Scientific semantics:** DisasterStory.csv contains AI-generated disaster storylines and knowledge-graph representations for 3,158 EM-DAT-seeded disaster events from 2014-2024 across 175 countries and 26 disaster types. Each record is keyed to an EM-DAT disaster number and combines standard event metadata with LLM-generated narrative fields such as key information, severity, drivers, impacts/exposure/vulnerability, multi-hazard risk, management practices and recovery recommendations, plus a simplified \`llama graph\` of extracted subject-predicate-object triples. The pipeline retrieves EMM news with RAG and uses LLM generation/extraction; it is contextual enrichment, not independent event, impact or causal ground truth. The published corpus represents roughly half of EM-DAT events in the period, the first experiment focuses on the English-language RAG index, media-source geography is highly uneven, retrieval/filtering can miss relevant events, and the simplified graph relation set is not a comprehensive causal model. High-stakes use requires triangulation and domain review.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** Zenodo exposes the v1 record publicly, but this contract authorizes no file request, record crawl, retry loop or repeated snapshot polling. No repository-specific rate budget or durable automated-download entitlement was established. The JRC catalogue's separate daily-updated resource must not be polled through this snapshot contract.

**Mutability notes:** The reproducibility anchor is the immutable Zenodo v1 record DOI 10.5281/zenodo.18598183 and its DisasterStory.csv file, published 2026-02-10. Zenodo currently records MD5 \`bd47fdf75d7c7264c8aabea097dbc530\`; future execution must additionally bind requested/final URL, retrieval UTC, byte count, SHA-256, CSV header/schema and record count. The JRC Data Catalogue declares a daily update frequency for its maintained resource, while the Scientific Data descriptor says regular updates are planned; neither may silently replace this v1 snapshot.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The JRC Data Catalogue applies the European Commission reuse notice to its downloadable resource and explicitly notes that reuse does not cover documents subject to third-party intellectual-property rights. The generated dataset is seeded from EM-DAT and news retrieved through EMM; upstream data/news rights and generated-output reuse therefore require source-specific analysis. The Zenodo v1 page is publicly accessible and the paper states that data/code/workflows are openly available, but the rendered Zenodo Rights section does not currently expose an explicit licence text sufficient for this repository to promote redistribution or commercial-use authority. Rights remain not reviewed; no persisted copy or derivative publication is authorized by this access contract.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://zenodo.org/records/18598183>
- <https://doi.org/10.5281/zenodo.18598183>
- <https://data.jrc.ec.europa.eu/dataset/747cf15b-87b4-4b92-a1be-10465c972929>
- <https://doi.org/10.2905/JRC.CJDXGM8>
- <https://doi.org/10.1038/s41597-026-07036-2>
- <https://joint-research-centre.ec.europa.eu/jrc-news-and-updates/new-dataset-uses-ai-and-disaster-news-fill-knowledge-gaps-and-map-interconnected-risks-2026-05-05_en>

**Notes:** Bounded immutable-snapshot access documentation for Issue \#264 / \#173. The maintained JRC CSV remains a discovery/current-data source, but model/research reproducibility should prefer this pinned Zenodo v1 snapshot unless a newer release is intentionally reviewed. No provider request, CSV byte, parser, LLM/RAG execution, knowledge-graph ingestion, workflow, admission promotion or publication decision is introduced.
