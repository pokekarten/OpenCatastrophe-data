<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/emodnet.geology.geological-events.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `emodnet.geology.geological-events.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** emodnet.geology.geological-events

## Source ids

- emodnet.geology.geological-events

**Provider:** European Marine Observation and Data Network / EMODnet Geology / ISPRA

**Interface type:** wfs

**Status:** documented_only

**Documentation url:** <https://emodnet.ec.europa.eu/en/emodnet-web-service-documentation>

**Service root:** <https://drive.emodnet-geology.eu>

**Api version:** OGC WFS 2.0.0 / EMODnet Geology ISPRA Events and Probabilities

## Access scope

- metadata
- catalogue
- bulk

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- get_capabilities
- describe_feature_type
- get_feature

### Path templates

- /geoserver/ispra/wfs

**Parameter rules:** Documentation-only WFS contract; no request is authorized yet. A future reviewed adapter must hard-code SERVICE=WFS and VERSION=2.0.0 and compile only GetCapabilities, DescribeFeatureType or a bounded GetFeature request. Callers must never supply arbitrary service roots, type names, CQL/filter expressions, property names, SRS/CRS identifiers, output formats, sort clauses, pagination, URLs or headers. Initial exact type-name evidence includes \`ispra:earthquakes\`, \`ispra:landslide_pol_100k\`, \`ispra:landslide_lin_100k\`, \`ispra:landslide_pt_100k\`, \`ispra:volcanic_center_pol_100k\`, \`ispra:volcanic_center_lin_100k\`, \`ispra:mud_volc_fluid_emis_pt_100k\`, and \`ispra:tectonics_lin_100k\`; this list is evidence, not execution authority. Before any GetFeature implementation, re-fetch current capabilities/DescribeFeatureType, freeze the complete intended layer allow-list and attribute schema, and choose one bounded feature-count/AOI recipe. The WMS 1.3.0 and WMTS endpoints are secondary visualization services and are not authorized by this WFS contract.

## Response contract

### Expected media types

- application/xml
- text/xml
- application/gml+xml

**Format:** OGC WFS 2.0.0 service metadata, feature schemas and vector-feature responses. Exact GetFeature output encoding must be re-confirmed from the live ISPRA capabilities before execution; no JSON/GeoJSON assumption is made by this contract.

**Scientific semantics:** EMODnet Geology Events and Probabilities is a harmonised multi-layer inventory of marine geological events and related products, including earthquakes, submarine landslides, volcanoes, tsunamis, fluid emissions and Quaternary tectonics at 1:100,000 and 1:250,000 scales, plus event-distribution and submarine-landslide-susceptibility products. Event layers record mapped/reported occurrences assembled from partner surveys, third-party cooperation and literature; blank areas do not necessarily mean no occurrence and completeness is spatially heterogeneous. The event inventory does not directly constitute geohazard assessment. The landslide susceptibility product is model-derived and must remain distinct from occurrence inventories. Geometry, scale, source references, lineage and layer-specific attributes are scientifically material.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `262144`

**Max sample bytes:** `5242880`

**Retry policy:** none

**Rate limit notes:** EMODnet documents open OGC services but no repository-specific numeric request budget was established. This documented-only contract authorizes no capabilities fetch, schema request, GetFeature call, crawl, pagination loop or retry. A future canary must use one exact layer and a very small bounded feature/AOI request through the trusted network plane.

**Mutability notes:** EMODnet Geology is actively maintained; the aggregate Events and Probabilities metadata currently records revision 2025-09-04 and child metadata can have later metadata stamps. Reproducible use must bind WFS version, exact type name, metadata identifier/revision, schema, CRS, request fingerprint, retrieval UTC and response hash. Do not silently combine 1:100k and 1:250k layers or treat later service content as byte-identical to an earlier extraction.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_reviewed

**Terms url:** <https://emodnet.ec.europa.eu/en/terms-use-emodnet-online-services-data-and-data-products>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The aggregate Events and Probabilities metadata and several current child-layer records state CC BY 4.0 and no public-access limitations. EMODnet's Terms of Use also state that EMODnet-produced data products are generally EU-owned and CC BY 4.0 unless indicated otherwise, while requiring users to inspect accompanying metadata and respect data-originator licences/restrictions. Because the source family aggregates partner, third-party and literature-derived material and this review did not verify every intended layer's current metadata, dataset-level redistribution remains fail-closed rather than inherited provider-wide. Service terms are recorded separately, but durable commercial automation remains unknown pending a dedicated service-use review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://emodnet.ec.europa.eu/en/emodnet-web-service-documentation>
- <https://emodnet.ec.europa.eu/en/geology-1>
- <https://emodnet.ec.europa.eu/en/terms-use-emodnet-online-services-data-and-data-products>
- <https://metadata.europe-geology.eu/record/basic/e645855c332be48b6a52ed4e5e7b15f688caeb55>
- <https://metadata.europe-geology.eu/record/basic/8966f2185775edeacc4eeaf748b728bbc48f7331>
- <https://metadata.europe-geology.eu/record/basic/ecb22f233db3b5c3dfbe94939df786605a2cac3c>
- <https://metadata.europe-geology.eu/record/basic/eefa2e56ab2c848359e1eea720b6c2a4557f82c8>
- <https://metadata.europe-geology.eu/record/basic/43104c34cb25ac6021f17846d5dabd87c45cf17d>

**Notes:** Bounded source-access documentation for Issue \#261 / \#173. The canonical data-access lane is WFS 2.0.0; WMS 1.3.0 remains visualization-only evidence here. No provider request, feature byte, parser, adapter, workflow, admission or publication decision is introduced. A future first feature canary should select one exact, metadata-reviewed layer such as the 100k submarine-landslide polygon layer only after its schema, attribution and requested output format are frozen.
