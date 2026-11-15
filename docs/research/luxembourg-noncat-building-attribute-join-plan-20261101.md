<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg building attribute enrichment from non-CAT datasets — source-to-field plan

**Date: 2026-11-01. Status: research and evidence checked, not admitted data.**
Related canonical discovery: `landscape/sources-luxembourg-cross-domain-building-20261101.json`.

## Why this is unusually high-leverage

The existing, real EUBUCCO v0.2 Luxembourg `LU00` original Parquet has **186,171** building rows, but only **74 non-null construction-year values**; `floors` is non-null in all 186,171 rows with 181,134 **model-estimated**, and height is non-null in all rows but many values have non-observed provenance. These counts are documented from exact SHA-pinned original GitHub Actions runs (merged #919). A 250m x 250m central Luxembourg rooftop-versus-EUBUCCO test found **149 ACT roof segments, 45 EUBUCCO footprints, 9 isolated high-IoU matching candidates and 136 ambiguous ACT segmentation cases** (merged #924). **Do not confuse roof polygons with individual structures.**

This research identifies *where new, independent evidence might be found for missing building age, shape, roof, use and high-value special construction*, rather than using synthetic missing-value fills.

## Field-to-source decision map

| Target attribute / problem | Source | Original evidence and join | Forbidden inference / blocker | Priority |
| --- | --- | --- | --- | --- |
| Roof pitch/azimuth, roof-vs-building segmentation | Klima-Agence 2025 solar cadastre | Published 58.8MB `.shp` + 212.2MB `.dbf` building-polygon Shapefile parts; accompanying vendor document names `hid`, `pv` and separate WMS **roof-facet** `tilt`, `aspect`, `flat`, `area3d` | **Do not assume facet fields occur in building SHP**. Publisher labels 'Other (Open)', not yet commercial-cleared. `hid` != ACT `buildingid`. Photovoltaic *potential* != actual equipment. Check available data and WMS access separately | P0 |
| Reliable construction-era distribution | STATEC RP2021 `DF_B1706` + municipality tables `DF_B1707` | Official housing census counts by age band, dwelling/building type and occupancy | Dwelling counts **not** building counts; aggregate age-band shares must never be assigned deterministically to individual EUBUCCO polygons or used as independent proof of them | P0 |
| Historic building age upper/lower bounds | ACT 1967, 2001, 2025 aerial photography | Independent time-specific appearance checks on human-reviewed or model-labelled rooftops with known image dates | 1967 portal **licence unspecified**: block byte ingestion/redistribution until written confirmation. 2001 and 2025 portal CC0. Presence is only an age constraint, NOT actual year or survival of original structure | P1 |
| Current national historic/protected property flags | Géoportail/INPA Cultural Monuments INSPIRE GML (6.4MB, Jul 2026) | GML geometries and preserved protected-site identifiers, followed by reviewed intersection with ACT rooftop/official cadastral parcels | Protection is site/parcel/object scope; no universal building-age or material classification; many-to-many geometry possible | P1 |
| Public facility floor/energy exposure | Luxembourg Ministry of Economy EU 2023/1791 Art.6 May 2026 `Inventaire.xlsx` | Publicly disclosed heated/cooled public assets >250m2, one building per workbook row, energy reference area, measured consumption if available, EPC PDF reference | Partial nonrepresentative inventory, rights for XLSX/PDF reuse need explicit review; floor energy reference area != footprint or insured replacement value. Keep public address/operator fields out of model's public diagnostics | P1 |
| National building-stock changes | STATEC permits `DF_D411x` versus completions `DF_D4200`, surface `DF_D4202` | Calibrate national/regional growth after EUBUCCO upstream vintages; preserve permit vs completed distinction | No exact building/polygon IDs and differing regions, 2016–2026 source vintages; never invent individual demolished/new houses from aggregate flows | P1 |
| Public addresses quality | ACT CACLR Oct 2026 1.9MB ZIP | Official street/house-number/postcode reference, separate permissioned CTIE REST API | Official register **does not contain coordinates**, and address/dwelling/parcel/building are not one-to-one. Avoid linking individual dwelling EPC or owners into the public registry | P2 |
| Residential energy-efficiency distribution | Luxembourg Economy Ministry anonymised aggregate EPC request | Explicit official request process for nationally aggregated residential-only energy certificates | **Not public building-level API or microdata**. Needs user-submitted approved request; never scrape or claim direct per-building joins | P2 |
| Cross-country age distribution | Eurostat census 2021 `cens_21dwop_r3` | NUTS3 dwelling counts by period/occupancy as regional priors | Not geolocated building data; missing/suppressed cells and dwelling-vs-building denominators must be preserved | P2 |
| Independent (?) European dwellings | JRC-ESTAT 2021 census 1km dwelling grid | 1km estimated disaggregation anchored to LAU dwelling totals | **NOT independent of EUBUCCO**: producer explicitly lists EUBUCCO v0.1, DBSM, Overture, GHS-BUILT upstream. Use as an aggregate consistency challenge only | P2 |
| Municipal renovation aid | Klima-Agence 2025 policy eligibility spreadsheet | Structural incentive-policy availability (subsidies eligible for roof insulation, retrofit, heat pump) | Eligibility is NOT an observed retrofit, paid subsidy or increased resilience of any individual building. Only context | P3 |

## Primary source anchors and sizes / rights

- Solar cadastre source: <https://data.public.lu/en/datasets/potentiel-solaire-au-luxembourg/>. Provider's 2025 German documentation is <https://download.data.public.lu/resources/potentiel-solaire-au-luxembourg/20251003-115312/dokumentation-datenexport-wms-luxemburg-20250904.pdf>. The provider documentation explicitly says its building `hid` connects *its own* product files, not ACT/EUBUCCO namespaces; `x_2169/y_2169` and WGS84 coordinates describe a point *inside* the roof polygon, not necessarily its centroid. The WMS lists building-level `hid` and roof-facet `tilt/aspect/flat` in different layers. It also describes a 2020 existing PV/ST system-detection layer; this is historic **model detection**, not verified 2025 asset registry.
- 1967 aerial imaging: <https://data.public.lu/en/datasets/orthophoto-1967/>. Provider license label 'License Not Specified', 12.3GB full-country file; this is research discovery only, no authorised download yet.
- 2001 imagery: <https://data.public.lu/en/datasets/orthophoto-officielle-du-grand-duche-de-luxembourg-edition-2001/>, 316 files with municipality JP2 tiles, catalogue CC0.
- 2025 summer image: <https://data.public.lu/en/datasets/orthophoto-officielle-du-grand-duche-de-luxembourg-edition-ete-2025/>, 10cm and EPSG:2169 with original flights 2025-05-10..13; full-country 64GB RGB, use only licensed bounded tiles or WMS, not the full national product.
- Historic/protected sites: <https://data.public.lu/en/datasets/inspire-annex-i-theme-protected-sites-protected-sites-cultural-monuments/>, official CC0 GML 6.4MB.
- Government EPC aggregate request: <https://meco.gouvernement.lu/fr/domaines-activites/energie/efficacite-energetique/acces-donnees-batiments.html>; residential aggregates on application, not a public building register.
- Public buildings energy inventory: <https://data.public.lu/en/datasets/inventaire-dans-le-cadre-de-larticle-6-de-la-directive-ue-2023-1791-relative-a-lefficacite-energetique/>; initial incomplete dataset, separate file-level rights and scope review.
- JRC dwelling grid: <https://data.jrc.ec.europa.eu/dataset/50cfa4c6-406e-47ce-a092-64a2c5d18303>; modelled grid derived in part from EUBUCCO v0.1 and DBSM, cannot serve as unbiased independent building truth.

## First reproducible pilot to advance beyond a catalogue

**P0 experiment A: Klima-Agence solar roof source receipt.**

1. Obtain **exact 2025 original** five Shapefile components `SHP/DBF/SHX/PRJ/CPG` only after provider rights decision ('Other (Open)' is not an automatically accepted commercial licence). Capture immutable original HTTPS URLs, declared 2025 version, individual SHA-256, field encodings, spatial CRS and unique `hid` count; do not use the unreliable multipart-like catalogue md5 strings as validated SHA.
2. Audit field names and actual per-building roof geometry versus the separate vendor WMS faceted roof layers; record whether `tilt/aspect/flat/area3d` are in *accessible downloads* or WMS only. Do not manufacture unavailable original source features.
3. Use exact prior ACT2023v2 GeoPackage `buildingid` and EUBUCCO `LU00` SHA receipts, the same fixed 250m x 250m window, and compare **three distinct segmentation schemas**: ACT 2023 rooftop polygon, Klima-Agence modelled 2025 building roof, EUBUCCO original ground/cadastre footprint. Preserve 1:n / n:1. Do not claim independent geometric validation of another dataset when they share upstream footprints or elevation models.
4. For any *actual accessible facet polygons* in original source, construct building-to-facet **one-to-many** relationships, retaining original `hid`, facet slope, aspect and roof-area references; never flatten/multiply facets into one fictitious independent insured building. Use human geometric adjudication before any join to ACT `buildingid`.

**P0 experiment B: missing age fields with aggregate, not individual, validation.**

1. Retrieve exact LUSTAT tables `DF_B1706`, `DF_B1707`, `DF_D4200` using official dissemination/API as allowed; document table dimensions, time/reference geographies, suppression, population, number of *dwellings* vs *buildings*.
2. Compute region/building-type-level age-band distributions and permitted/completed flows (with coherent reference years and correct units).
3. Apply priors only to *distributions* of synthetic portfolios and label `statistical_estimate` with uncertainty and lineage. **Do not fill individual EUBUCCO missing construction years with a made-up exact year**.
4. Later use only physically verified historic imagery or official uniquely matched building document (permits, register) for actual bounded building-specific construction constraints.

## Status and next gates

All 14 candidates remain `not_admitted`, rights/science `not_reviewed`. No raw files, rooftop addresses, named individuals, energy certificates, building-to-insurer crosswalks or artefacts are saved in the GitHub source catalogue or directly to production insurance Neon. A broad public website catalogue/linked PDF is evidence that a dataset is described, **not** that it is downloadable, legally reusable or scientifically valid.

The success metric is *new verified actual roof/age/construction evidence*, with source identity, age and segmentation error rates measured. Source counts alone do not improve CAT model loss accuracy.
