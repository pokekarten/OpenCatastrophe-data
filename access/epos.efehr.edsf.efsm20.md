<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/epos.efehr.edsf.efsm20.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `epos.efehr.edsf.efsm20.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** epos.efehr.edsf.efsm20

## Source ids

- epos.efehr.edsf

**Provider:** Istituto Nazionale di Geofisica e Vulcanologia / Seismofaults / EFEHR / EPOS

**Interface type:** wfs

**Status:** documented_only

**Documentation url:** <https://www.seismofaults.eu/efsm20documentation>

**Service root:** <https://services.seismofaults.eu>

**Api version:** EFSM20 main dataset 2020; portal publication 2022; DOI 10.13127/efsm20; OGC WFS

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

- /EFSM20/ows

**Parameter rules:** Documentation-only contract; no WFS request is authorized yet. Future execution must keep the service root and /EFSM20/ows path repository-controlled and compile only GetCapabilities, DescribeFeatureType or a small bounded GetFeature request. Callers must never supply an arbitrary URL, dataset/version path, typeName/QName, CQL/filter expression, property list, CRS/SRS, output format, paging/sort clause or header. Current EFSM20 documentation lists ten main-dataset tables distributed via OGC WFS: EFSM20_CF_TOP, EFSM20_CF_BOT, EFSM20_CF_MID, EFSM20_CF_PLD, EFSM20_CFDepths, EFSM20_SlabDepths, EFSM20_SI_Parameters, EFSM20_SI_Discretization, EFSM20_SI_Realizations and EFSM20_IS_Lattice. Those documented table names are evidence only; before a GetFeature adapter is enabled, re-fetch current GetCapabilities and DescribeFeatureType and freeze the exact WFS QName, schema, supported WFS version, CRS and output encoding. EDSF13 paths/names and EFSM20 Meshes paths/names are explicitly outside this contract.

## Response contract

### Expected media types

- application/xml
- text/xml
- application/gml+xml

**Format:** OGC WFS service metadata, feature schemas and vector-feature responses for the EFSM20 main dataset. EFSM20 is also distributed as downloadable GIS files including GeoJSON, but this contract freezes only the current WFS service family and does not infer an executable GeoJSON-download path.

**Scientific semantics:** The European Fault-Source Model 2020 (EFSM20) is a continental-scale Euro-Mediterranean fault-source model developed as geologic input to ESHM20. The main dataset contains fault geometry and activity parameters for two principal source categories: crustal faults and subduction systems. Current provider documentation describes 1,248 crustal faults spanning about 95,100 km and four subduction systems, with coverage focused on a 300 km buffer around target European countries and slab depths to 300 km. The model is epistemically uncertain and is not guaranteed complete, accurate or current for other applications; local/site-specific investigations remain necessary for local decisions. Absence of a mapped fault is not evidence of zero seismic hazard. EFSM20 is distinct from ESHM20 hazard outputs and from the separately published 2024 EFSM20 3D triangular-mesh derived product.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `262144`

**Max sample bytes:** `5242880`

**Retry policy:** none

**Rate limit notes:** The Seismofaults/INGV portal documents public WFS services and monitors them operationally, but no repository-specific numeric request budget or durable automated/commercial service entitlement was established in this review. This documented-only contract authorizes no capabilities request, schema request, GetFeature query, pagination loop, retry or bulk mirror.

**Mutability notes:** Scientific identity is pinned to the EFSM20 main dataset, model/version year 2020, DOI 10.13127/efsm20 and the main EFSM20 WFS service family. The 2025 portal report records the main dataset as published 10/2022 with ten WFS and six WMS layers, while the separately derived EFSM20 Meshes product is version 2024/published 11/2024 with its own DOI and six WFS layers. Any future extraction must freeze current capabilities/schema, exact QName, request fingerprint, retrieval UTC, response byte count/SHA-256 and provider metadata. Do not silently substitute EDSF13, EFSM20 Meshes or a later differently versioned fault model.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** The authoritative EFSM20 dataset and documentation pages state that, except where otherwise noted, EFSM20 is licensed under CC BY 4.0 and provide DOI 10.13127/efsm20. This supports dataset reuse and redistribution with attribution, subject to any dataset-specific exception noted by the provider. The platform separately warns that each distributed dataset has its own licence. This review did not establish separate WFS service automation/commercial terms or a numeric request policy, so automated execution remains disabled despite verified dataset reuse rights. Any persisted sample still requires exact feature/schema provenance and attribution review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://www.seismofaults.eu/efsm20>
- <https://www.seismofaults.eu/efsm20documentation>
- <https://seismofaults.eu/services/efsm20-services>
- <https://data.ingv.it/metadata/web_service_eng>
- <https://doi.org/10.13127/efsm20>
- <https://seismofaults.eu/documentation/portal-reports/portal-report-2025>
- <https://www.seismofaults.eu/documentation/portal-reports/portal-report-2024>

**Notes:** Bounded current-child access resolution for Issue \#262 / \#173. The existing landscape source \`epos.efehr.edsf\` remains the discovery/service-family identity; this access ID deliberately selects current EFSM20 main-dataset semantics rather than obsolete EDSF13. EDSF13 is deprecated and retained for reproducibility only. EFSM20 Meshes (DOI 10.13127/efsm20/meshes) is a separate derived product and is not authorized here. No provider request, XML/GML/GeoJSON byte, parser, adapter, workflow, admission promotion or publication decision is introduced.
