<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# BNPB 2025 house damage and DOSM 2025 flood losses: official source field/rights preflight (2026-11-11)

**Evidence class:** source-provider public *metadata / text*, reviewed read-only using the available search/web intermediary. This is a source-specific research receipt, **not** original XLSX/PDF acquisition, exact HTTP byte-level receipt, scientific approval, release, licence admission, or insurance portfolio / model input. This document adds no second source registry: canonical candidate records live in [the 2026-11-11 landscape JSON](../../landscape/sources-observed-water-damage-wildfire-20261111.json).

## 1. BNPB: exact original dataset and two different XLSX products

Publisher: Indonesia's Badan Nasional Penanggulangan Bencana (BNPB), official Satu Data Bencana portal.

- Dataset landing page: https://data.bnpb.go.id/dataset/kompilasi-data-kejadian-dan-dampak-bencana-2025
- **Dataset/package ID:** `58878b43-41b5-4ffb-b851-c6d8c8c4d438`; website says publication `2026-07-01`, last modified `2026-07-08`, reporting year **2025**. The latter are not loss/event dates.
- Exact *province × peril house-damage* resource: https://data.bnpb.go.id/dataset/58878b43-41b5-4ffb-b851-c6d8c8c4d438/resource/43b83e79-c8b6-4b9a-b2f0-d1cbd9cfa636
  - Resource ID `43b83e79-c8b6-4b9a-b2f0-d1cbd9cfa636`, resource page advertises `XLSX`, size `18,955` bytes, data last updated `2026-07-02`.
  - Indexed data dictionary: `Kode Wilayah Provinsi`, `Provinsi`, `Latitude`, `Longitude`, and peril-specific columns `BANJIR`, `CUACA EKSTREM`, `ERUPSI GUNUNG API`, `GELOMBANG PASANG DAN ABRASI`, `GEMPABUMI`, `KEBAKARAN HUTAN DAN LAHAN`, `KEKERINGAN`, `TANAH LONGSOR`, `TSUNAMI`. `KEKERINGAN` and `TSUNAMI` are typed **text**, while several other peril columns are numeric. **Text, no-data, blank, and non-reported are not automatically numerical zero.**
- Distinct *event/severity summary* resource: https://data.bnpb.go.id/dataset/kompilasi-data-kejadian-dan-dampak-bencana-2025/resource/6e947c9c-2404-4c02-b743-34dc5320f399
  - Resource ID `6e947c9c-2404-4c02-b743-34dc5320f399`, `XLSX`, page-listed size `12,646` bytes, published product metadata date `2026-07-02`.
  - Dictionary includes `Kode Bencana`, `Jenis Bencana`, `Jumlah Kejadian`, `Rumah Rusak Berat`, `Rumah Rusak Sedang`, `Rumah Rusak Ringan`, plus casualties and facility impacts.
  - Despite a landing-page title containing `Menurut Provinsi`, the visible *resource dictionary* does **not** independently establish a province key for this summary. Do **not** join summary severity totals onto each province × peril record or infer province × peril × damage-severity cells without parsing the original XLSX sheet and verifying the exact meaning of each dimension.

**Original publisher's licence display:** each of these two resource pages labels its resource **Open Data Commons Attribution License** (ODC-By). This is more precise than the dataset's generic classification `terbuka` and is positive source evidence. Still review the exact asset scope, attribution and any upstream exceptions, dataset revisions, API-use conditions, and original publication terms before approving public bytes or CAT model use. Licensing the resource does **not** mean OpenCatastrophe has approved a download/redistribution or data admission.

**Access status of this review:** official provider HTML resource records were inspected; an attempted bounded read of `https://data.bnpb.go.id/api/3/action/resource_show?id=43b83e79-c8b6-4b9a-b2f0-d1cbd9cfa636` returned no accessible response in this environment. No source XLSX, SHA-256, row count, observed numerical damage, original workbook sheet layout or tested download URL is claimed. `43...` and `6e...` are publisher IDs, not hashes.

