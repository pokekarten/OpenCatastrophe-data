<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hazard Plain 2026-10: original county-level content quality receipt

**Observation date:** 2026-11-09 11:42 UTC  
**Independently executed original-source QA:** [GitHub Actions run 42611083360](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42611083360), job `129139377530`, runner `research_runners/hazardplain_202610_county_content_qa_v0.py`, matching the pinned 2026-10 original CSV sources.  
**Source input identity:** original provider manifest at [files.hazardplain.org](https://files.hazardplain.org/r/2026-10/bulk/manifest.json), pinned SHA-256 `e04a707ab5b96a71e81f6ac29a584f3cb43acb5ec88c5e9669e092b5076434b4`; three original CSV byte hashes listed in [exact-byte receipt](hazardplain-202610-original-csv-exact-byte-receipt-20261108.md).

The original CSV sources were downloaded in bounded memory on GitHub Actions and their exact file sizes/hashes, headers and row counts rechecked **before** quality profiling. No original CSV bytes, county-specific records, individual FIPS IDs, site-level loss values or external artifacts were committed or uploaded. Fourteen hermetic synthetic regressions ran successfully in the same focused canary. This report is an **aggregated research-quality receipt**, not independent scientific/actuarial validation.

## Actual observed quality counts

| Check | Result |
| --- | ---: |
| Unique five-digit county keys in each of all three tables | 3,232 |
| Counties present in all three original tables | 3,232 |
| Counties appearing in NRI but not NFIP aggregate (and reverse) | 0 / 0 |
| EAL outlier (county, peril) keys absent from NRI source pairs | 0 |
| Invalid / duplicate county or county-peril keys (selected controls) | 0 |
| Original NRI county × hazard rows | 58,176 |
| Counties with exactly 18 distinct hazards in NRI | 3,232 |
| NRI hazards with `applicable=true` | 46,327 |
| NRI hazards with `applicable=false` | 11,849 |
| NRI `eal_total` nonempty positive/zero | 44,596 / 1,257 |
| NRI `eal_total` blank, all applicability classes | 12,323 |
| **NRI `applicable=true` AND `eal_total` blank** | **474** |
| NRI `applicable=false` AND `eal_total` blank | 11,849 |
| Outlier diagnostics rows | 45,853 |
| Outlier `outlier=true` / `outlier=false` flags | **57 / 45,796** |
| EAL outlier `neighbor_median_eal` blank | 798 |
| EAL outlier `rate_ratio` blank | 1,181 |
| NFIP repetitive-loss county aggregate rows | 3,232 |
| NFIP counties with `any_category` positive / zero | 2,279 / 953 |
| NFIP counties with `unassigned` positive | 295 |
| NFIP counties with `member_not_listed_here` positive | 59 |
| Distinct NFIP `as_of_date` labels | 1 |

The selected numeric fields in this exact source snapshot had only blank, zero, or positive values; the original-source checker recorded **no negative, nonfinite, nonnumeric, or fractional NFIP count values** in its selected profiles. It did not test every numeric column or prove every row's domain-specific scientific validity.

## Scientific interpretation and deterministic guardrails

1. **Do not replace blank NRI `eal_total` with zero.** There are 11,849 explicitly non-applicable hazard/county rows with blank AAL and **474 applicable rows with blank AAL**. These are distinct classes of missingness; the second class requires separate source review before any synthetic portfolio risk allocation. AAL of exactly zero is a separate legitimate observed model output class (1,257 NRI rows).
2. The 57 true `outlier` flags are *secondary diagnostic flags* based on county-neighbor comparisons, FEMA NRI modeled risk and NOAA Storm Events source coverage. An outlier flag is neither proof of an erroneous model loss nor an approved automatic bias correction.
3. The NRI `eal_total` is modeled *economic expected annual loss*, not claim cashflow, insurer net loss, a policy exposure amount, an event loss table, or a standalone AEP/OEP. Its 18-hazard county coverage does not imply the 18 modeled hazards are independent or may be summed as an insurer portfolio.
4. The **NFIP FMA/NFIP RL and SRL categories overlap** and include potentially mitigated, no-longer-insured or demolished properties. The 3,232 county aggregates do not describe individual buildings, national property counts, market-wide flood coverage or a claim severity distribution. Do not sum four category counts into a count of unique insured sites, or equate `any_category` directly to exposure TIV.
5. County key *shape* and cross-source coverage have been checked, but **geographic vintage, Census/FIPS reclassifications, FEMA location uncertainty, NFIP-to-county assignment, missingness mechanisms and source dependency/independence** have not been independently established.
6. Source publication and upstream usage rights require formal review; the source registry remains **`rights_review_status:not_reviewed`, `scientific_review_status:not_reviewed`, `admission_status:not_admitted`**. No original source records were exported to our database, and no insurer AEP/OEP or gross/net results have been generated.

## Next bounded, high-value scientific tasks

- Audit the **474 applicable-but-blank AAL** original county×hazard combinations by reviewed hazard taxonomy and missingness reason, excluding individual FIPS and any proprietary source asset identifiers from outputs. Use official NRI v1.20 methodology to distinguish unmapped/model-missing values from actual zero, unsupported hazard and version mismatch.
- Review the **57 outlier flags** against the original NOAA coverage and hazard-specific `caveat` logic; never automatically alter loss estimates.
- Reconcile the county FIPS/vintage against an independently pinned U.S. Census 2020/2025 county reference, explicitly handling territorial and former/renamed county keys before any GIS or portfolio join.
- Review the [FEMA-0596 NFIP multiple-loss property definitions](https://catalog.data.gov/dataset/nfip-multiple-loss-properties) and [Hazard Plain methods](https://hazardplain.org/methods/) for FMA/NFIP overlapping definitions, location privacy and incomplete-geocoding limitations before aggregate insurance use.

**Scope:** only publicly published derivative aggregate source values and diagnostics were checked; no policyholders, private buildings, claims at property level or source-specific independent holdout evidence were obtained.
