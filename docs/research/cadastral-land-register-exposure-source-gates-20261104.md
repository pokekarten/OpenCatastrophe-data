<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Land registers, cadastral parcels and sales records for synthetic CAT exposure — 2026-11-04

**Status:** source-page metadata review / discovery only. No provider bytes downloaded, no rights/science admission, no insurer data or individual title searches performed. Canonical proposals in `landscape/sources-cadastral-land-register-20261104.json`.

## Why this matters

A legal title (ownership/rights), a cadastral parcel (land area), a building footprint (one or more physical structures), a dwelling unit and a policy-risk location are DIFFERENT objects. Never infer a 1:1 cardinality. Parcel geometry improves location-to-hazard overlays and land-use classification; transactions can weakly constrain local market price distributions, but neither defines rebuild cost (construction-only) nor insurance total insured value (TIV).

Safe conceptual chain: **registered parcel → spatially intersecting physical buildings → independently verified building/use/floors/age → regional construction replacement cost and sums-insured priors → synthetic policy count/coverage/deductible/limits → independently accepted hazard + vulnerability → gross/net event losses**. All probabilistic links must retain an uncertainty estimate and source lineage.

## Already covered in repo (not duplicates)

- `landscape/sources-european-building-registers.json`: NL BAG, FR RNB/BD TOPO/BDNB, ES INSPIRE Buildings, DK BBR, PL BDOT10k etc. These are BUILDINGS and addresses, not land-title records or sales registries.
- `landscape/sources-berlin-alkis-pilot-20261101.json` and Berlin/Hessen research: ALKIS building geometry probes, not NRW parcel INSPIRE/Grundsteuer tax dataset.
- `landscape/sources-gis-geocoding-foundations-20261104.json`: OpenAddresses and ACT BD-Adresses. Address coordinates must not be confused with title geometry.
- `landscape/sources-luxembourg-cross-domain-building-20261101.json`: Luxembourg buildings/roofs, historic orthophotos and addresses; official PCN is a separate parcel and building mapping source.

## Priority pilots

1. **NRW property parcels**: official INSPIRE ALKIS WFS (source metadata: 2026-09-01, WFS returned max 100000 objects/query, DL-DE-Zero 2.0). Use small bounded feature request; join via parcel ID/geometry to existing ALKIS buildings, then validate against flood polygons. The NRW fiscal CSV additionally supplies land-use and areas but **its Grundbuchblattnummer field is strictly tax-purpose-only**. Do NOT ingest/export/use that restricted field in CAT. Official evidence: https://www.geoportal.de/info/6ee0316c-fff3-4c04-89c1-3aa2b453f95a and https://grundsteuer-geodaten.nrw.de/Beschreibung_Schnittstellen.pdf, p.2 (exception). The 2026 GovData CSV is https://data.gov.de/suche/daten/grundsteuerdaten-nrw-flurstucke06c57.
2. **France parcel-to-sale**: Etalab cadastral vector parcels / buildings derived from PCI and Cerema DVF+ release 2026.2, coverage 2014-01 through 2026-06, GeoParquet/GeoPackage/PostGIS. Newest quarters incomplete; DGFiP prohibits reidentification and external search-engine indexing of DVF. Evaluate aggregate median/trimmed-price distribution per region and residential type; never treat consideration as replacement value. https://cadastre.data.gouv.fr/datasets/cadastre-etalab and https://datafoncier.cerema.fr/actualites/la-nouvelle-version-dvf-open-data-20262-disponible.
3. **England/Wales record-linked price**: HM Land Registry November 2026 freehold INSPIRE polygon GML + September 2026 Price Paid Data + 2026-new transaction UID → INSPIRE ID lookup. Excellent explicit public transaction-to-title link, but only matched freeholds; lookups are not back-dated; one sale maps to multiple polygons. Price Paid address-derived rights and lookup terms need separate review. https://use-land-property-data.service.gov.uk/datasets/inspire / https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads / https://www.gov.uk/government/statistical-data-sets/transaction-unique-identifier-and-inspire-id-look-up-table-dataset.
4. **Luxembourg**: official ACT PCN parcels and buildings (2026-11-02 SHP ZIP / GeoJSON, advertised CC BY 4.0). INSPIRE CP derivative can be older and historic geometry less precise. Compare against current ACT building dataset as shared upstream, not independent holdout. https://data.public.lu/en/datasets/plan-cadastral-numerise-pcn/.
5. **Netherlands**: BRK Kadastrale Kaart public OGC API parcel polygons independently enrich existing BAG (building) records. This is a parcel/building *crosswalk* with many-to-many relationships, NOT proof of ownership or per-building insured value. https://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/perceel?f=html.
6. **Switzerland Geneva / Spain**: Geneva cadastral EGRID ArcGIS and Spanish Catastro public nonprotected attributes. Validate service licensing, entity level and access restrictions before data transfer. https://vector.sitg.ge.ch/arcgis/rest/services/CAD_PARCELLE_MENSU/FeatureServer/0 / https://www.catastro.hacienda.gob.es/es-ES/acceso_infocat.html.