**Next original-byte acceptance challenge:** retrieve **only** these two pinned XLSX resources via a rights-reviewed, bounded no-redirect provider route outside Git. For each: preserve exact response URL/time/content-type/byte-size/SHA-256; verify XLSX ZIP integrity and native worksheet dimensions, province codes, peril column types, missing sentinels and severity/aggregation semantics; quarantine duplicates, non-finite values, unknown population/temporal coverage and numerical coercion. Use separately held-out events/years where source lineage allows it, never silently treat provincial geographic centroids as insured building locations.

## 2. DOSM: 2025 historical economic flood losses, **not insured claims**

- Official release: https://www.dosm.gov.my/portal-main/release-content/special-report-on-impact-of-floods-in-malaysia2025
- Official press statement: https://www.dosm.gov.my/uploads/release-content/file_20260415115507.pdf
- DOSM official portal terms: https://www.dosm.gov.my/portal-main/article/term-of-use
- Release date: `2026-04-15`; event/survey year **2025**; source headline total **636.9 million Malaysian ringgit** versus **933.4 million MYR** for 2024.

| 2025 economic loss component | Million MYR | Published methodological boundary |
|---|---:|---|
| Public assets and infrastructure | 380.2 | Separate government administrative records |
| Living quarters | 183.8 | Survey/field/telephone observations |
| Agriculture | 52.6 | Separate government administrative records |
| Business premises | 13.4 | Survey/field/telephone observations |
| Vehicles | 6.8 | Survey/field/telephone observations |
| Manufacturing | 0.1 | Survey/field/telephone observations |
| **Headline total** | **636.9** | Rounded reported sums, not audited insured losses |

The exact displayed six components sum to **636.9 million MYR**; this arithmetic is only an internal published-summary check, not raw-data validation. DO NOT convert a percentage of surveyed flood victims reporting insurance into national flood insurance penetration. The press statement's **5.5%** refers to people in the study/case studies, not all Malaysian policies.

### Explicitly unresolved regional contradiction

Publisher-indexed DOSM release text/media statement and a separately linked original infographic show **different state labels** beside some identical sector loss values (for instance which state is associated with the top `32.6 million MYR` residential-loss figure). The exact original infographic image versus PDF page should be inspected visually before attributing those figures to any state; a screenshot retrieval of the media-statement PDF was not available through the research interface at this review. **Quarantine region × sector targets**; trust the national total and six sector summaries only as presently corroborated by more than one official DOSM representation. This is a research observation requiring provider reconciliation, not an assertion that one published version is the authoritative correction.

### Official reuse terms and boundaries

The official DOSM `Term of Use` page says that data accessible through the portal can be copied, adapted, redistributed, combined with other data and used **commercially** as well as noncommercially under the government Open Data Terms of Use 1.0. It requires a credit reading **"Data source: Department of Statistics Malaysia"**, no false suggestion of governmental endorsement, lawful use, and updates or notices when data are withdrawn or superseded. This is **publisher-level positive rights evidence**, not a completed exact-release/third-party-rights review, public-byte admission or model approval. The current research landscape must retain `rights_review_status=not_reviewed` and `admission_status=not_admitted`.

### Next defensible scientific use

If and when source rights and original-byte provenance are verified, a predefined **2025 Malaysia flood economic-loss sector plausibility check** may compare a similarly scoped modelled historical gross economic loss estimate against the DOSM national/sector totals. It is not a direct comparison with insurer paid claims, replacement value/TIV, or 10,000-year annual OEP/AEP. A spatial model cannot calibrate individual building damage curves from a state-level economic total without explicit exposure, hazard, reporting and uncertainty treatment.

## Cross-source controls

- Retain separate source products and their exact years; a 2025 annual provincial report and a 2025 national survey do **not** define event-specific, independent severity-loss observations.
- Do not use national statistics as claim-level or building-level targets. Do not collapse unknown, missing or non-numeric sentinel values to zero.
- Never add provider original XLSX/PDF bytes to public Git in this non-admission phase.
- Re-run source licence reviews at the exact selected release before a public derivative or any commercial model use.
