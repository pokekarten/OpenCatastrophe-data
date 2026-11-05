<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# 45 unresolved official-regulator research observations — primary-source recheck

**Source recheck performed on 2026-11-01** against live official public
register pages and GLEIF LEI API. This is an incremental **source-identity
check** of selected existing CAT-Neon research observations; the source
registers are not imported as a complete population and no crosswalk,
new legal entity, insurance exposure or CAT model input is admitted.

## APRA (Australia): 18/18 official section match

All **18** research observations in
`insurance-risk-core/main.entity.licence_observation` with
`feed_id=apra_general` and missing `organization_id` appear as exact
Unicode-normalised text matches **within APRA's specific "Authorised to
conduct new or renewal insurance business" section**, not just elsewhere
on the page. APRA's official register is headed "List of registered general
insurers", with source update date **23 September 2026**:

https://www.apra.gov.au/registers/list-registered-general-insurers

This establishes that the names on the selected research rows occur in
APRA's published *authorised* list as presented during the 2026-11-01
check. It is **not** a verified ACN, ABN, ARBN, LEI, domicile, licence
condition, ownership link or a complete APRA market inventory. All 18
rows still lack structured `lei` and `local_registration_id`.

## MAS (Singapore): 20/20 exact class-and-name matches

All **20** currently unlinked observations in the MAS curated research
feed appear as exact Unicode-normalised names in the **corresponding
official MAS Financial Institutions Directory category**, rather than in
an unfiltered collection.

| Official MAS insurance category | Matched unlinked research rows | Official public source |
| --- | ---: | --- |
| Reinsurer (General) | **13 / 13** | [MAS General](https://eservices.mas.gov.sg/fid/institution/print?sector=Insurance&category=Reinsurer%20%28General%29) |
| Reinsurer (Composite) | **5 / 5** | [MAS Composite](https://eservices.mas.gov.sg/fid/institution/print?sector=Insurance&category=Reinsurer%20%28Composite%29) |
| Direct Insurer (General) | **1 / 1** | [MAS Direct General](https://eservices.mas.gov.sg/fid/institution/print?sector=Insurance&category=Direct%20Insurer%20%28General%29) |
| Direct Insurer (Composite) | **1 / 1** | [MAS Direct Composite](https://eservices.mas.gov.sg/fid/institution/print?sector=Insurance&category=Direct%20Insurer%20%28Composite%29) |

There is **no assumption** that a "Singapore Branch" is a new Singapore
incorporated legal entity. The names are listed in the directory, not
authenticated by local UEN or parent home-country LEI, and public
directory status does not establish any CAT treaty eligibility or
underwriting portfolio.

## EIOPA (EU): 7/7 GLEIF LEI Level-1 corroborations

The remaining **seven** `eiopa_insurers` observations carry an exact
recorded LEI. Independent GLEIF original HTTP API reads on 2026-11-01
found all seven LEIs as `ISSUED`, with `ACTIVE` legal entities and the
same jurisdictions as the EIOPA observations. **Five** original legal
names were exact; **one** EIOPA name was recorded as a GLEIF preferred
ASCII transliteration; **one** expanded the abbreviated legal form.
**Three** local registry-number texts matched GLEIF `registeredAs`
exactly; **four** need separate register-scheme review.

See [seven-row evidence and individual original GLEIF SHA-256 values](eiopa-gleif-seven-identity-check-20261101.md)
and the [successful public original-source GitHub run](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41327623712).

EIOPA original public register:
https://register.eiopa.europa.eu/registers/register-of-insurance-undertakings .
The source EIOPA research rows have **null `source_as_of`** and their original
CSV bytes are **not pinned**. Do not infer fresh/current insurer licence
authorisation from the GLEIF legal-entity status.

## Summary and permitted next steps

| Research cohort | Rows rechecked | Still unlinked in Neon | Missing work |
| --- | ---: | ---: | --- |
| APRA | 18 | 18 | Exact ACN/ARBN/ABN or LEI, official source-byte/rights/conditions checks |
| MAS | 20 | 20 | Home-country branch versus Singapore company, UEN, LEI, licensed role |
| EIOPA/GLEIF | 7 | 7 | EIOPA source date and national-regulator confirmation, four local-number schemes |
| **Total** | **45** | **45** | No unverified legal links or portfolio promotion |

The [read-only Neon triage SQL](../../research_runners/sql/regulator_45_identity_triage_readonly_v0.sql)
reports the persistent database state separately. A successful name or LEI
source check must **not** silently change `identity_resolution_status`,
`entity.organization`, group relationships, portfolio exposure, admitted
source classes or any financial/CAT model result.

The APRA and MAS checks were from publicly accessible rendered primary
register sections. The exact original raw HTTP bytes and byte-level
SHA-256 for those *two* providers were not acquired or pinned through this
research task; do not mislabel page-text matches as original-byte receipts.
