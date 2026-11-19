<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/smithsonian.gvp.votw.v5-4.wfs.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `smithsonian.gvp.votw.v5-4.wfs.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** smithsonian.gvp.votw.v5-4.wfs.documented

## Source ids

- smithsonian.gvp.volcanoes-of-the-world.v5.4.0

**Provider:** Smithsonian Institution / Global Volcanism Program

**Interface type:** wfs

**Status:** restricted_by_terms

**Documentation url:** <https://volcano.si.edu/database/webservices.cfm>

**Service root:** <https://webservices.volcano.si.edu/geoserver>

**Api version:** `null`

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_public_service_documentation

### Path templates

- /GVP-VOTW/wfs

**Parameter rules:** Documentation-only, no network probe, GetCapabilities, DescribeFeatureType, GetFeature, layer query, screenshot, bulk download, data scraping, source-byte storage or derivative publication is authorized by this contract. The provider publishes a GetCapabilities URL with request=GetCapabilities and examples limited to 100 records; examples indicate endpoint shape but do not imply OpenCatastrophe is permitted to call it for insurer CAT workflows. No caller-controlled URL, query, version, layer, CRS, filter, bbox, redirects, credentials or output format can be provided. Require source-specific written permission and reviewed API terms before a separate executable contract is proposed.

## Response contract

### Expected media types

- text/xml
- application/xml

**Format:** Provider WFS service documentation only; expected GetCapabilities XML is a documented future possibility, not a probed or validated current response.

**Scientific semantics:** The provider documents Holocene volcanoes, Pleistocene volcanoes and Holocene eruptions as WFS feature layers; service version/layer names and feature IDs require exact bounded evidence before acquisition. Catalogue coordinates are not volcanic-event footprints, ash depth/intensity, recurrence probabilities, loss costs or claims. Preserve VOTW v5.4.0 dataset citation, original sources and reporting/censoring uncertainty.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** No OpenCatastrophe API probes or automated requests are permitted. This is intentionally a rights-blocked source; do not equate the publicly displayed 100-feature example with permission for commercial reuse.

**Mutability notes:** GVP warns website content may change without corresponding version bumps. Freeze original release cited by the provider, retrieval date and record IDs before any use. This contract does not freeze any real response, server schema, WFS protocol version or source bytes.

## Rights and policy

**Dataset rights status:** restricted

**Api terms status:** unknown

**Terms url:** <https://volcano.si.edu/gvp_termsofuse.cfm>

**Commercial automation status:** prohibited

**Redistribution status:** unknown

**Notes:** Smithsonian GVP Terms of Use explicitly prohibit commercial purposes without prior written permission, including selling products/services incorporating Content. The database compilation is described as work of US government employees, but GVP still conditions site content use on the Smithsonian Terms, and individual contributions may have third-party rights. For insurer CAT models, do not interpret generic open web services, publication DOI, government employee status or GIS format availability as a commercial-use or redistribution licence. Written authorization for exact intended output/use and rights/terms review is required before any source-byte acquisition.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** do_not_automate

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://volcano.si.edu/database/webservices.cfm>
- <https://volcano.si.edu/gvp_termsofuse.cfm>
- <https://volcano.si.edu/gvp_votw.cfm?vn=300001>
- <https://volcano.si.edu/gvp_cite.cfm>

**Notes:** T0 documented/rights-restricted access profile. No Geoserver endpoint request, WFS metadata request, local file, Neon insert, admission manifest or insurer modelling is authorized or claimed. The prior 5.3.6 registry candidate remains separate as a historical release. Next possible gate: seek Smithsonian written permission and review whether the exact 5.4.0 WFS dataset can be commercialized; only then design a one-layer 1–10-feature metadata probe and reproducible versioned event crosswalk.
