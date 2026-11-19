<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# TWIA 2025: two alternative synthetic subcounty allocation priors v0

**Research-only; no geocoded insured assets, no OED/ORD, no original provider PDF data extraction and no CAT loss model.** This is the immediate executable follow-up to [TWIA county/class source reconciliation](twia-2025-liability-county-class-reconciliation-v0.md) and the [insurer pilot decision](carrier-synthetic-cat-portfolio-pilot-selection-20261104.md).

## What was actually added

- `research_runners/twia_synthetic_microzones_v0.py` uses the existing `twia_liability_2025_reconciliation_v0.reconcile()` and exact normalized input contracts. A failed date, county/class total, or published 2025 class control blocks the new step.
- Each of the **45 county × class input cells** is split into **three explicitly imaginary labels**. Two mutually exclusive, deterministic worlds are produced: `distributed` (weights 1:1:1) and `concentrated` (8:2:1). This is a **mathematical non-identifiability test**, NOT an informed geographic estimate of proximity to the Texas coast, a county subdivision, building coordinate, assigned policyholder, or actual concentration.
- Each world has **135 hypothetical cells**, each with **five separately conserved measures**: policies in force, risks in force, direct liability USD, indirect liability USD, and YTD written premium USD. The two worlds must **not** be summed as if they were two simultaneous portfolios.
- Integer-only largest-remainder allocation conserves every county/class source number exactly, with deterministic tie-breaks. Commercial policies may have multiple risks: the difference `risks - policies` is allocated separately and nonnegatively, preserving `risks >= policies` in each fictional cell. Direct insurance liability is apportioned against hypothetical risk counts, not real replacement cost/TIV. Indirect liability remains separate; YTD premiums remain a historical flow, even when a period-end risk count is zero.
- The script refuses source control failures, duplicate/missing classes/counties, 2025 date mismatch, invalid SHA form, negative/float/boolean amounts, zero-risk positive direct liability, nonabsolute output path and existing outputs. Output is create-only, outside the Git checkout, and includes normalization SHA values. **These SHAs cover local normalized inputs, not the original PDF.**
- Output explicitly reports false for original-provider byte verification, rights approval, building coordinates, physical geography, actual insurer portfolio, observed insured TIV, OASIS-OED readiness, CAT model validation and verification of actual reinsurance terms. It contains no true subcounty boundary or coordinate.

## Execute with strictly fictional test inputs

```bash
python -m unittest tests.test_twia_synthetic_microzones_v0 -v

# Assuming separate, authorised, locally normalised county.csv and county_class.csv
# that conform to the older TWIA source checker:
python research_runners/twia_synthetic_microzones_v0.py \
  --county-csv /private/twia_county.csv \
  --county-class-csv /private/twia_county_class.csv \
  --mode synthetic \
  --output-json /private/brand_new_twia_synthetic_worlds.json
```

`--mode published-2025` also checks the public national *class* totals, but even perfect aggregate checks **do not prove the per-county source rows were correctly extracted from the original official TWIA PDF**. Never substitute a synthetic output for an independently verified insurer source in a CAT run.

## Validation evidence, 2026-11-04

The source file compiled locally. **19/19 standalone synthetic unit tests pass**, covering distinct worlds, full 15×3 input, 45×3 output per world, conservation of all five source measures at every input grain, no invented coordinates/OED, large integer precision, deterministic ordering, invalid and missing values, duplicate classes, wrong period, failed reconciliation and zero-policy historical premium retention.

Tests were run with a **local identity-only stub of the pre-existing TWIA constants** to isolate pure allocation logic; GitHub CI must separately verify importing the actual existing source checker and repository-wide checks. This does not establish original PDF reading, exact-head CI success, any original insured exposure, or any native Oasis model execution.

## Source joins to research next — no duplicated admissions

- [TWIA 2025-12-31 public report](https://www.twia.org/wp-content/uploads/TWIA-Liability-Report-20251231.pdf): 15 counties (14 whole plus eligible Harris portion), 3 classes, year-end direct/indirect liability, policies and risks. Keep original PDF version and page/column lineage. Public page content is not itself permission to redistribute original provider rows.
- [TWIA current wind/hail eligibility](https://www.twia.org/coverage-eligibility/) and [Texas Department of Insurance mapped catastrophe territory](https://www.tdi.texas.gov/wind/maps/): Harris County is **not whole-county eligible**. City and east-of-Highway-146 constraints must be resolved from authoritative GIS boundary, law, date and rights before a spatial model.
- [USACE National Structure Inventory 2026 technical documentation](https://www.hec.usace.army.mil/confluence/nsi/technicalreferences/2026/technical-documentation): **already registered in the repo** at `access/usace.nsi.base.2026.json`. Potential real physical building *prior* (modelled points, occupancy, assumed values, vintage/QA limitations), **not** an insured TWIA-property inventory. Review exact download scope and rights before any use.
- [TWIA coverage/perils](https://www.twia.org/about-us/overview/): wind and hail, not surge/flood. Resist generic hurricane footprint converting surge into insured TWIA wind loss.
- [NSI 2022 public FAQ](https://www.hec.usace.army.mil/confluence/nsi/technicalreferences/2022/frequently-asked-questions): documentation explicitly warns modelled/randomly assigned attributes; **never assert physical stock positions or insured valuation as observations**.

## Next strict model gate

1. Source-original PDF SHA, permitted use, exact full county × class row verification, and stable 2025-12-31 source receipt, with external original bytes never committed to Git.
2. Model **one physically meaningful location prior** (e.g. county NSI baseline) and **another independent prior** (e.g. Overture footprints + local building attributes), including the partial Harris perimeter, source-vintage and privacy/rights review. The mathematical microzones produced here are placeholders, not these physical priors.
3. Couple each alternative to an admissible, frozen, independent hurricane **windfield** and wind/hail vulnerability; preserve zero-loss exposure and historical aggregate benchmarks as holdouts.
4. Produce native OED -> GUL -> IL -> YLT / OEP / AEP with invariant checks and separate contract assumptions for net losses. **No calibration/PML validation claim** from synthetic placeholders or reported insurer funding alone.
