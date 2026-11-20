<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Marche 2022 — conditional observed component damage by outside water depth

**Research execution:** 2026-11-09. **Status:** research-only, not admitted. **Pinned release:** https://doi.org/10.5281/zenodo.17457884 (v1.0.1). **Paper:** https://doi.org/10.5194/essd-17-6487-2025.

This note reports only coarse aggregates from a single-event field survey, **not** a monetary or insurance loss calibration. No survey IDs, original rows, exact locations, raw damage values, coordinates or original ZIP files are committed.

## Original data pairing and provenance

All inputs are exact frozen publisher ZIPs, verified against published MD5 and independently measured SHA-256, including the original Form A dictionaries and parent counts. Separate sectors have distinct outcome definitions:

| Sector | Outside depth (m) | Form A observed binary outcome | Original dictionary | Outcome observations | Valid depth + outcome pairs |
| --- | --- | --- | --- | ---: | ---: |
| Industrial / commercial | Column AY, hw | BK, building structure and plants damage (1 yes, 0 no) | Dictionary A row 61, boolean; 6 no-data | 127 of 133 | 121 |
| Residential | Column AG, hw | AX, external coating / plaster damage (yes / no) | Dictionary A row 45, boolean; 1 no-data, wording external coating/perimeter | 122 of 123 | 120 |

Outside depth hw is measured/reconstructed **in metres**, distinct from the derived water surface elevation (terrain + hw + building elevation adjustment). The previous original-data gate reproducibly found **126 industry + 121 residential = 247 numeric** hw values; 7 and 2 no-data respectively. Source coded "-" is missing/unknown, **not** measured depth zero and **not** absence of damage. Industry structural/plant damage and residential exterior plaster damage are NOT the same outcome.

## Empirical depth bins, original v1.0.1

Use fixed half-open external-depth ranges in metres: [0,0.5), [0.5,1), [1,2), [2,infinity).

| Sector | Outside depth, m | Paired properties | Positive recorded component damage | Within-survey positive fraction | Descriptive Wilson 95% |
| --- | --- | ---: | ---: | ---: | ---: |
| Industrial | [0,0.5) | 31 | 26 | 83.87% | 67.37%–92.91% |
| Industrial | [0.5,1) | 56 | 45 | 80.36% | 68.16%–88.66% |
| Industrial | [1,2) | 30 | 25 | 83.33% | 66.44%–92.66% |
| Industrial | [2,infinity) | suppressed | suppressed | suppressed | suppressed |
| Residential | [0,0.5) | suppressed | suppressed | suppressed | suppressed |
| Residential | [0.5,1) | 49 | 11 | 22.45% | 13.02%–35.88% |
| Residential | [1,2) | 48 | 16 | 33.33% | 21.68%–47.46% |
| Residential | [2,infinity) | suppressed | suppressed | suppressed | suppressed |

**Suppression rule:** publish a cell only when at least 10 paired properties, at least 3 positives, and at least 3 negatives. No exact suppressed counts or positive totals are published for those cells. Aggregation is data minimization, not an anonymity or commercial-privacy approval.

**Disclosure limitation:** Suppressing individual small-bin outputs does not prove anonymity. The already documented sector-wide valid-pair counts and published bins may reveal residual small-bin sizes by subtraction. No per-building IDs, individual outcomes or exact original coordinates are exported; independent privacy and permitted-use review is still required before any downstream release.

**No monotonicity enforcement:** industry fractions are high and roughly flat/nonmonotone; two sufficiently populated mid-depth residential bins show increasing exterior coating/plaster occurrence. Their descriptive intervals overlap. Do **not** infer causal depth effect, universality, between-sector comparability, or out-of-event validation.

## Reproducibility and execution

Runner: [research_runners/marche_2022_component_damage_depth_bands_v0.py](../../research_runners/marche_2022_component_damage_depth_bands_v0.py).

Synthetic tests: [tests/test_marche_2022_component_damage_depth_bands_v0.py](../../tests/test_marche_2022_component_damage_depth_bands_v0.py).

- Execute Python stdlib unittest discovery with pattern test_marche_2022_component_damage_depth_bands_v0.py.
- Run the module research_runners.marche_2022_component_damage_depth_bands_v0 with the --industrial-zip and --residential-zip arguments pointing to **privately held original source ZIPs outside Git**.
- Original ZIPs come from https://zenodo.org/api/records/17457884 ; the executable locally checks frozen identities and source definitions before reporting aggregates.

On **2026-11-09**, isolated execution of code frozen at commit b840234adf5f2f7b91710d05cf7ba80d87220936 against both exact original Zenodo ZIPs gave **13/13 synthetic tests passed**, original analysis exit code **0**, and aggregate-only results. Source runner SHA-256: a5b911fab25015b38f2e827fc576b3cb83cd0d1edb77472ebf76b3e4a0c0fa8e. This is **not a full GitHub Actions CI run**.

## What these data cannot establish

The 2025 paper reports only around **3%** of damaged residential properties and **15%** of affected businesses were surveyed, within **3 of 14** strongly affected municipalities. Survey selection was **not a random sample** of all insurer exposures, flooded/non-flooded assets or even all affected properties. Copernicus EMSR634 was already used in selection and is not an independent flood-footprint validation dataset.

These two source outcome flags represent binary **component damage** conditional on sample inclusion. They are not all-building monetary damage, insured claim severity, policy payouts, insurance penetration, sums insured, replacement values, TIV, or total catastrophe losses. Even the simple Wilson uncertainty bounds do not account for spatial sampling correlation or survey selection. A one-event sample has no event-disjoint validation split and does not yield annual flood frequency, AEP/OEP/OIP/IP, gross/net, or policy layer losses.

The Zenodo derived-dataset release advertises CC BY 4.0, but detailed property coordinates and individual survey microdata require independent privacy, rights and permitted-use assessment. The original source **remains not_admitted** in the canonical source registry. No Neon ingestion, insurer portfolio construction, OED export or production calibration is authorized.

**Next research gate:** validate mapped binary damage outcomes against the corresponding original data dictionaries and identify a second independent flood event/geography with lawful de-identified records, plus external exposure/TIV or claims. Only then attempt transferable vulnerability and insurer-loss calibration.
