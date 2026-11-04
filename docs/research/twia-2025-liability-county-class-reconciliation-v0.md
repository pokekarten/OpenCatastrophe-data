<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# TWIA 2025-12-31 county × class normalized liability preflight v0

**Research-only.** Source PDF is not committed, downloaded by this change, copied into a fixture or programmatically interpreted here. Passing unit tests or a normalized-file audit **never** confirms the original PDF/rights, source completeness, actual insurer asset coordinates, insured property TIV, OASIS-ready model input or fitted loss distribution.

This is a narrow first executable follow-up to [carrier-specific pilot selection](carrier-synthetic-cat-portfolio-pilot-selection-20261104.md). It does not overlap the existing Florida OIR statewide x company / Texas ZIP market QA in [the prior research](florida-texas-exposure-reconciliation-v0.md).

## First-party primary report and original visual semantics

- Publisher landing: https://www.twia.org/about-us/financial-reports/
- Direct, dated report: https://www.twia.org/wp-content/uploads/TWIA-Liability-Report-20251231.pdf
- **Snapshot:** 2025-12-31, not 2025-09-30 or 2025-11-30.
- **Page 1 of 5:** 15 TWIA territory county names, 2024 and 2025 PIF/exposure/YTD premium columns. **Only the 2025 columns** are in this profile.
- **Pages 2–5:** for every county, three classes **Commercial, Manufactured Home, Residential** and a county sum. **Use "In-Force at End of Quarter → Policies/Risks"** for counts; **"Written Liability at End of Quarter → Direct/Indirect"** for amounts and **"Written Premium → YTD"** for premium. Neither "Risks Written YTD" nor quarter-only premium is a PIF/AEP input.
- The geographic insurer scope is 14 entire coastal counties **plus eligible portions of Harris County**. A generic full Harris building-stock join is **not** TWIA coverage.

### Independently published high-level controls (not provider data ingestion)

The last report page prints the following total class controls. These *public facts* are in the checker as expectations to catch mis-normalization; no per-county source rows are stored in Git.

| TWIA class | PIF | Risks in force | Direct liability USD | Indirect liability USD | 2025 YTD written premium USD |
|---|---:|---:|---:|---:|---:|
| Commercial | 8,099 | 16,719 | 11,584,286,100 | 226,802,179 | 117,408,620 |
| Manufactured Home | 1,850 | 1,850 | 140,801,200 | 0 | 3,739,524 |
| Residential | 274,897 | 274,897 | 114,730,637,300 | 14,569,652,580 | 699,716,387 |
| **Total** | **284,846** | **293,466** | **126,455,724,600** | **14,796,454,759** | **820,864,531** |

**Do not add direct + indirect liability as unique insured physical-property TIV.** A commercial **policy** can include multiple **risks**, and counting 284,846 policies as exactly 284,846 distinct geocoded buildings is demonstrably incorrect. An observation at company × county is still not evidence of which property locations this insurer covers. Statewide Texas TDI market policies and TWIA coastal policy exposures must not be substituted for each other.

## Normalized-input interface

**No licensed original provider rows may be committed.** External operator performs any authorized PDF extraction and independently records exact original bytes/size/sha256, report edition, publisher terms, normalization script hash and row-page reconciliation *outside Git*. The checker operates on two local, rights-reviewed UTF-8 CSVs without separators in nonnegative integer dollar/count fields:

1. \`county.csv\` — **exact columns in exact order**: \`record_kind,report_as_of,county,policies_in_force,direct_liability_usd,ytd_written_premium_usd\`. Exactly 15 county rows with \`record_kind=county\`.
2. \`county_class.csv\` — **exact columns in exact order**: \`record_kind,report_as_of,county,policy_class,policies_in_force,risks_in_force,direct_liability_usd,indirect_liability_usd,ytd_written_premium_usd\`. Exactly 45 rows with \`record_kind=county_class\`.

Both use \`report_as_of=2025-12-31\`. Case, whitespace, dollar precision and full named roster are strict; do not silently suppress, round, impute or treat missing/NA as zero. There is no implicit CSV coordinate/ZIP/physical building mapping.

\`\`\`bash
# With wholly invented local synthetic CSVs:
python research_runners/twia_liability_2025_reconciliation_v0.py \
  --county-csv /private/synthetic_county.csv \
  --county-class-csv /private/synthetic_county_class.csv \
  --mode synthetic

# Only *after* independent original-source rights/receipt/normalization review:
python research_runners/twia_liability_2025_reconciliation_v0.py \
  --county-csv /private/normalized_2025_county.csv \
  --county-class-csv /private/normalized_2025_county_class.csv \
  --mode published-2025

python -m unittest tests.test_twia_liability_2025_reconciliation_v0 -v
\`\`\`

**Output contract:** sha256 of the supplied *normalized* CSVs, count of rows, compared actual totals, per-county cross-grain mismatch names, published three-class/grand-total mismatches and unconditionally false \`original_provider_bytes_verified\`, \`source_licensing_admitted\`, \`observed_insured_building_positions\`, \`model_input_approved\`, \`gross_net_reinsurance_verified\`.

Exit code **2** for numeric inconsistency, exception for malformed/stale/ambiguous rows. **Even a passing \`published-2025\` CSV may be entirely fabricated:** a negative adversarial regression test constructs fictitious per-county class allocations that satisfy *all* published class and national totals, and the model-readiness flags remain false. This concretely proves the insufficiency of aggregate-only reconciliation.

## Local execution evidence

- 17 independent synthetic-only unit tests passed using Python unittest (2026-11-04), including record omissions/duplication, impossible risk counts, wrong 2025-09-30 vintage, unknown county/class, currency/count suppression, direct/indirect separation, observed aggregate-control rejection and nonidentifiability even when published totals are matched.
- Python compileall passed for the two added files in the same local checkout-shaped folder.
- This does **not** claim full repository-wide \`python scripts/check_all.py\` or GitHub exact-head CI, original PDF/terms review or any model simulation.

## Next causal gate

1. Independently obtain/source-pin original TWIA PDF bytes, identify rights for exact intended scientific/commercial usage and verify provider page rows against a controlled extraction artifact. **Original bytes remain outside Git**.
2. Add bounded row-level *independent* county controls from a verifier holding the original PDF. A published national total alone does not ensure a truthful county surface; avoid transcribing all raw official county data as code fixtures.
3. Match one **2025-12-31** physical-building coverage proxy by county and **Harris eligible subarea only**; require separate building geometry/occupancy/age/replacement-cost, insured take-up and coverage constraints. Construct at least two independent synthetic geography priors with deterministic integer-dollar conservation.
4. Only after rights, hazard/vulnerability and scientific review, run OASIS/GUL→IL and NextGen event/annual simulations. Treat TWIA vendor-rate-adequacy model AAL/PML from a **2024-11-30 exposure basis** as a *different vintage* until explicitly reweighted/reproduced with unaltered validation targets.
5. Reinsurance/funding is an **independent** treaty/contract study; 2025 funding pool, retained shares and net loss cannot be deduced from published funding totals alone.
