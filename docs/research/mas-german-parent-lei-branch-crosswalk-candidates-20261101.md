<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Three selected MAS foreign-branch candidates: verified legal LEIs, not new legal entities

**Evidence reviewed 2026-11-01.** The CAT-only Neon database already
has three verified Germany-domiciled legal organizations and their verified
GLEIF LEIs. Independent 2026-11-01 GLEIF Level-1 API reads confirmed all
three parent legal entities `ACTIVE` and their *parent* LEI registrations
`ISSUED`, with legal jurisdiction **DE**. The MAS Financial Institutions
Directory separately lists exactly the corresponding named **Singapore
branches**, with `Incorporated in Germany`.

This is a three-case **manual link proposal**, not an approved new
licence-to-parent mapping, organisation row, legal group, or CAT exposure.

| Existing MAS research key / licence | Existing verified DE organization | Parent LEI / registeredAs | Official MAS and GLEIF |
| --- | --- | --- | --- |
| `other_001` — Allianz SE, Singapore Branch / Reinsurer (Composite) | Allianz SE | `529900K9B0N5BT694847` / HRB 164232 | [MAS institution](https://eservices.mas.gov.sg/fid/institution/detail/3329-ALLIANZ-SE-SINGAPORE-BRANCH), [GLEIF parent](https://api.gleif.org/api/v1/lei-records/529900K9B0N5BT694847) |
| `other_010` — Allianz Global Corporate & Specialty SE Singapore Branch / Direct Insurer (General) | Allianz Global Corporate & Specialty SE | `F240A7PWJB2BLKELB442` / HRB 208312 | [MAS institution](https://eservices.mas.gov.sg/fid/institution/detail/3526-ALLIANZ-GLOBAL-CORPORATE-SPECIALTY-SE-SINGAPORE-BRANCH), [GLEIF parent](https://api.gleif.org/api/v1/lei-records/F240A7PWJB2BLKELB442) |
| `other_006` — Münchener Rückversicherungs-Gesellschaft, Singapore Branch / Reinsurer (Composite) | Münchener Rückversicherungs-Gesellschaft Aktiengesellschaft in München | `529900MUF4C20K50JS49` / HRB 42039 | [MAS institution](https://eservices.mas.gov.sg/fid/institution/detail/3092-MUNCHENER-RUCKVERSICHERUNGS-GESELLSCHAFT-SINGAPORE-BRANCH), [GLEIF parent](https://api.gleif.org/api/v1/lei-records/529900MUF4C20K50JS49) |

**Additional independent issuer evidence**:

- [Allianz worldwide Singapore contacts](https://www.allianz.com/en/about-us/company/contact/singapore.html)
  identify `Allianz SE Singapore Branch` separately from `Allianz
  Insurance Singapore Pte. Ltd.` and `Allianz SE Reinsurance Branch Asia
  Pacific`. Do not collapse operating units merely by a shared street
  address or group brand.
- [Munich Re worldwide office listings](https://www.munichre.com/en/company/about-munich-re/munich-re-worldwide.html)
  and [Munich Re's own imprint](https://www.munichre.com/de/allgemein/impressum.html)
  independently connect the Singapore and Munich presence and quote
  parent `HRB 42039` and `529900MUF4C20K50JS49`.
- An [Allianz Global Corporate & Specialty SE Singapore Branch
  disclosure for 2022](https://commercial.allianz.com/content/dam/onemarketing/commercial/commercial/countries/singapore/AGCS-SG-Annual-Report-2022.pdf)
  explicitly describes the Singapore branch as part of the German
  company. This is **historical fiscal-year evidence**, not a 2026
  underwriting portfolio or model input.

## Crucial distinction: Allianz Commercial has a separate branch LEI

The 2026-11-01 GLEIF original API resolves these **two distinct LEI
identity scopes**:

| Field | Singapore branch | German head office / legal entity |
| --- | --- | --- |
| LEI | `984500D1360HXAUAEF86` | `F240A7PWJB2BLKELB442` |
| LEI entity.category | `BRANCH` | `GENERAL` |
| Entity status | `ACTIVE` | `ACTIVE` |
| Registration status | **`LAPSED`** | **`ISSUED`** |
| Registry / number | ACRA `T11FC0131K` | Munich HRB 208312 |
| Legal country jurisdiction | DE | DE |
| Legal address country | SG | DE |

There is a **direct GLEIF relationship record**, rather than a fuzzy
brand/name inference:

- [Official GLEIF `head-office-relationship`](https://api.gleif.org/api/v1/lei-records/984500D1360HXAUAEF86/head-office-relationship):
  `IS_INTERNATIONAL_BRANCH_OF`, start-node branch
  `984500D1360HXAUAEF86`, end-node head-office
  `F240A7PWJB2BLKELB442`. The relationship object says **`ACTIVE`**
  but its **registration.status is `LAPSED`**.
- [GLEIF branch record](https://api.gleif.org/api/v1/lei-records/984500D1360HXAUAEF86):
  legal entity.category `BRANCH`, registration ACRA `T11FC0131K`,
  `LAPSED` LEI registration.
- [GLEIF parent record](https://api.gleif.org/api/v1/lei-records/F240A7PWJB2BLKELB442):
  category `GENERAL`, `ISSUED` LEI registration and Germany
  legal jurisdiction.
- An [insurer-published Singapore insurance terms document](https://commercial.allianz.com/content/dam/onemarketing/commercial/commercial/countries/singapore/03-Singapore-Summit-ToB.pdf)
  independently names company registration `T11FC0131K`. This is a
  first-party published number, **not** a direct ACRA registry API
  read or legal confirmation of registration validity as of today.

**Do not** interpret `relationship.status=ACTIVE` as
`relationship.registration.status=ISSUED`, or infer that the parent
entity's `ISSUED` LEI renews the branch's `LAPSED` LEI. The branch
may still be listed/licensed by MAS even when the GLEIF LEI registration
has lapsed. A lapse is an identifier-data-quality state, **not proof of
insurance licence cancellation**.

## Independent CAT-Neon source-scope check

The read-only SQL
[`research_runners/sql/mas_three_verified_lei_branch_review_v0.sql`](../../research_runners/sql/mas_three_verified_lei_branch_review_v0.sql)
was executed on CAT-only Neon main and returned **exactly 3/3**
eligible-for-manual-review MAS observations, **3/3** separate existing
verified parent organizations, **0** added organization links and
**0** new exposures. The SQL requires exact pinned MAS names and
licence classes plus the parent LEI, expected parent legal name,
domicile country and `identity_status=verified`. No string-only fuzzy
join or silent branch country overwrite is permitted.

Synthetic offline negative tests under
`tests/test_mas_three_verified_lei_branch_review_v0.py` run the
actual read-only SQL to reject a wrong MAS licence class, wrong parent
legal name, or an already-linked source observation. The distinct
`LAPSED` branch LEI is asserted.

**Next gate**: exact dated corporate/regulator evidence for each local
branch identifier, review of GLEIF relationship registration status and
legal entity-to-establishment model schema, then explicitly approved
branch-to-parent crosswalk rows. CAT exposures, group insurance shares,
reinsurance treaties and financial contracts remain unknown. No Neon
writes or model admission were performed.
