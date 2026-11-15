<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/fr.meteofrance.hourly-climate-stations.openlicence-v2.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `fr.meteofrance.hourly-climate-stations.openlicence-v2.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** fr.meteofrance.hourly-climate-stations.openlicence-v2

## Source ids

- fr.meteofrance.hourly-climate-stations.openlicence-v2

**Provider:** Météo-France via data.gouv.fr

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-horaires>

**Service root:** <https://www.data.gouv.fr>

**Api version:** Public data.gouv.fr dataset-catalogue v1 only (anonymous); separate account-gated Météo-France Climatologie API is not this interface; hourly department/decade CSV.GZ and exact wind variable not pinned

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

- inspect_fixed_publisher_dataset_metadata

### Path templates

- /api/1/datasets/donnees-climatologiques-de-base-horaires/

**Parameter rules:** Documentation-only, no automatic source request or caller-selected path, unbounded domain, secrets, crawler, bulk extraction or retries. Metadata path(s) are only candidate exact origins; actual provider GET requires independently reviewed provider machine-use terms, exact URL, byte cap, body hash and source-specific approved workflow. The separate official Météo-France Climatologie API at portail-api.meteofrance.fr/web/fr/api/DonneesPubliquesClimatologie is account-gated and is NOT an allowed host, path, operation or authentication mode here; access to that service requires a distinct source-specific contract and authorisation.

## Response contract

### Expected media types

- application/json

**Format:** Public dataset metadata: license, publisher, resource IDs and update timestamps. No station observations, field dictionary source bytes or hourly CSV included.

**Scientific semantics:** Dataset represents climatologically controlled hourly stations by French department and period. Mainland UTC vs overseas FU must be distinguished; hourly gust (not mean wind), QC flags, instrument height, units, temporal support and duplicate station lineage require exact original CSV and dictionary. Neither annual storm frequency nor insurer vulnerability, TIV or losses derived.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** No independently verified rate entitlement for the anonymous data.gouv.fr dataset metadata endpoint; retain documented_only with no approved requests or schedules. The separately advertised registered Météo-France Climatologie API states a 100 requests/minute maximum on its own official API listing (checked 2026-11-14); this is NOT a rate allowance for data.gouv.fr catalogue traffic and does not grant an account or authorise automated access.

**Mutability notes:** Catalogue may include 1,000+ changing official resource entries; pin one exact department, period, last_modified and file SHA before any comparison.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-horaires>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Publisher catalog states Licence Ouverte / Open Licence 2.0. That is evidence for this named dataset at catalog level, not independently for each external CSV resource, automated server cadence, hazard/model suitability or derivatives of station measurements. Attribution, resource version and original quality dictionary remain mandatory. The publisher separately advertises an account-gated Climatologie API with its own service boundary; the dataset Open Licence 2.0 must not be interpreted as proof of API account access, authorised throughput, raw-resource publication or CAT-model approval.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-horaires>
- <https://www.data.gouv.fr/api/1/datasets/donnees-climatologiques-de-base-horaires/>
- <https://guides.data.gouv.fr/api-de-data.gouv.fr/reference/datasets>
- <https://www.data.gouv.fr/dataservices/api-donnees-climatologiques>

**Notes:** One public dataset JSON endpoint was accessed using an external web read on 2026-11-14, NOT through a trusted source-native GitHub runner; neither binary resource nor exact API response SHA is verified. This contract itself authorizes no HTTP requests. T0 transport distinction checked on the official French data portal on 2026-11-14: the public catalogue and registered Climatologie API are different services; the registered service advertises 100 req/min only for itself. This record does not authorise either live API probe or source-byte download.
