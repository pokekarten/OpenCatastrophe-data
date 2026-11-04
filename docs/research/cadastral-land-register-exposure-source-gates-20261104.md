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

**New discovery candidate:** \`uk.hmlr.transaction-uid-uprn-lookup.2026\` (12th catalogue entry). Official HM Land Registry [technical specification](https://www.gov.uk/government/statistical-data-sets/technical-specification-transaction-unique-identifier-and-uprn-look-up-table-dataset) confirms this is a *separate* monthly transaction UID → addressable UPRN relation, also without back-dating. Coverage includes matched freehold **and** leasehold registered sale transactions where OS/Royal Mail PAF address-linkage exists. Multiple UPRNs may correspond to one sale (e.g. several flats in a building), and unaddressed land/new builds may have none. UPRN is neither an INSPIRE freehold polygon nor a physical building ID. Supplier declares OGL 3.0 for HMLR **and** Ordnance Survey source contributions; Price Paid address-related licensing still applies. Do not join one UPRN to multiple buildings without independently verified object identity and matching vintage.

**Executable bounded diagnostic:** \`scripts/audit_hmlr_inspire_sale_linkage_v0.py\` accepts a stripped, analysis-only JSON consisting of \`source_family\`, \`snapshot_date\`, \`transactions\` (transaction UID / sale date / positive integer GBP paid), \`lookup\` (UID/INSPIRE ID) and \`polygons\` (INSPIRE ID). It rejects all unexpected fields including owners, addresses, title references, and restricted Grundbuch identifiers; bounds rows/bytes and checks dates, identities, duplicates and missing references. Aggregate output distinguishes *unique transactions* from *polygon links* and explicitly blocks interpreting sales prices as insured values, reinstatement costs or insurer ownership.

Run the **synthetic-only** unit tests:

\`\`\`sh
python -m unittest tests.test_audit_hmlr_inspire_sale_linkage_v0 -v
\`\`\`

Eight tests were run locally 2026-11-04 successfully before upload. One illustrative synthetic test has £400,000 and £300,000 matched sales; the £400,000 sale relates to two distinct polygons. Summing across polygon rows incorrectly gives £1,100,000 instead of the correct £700,000 distinct matched transaction total. The audit reports an artificial **£400,000** overcount and suppresses exact duplicate link rows. This is a correctness demonstration with fake IDs/prices, **not** a provider-byte/API integration or a real market claim.

**Additional public-sector research lead, not yet catalogued/admitted:** Geobasis NRW's [INSPIRE WFS 'öffentliches Eigentum'](https://www.geoportal.de/info/5b576174-4cdc-46cb-afaf-d7b3abf5923d) publishes property-level *public ownership* context; the metadata says nonpublic owners are anonymised. This might help *municipal/public-sector* synthetic portfolios after field-level privacy and rights screening. DO NOT pull or retain \`Eigentümer\`, \`Buchungsblattkennzeichen\`, identifying free text or individual property owners into public CAT training/analytics. Public ownership status is not evidence that the building is insured by R&V.

**Before model integration:** run canonical landscape contract + generated Markdown parity tests in the repository; inspect new source's licence and original per-field rights; use a small polygon-only, non-personal provider sample with a fixed snapshot and hash; quantify multi-parcel, multi-building and many-address relationships. No scientific/rights/source admission follows automatically from passing these checks.
