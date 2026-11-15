<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# US wildfire original-source event identity review (2026-11-03)

**Research-only, non-admission.** No provider dataset bytes have been fetched, persisted, imported into Neon, approved for commercial reuse or admitted to a CAT model. Two authoritative complementary products are recorded in [canonical landscape JSON](../../landscape/sources-us-wildfire-observations-20261103.json) and its generated Markdown view. GitHub paths here are public metadata only.

## Publisher evidence and distinct measurements

1. **MTBS, USGS/USFS:** [MTBS product](https://burnseverity.cr.usgs.gov/products/mtbs), [official direct-download catalogue](https://burnseverity.cr.usgs.gov/direct-download?product=MTBS), [2026 portal modernisation](https://www.usgs.gov/centers/eros/news/new-improvements-burn-severity-portal-announced). Fire perimeter polygons and burn-severity rasters for *mapped large fires*; portal range 1984-2026 is not proof of a complete 2026 season. The 2026 reprocessing altered some historical severity pixels, area estimates or coordinate representation, so legacy-vs-current comparison requires exact source vintage and projected area method.
2. **FPA FOD, USDA Forest Service:** [Seventh Edition original metadata](https://www.fs.usda.gov/rds/archive/products/RDS-2013-0009.7/_metadata_RDS-2013-0009.7.html), [current-edition REST MapServer](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer). The fixed archival edition `FPA_FOD_20260615` was published 2026-08-04, spans 1992-2024 and contains around 2.66 million georeferenced *incident points* from mixed fire-reporting systems. Archival downloads include GeoPackage and SQLite; the live MapServer may update between editions.

## Concrete proposed identity bridge (not executed)

- Read the **original USFS variable dictionary**, exact archived SQLite/GeoPackage edition, and MTBS original fire-ID field definitions; pin content identity, year, source version, checksum and time-of-download.
- First-stage deterministic linkage uses non-null, normalized `FPA_FOD.MTBS_ID` against MTBS event IDs with exact string comparison. Record cardinality and missing/duplicate/many-to-many matches. Do **not** silently replace unresolved IDs with name similarity, nearest point, temporal windows or overlapping polygon heuristics.
- Preserve `ICS_209_PLUS_INCIDENT_JOIN_ID` in a separate identity namespace. Avoid multiplying incidents because one MTBS perimeter may correspond to a complex fire or one incident may have multiple agency reports. MTBS and FPA FOD are **not independent scientific observations** where FPA FOD already incorporates `MTBS_ID`.
- For a bounded holdout, keep ignition/discovery **point** from FPA FOD, observed large-fire **perimeter** and **burn severity** from MTBS, published **fuel** from LANDFIRE, **surveyed structure damage** from CAL FIRE DINS and **building exposure** in separate typed roles. Burn severity, observed fire size, modeled potential, surveyed damage and insured losses are five different quantities.
- Quantify selection bias: MTBS only covers mapped large fires and also includes prescribed fires; FPA FOD requires only approximately one-square-mile minimum point precision and merges different jurisdictions. A zero join or missing mapped perimeter must not be interpreted as no fire or zero loss.

## Bounded next technical actions and blocking gates

1. Review original archive terms and any per-product API/service terms separately. A publicly accessible dataset is not yet redistribution or commercial-model permission. Preserve `not_reviewed` for both candidates until actual reviews.
2. T0 metadata: record exact archive edition and authoritative MTBS 2026 product/vintage. T1: only permitted bounded HEAD/metadata checks. T3: after rights review, one exact fixed-year/region sample, byte count, SHA-256, parsing and field-identity receipt outside public Git.
3. Write deterministic offline tests with **synthetic** repeated `MTBS_ID`, null IDs, false spatial neighbors, prescribed fires, duplicate reporting units and stale product version. A join must fail closed when version, CRS, event type or identity confidence is not pinned.
4. Promote a specific source to an admitted manifest only after legal and scientific review, exact asset evidence and an explicit consumer use. No raw data, policyholder detail, proprietary vendor results or inferred insured valuations belong in this public repository.

## Existing work overlap

Already known, not new source IDs: `noaa.ncei.storm-events` (weather reporting rather than wildfire polygons), `us.calfire.frap.historical-fire-perimeters.firep25-1` (California perimeters), `us.calfire.dins.structure-damage` (field damage), `us.nifc.wfigs.interagency-perimeters` (operational perimeter sources), `nasa.lance.firms.active-fire` (satellite hotspots), `us.landfire.fuel-vegetation.2025` (model fuel covariates). Proposed entries add historical mapped burn severity and nationally harmonized fire-report point IDs without duplicating those product identities.
