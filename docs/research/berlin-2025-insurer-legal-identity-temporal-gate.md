<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source-backed insurer legal-entity identity gate — Berlin 2025

**Review date: 2026-11-05.** This extends the already merged [eight reported insurer-to-corporate-account associations](public-named-insurer-account-report-v0.md) and [five-insurer Berlin corporate dwelling reference](public-named-insurer-berlin-corporate-stock-report-v0.md), without editing those observational sources or mapping real buildings to insurers.

## Original-source findings and non-matches

| Original Berlin Senate source label | Legal entity identity status | Critical source and consequence |
| --- | --- | --- |
| **R+V Allgemeine Versicherung AG** | **Regulator-correspondence match**, German legal company LEI `5299009UN4CBXZ336M65` | [French ACPR public regulator record](https://acpr.banque-france.fr/fr/fiche-detaillee/rv-allgemeine-versicherung-aktiengesellschaft-0), reference 225615: R+V Allgemeine Versicherung Aktiengesellschaft, Raiffeisenplatz 1, Wiesbaden, Germany, LEI as quoted. This matches the issuer's German corporate entity *name and jurisdiction*, not the still-unknown building policy details or 2026 renewal. |
| **R+V name collision** (excluded, **not** an original Senate legal-party assignment) | LEI `815600FA8F92119B8D12` must **not** be assigned to the German company | [Bloomberg LEI registration record](https://lei.bloomberg.com/leis/view/815600FA8F92119B8D12) says legal address Milan, entity category **BRANCH** and parent/head-office R+V Versicherung AG `529900Z5KBA9KJP6EK09`. This is different from the German R+V Allgemeine legal entity. Also, that parent is **not** automatically identical with R+V Allgemeine. |
| **Allianz AG** | **Unresolved short source label** | [ACPR registry identifies Allianz Versicherungs-Aktiengesellschaft](https://acpr.banque-france.fr/fr/fiche-detaillee/allianz-versicherungs-aktiengesellschaft) with LEI `529900X5FHSYN4P5R285`, but the Berlin Senate uses only "Allianz AG." It does **not** establish that this is the named contracting company rather than another insurer/holding entity in the group. Candidate LEI stored only as **not joined**. |
| **ERGO** | **Unresolved brand/source label** | The Berlin answer reports only ERGO, not a specific legal underwriting company, verified registered name, register identifier or LEI. No LEI guess in the output. |
| **Generali** | **Unresolved brand/source label** | [ACPR separately lists Generali Deutschland Versicherung AG](https://acpr.banque-france.fr/fr/fiche-detaillee/generali-deutschland-versicherung-ag-0), LEI `5493007JO8UEQ68NG776`. The Senate merely writes "Generali", which does **not** establish that the named 2025 Gewobag insurer was that precise legal entity. Candidate LEI stored only as **not joined**. |
| **Westfälische Provinzial Versicherung AG** | **Historical merged legal name; 2025 contracting-party mapping unresolved** | [Austrian financial regulator FMA](https://www.fma.gv.at/bestanduebertragung-von-der-westfaelische-provinzial-versicherung-aktiengesellschaft-auf-die-provinzial-versicherung-ag-ehemals-provinzial-rheinland-versicherung-ag/) confirms the transfer of the whole non-life book to **Provinzial Versicherung AG**, effective 2021-01-01. [Provinzial 2021 corporate annual disclosures](https://www.provinzial-konzern.de/) also describe a merger entered in December 2021. A 2025 Senate document still naming the former insurer is a **legacy-company-name risk**, not proof that the now-extinct company was a current standalone underwriter. Do not silently replace the HOWOGE insurer with a successor LEI or infer actual renewal. |

## Machine-readable controls

The canonical research-specific [five-label TOML](../../research/observations/berlin_named_carrier_lei_temporal_preflight_20261105_v0.toml) separately captures **only one regulator-confirmed German LEI association**, three ambiguous/brand original labels, and one historical name with documented successor company. Unknown names retain null legal-entity identity in reports. Its [read-only validator and report projection](../../research_runners/public_named_insurer_lei_identity_gate_v0.py):

- Crosschecks the five original labels and eight original carrier–company associations from the already merged Senate observation rather than creating another independent account registry.
- Uses the existing repository ISO 17442 LEI checksum implementation; refuses the Italian branch code as the German legal R+V, refuses an Allianz/Generali candidate becoming a contract-party LEI solely from a shorter Senate label, refuses ERGO guesses and rejects silent auto-substitution of the historical Westfälische Provinzial entity.
- Marks all eight company relationships as original *April 2025* reported relationships, never current 2026 verified coverage. Prevents counting a legal company, a foreign branch or group ownership as an extra insured portfolio.
- Uses SHA-256 of the two exact local canonical TOML bytes, not falsely presented as **newly independently hash-verified GLEIF/ACPR HTTP original responses**. Official regulator and GLEIF original bytes were not fetched or pinned in this run.
- Keeps insurer account relationships, corporate dwelling stock, legal entity registration, legal successor, group ownership, branch registration, active underwriting licences and insured site locations as distinct fact types.

## Reproduce (no internet or DB writes)

```bash
python research_runners/public_named_insurer_lei_identity_gate_v0.py > /tmp/berlin_named_carrier_legal_identity_v0.json
python -m unittest discover -s tests -p 'test_public_named_insurer_lei_identity_gate_v0.py' -v
```

All 17 negative and positive unit tests are synthetic/in-memory transformations of public observation metadata; no provider bytes, personally identifying building addresses or third-party proprietary records are committed. The runner fails on conflicting source labels, unexpected entity identifiers, invalid LEI checksums, missing merger evidence, branch-as-head-office assignment and false current policy or CAT asset assertions.

## Still blocked

1. Preserve **R+V regulator-identified LEI** as research evidence, not as validated insurer permission, exact insurer claim allocation, policyholder asset or CAT model admission. Original regulator/GLEIF response bodies and versioned record status should be captured independently before cross-database materialisation.
2. Obtain a **source-account-specific** original insurer name or tender/contract-party schedule to resolve Allianz, ERGO and Generali; do not "solve" an original source ambiguity using a guess about the largest or best-known group subsidiary.
3. For the 2021 merged Westfälische Provinzial legal company, verify the actual relevant **2025 HOWOGE contractual legal party** and effective 2026 renewal status independently. Historical merger is proven; HOWOGE contract terms are not.
4. Maintain separate review for regulatory insurer identity, insurer group perimeter, underwriting risk locations, building-dwelling conversions, coverage fraction, co-insurance share, TIV, peril and treaties. The report remains **non-admitted research**.
