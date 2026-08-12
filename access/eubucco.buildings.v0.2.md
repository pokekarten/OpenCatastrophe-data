<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/eubucco.buildings.v0.2.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `eubucco.buildings.v0.2.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** eubucco.buildings.v0.2

## Source ids

- eubucco.buildings.v0.2

**Provider:** EUBUCCO project (Potsdam Institute for Climate Impact Research / Technical University Berlin)

**Interface type:** object_store

**Status:** documented_only

**Documentation url:** <https://docs.eubucco.com/v0.2/data-access/cli/>

**Service root:** <https://s3.eubucco.com>

**Api version:** v0.2

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- fetch_nuts2_parquet

### Path templates

- /eubucco/v0.2/buildings/parquet/nuts_id=\{nuts2_id\}/\{nuts2_id\}.parquet

**Parameter rules:** Future execution must be repository-constructed for one independently reviewed EUBUCCO v0.2 NUTS2 region only. Partition identity follows EUBUCCO's modified NUTS-2016 geography and must not be silently reinterpreted through another NUTS vintage or unmodified boundary set without an explicit reviewed crosswalk. The trusted implementation must validate one canonical NUTS2 identifier, substitute the identical identifier into both fixed path positions and reject caller-supplied hosts, arbitrary object keys, recursive prefixes, query strings, headers, SQL predicates or alternate formats. Before enabling a probe or sample, freeze the exact NUTS2 region and object identity and review the geometry/source composition and applicable regional/source licences. Full-tree S3 sync, country recursion, website ZIPs, DuckDB/Python streaming and the Zenodo bulk archive are secondary documented access paths and are not executable through this contract.

## Response contract

### Expected media types

- application/octet-stream

**Format:** EUBUCCO v0.2 Apache Parquet building partition for one NUTS2 region; footprint geometry is WKB in ETRS89 / EPSG:3035 and the dataset carries source/provenance and uncertainty fields.

**Scientific semantics:** EUBUCCO v0.2 is a harmonized European building-characteristics database assembled from governmental registries, OpenStreetMap and Microsoft building footprints. Geometry and attributes do not have one uniform evidence class: provider fields distinguish geometry source and per-attribute provenance, while some attributes are merged from other sources or estimated with machine learning and carry uncertainty information. EUBUCCO v0.2 partitions use the provider's modified NUTS-2016 geography; a partition must not be reinterpreted as another NUTS vintage without an explicit crosswalk. For OSM-derived records, geometry_source_id and attribute \*_source_ids are EUBUCCO-local sequential indices rather than original OpenStreetMap object IDs and cannot by themselves resolve an upstream OSM object. Any later catastrophe-risk use must preserve v0.2 identity, the selected modified-NUTS-2016 partition, EPSG:3035 geometry semantics, geometry and attribute source fields, confidence/uncertainty information and known regional/source limitations. Building presence or attributes do not by themselves establish replacement value, occupancy value, vulnerability, damage/loss or insured loss.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `52428800`

**Retry policy:** bounded_backoff

**Rate limit notes:** No repository-specific rate assumption is made. Future execution must remain one explicitly reviewed NUTS2 object and must not expand into recursive country or full-dataset synchronization. The provider documents anonymous S3-compatible access, but that availability is not an authorization for uncontrolled harvesting.

**Mutability notes:** The object path is version-namespaced as v0.2, but this contract does not claim that the live object-store bytes are immutable. Every future receipt must bind retrieval UTC, exact NUTS2 object path, byte count and SHA-256. For a citable archival snapshot, EUBUCCO documents Zenodo DOI 10.5281/zenodo.7225259; archive identity must still be independently bound before scientific use.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** restricted

**Redistribution status:** restricted

**Notes:** EUBUCCO v0.2 documentation states that the dataset is generally licensed under ODbL v1.0, with regional exceptions: Prague geometry source gov-czechia-prague is CC-BY-SA and Abruzzo geometry source gov-italy-abruzzo is CC-BY-NC. The documentation instructs users who need an ODbL-only dataset to filter out those sources. Therefore an arbitrary v0.2 region/full-dataset path cannot be treated as uniformly cleared for commercial automation or unrestricted redistribution. Exact NUTS2/source composition, attribution, share-alike/database obligations and any non-commercial constraint must be reviewed before execution or persistence. Separate object-store service/API terms are not established by this review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://docs.eubucco.com/v0.2/data-access/cli/>
- <https://docs.eubucco.com/v0.2/data-format/partitioning/>
- <https://docs.eubucco.com/v0.2/data-format/>
- <https://docs.eubucco.com/v0.2/data-format/metadata/>
- <https://docs.eubucco.com/v0.2/license/>
- <https://docs.eubucco.com/v0.2/data-access/zenodo/>

**Notes:** Static access contract only. It documents one future bounded anonymous NUTS2 Parquet-object route while leaving execution disabled. No provider object, S3 listing, Parquet row, sample, ZIP or other external byte was requested, acquired or persisted by this builder. EUBUCCO v0.2 uses NUTS2-partitioned Parquet as its primary high-performance distribution and provides source/provenance metadata needed to distinguish governmental, OSM, Microsoft, merged and estimated information. Before status can advance beyond documented_only, an independent review must freeze one exact NUTS2 object and source composition, resolve commercial/service/redistribution obligations for that region, and define bounded expected response evidence without enabling recursive access.
