<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V Allgemeine 2025 — source-bound Neon research readiness v1

**Rechecked 2026-11-05.** A read-only research-only [SQL gate](../../research_runners/sql/rva_solo_2025_neon_readiness_v0.sql), not a new legal-entity registration, insured CAT portfolio, licensed source import or model approval. It can never assert that the real insurer lacks customers or locations merely because the research database has zero registered positions.

## Reused legal identity evidence, not a second directory

- **German solo underwriter:** R+V Allgemeine Versicherung Aktiengesellschaft (publisher alias R+V Allgemeine Versicherung AG), Wiesbaden, HRB 2188 per [official issuer imprint](https://www.ruv.de/impressum). Solo LEI **5299009UN4CBXZ336M65**, also recorded against HRB 2188 by [Bloomberg's LEI record](https://lei.bloomberg.com/leis/view/5299009UN4CBXZ336M65). Crucially, our repository already has an [ACPR regulator LEI/source proof](../../research/observations/berlin_named_carrier_lei_temporal_preflight_20261105_v0.toml), [regulator record 225615](https://acpr.banque-france.fr/fr/fiche-detaillee/rv-allgemeine-versicherung-aktiengesellschaft-0), and [working independent identity-checker](../../research_runners/public_named_insurer_lei_identity_gate_v0.py). Reuse those exact canonical observations; do not invent another register or treat the Italian branch as a German company.
- **Separate parent:** R+V Versicherung AG, HRB 7934, LEI **529900Z5KBA9KJP6EK09** per [its own publisher imprint](https://www.rv-re.com/de/imprint). The SQL excludes this identifier from the solo company. The unrelated Italian R+V branch LEI **815600FA8F92119B8D12** was already excluded by the referenced Berlin preflight.
- **Different parent concepts:** The original [2025 HGB report](https://www.ruv.de/ueber-uns/unternehmen/geschaeftsberichte) states R+V KOMPOSIT Holding GmbH holds **94.5%** of R+V Allgemeine and is 100% held by R+V Versicherung AG. A LEI consolidation parent is **not necessarily the immediate equity owner**.

## Three non-interchangeable observed anchors (2025)

| Exact issuer/accounting population | Original issuer source | Amount or count |
| --- | --- | ---: |
| **Solo Solvency II SFCR**, Fire & Other Property, 2025 gross written premium | [2025 solo SFCR](https://www.ruv.de/dam/jcr%3A9c8441a7-28dd-4d98-9b79-3eb3c8b4afa5/2025-SFCR-Allgemeine.pdf), printed p. 11 | **EUR 2,223,182,000** |
| **Solo HGB**, self-written connected-buildings gross booked premium | [Publisher 2025 HGB report index](https://www.ruv.de/ueber-uns/unternehmen/geschaeftsberichte), printed p. 8 | **EUR 997,710,000** |
| **Solo HGB**, connected-buildings year-end policies/contracts | Same 2025 HGB, movement table printed p. 77 | **1,060,546 contracts** |

All are issuer financial/accounting observations; **none is physical building inventory, address, company-specific regional share, replacement value, insured TIV or catastrophe claims**. The premiums use different accounting scopes and may not be reconciled or divided by the year-end contract count as an earned premium proxy.

The [2019–2025 source-typed HGB research](../../research/observations/rva_solo_hgb_property_2019_2025_v0.toml) already flags **two corporate perimeter breaks**: a Condor merger in 2024, and the 2025 **R+V Direktversicherung AG** merger effective **1 August 2025** with **economic effect back to 1 January 2025**. Distinguish changes in legal entity mix from underwriting growth; never interpret naive 2024-to-2025 differences as physical portfolio growth. The [2025 SFCR typed observation](../../research/observations/rva_solo_2025_public_sfcr_v0.toml) remains a distinct accounting source.

## Current Neon result (exact SQL fetched from this branch and executed as one SELECT)

Neon project: **insurance-risk-core**; default branch; database **insurance**; 2026-11-05. No DML or DDL.

| Output | Live count |
| --- | ---: |
| verified_solo_entities | 0 |
| issuer_source_linked_solo_entities | 0 |
| verified_solo_identifier_rows | 0 |
| exact_source_bound_solo_lei_rows | 0 |
| parent_lei_wrongly_on_solo_rows | 0 |
| group_or_other_candidates | 2 |
| solo_directory_candidates | 1 |
| other_rv_directory_candidates | 3 |
| source_bound_exact_sfcr_property_gwp_rows | 0 |
| source_bound_exact_hgb_building_contract_rows | 0 |
| source_bound_exact_hgb_building_gwp_rows | 0 |
| company_linked_portfolios (all types) | 0 |
| company_linked_synthetic_portfolios | 0 |
| company_linked_reported_aggregate_portfolios | 0 |
| company_linked_real_restricted_portfolios | 0 |
| company_linked_portfolio_versions | 0 |
| company_linked_exposure_units | 0 |
| next_gate | BLOCKED_UNVERIFIED_OR_AMBIGUOUS_SOLO_LEGAL_ENTITY |

**Why still blocked?** A research directory candidate, GLEIF LEI observed in a GitHub research file, and an issuer PDF citation are **not the same as a registered, source-key-linked, verified Neon legal-entity row**. This gate requires a matching complete legal person, source-backed exact LEI (not a generic identifier), separate original-accounting metric rows and an independently versioned research portfolio. The final status even when those are filled is **RESEARCH_ONLY_NEEDS_HAZARD_VULNERABILITY_RIGHTS_AND_TREATY_REVIEW**.

## Exact next admission tasks (proposed, not executed)

1. **Verify and version source bytes and permissions:** official company imprint, original HGB/SFCR PDF hashes and original ACPR/GLEIF record status. Earlier TOML and retrieved PDF text **do not** establish newly independently hash-verified provider bytes or bulk redistribution rights.
2. **Register legal entity with issuer evidence:** exact long German legal name, HRB 2188 and issuer source key; attach verified LEI 5299009UN4CBXZ336M65 under separately reviewed identity source, not parent LEI or Italian branch. Re-run identity gate.
3. **Register three distinct published financial observations:** source-keyed 2025 SFCR Fire/Other Property premium EUR 2,223,182,000, HGB connected-buildings direct premium EUR 997,710,000, and year-end connected-buildings stock 1,060,546 contracts. Preserve both accounting bases and scopes.
4. **Build scenario-only exposure:** use [existing company-anchored national macro scenario sensitivity](rva-2025-issuer-anchored-geography-identification-v0.md), without GWP-to-TIV mapping. Create a versioned synthetic portfolio, independent geography weights and explicit coverage assumptions only after separate review.
5. **Native CAT/finance gate:** compatible original hazard and vulnerability, checked rights, geocoded OED exposures, scenario-bound policy terms and explicit fictional reinsurance; independently review annual occurrence/sample probabilities and Gross/Net EP. No model or insurer scientific approval implied.

## Coordination with the parallel synthetic OED exporter

[OpenCatastrophe-data PR #1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373) already prepares an OED 5.0 **synthetic** 10,000-policy sample (or optional full fictional policy population) from the separate 400-Kreis × ten-age-band research allocator. Its outputs deliberately have **no geolocated insured site positions** and are marked NOT_GEOLOCATED_NOT_MODEL_READY. The new database source/identity gate here is therefore a **precondition** before any company-labelled OED rows from #1373 could be registered as Neon insurer exposure, and #1373 must not be treated as a native loss/OEP/AEP result. Reuse #1373; do not create a redundant OED exporter in #1372.

The [offline source-contract tests](../../tests/test_rva_solo_neon_readiness_v0.py) check consistency of existing typed source records, both LEIs, accounting distinctions, two merger years and absence of database mutation SQL. They **do not replace running SQL against Neon**. The SQL was successfully executed; full GitHub CI and independent code review must be checked separately. No productive Neon rows or external original PDF bytes were added.
