<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V Allgemeine 2025 — Neon company/exposure readiness gate

**Research-only, 2026-11-05.** Read-only reconciliation, not legal-entity registration, raw-data import, source approval, observed insured portfolio or CAT run.

Executable SQL: [rva_solo_2025_neon_readiness_v0.sql](../../research_runners/sql/rva_solo_2025_neon_readiness_v0.sql).

## Exact issuer source and identity boundary

- **Solo legal entity**: R+V Allgemeine Versicherung AG, **not** R+V Versicherung AG (group parent) or another R+V-branded company. The [official 2025 solo SFCR](https://www.ruv.de/dam/jcr%3A9c8441a7-28dd-4d98-9b79-3eb3c8b4afa5/2025-SFCR-Allgemeine.pdf) identifies HRB 2188, Amtsgericht Wiesbaden, 31 December 2025 reporting date; the [issuer legal notice](https://www.ruv.de/impressum) independently states HRB 2188. These sources do not independently establish a verified LEI, insurer-location allocations or bulk reuse rights.
- **2025 accounting anchor**: EUR 2,223,182,000 *gross written premium* for Feuer- und andere Sachversicherungen, solo SFCR A.2. Reusable typed internal source receipt: [rva_solo_2025_public_sfcr_v0.toml](../../research/observations/rva_solo_2025_public_sfcr_v0.toml); FFBK cross-check: research/reinsurance/solo_sfcr_de_fr_profiles_2025_v0.json, profile RVA_DE_2025. This number is **not** insurer TIV, CAT-only premium, insured site count, PML, annual loss or market share.
- **Names must not auto-merge**: The directory label R+V Allgemeine Versicherung Aktiengesellschaft is a research-only legal-person **candidate**. The organization candidates R+V Versicherung and R+V Versicherung AG are **not** independent proof of the R+V Allgemeine solo carrier.

## Verified live read-only execution

Target: Neon **insurance-risk-core**, default branch, **insurance** database. The exact committed SQL file was fetched from GitHub and executed verbatim via the Neon SQL interface; no Neon database writes.

| Output column | 2026-11-05 result |
| --- | ---: |
| verified_solo_entities | 0 |
| verified_solo_identifiers | 0 |
| non_solo_group_or_other_candidates | 2 |
| solo_directory_candidates | 1 |
| other_rv_directory_candidates | 3 |
| source_linked_exact_property_gwp_rows | 0 |
| company_linked_portfolios | 0 |
| company_linked_portfolio_versions | 0 |
| company_linked_exposure_units | 0 |
| next_gate | BLOCKED_UNVERIFIED_OR_AMBIGUOUS_SOLO_LEGAL_ENTITY |

These are database state and evidence-gate results, not assertions that the actual insurer has no properties. Counts are not worldwide completeness measures. The query first requires exact legal-person name, verified identity state, DE domicile and insurer type, then looks up source-linked 2025 gross property premium and company-linked portfolio versions and exposure. A registered source key does not independently establish rights, original-byte authenticity or scientific admission.

## Ordered next steps

1. **Identify the exact solo company**: review the original official issuer/legal-register record, HRB 2188 and lineage, and resolve authoritative identifier (including LEI only if independently verified). Register a matching organization and verified identifier only after actual evidence review. Never infer the solo identity from a group candidate.
2. **Link source-qualified financial evidence**: independently recheck PDF original bytes/typed issuer receipt, publisher accounting basis and 2025 figures. The intended metric schema contract is metric_name=fire_and_other_property_gwp, value=2223182000, unit=EUR, currency_code=EUR, year=2025, business_scope=solo_direct, gross_net_basis=gross and measurement_kind=published_observation. It additionally needs a canonical registered source key. This is a contract, not authorization to write a metric now.
3. **Version synthetic scenarios separately**: use the existing [R+V fictional property bridge](rva-oasis-portfolio-bridge-v0.md), maintain distinct assumed site counts and TIV, require explicit scenario provenance. Never reverse-engineer actual insured site values directly from GWP or a bank/agency distribution map.
4. **Validate physical peril and financial stack**: independently review original hazard/vulnerability source rights, event geographies, perils, OED/ORD, explicitly fictional treaty assumptions, and a native reproducible multi-year loss engine. This SQL never declares CAT production-ready even after accounting and database registration; it deliberately returns RESEARCH_ONLY_NEEDS_HAZARD_VULNERABILITY_RIGHTS_AND_TREATY_REVIEW.
5. **Re-run and preserve proof**: record immutable Git blob, execution date, Neon project/database, returned row and any actual admitted source hashes. Git blob identity is distinct from the issuer PDF's original SHA-256.

## Scope and related work

This specialized company-specific database admission gate complements the generic insurer market-share research in OpenCatastrophe-data PR #1351 and the fictional Zurich gross/net research in NextGen PR #280; it does not replace them. No SQL DDL, DML, customer locations, provider binaries or production model approval are included.
