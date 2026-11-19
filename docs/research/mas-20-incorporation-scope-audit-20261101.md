<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# MAS insurance cohort: 20 verified institution-detail pages and incorporation scope

**Observed 2026-11-01; source-identity research only.** A separate live check
fetched **all 20 official MAS Financial Institutions Directory detail pages**
corresponding to the 20 unlinked
`insurance-risk-core/main.entity.licence_observation` research rows.
All 20 pages displayed the precise institution name and the same insurance
licence category as in Neon. The repository's read-only source URL and
`Incorporated in`-label mapping is in
[`research_runners/sql/mas_20_incorporation_scope_readonly_v0.sql`](../../research_runners/sql/mas_20_incorporation_scope_readonly_v0.sql).
This audit carries MAS metadata and per-record official detail URLs;
it does **not** publish MAS page content or claim a byte-identical HTTP
source receipt.

## Verified differences that matter for a worldwide insurer model

| Test | Observed result |
| --- | ---: |
| Official MAS individual detail pages matched on name and licence class | 20/20 |
| MAS detail-page label says `Incorporated in` outside Singapore | 18 |
| MAS detail-page label says `Incorporated in Singapore` | 2 |
| Research observation name explicitly contains `Singapore Branch` | 16 |
| Unlinked rows with `home_country IS NULL` in CAT Neon | 20/20 |
| Pre-existing organization links created or changed by this review | 0 |

The 18 non-Singapore MAS labels break down into Germany 4, Bermuda 4,
United States 3, and one each for China, Spain, United Kingdom,
Switzerland, South Korea, Turkey and Japan. The two Singapore MAS labels
refer to **ALLIANZ INSURANCE SINGAPORE PTE. LTD.** (no branch in its name)
and **XL RE EUROPE SE SINGAPORE BRANCH** (explicit branch in its name).
The label describes the public MAS institution record, **not necessarily
the country of incorporation of a global legal entity**. It must not
silently populate `entity.organization.domicile_country` or
`entity.licence_observation.home_country` without a reviewed source and
relationship contract.

Selected official examples:

- [Allianz SE Singapore Branch](https://eservices.mas.gov.sg/fid/institution/detail/3329-ALLIANZ-SE-SINGAPORE-BRANCH):
  `Incorporated in Germany`, MAS `Reinsurer (Composite)`.
- [Allianz Insurance Singapore Pte. Ltd.](https://eservices.mas.gov.sg/fid/institution/detail/232430-ALLIANZ-INSURANCE-SINGAPORE-PTE-LTD):
  `Incorporated in Singapore`, MAS `Direct Insurer (Composite)`.
- [General Reinsurance AG Singapore Branch](https://eservices.mas.gov.sg/fid/institution/detail/3097-GENERAL-REINSURANCE-AG-SINGAPORE-BRANCH):
  `Incorporated in Germany`, MAS `Reinsurer (Composite)`.
- [Aspen Bermuda Limited Singapore Branch](https://eservices.mas.gov.sg/fid/institution/detail/239249-ASPEN-BERMUDA-LIMITED-SINGAPORE-BRANCH):
  `Incorporated in Bermuda`, MAS `Reinsurer (General)`.

## Exception: XL Re Europe SE — keep two registration identities separate

[MAS XL RE EUROPE SE Singapore Branch detail](https://eservices.mas.gov.sg/fid/institution/detail/419759-XL-RE-EUROPE-SE-SINGAPORE-BRANCH)
reports `Incorporated in Singapore` and `Reinsurer (General)` for the
Singapore institution. Independently,

- [GLEIF Level-1 LEI `6354005OC5UTPXJQ9E28`](https://api.gleif.org/api/v1/lei-records/6354005OC5UTPXJQ9E28)
  returns `XL RE EUROPE SE`, country of legal jurisdiction **IE**,
  `ACTIVE` entity, `ISSUED` LEI and Irish legal registration
  **423311**.
- [UK Companies House overseas-company record FC038352](https://find-and-update.company-information.service.gov.uk/company/FC038352)
  independently records the company as **incorporated in Ireland**,
  Irish register number **423311**.
- [The insurer's own Singapore transfer notice](https://axaxl.com/-/media/axaxl/files/pdfs/about-us/our-companies/singapore/crchxlre-sot-notice-of-intention-axa-xl-14-nov-version.pdf)
  explicitly describes **XL Re Europe SE** as incorporated in Ireland
  with a registered Singapore branch **XL Re Europe SE Singapore Branch**
  and Singapore branch UEN **T23FC0075C**. This is historical notice
  evidence, not a current CAT portfolio or proof of transfer completion.

**Resolution for research:** Record **two different evidence scopes**:
(1) `MAS-institution-local-incorporation-label=Singapore` for the branch;
(2) `GLEIF-parent-legal-jurisdiction=IE` for the legal entity, with
Irish registration 423311 and the referenced Singapore branch UEN.
Do **not** treat the MAS label as if it superseded the GLEIF legal
entity, and do not promote a legal-entity or branch relationship in Neon
until the precise first-party register identity and its effective dates
are reviewed under the existing crosswalk governance.

The Singapore public branch UEN found in historical issuer documentation
must not be silently assigned to the distinct Irish parent LEI. The
model should treat a local licensed branch/establishment, the legal
company and the corporate group as **three separately keyed scopes**.

## Execution and open gates

The read-only SQL audit was executed against CAT-only Neon main and
returned **20/20** present, **0** wrong licence categories, **16** branch
labels, **18** foreign MAS labels, **2** Singapore MAS labels and **1**
explicit XL identity-scope conflict. The real `home_country` columns
remain **NULL** for all 20. Synthetic-only SQL regression tests are in
`tests/test_mas_20_incorporation_scope_readonly_v0.py`.

No official MAS original page response body or publisher byte SHA-256 was
pinned here, so this is *live rendered-page verification* only. Neither
the global legal parent identity, effective licence conditions, CAT
portfolio, branch-to-parent treaty allocation, loss location nor
regulatory solvency figures can be inferred from the detail-page label.

**Model release, legal matching and database writes remain blocked.**
