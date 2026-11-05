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


## Isolated Neon identity-stage rehearsal (2026-11-05)

**Not production:** A disposable Neon branch named `rva-solo-identity-rehearsal-20261105`, branch ID `br-steep-hill-bahgylx3`, was created from default `main`. Only this branch received two metadata-only `registry.source_record` rows, one verified-legal-identity `entity.organization` row and its exact `GLEIF_LEI` identifier row. All four INSERTs were executed as one transaction. No source PDFs, model output, third-party raw data, personal customer information or company exposure were inserted.

Source metadata keys, based on canonical existing GitHub blobs:

| Source key | Existing canonical GitHub file, immutable blob SHA | Original reference and rights |
| --- | --- | --- |
| `research:rva:issuer:sfcr2025` | `research/observations/rva_solo_2025_public_sfcr_v0.toml`, `5425011d27d1e18d6b892066ed0c1b0c0e36c20c` | [Issuer imprint](https://www.ruv.de/impressum), publisher original bytes not re-hashed; use limited to legal identity metadata |
| `research:rva:acpr:lei20261105` | `research/observations/berlin_named_carrier_lei_temporal_preflight_20261105_v0.toml`, `912ca18ce95d61bfd5efea1388cbb003cbdc1bd2` | [ACPR ID 225615](https://acpr.banque-france.fr/fr/fiche-detaillee/rv-allgemeine-versicherung-aktiengesellschaft-0), original response bytes not re-hashed; metadata-only |

Both rows have `classification=landscape_candidate`, `admissible_for_raw=false`, explicit non-cleared third-party source rights and `provider_original_bytes_hashed=false`. Only the independent **legal-person identity** is verified, by corroborated publisher imprint + regulatory LEI + [external LEI record](https://lei.bloomberg.com/leis/view/5299009UN4CBXZ336M65), not the right to reuse documents or a company's risk placements. In particular, do not conflate legal identity `verified` with `model_input_ready`.

The exact read-only SQL from this PR was executed **twice**, once against default main and once against the isolated branch:

| Exact gate | Main | Isolated branch |
| --- | ---: | ---: |
| `verified_solo_entities` | 0 | 1 |
| `issuer_source_linked_solo_entities` | 0 | 1 |
| `exact_source_bound_solo_lei_rows` | 0 | 1 |
| `parent_lei_wrongly_on_solo_rows` | 0 | 0 |
| `source_bound_exact_sfcr_property_gwp_rows` | 0 | 0 |
| `source_bound_exact_hgb_building_contract_rows` | 0 | 0 |
| `source_bound_exact_hgb_building_gwp_rows` | 0 | 0 |
| `company_linked_portfolio_versions` | 0 | 0 |
| `company_linked_exposure_units` | 0 | 0 |
| `next_gate` | `BLOCKED_UNVERIFIED_OR_AMBIGUOUS_SOLO_LEGAL_ENTITY` | `BLOCKED_SOLO_SFCR_METRIC_NOT_SOURCE_LINKED` |

**New fail-closed financial requirement:** After this isolated test, the SQL now counts a published financial metric only when the source record has `review_status='verified_original_financial_observation'` plus both typed flags `publisher_original_sha256_verified=true` and `accounting_line_and_basis_verified=true`. This prevents an arbitrary research-only source-key from advancing financial readiness. It is deliberately **not** a requirement to redistribute the publisher PDF or to admit restricted original bytes as CAT loss input.

The public issuer PDF text was rechecked externally against the [2025 SFCR](https://www.ruv.de/dam/jcr%3A9c8441a7-28dd-4d98-9b79-3eb3c8b4afa5/2025-SFCR-Allgemeine.pdf), Fire/Other Property `2.223.182 TEuro` (PDF index page 12), and [2025 HGB](https://www.ruv.de/dam/jcr%3Ae0e32e31-09ff-4b0f-b693-2c6c9bee9bb5/01_GB%202025_R%2BV%20Allgemeine%20Versicherung%20AG_final.2026-04-21-14-59-23.pdf), `997.710 TEuro` (PDF index page 8) and `1.060.546` year-end contracts (PDF index page 77). The web PDF page-image inspection and separate original-byte download were unavailable in this check, so **no new original provider PDF SHA-256, page-image proof, or financial production approval** is claimed. The typed TOML values and observed source text agree; independent source-byte admission is still required.

**Promotion process:** keep main unchanged; independently acquire/pin original publisher file hashes and usage-rights decisions, review source contracts, and only then prepare separately reviewed idempotent legal-person/metric registration. Do **not** merge the Neon rehearsal branch as a replacement for main and do not import the fictional 10k Oasis OED sample as an observed company portfolio.


## 2026-11-05 update: original publisher PDFs pinned and isolated financial metric rehearsal

**This section supersedes any earlier statement in this document that the 2025 publisher PDFs were not hash-verified.** Actual original PDF bytes were downloaded ephemerally by [GitHub original-byte workflow #42095783671](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42095783671) and checked for source URL, complete PDF signature, issuer/financial text markers and exact page counts. A second run, [#42096075662](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42096075662), **PASS**, confirmed the same bytes and compared them against hard-coded SHA-256 and byte-length pins. Both were GitHub-hosted; **independent verification from a second execution environment has not been done**. The original PDFs were not copied to GitHub or Neon.

| Official source, 2025 | Original SHA-256 | Exact bytes | PDF pages | Semantic marker gate |
| --- | --- | ---: | ---: | --- |
| Solo SFCR, [issuer PDF](https://www.ruv.de/dam/jcr%3A9c8441a7-28dd-4d98-9b79-3eb3c8b4afa5/2025-SFCR-Allgemeine.pdf) | `0a941b729dc6b490a5ad285ae1e1f15f4aa8ec183fb00b3d470f780a99ff996a` | 2,069,226 | 86 | 4/4 |
| Solo HGB, [issuer PDF](https://www.ruv.de/dam/jcr%3Ae0e32e31-09ff-4b0f-b693-2c6c9bee9bb5/01_GB%202025_R%2BV%20Allgemeine%20Versicherung%20AG_final.2026-04-21-14-59-23.pdf) | `85a82b7a199d583e1e07efbc93317ce8bd3bab99381f54b742e997d70e2c19fa` | 1,468,631 | 98 | 4/4 |

New machine-readable, no-original-byte research source receipts: [SFCR TOML](../../research/observations/rva_solo_2025_sfcr_original_pdf_sha_receipt_v0.toml) and [HGB TOML](../../research/observations/rva_solo_2025_hgb_original_pdf_sha_receipt_v0.toml). New bounded [source runner](../../research_runners/rva_solo_original_financial_pdf_receipt_v0.py) and [11+ offline tests](../../tests/test_rva_solo_original_financial_pdf_receipt_v0.py) reject nonpublisher redirects, truncated/oversized PDFs, exact SHA drift and false financial vs insured-location claims. The runner uses pinned `pypdf==5.9.0` **only in the source-proof workflow** and never uploads PDFs, retains sensitive addresses or writes database rows.

**Isolated Neon research branch** `rva-solo-identity-rehearsal-20261105`, ID `br-steep-hill-bahgylx3`: after existing verified legal-person metadata, an atomic transaction registered **two additional original-source-only financial receipts** (`admissible_for_raw=false`, redistribution rights not cleared) and three separate 2025 typed *national financial/accounting observations*:

- SFCR Fire and Other Property solo GWP **EUR 2,223,182,000**, business_scope=solo_direct, gross, 2025.
- HGB direct Connected Buildings GWP **EUR 997,710,000**, separate HGB source and accounting scope.
- HGB Connected Buildings **1,060,546 year-end contracts**, as-of date **2025-12-31**, unit=contracts (not a geocoded building or location count).

The exact GitHub SQL was executed on Neon main and isolated branch after the transaction:

| Readiness evidence | Neon main | Neon isolated branch |
| --- | ---: | ---: |
| verified solo company and exact LEI | 0 / 0 | 1 / 1 |
| source-reviewed SFCR gross property premium | 0 | 1 |
| source-reviewed HGB connected-buildings gross premium | 0 | 1 |
| source-reviewed HGB connected-buildings year-end contracts | 0 | 1 |
| company-linked synthetic portfolios / portfolio versions / exposure units | 0 / 0 / 0 | 0 / 0 / 0 |
| next gate | `BLOCKED_UNVERIFIED_OR_AMBIGUOUS_SOLO_LEGAL_ENTITY` | `BLOCKED_COMPANY_SYNTHETIC_EXPOSURE_NOT_REGISTERED` |

**Important:** No production Neon writes were made. The isolated three financial rows are **verified source-specific observations**, not insurance TIV, insured site counts, CAT model frequency, peril losses, net PML, source bulk-reuse rights, or a licence to upload original PDFs. The GitHub authoring branch and isolated Neon branch must **not** be merged/promoted automatically. The next milestone is separately source-bound, explicitly nongeocoded synthetic OED/Neon portfolio-version metadata from [PR #1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373); a native German GUL/IL/RI/AEP/OEP is **still blocked** until actual model-compatible hazard/vulnerability, WGS84 synthetic placement and validated insurance-financial terms.


## 2026-11-05 final research rehearsal: exact OED sample provenance, never a geolocated model

A separate Neon **research-only isolated branch** transaction registered **one** company-linked synthetic portfolio, **one** 2025 scenario version, **one** non-geocoded `regional_aggregate` exposure-unit **and one source metadata record** based on the independently validated [PR #1373 original OED six-scenario audit](https://github.com/pokekarten/OpenCatastrophe-data/blob/research/rva-2025-oed-staging-20261105/docs/research/rva-2025-oed-validated-scenario-comparison-20261105.md), exact Git blob `3df8b815ded3d01e1e60f99bf71982801bf0372c`, [source CI #42077035364](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42077035364).

- `portfolio_type=synthetic`, uniquely named `RVA_LIKE_2025_10K_FLAT_NONGEOCODED_RESEARCH`, solo insurer-linked for reproducibility, **NOT an observed R+V policy portfolio**.
- One version `UNIFORM_PHYSICAL_2022_AGE_FLAT_450K_SAMPLE_10K`; scenario weight `PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY`, invented flat 450k EUR per sample location, **10,000 fictional policies only**, **EUR 4.5bn hypothetical sample TIV**. The published 2025 national stock **1,060,546 contracts** is an *independent company control*, not an asset count assigned to 10,000 insurer locations. This toy value is not company TIV, a CAT loss, a premium-to-TIV inference or an estimate of insured assets.
- `exposure_unit.unit_type=regional_aggregate`, `region_code=DE_AGGREGATE_NOT_GEOLOCATED`, `assumption_status=synthetic`, **location IS NULL**. No hazards, taxonomies, policy coverages, reinsurers, treaties, event occurrence rates or loss simulations were inserted.
- `portfolio_version.scenario_hash=NULL` deliberately until the exact OED artifact manifest scenario hash is independently recovered. A Git blob SHA is source-document evidence, not the scenario byte SHA.
- Original OED 5.0 policy CSV files and third-party physical building geometries were **not** imported into Neon. The source registry record remains **non-admitted for raw data**, with no geocoded model-input licence.

The exact updated GitHub SQL query now counts separately whether the synthetic exposure unit actually has geometry. Tested on both DB branches:

| Gate row | Neon default main | Neon isolated research branch |
| --- | ---: | ---: |
| solo company and exact LEI | 0 / 0 | 1 / 1 |
| source-reviewed original 2025 financial metrics | 0 | 3 |
| company-linked synthetic portfolio versions | 0 | 1 |
| company-linked exposure units | 0 | 1 |
| synthetic exposure units with non-null geometry | 0 | **0** |
| next gate | `BLOCKED_UNVERIFIED_OR_AMBIGUOUS_SOLO_LEGAL_ENTITY` | **`BLOCKED_SYNTHETIC_EXPOSURE_HAS_NO_GEOMETRY`** |

Even if geometry were provided in future, the terminal report remains `RESEARCH_ONLY_NEEDS_HAZARD_VULNERABILITY_RIGHTS_AND_TREATY_REVIEW`. This is **not** validation of source-compatible WGS84 coordinate semantics, German stochastic event frequency, vulnerability, a native Oasis GUL/IL/RI run or gross/net OEP/AEP.

The realistic next workflow is to admit/transform original source-licensed 2022 NRW physical footprints and validate EPSG:4647 → 4326, *then* select explicitly fictional site locations independent of the carrier's unknown customers. Existing [#1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373) should own OED/geocoding; this PR remains the independent database evidence gate. **No Neon main writes, no raw-PDF or OED policy CSV redistributions.**
