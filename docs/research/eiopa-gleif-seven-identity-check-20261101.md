<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Seven EIOPA licence observations: independent GLEIF Level-1 check

**Research evidence checked 2026-11-01.** Scope is the CAT-only Neon
`insurance-risk-core/main.entity.licence_observation` table, not a
production identity admission. The seven regulator *research observations*
all lack `source_as_of`, so the exact original EIOPA CSV date and source bytes
are **not pinned**. This is an identity consistency check with [GLEIF Level-1
API](https://www.gleif.org/en/lei-data/gleif-api), not a fresh EIOPA
authorisation or solvency-status determination.

The GLEIF API was independently queried for each of the seven exact LEIs
using `https://api.gleif.org/api/v1/lei-records/<LEI>`. All seven original
HTTP responses returned the requested LEI, expected legal jurisdiction and
legal-address country, active legal-entity status `ACTIVE`, and LEI
registration status `ISSUED`. These are GLEIF record properties, *not*
insurer licence statuses.

| LEI | EIOPA jurisdiction | Name relationship to GLEIF | EIOPA local ID vs GLEIF registeredAs | Review status |
| --- | --- | --- | --- | --- |
| [259400VDTC20UW6M5D80](https://api.gleif.org/api/v1/lei-records/259400VDTC20UW6M5D80) | LV | exact | `049` vs `40003494976`: different registry scope | Identity corroborated by LEI; local ID manual review |
| [63670018BQ5R7IKA8T76](https://api.gleif.org/api/v1/lei-records/63670018BQ5R7IKA8T76) | DK | exact | `53118` vs `39437392`: different registry scope | Identity corroborated by LEI; local ID manual review |
| [213800AEQ6JQDLCWQN31](https://api.gleif.org/api/v1/lei-records/213800AEQ6JQDLCWQN31) | ES | exact | `M0328` vs `M0328`: exact | Legal identity and local identifier corroborated |
| [213800LXNGNQ5O1XBW47](https://api.gleif.org/api/v1/lei-records/213800LXNGNQ5O1XBW47) | MT | exact | `C 51071` vs `C 51071`: exact | Legal identity and local identifier corroborated |
| [529900SURJXJXSY5O039](https://api.gleif.org/api/v1/lei-records/529900SURJXJXSY5O039) | LT | manual variant: GLEIF legal name expands `AB` to `Akcinė bendrovė` | `110051834` exact | Legal identity corroborated by LEI/registry number; name variant requires review |
| [95980020140005024486](https://api.gleif.org/api/v1/lei-records/95980020140005024486) | ES | GLEIF **explicitly lists exact EIOPA text as preferred ASCII transliteration** | `P3159` vs `1000334867575`: different registry scope | Strong alternate-name evidence; local ID manual review |
| [7437008CXP8UX8KITQ76](https://api.gleif.org/api/v1/lei-records/7437008CXP8UX8KITQ76) | FI | exact | `01450820` vs `0145082-0`: punctuation candidate, **not** exact | Identity corroborated by LEI; format/manual review |

**Audit totals:** 7/7 LEIs `ISSUED` and entities `ACTIVE`; 7/7 legal
jurisdictions agree; 5 exact legal-name matches, 1 exact preferred ASCII
transliteration, 1 separately flagged Lithuanian abbreviation/expansion;
3 exact local registered-as identifiers, 4 unresolved numbering/format
differences. No `entity.organization` rows were created or linked by
this check. The existing seven observations remain `unmatched`.

For a reproducible review, run
`python -m scripts.eiopa_gleif_seven_identity_receipt_v0 --live`.
This explicitly accesses only these seven public LEI endpoints with bounded
responses and outputs hashes and metadata, never raw provider rows, and
never writes to Neon. Synthetic offline regression tests are under
`tests/test_eiopa_gleif_seven_identity_receipt_v0.py`. Independently,
`research_runners/sql/eiopa_gleif_identity_7_readonly_v0.sql` checks the
seven existing Neon observations without using names as legal keys.

GLEIF reference data are provided under [CC0 1.0 and GLEIF's access terms](https://www.gleif.org/en/meta/lei-data-terms-of-use).
This work makes no claim of affiliation with or endorsement by GLEIF.
Primary official EIOPA register information is published at
https://register.eiopa.europa.eu/registers/register-of-insurance-undertakings.
The EIOPA register warns that its publication may differ from national
registers; independently verify licence status with the relevant
national authority before changing `identity_resolution_status`.

**Do not** infer corporate control, branches, group accounting, financial
metrics, exposure or treaty eligibility. Source original-byte hashes from
new GLEIF retrievals are not retroactive hashes for the prior EIOPA CSV.
All CAT model-input gates remain closed.


## Original GLEIF HTTP response SHA-256 evidence

A public [GitHub Actions original-source test](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41327623712)
successfully performed **7 of 7** explicitly bounded GLEIF API reads, following 10
synthetic fail-closed regression tests. Each original response body was hashed
**before** extracting the selected fields. The following are hashes of the
individual GLEIF API responses retrieved on 2026-11-01, **not** hashes of
EIOPA original CSV files or a permanent assertion that GLEIF records cannot
change.

| GLEIF LEI | Original response SHA-256 |
| --- | --- |
| `213800AEQ6JQDLCWQN31` | `71d4d2fac9f527ba43b104860dc91fa29adabdd5b9526433dc821141cef280be` |
| `213800LXNGNQ5O1XBW47` | `f8b6668646feb1ce52a9e952e98b996d6c94e3e231ce4b4cc561271b5e144f8e` |
| `259400VDTC20UW6M5D80` | `27ae892295f9bfe2e0c9dcf952efc42d811956d9779bd706d3f6a1127fb00301` |
| `529900SURJXJXSY5O039` | `02f7712781985683f908a8b825b39fbcb5a291466f892fac9d1119a44f96c907` |
| `63670018BQ5R7IKA8T76` | `e8423ea7b5445db25e8c0c40dc85665ee8e0a2c884e58a31d9a6a004776c1ffc` |
| `7437008CXP8UX8KITQ76` | `8e6efcea65af000158ad526129bc5b1fd8396b0fbd9e675a3157038dc7d54c19` |
| `95980020140005024486` | `c79fbd361182faa7f1d451342df3a1712a8bdd89300c524dc8b81d5077f4ce84` |

The execution retained no original response bodies in GitHub artifacts.
All seven reported the same statuses and name/registration review categories
as above. The results can be replayed only as a new dated observation because
the GLEIF API may publish newer data. No Neon writing was performed.