## Negative and restricted evidence

- Germany §12 GBO: individual Grundbuch inspection requires documented legitimate interest, not blanket bulk public reuse: https://www.gesetze-im-internet.de/gbo/__12.html. Never harvest private individual owners. Parcel/boundary geometry is a separate register.
- Bayern states ALKIS parcel vectors/boundary points are NOT freely distributed, even though some map layers and LoD2 building products are open: https://www.geodaten.bayern.de/odd/m/3/html/faq.html.
- BKG 2026 FS-DE describes circa 53.7 million records in the current product, excluding Bavaria, and supply primarily for federal bodies: https://www.bkg.bund.de/SharedDocs/Produktinformationen/BKG/DE/P-2026/260305_FS-DE.html. Do not assume unrestricted national bulk download.
- Spain's protected owner and cadastral value services require authentication/legal authorisation; ordinary geometry and nonprotected metadata are a separate tier.
- No owner name, title record, household address or fiscal-only register identifier belongs in Git/public synthetic insurance data.

## Required evaluation gate

1. Source identity: authoritative product URL, exact revision/date, provider licence and per-field restrictions, requested bbox and raw bytes hash.
2. Model identity: parcel versus title versus building versus dwelling versus property sale versus policy risk.
3. Spatial verification: CRS, geometry validity, correct area projection, parcel split/merge, shared lineage, one-to-many address/building/title link, matching confidence.
4. Temporal verification: parcel and building vintage, demolition/new construction, transaction date versus snapshot date, no time-travel.
5. Property valuation: prefer *construction replacement cost* independent of land; adjust market sales for land share, building mix, age and regional costs. Never equate sales transaction with insured sum.
6. Privacy/rights: drop prohibited identifiers BEFORE storage; no individual title harvesting, household profiling or deanonymisation. Record permitted fields and required attribution.
7. Model admission: only separate manifest + source review can admit exact bytes for downstream models; metadata candidate stays `not_admitted`.
8. Bounded pilot evaluation: measure join coverage, false match rate, % valid geometry, % buildings with parcel, region/type price prior uncertainty, effect on aggregate gross/net OEP/IP outputs. No synthetic policy can be claimed real.

## Execution status

Original government/provider documentation verified by public web review 2026-11-04. **Not** an end-to-end downloader test, not a model calibration, not a legal opinion, not a production Neon import. Next step is one bounded nonpersonal public-data parcel-feature probe per priority region and independent source admission reviews.


## Update 2026-11-04: operational cardinality gate and additional UPRN source

