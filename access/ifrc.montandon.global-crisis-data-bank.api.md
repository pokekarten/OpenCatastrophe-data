<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ifrc.montandon.global-crisis-data-bank.api.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ifrc.montandon.global-crisis-data-bank.api.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ifrc.montandon.global-crisis-data-bank.api

## Source ids

- ifrc.montandon.global-crisis-data-bank.api

**Provider:** International Federation of Red Cross and Red Crescent Societies (IFRC) / Montandon Global Crisis Data Bank

**Interface type:** stac

**Status:** blocked_credentials

**Documentation url:** <https://montandondata.org/get-started.html>

**Service root:** <https://montandon-eoapi.ifrc.org>

**Api version:** Montandon STAC API (CQL2 / Monty extension; production endpoint advertised in official onboarding)

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** bearer_token

**Credential reference:** IFRC_MONTANDON_API_TOKEN

**Registration url:** <https://go.ifrc.org/montandon-landing>

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_stac_catalogue_documentation

### Path templates

- /stac

**Parameter rules:** Documented-only, zero network execution authority. Montandon requires a token generated in an approved IFRC GO account; IFRC_MONTANDON_API_TOKEN is a symbolic future secret reference, never a stored token. No anonymous STAC request, arbitrary query, CQL2 filter, pagination, search, link following, asset download, credential sharing or return-data persistence is authorized. The stage endpoint in Monty developer docs is NOT the production service.

## Response contract

### Expected media types

- application/json
- application/geo+json

**Format:** STAC API catalog/collection/item metadata with Monty event, hazard and impact roles and CQL2 queries, only after separate authenticated access review.

**Scientific semantics:** Monty item IDs, issuer src_event_id, episode_number and source-local corr_id are distinct. Monty documentation explicitly warns that monty:corr_id is not a cross-source global join key. Event-to-event candidates require hazard/country/temporal and optional geometry tests; same crisis is not proof of same physical shock, contractual occurrence, independent hazard evidence, observed property damage or insured loss. Field event datetime is not a source publication or our receipt time.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `262144`

**Max sample bytes:** `1048576`

**Retry policy:** none

**Rate limit notes:** No live automated queries authorized until access token, provider API service terms and per-upstream reuse rights are independently qualified; no repository-specific rate entitlement assumed.

**Mutability notes:** Montandon and its source-provider transformations are mutable. Future receipts require authenticated identity provenance without the secret, exact source STAC ID/collection, upstream issuer event ID, transforming software/version, event issue/publication/ingest times, geometry, hazard taxonomy, original asset hash where allowed, known cross-source dependencies and a distinct arrival/knowledge-cut time.

## Rights and policy

**Dataset rights status:** unknown

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The official Montandon onboarding says API token access is required because underlying providers include licensed/restricted data. Public STAC documentation and accessible landing pages do not grant blanket commercial automation or raw/derived redistribution rights; review each source/product, bearer-token terms and intended insurance use independently.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-03

## Evidence urls

- <https://montandondata.org/get-started.html>
- <https://go.ifrc.org/montandon-landing>
- <https://ifrcgo.org/monty-stac-extension/model/stac-api/correlation_algorithms/>
- <https://github.com/IFRCGo/monty-stac-extension>

**Notes:** First source-specific access contract for the already registered landscape candidate. Token remains absent and no provider request, STAC item, raw asset, claims record, Neon write, scientific model run or source admission is implemented. The companion research gate uses fully invented STAC items only.
