<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Insurance source-to-company assignment: two-branch fail-closed preflight (2026-11-04)

## Objective

Never infer a **real legal insurer x ZIP x property insured TIV** merely by combining separate aggregate statistics. These independent SQL receipts deliberately **do not perform a cross-branch SQL join** or import original provider records.

## Live execution / evidence

Database: separate Neon project `insurance-risk-core`, database `insurance`. Read-only execution on 2026-11-04; explicit branch IDs selected in the Neon connector.

1. `research_runners/sql/insurance_market_assignment_validation_v0.sql` on validation branch `validation-schema-20261031` (`br-summer-sky-bawujqu8`): **442** Florida official report rows; **160** reported NAIC codes; **442** original XLSX SHA references; **0** rights-reviewed; **0** carrier x ZIP; **0** parcel TIV. Texas **9194** ZIP x policy type rows, **2069** ZIP5 values, **0** original provider HTTP hashes, **0** legal insurer identity rows, **0** actual insured TIV rows. **4** negative values; **4** quarantined; **0** misclassified rows. First gate: `BLOCKED_ORIGINAL_SOURCE_PROVENANCE`. Both report sources use 2025-12-31 as their observed as-of date, but matching dates do not fix incompatible observational grains.
2. `research_runners/sql/insurance_directory_admission_main_v0.sql` on `main` (`br-late-recipe-ba1cr8hc`): **18180** third-party directory candidates across **181** country slugs; **0** source original hashes, **0** admitted rows; **22** verified legal entities but **0** domiciled in US. First gate: `BLOCKED_ORIGINAL_PROVIDER_SHA_COVERAGE`.

**Branch boundary:** `research.insurer_directory_candidate_v0` was not present on validation; Florida/Texas report tables were not present on main. A naïve single-branch SQL join fails. These two receipts can be compared *as separate evidence*; they do not combine to an approved exposure dataset.

## Source semantics

- Florida OIR original company x statewide policy-type data carry reported NAIC identifiers and aggregate exposure/premium measures, but **not** per-ZIP carrier allocation, parcel replacement value, all-market filer coverage, commercial source reuse review, or CAT calibration.
- Texas TDI ZIP5 x policy-type statistics contain **no legal insurer identifier or actual insurer TIV**. The four signed-negative cells are quarantined, not silently set to zero or counted as positive policies. Original HTTP source SHA256 is still missing in each row.
- The 18,180 worldwide insurer directory rows are secondary discovery candidates, not legal identity certification or admitted company share evidence. Do not assign a company's market share to ZIPs by name matching.
- Verified organizations (main) and source-specific legal identity evidence must be resolved via regulator/NAIC/LEI and effective dates; absence of a verified US-domiciled core entity here is **not** proof no US insurers exist worldwide.

## Next acceptance gates

1. Verify original Texas TDI provider bytes, licensing, headers/source date, suppression code semantics and immutable SHA256 receipts on an isolated branch.
2. Verify Florida report universe, policy-type denominator, regulatory company identity and source reuse rights; company x ZIP exposure requires *independent* evidence, not a proportional split asserted as fact.
3. Link regulator NAIC legal entities to core organizations with effective-date evidence; keep unmatched as candidates.
4. Add geolocated, valuation-qualified building/insured uptake marginals and an explicit stochastic *synthetic* allocation scenario, with calibrated uncertainty and insurer abstention where no hard constraints exist.
5. Only after separate rights, scientific hazard/vulnerability and treaty checks, hand versioned synthetic portfolios to NextGen. These SQL receipts provide **zero** production model admission.

## Reproduce

Run each SQL file on its explicitly named branch with database `insurance`. Both are single read-only `WITH ... SELECT` statements. Record the output aggregate, query commit SHA and selected branch ID in the research log. No personal insured data, original raw source bytes, or production DB writes were used here.