**New discovery candidate:** `uk.hmlr.transaction-uid-uprn-lookup.2026` (12th catalogue entry). Official HM Land Registry [technical specification](https://www.gov.uk/government/statistical-data-sets/technical-specification-transaction-unique-identifier-and-uprn-look-up-table-dataset) confirms this is a *separate* monthly transaction UID → addressable UPRN relation, also without back-dating. Coverage includes matched freehold **and** leasehold registered sale transactions where OS/Royal Mail PAF address-linkage exists. Multiple UPRNs may correspond to one sale (e.g. several flats in a building), and unaddressed land/new builds may have none. UPRN is neither an INSPIRE freehold polygon nor a physical building ID. Supplier declares OGL 3.0 for HMLR **and** Ordnance Survey source contributions; Price Paid address-related licensing still applies. Do not join one UPRN to multiple buildings without independently verified object identity and matching vintage.

**Executable bounded diagnostic:** `scripts/audit_hmlr_inspire_sale_linkage_v0.py` accepts a stripped, analysis-only JSON consisting of `source_family`, `snapshot_date`, `transactions` (transaction UID / sale date / positive integer GBP paid), `lookup` (UID/INSPIRE ID) and `polygons` (INSPIRE ID). It rejects all unexpected fields including owners, addresses, title references, and restricted Grundbuch identifiers; bounds rows/bytes and checks dates, identities, duplicates and missing references. Aggregate output distinguishes *unique transactions* from *polygon links* and explicitly blocks interpreting sales prices as insured values, reinstatement costs or insurer ownership.

Run the **synthetic-only** unit tests:

```sh
python -m unittest tests.test_audit_hmlr_inspire_sale_linkage_v0 -v
```

Eight tests were run locally 2026-11-04 successfully before upload. One illustrative synthetic test has £400,000 and £300,000 matched sales; the £400,000 sale relates to two distinct polygons. Summing across polygon rows incorrectly gives £1,100,000 instead of the correct £700,000 distinct matched transaction total. The audit reports an artificial **£400,000** overcount and suppresses exact duplicate link rows. This is a correctness demonstration with fake IDs/prices, **not** a provider-byte/API integration or a real market claim.

**Additional public-sector research lead, not yet catalogued/admitted:** Geobasis NRW's [INSPIRE WFS 'öffentliches Eigentum'](https://www.geoportal.de/info/5b576174-4cdc-46cb-afaf-d7b3abf5923d) publishes property-level *public ownership* context; the metadata says nonpublic owners are anonymised. This might help *municipal/public-sector* synthetic portfolios after field-level privacy and rights screening. DO NOT pull or retain `Eigentümer`, `Buchungsblattkennzeichen`, identifying free text or individual property owners into public CAT training/analytics. Public ownership status is not evidence that the building is insured by R&V.

**Before model integration:** run canonical landscape contract + generated Markdown parity tests in the repository; inspect new source's licence and original per-field rights; use a small polygon-only, non-personal provider sample with a fixed snapshot and hash; quantify multi-parcel, multi-building and many-address relationships. No scientific/rights/source admission follows automatically from passing these checks.

## Original API accessibility probes — 2026-11-04

| Candidate | Original bounded/metadata endpoint | Observed response | Interpretation |
| --- | --- | --- | --- |
| Netherlands BRK perceel | https://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/perceel/items?f=json&limit=1 | HTTP **200**, application/geo+json, one feature; timeStamp=2026-11-04T20:16:15Z | Operational bounded machine-readable response for one record; not licence/admission or BAG relation |
| NRW INSPIRE ALKIS parcels | https://www.wfs.nrw.de/geobasis/wfs_nw_inspire-flurstuecke_alkis?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities | HTTP **500**, OGC Proxy Internal Server Error | Access not confirmed through this fetch route; block any claim of available feature bytes |
| NRW INSPIRE ALKIS parcels, canonical provider syntax | https://www.wfs.nrw.de/geobasis/wfs_nw_inspire-flurstuecke_alkis?REQUEST=GetCapabilities&SERVICE=WFS | HTTP **500**, same error | Failure was not merely explicit VERSION parameter; provider/proxy path-specific issue remains possible |

Response metadata and one Dutch feature structure were inspected only; **no raw provider feature bytes, owner/title identifiers, geometry dumps or full transaction files committed**. Dutch sample fields include cadastral identifier, municipality, area, validity/status and MultiPolygon geometry. Official CC BY 4.0 statement and live response do not equal model admission. See https://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1?f=html and https://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/perceel?f=json.

**NRW source-vintage drift:** Geoportal's WFS metadata lists ALKIS source vintage **2026-09-01**, but GovData's current listing describes **2026-10-01** (https://www.govdata.de/suche/daten/inspire-nw-flurstucke-grundstucke-alkis1b731). This is unresolved catalogue inconsistency; do not pin raw features until original service responds and its actual version is captured.

**Pilot choice updated:** first bounded live candidate ingestion should use the Netherlands' confirmed OGC parcels endpoint. NRW remains a Germany/R&V priority, blocked pending an independent service-health/proxy retry or sanctioned official alternative download. None of these probes establish BAG crosswalk, physical building identity, building replacement cost, insurer coverage or TIV.

## First same-bbox real-provider PDOK evidence — 2026-11-04

**Bounded location window (CRS84 west,south,east,north):** `5.1202,52.0902,5.1206,52.0906` (a very small research window). Queries use the same bbox and `limit=40`, `f=json`:

- BRK: https://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/perceel/items?bbox=5.1202,52.0902,5.1206,52.0906&limit=40&f=json — timestamp 2026-11-04T20:25:18Z, 19 parcel MultiPolygon features, `numberReturned=19`, no `next` link.
- BAG: https://api.pdok.nl/kadaster/bag/ogc/v2/collections/pand/items?bbox=5.1202,52.0902,5.1206,52.0906&limit=40&f=json — timestamp 2026-11-04T20:25:22Z, 21 building Polygon features, `numberReturned=21`, no `next` link.
- BAG status observed: 19 `Pand in gebruik` (in use) and 2 `Niet gerealiseerd pand` (not realised). Non-realised buildings are *not* active exposure.
- **Illustrative geometry-centroid containment diagnostic** (local recentered shoelace calculation, not verified PostGIS overlap): 13/21 building centres fell inside one of 19 returned parcel geometries; 8/21 did not; no centre fell in >1 parcel; among 19 in-use buildings, 11 had one parcel-centroid candidate. This does **not** mean the other 8 buildings lack land, nor that the 13 are legally verified parcel/building relations. Building and parcel snapshots are both time-sensitive and original data should not be redistributed without scope review.
- A naive shoelace centroid using absolute 5.x/52.x degree coordinates gave numerically unstable results for tiny rooftops. **Recenter polygon coordinates before computing area-weighted centroid**; the corrected diagnostic found zero building centroids outside their own Polygon for this test. Always distinguish 'centroid-in-parcel' from actual building footprint overlap/area proportion. The open cadastral map is indicative and not a legally precise boundary survey.

**New reproducibility code, offline/fail-closed:** `scripts/audit_pdok_brk_bag_centroid_v0.py` and `tests/test_audit_pdok_brk_bag_centroid_v0.py`. The diagnostic requires local bounded original GeoJSON snapshots and a separately declared shared bbox; rejects result pagination, wrong CRS84 coordinate ranges, older than one-day source-time drift, sensitive owner/address/title fields, future ambiguity or invalid data. It only prints aggregate candidate counts, never source IDs. This program is **not** a polygon intersection engine and must never feed an exposure model until a licensed source manifest and accurate spatial join are independently reviewed.

```sh
python -m unittest tests.test_audit_pdok_brk_bag_centroid_v0 -v
python scripts/audit_pdok_brk_bag_centroid_v0.py --parcels /private/pdok-parcels-40.json --buildings /private/pdok-bag-panden-40.json --bbox 5.1202,52.0902,5.1206,52.0906
```

**Validation status:** current CI is pending as of this research note; do not claim these new Python unit tests have passed until execution evidence is available. No parcel/building source records, household details, addresses, or provider bytes have been committed.

## Direct official building crosswalk: BGT Bebouwing → BAG pand — 2026-11-04

**Important change of plan:** The official BRK Kadastrale Kaart [Bebouwing collection](https://api.pdok.nl/kadaster/brk-kadastrale-kaart/ogc/v1/collections/bebouwing?f=html) is a BGT-derived building-footprint subset with an explicit `identificatie_bag_pnd` field linking to BAG `pand.identificatie`. It is neither the same entity as the cadastral `Perceel` nor an independent validation source: the BGT building geometry and BAG ID share documented official lineage. Catalogued separately as `nl.kadaster.bgt-bebouwing-bagid.2026` because the *feature class and intended role* are distinct from parcel geometry, not because it is an independently measured hazard observation.

Live source check in the same bounded CRS84 window `5.1202,52.0902,5.1206,52.0906` with `limit=40` (all responses `numberReturned` consistent, **no `next` links**):

| Source collection | 2026-11-04 response timestamp | Feature count | What it contains |
| --- | --- | ---: | --- |
| BRK `perceel` | `20:32:13Z` | 19 | parcel geometries / stable cadastral IDs, not owners |
| BRK `bebouwing` | `20:32:15Z` | 9 | BGT-derived building geometries and explicit BAG pand IDs |
| BAG `pand` | `20:32:11Z` | 21 | registered building attributes and lifecycle status |

**Direct official ID relation:** all 9 BGT features have nonempty `identificatie_bag_pnd` and each matched one of the 21 returned BAG IDs: **9/9 unique matched BAG pand identities**. All 9 matched BAG buildings have status `Pand in gebruik`; BGT statuses were `bestaand`. An exploratory stabilised-centroid containment test additionally placed all **9/9** BGT building centres in one of the 19 BRK parcel geometries. That latter parcel relation is **not** an official ID link; it remains an unverified spatial candidate until correct EPSG:28992 projected polygon intersection, share-of-footprint areas, partial overlap, split parcels and temporal geometry are assessed.

**Interpretation:** a valuable provisional chain exists: `BRK cadastral parcel polygon ⇢ BGT-derived Bebouwing polygon ⇢ explicit BAG pand ID ⇢ BAG building characteristics`. Never assert 9/9 nationwide completeness or apply the 9/9 statistic to the other 12 BAG buildings (BGT is explicitly a subset). A building can occur on multiple parcels; a parcel can host multiple buildings; one BAG pand may have multiple BGT source geometries. This chain is still not a legal ownership record, a policy assignment, a reconstruction-cost estimate or an insured total value.

**Executable, offline fail-closed identity diagnostic:** `scripts/audit_pdok_bgt_bag_identity_v0.py` plus `tests/test_audit_pdok_bgt_bag_identity_v0.py`. It counts exact ID matches, duplicate geometries per BAG ID, missing/ambiguous source IDs and lifecycle status in aggregate without outputting individual identifiers or addresses. No provider bytes have been checked into Git.

```sh
python -m unittest tests.test_audit_pdok_brk_bag_centroid_v0 tests.test_audit_pdok_bgt_bag_identity_v0 -v
python scripts/audit_pdok_bgt_bag_identity_v0.py --bgt /private/pdok-bgt-bebouwing.json --bag /private/pdok-bag-panden.json --bbox 5.1202,52.0902,5.1206,52.0906
```

**Next scientific gate:** use approved/verified original feature bytes with an independent exact ID and geometry receipt. In projected CRS EPSG:28992, calculate ST_Area(ST_Intersection(bgt.geom, parcel.geom))/ST_Area(bgt.geom) for all intersecting parcels, report multi-parcel/multi-building topology and coverage including polygons outside the query bbox. Do not allocate 100% of one building's cost to every overlapping parcel. Only then consider building-level exposure priors from independently justified construction replacement-cost inputs. Unit tests/CI and rights admission remain independent.
