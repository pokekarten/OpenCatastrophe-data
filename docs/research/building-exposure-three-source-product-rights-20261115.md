<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Product-scoped exposure rights — BVV, DLR WSF2019, Overture Buildings (2026-11-15)

## What was actually verified

A new strictly **read-only** SQL query at
`research_runners/sql/building_exposure_source_rights_readiness_v0.sql`
joins the already existing research Neon source-rights matrix, each exact
product-scoped use-case rights record and source-wide sample SHA checks. It
does **not** create or update rights, issue an HTTP GET, fetch geodata or
admit a CAT model input.

**Actual Neon `insurance` research database readback (2026-11-15):**

| Source | Product-level external licence | Product-scoped reviewed uses | Internal use-case/right blockers |
| --- | --- | ---: | --- |
| `de.bayern.hausumringe` original district 091 | Official CC BY 4.0 | **7/7**, all independently provider-host documented | `automated_api_access=conditional`, `internal_neon_source_sample=conditional`; derived publication/raw redistribution each conditional; still `not_admitted` |
| `dlr.wsf.2019`, fixed original `WSF2019_v1_10_48.tif` | Official CC BY 4.0 | **0/7** | No product-scoped Neon use-case reviews; the existing `access/dlr.wsf.2019.native-geotiff.json` is `documented_only` and requires separate provider file-service review for new network requests |
| `overture.maps.buildings`, 2026-10-21.0 Buildings release | **ODbL** for the **theme** | **0/7** | No product-scoped commercial/API/derived database-use review in Neon. Original cloud Parquet research evidence is only on an isolated Neon branch; not in the production sample register |

The external licence evidence is [BVV official product use terms](https://www.geodaten.bayern.de/odd/m/3/html/nutzungsbedingungen.html),
[DLR WSF2019 official dataset catalogue](https://catalogue.geoservice.dlr.de/web/datasets/wsf_2019),
and [Overture official attribution/licensing](https://docs.overturemaps.org/attribution/).
In particular, Overture's Buildings theme is **ODbL** even where source
lineage includes Microsoft ML, Google, Esri or OSM. No generic MIT licence
of Overture's *software repository* applies to its original Buildings
database. Attribution, downstream use and any triggered ODbL database
obligations require a separate product-and-use review; a valid free-to-use
licence is not a direct claim that commercial model consumers can
republish insurer-facing derived building databases without review.

All model-input approvals in this report remain **false**. Original
BVV house-outline records cannot be equated to distinct insured
buildings. DLR WSF2019's 10 m settled **class** is not individual
building geometry, and 2019 versus later BVV capture is not a same-year
holdout. Overture original rowgroup/Luxembourg ACT overlaps have
no independent same-building physical-identity proof.

## Executed negative challenges without Neon mutation

The committed canonical SELECT was **actually executed** in read-only
Neon, returning precisely **three** source rows: BVV 7/7 reviewed
but automation incomplete; DLR 0/7; Overture 0/7; all model admissions
false. All BVV **10/10** and DLR **4/4** existing source-wide JSONB SHA
checks passed. Overture had **0** canonical main research samples; its
source-specific original Parquet geometry receipts remain only on the
separate restricted research branch.

Three further tests replaced the rights-ledger relation **in the
in-memory SQL statement only**, leaving all actual DB tables unchanged:

1. Inject seven fictitious `allowed` rights with real-host evidence:
   BVV remained **BLOCKED**, because the unchanged source-rights matrix
   still says automated access `conditional` and internal sample
   access `conditional`.
2. Inject seven fictitious `allowed` rights but use an
   attacker-controlled `geodaten.bayern.de.evil.example` URL: **0/7**
   evidence-host checks accepted; blocked.
3. Inject eight fictitious `allowed` records including a duplicate
   use-case: unique cases 7 but entries 8; blocked.

The code additionally checks the *same exact product_scope* for all
seven cases, rejects malformed/incomplete authority evidence, ensures
real stored JSONB sample SHA, and requires **the coarse matrix AND
the seven exact use-case records agree** before an operational
readiness indicator can ever become true. The indicator can never set
`cat_model_input_approved_by_this_audit`; separate release/asset,
science, validation, commercial modelling and insurer evidence remain
independent.

## Immediate next action

Review the **exact DLR original GeoTIFF** service terms for new automated
HTTP Range acquisition, separately from the existing historical
fixed-range sample; record scoped
`commercial_cat_modelling`, `automated_api_access`, internal
metadata/sample handling, derived publication and raw redistribution
permissions with original provider evidence. Review **Overture
2026-10-21.0 Buildings ODbL** for planned joined/derived insurance
exposure output, attribution and obligations for potentially
share-alike derived databases. No Neon rights entries should be promoted
from published product licence alone.

After rights, the scientifically next high-value milestone remains
a **second independent building-to-building reference pair**, not
BVV building versus DLR *settlement* overlap.
