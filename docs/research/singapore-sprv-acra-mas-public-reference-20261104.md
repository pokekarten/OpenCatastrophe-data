<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Singapore SPRVs: original ACRA/UEN, MAS licence and audited ILS loss references

**Checked 2026-11-04; public source reference and research-only identities.** This document points to the official sources and a *bounded* published insurance loss observation. It contains **no original government CSV, GLEIF HTTP response body, signed financial-statement PDF, cedant policy information, production-model input or Neon mutation**.

## Original Singapore ACRA entity register

The official dataset [Entities Registered with ACRA](https://data.gov.sg/datasets/d_3f960c10fed6145404ca7b821f263b87/view) is published by Singapore's **Accounting and Corporate Regulatory Authority** on data.gov.sg. Canonical dataset ID: `d_3f960c10fed6145404ca7b821f263b87`, collection `1`. [Original dataset metadata](https://api-production.data.gov.sg/v2/public/api/datasets/d_3f960c10fed6145404ca7b821f263b87/metadata) returned last update **2026-10-14 17:10:49 +08:00** and published coverage through **2026-10-11**. Fields include exact `uen`, `entity_name`, `uen_status_desc`, `issuance_agency_desc`, `entity_type_desc`, `uen_issue_date`. The dataset is updated monthly; today's API lookup is not proof of a company's status beyond that snapshot.

The [official documented datastore search endpoint](https://guide.data.gov.sg/developer-guide/dataset-apis/search-and-filter-within-dataset) was queried separately with `resource_id=d_3f960c10fed6145404ca7b821f263b87` and the exact JSON `filters={"entity_name": "NAME"}` for each of the four companies below, with `limit=10`. Each returned **exactly one** source record, `issuance_agency_desc=ACRA`, `uen_status_desc=Registered`, `entity_type_desc=Local Company`, and an exact legal-name/UEN match. The four UENs already exist as verified `ACRA_UEN` identifiers in a **separate read-only Neon query**; nothing was inserted or altered.

| Official ACRA exact legal name | Original UEN | UEN issue date | Official MAS institution code | Management role shown by MAS |
|---|---|---|---|---|
| ASTRO RE PTE. LTD. | `202117654Z` | 2021-05-19 | `RA16G` | Marsh Management Services Singapore |
| MANATEE RE III PTE. LTD. | `201912999K` | 2019-04-23 | `RA03G` | Marsh Management Services Singapore |
| NAKAMA RE PTE. LTD. | `202130681G` | 2021-09-02 | `RA18G` | Aon Insurance Managers Singapore |
| TOMONI RE PTE. LTD. | `202206915M` | 2022-02-28 | `RA21G` | Aon Insurance Managers Singapore |

Direct regulator references:
- [MAS official Insurance Company Returns](https://www.mas.gov.sg/statistics/insurance-statistics/insurance-company-returns), which prints all four institution codes and names.
- [Astro MAS Financial Institutions Directory](https://eservices.mas.gov.sg/fid/institution/detail/242727-ASTRO-RE-PTE-LTD).
- [Manatee MAS Financial Institutions Directory](https://eservices.mas.gov.sg/fid/institution/detail/224391-MANATEE-RE-III-PTE-LTD).
- [Nakama MAS Financial Institutions Directory](https://eservices.mas.gov.sg/fid/institution/detail/245761-NAKAMA-RE-PTE-LTD).
- [Tomoni MAS Financial Institutions Directory](https://eservices.mas.gov.sg/fid/institution/detail/251605-TOMONI-RE-PTE-LTD).

MAS classifies the entities as **Special Purpose Reinsurance Vehicles** licensed to contract with ceding insurers and fund obligations via insurance securitisation; this is **not** the same as a primary retail carrier or a consolidated global reinsurance group. A named MAS *manager* is a **service provider**, not automatically equity parent, treaty counterparty, insured portfolio owner or beneficial owner. A Singapore UEN does not automatically imply a globally registered GLEIF LEI.

The official data.gov.sg dataset identifies an Open Data Licence; refer to [the official licence](https://data.gov.sg/open-data-licence) for permitted use and exclusions. No automatic download/republication or import approval follows from this research note. MAS/BSX source rights and investor-report usage need independent review.

## Audited Manatee FY2024: bounded observed catastrophe settlement

The [signed audited Manatee Re III FY2024 financial statements](https://content.bsx.com/CompanyDocuments/1099939271/Manatee%20Re%20III%20-%20FS%20FY2024_final%20%28SIGNED%29.pdf) (printed note **page 20**, PDF page index **21**) disclose the specific **Hurricane Ida 2021** Class A loss for cedant **Safepoint Insurance Company**, as at **2023-12-31** and **2024-12-31**. This is not a native vendor model or exposure-location dataset.

| Original claim-note field, USD | 2023 | 2024 |
|---|---:|---:|
| Class A estimated Manatee loss payment | 17,947,952 | 17,947,952 |
| Cumulative paid to Safepoint | 13,218,418 | 14,837,495 |
| Remaining claim reserve | 4,729,534 | 3,110,457 |

Two exact original-note identities hold: **2023 paid + reserve = 17,947,952**; **2024 paid + reserve = 17,947,952**. Paid-to-date rose **1,619,077**, while remaining reserve fell **1,619,077**, with unchanged total estimate. The note also gives Safepoint's ultimate net loss **65,817,833 USD**, an attachment level **3,000,000 USD**, and a **displayed** (rounded) participation **28.57%**. An *exact* 28.57% multiplier on the simple excess over attachment differs from the reported payment by **897.1119 USD**, proving that blindly treating the printed percentage as exact contract wording is not justified. A 2/7 fraction is only a compatible arithmetic hypothesis, **not verified treaty economics**.

The company identifies **Manatee Shares Trust** as immediate/ultimate holding entity in printed note page **10**, and **Intertrust (Singapore) Ltd.** as share trustee. Separately, MAS identifies **Marsh** as an operating manager. These are distinct roles. Reinsured peril, cedant, SPV owner, asset location and investor security must not be merged by brand or by common management. Under FRS 117, the consolidated insurance liability and variable-note fair-value accounts have their own accounting definitions, not a direct one-for-one mapping from this public claim-note bridge.

## Later original securities lifecycle: current exposure caution

The historical audited FY2024 claim does **not** imply the 2019 notes or their original collateralised reinsurance capacity remain in force on 2026-11-04. The original issuer-supplied Bermuda Stock Exchange announcements document separate securities lifecycle events:

- [BSX announcement, 21 October 2022](https://www.bsx.com/article/1100801701): **Class B**, originally US$20,000,000 Series 2019-1 principal-at-risk variable-rate notes, **early redemption** reported to BSX and **delisted 2022-10-21**. The announcement does not give the actual cash principal repayment amount or the residual underlying treaty exposure.
- [BSX announcement, 29 June 2026](https://www.bsx.com/article/1100807273): maturity and redemption reported for **Class A**, originally US$20,000,000, **due 2026-06-08**, and the principal-at-risk variable-rate note program; both **delisted 2026-06-29**. The [original BSX Class A security record](https://www.bsx.com/company/1099939272) identifies **ISIN US562011AA46**, original BSX listing date **2019-06-21**, and status **Delisted** as of the issuer announcement.

A source-date caveat matters: the signed FY2024 annual report (note 13, printed p. 24) describes original **2019-05-30** issuances and an **original due date in June 2022**, whereas the official later BSX class security record gives the 2026 extended maturity. These are **different reported vintages**, not a licence to overwrite the 2019 issuance terms. Keep original dates, later amendments and actual delisting events separate.

**Correct classification:** `NOT_CURRENTLY_LISTED_AT_BSX` for Class A, Class B and the identified note program as of 2026-11-04. This **does not prove** that the SPV has dissolved, that the cedant has no remaining claims, that all contractual obligations have expired, that investors received the full original face value, or that there are no newer ILS securities issued by this legal entity. The actual contractual wording, settlement notices and winding-up filings must be verified separately. Neither face value nor the Class A/B lifecycle is an active 2026 insurer portfolio line.

The **canonical public source landscape** now includes the ACRA government company dataset, MAS SPRV regulator details, original Manatee FY2024 financial report and the two original BSX exit announcements in `landscape/sources-singapore-ils-acra-mas-20261104.json` with deterministic generated Markdown. Original ACRA singleton-response SHA-256 fingerprints and official query URLs are separately in `docs/research/acra-four-sprv-original-response-receipts-20261104.json`. No exchange-page HTML, raw government JSON, financial PDF or underlying reinsurance contract is checked in.

## Implementation boundary

The **private NextGen research PR #279** retains executable bounded GLEIF Level-1 metadata validation plus a reproducible integer-only [Manatee claim-note bridge](https://github.com/pokekarten/NextGen/pull/279): nine focused synthetic/adversarial tests passed locally; both code blobs match locally executed sources. **This public registry carries links and audit observations only**. Original ACRA data rows, GLEIF responses, MAS web pages and BSX PDF content are *not* checked into this repository.

Neither identity verification nor public historical claim reconciliation is admission of CAT hazard, vulnerability, geolocated TIV, real insurer insured positions, inward/outward treaty wording, retrocession or capital calculations. No database writes, source-import approvals, financial model admission or vendor-reconstruction claims.
