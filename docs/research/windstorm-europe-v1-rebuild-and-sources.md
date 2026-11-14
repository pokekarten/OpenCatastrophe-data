<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Windstorm Europe v1: integrated research model and external evidence

The independent map, lookup, response, sample and financial prototypes are
now connected by `research_runners/windstorm_europe_model_v1.py`. One JSON
configuration declares the portfolio, response classes, dependence groups,
physical scenario schedule, simulation years and financial terms. A single
command produces source provenance, sampled event gross/ceded/net losses,
annual losses and empirical EP diagnostics for the supplied scenario measure.

## Findings from live web research (14 November 2026)

1. [ECMWF/C3S Enhanced Windstorm Service](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis?tab=overview)
   provides all-year filtered storm tracks and 72h footprints at 0.25 degrees
   and statistical downscaling at 0.016 degrees. Hodges and TempestExtremes
   are alternative trackers. Full-domain and decontaminated fields have
   distinct support. These selectors must be preserved; do not add trackers
   or substitute a full-domain field for a decontaminated field.
2. [CLIMK publication](https://essd.copernicus.org/articles/17/4431/2025/)
   selects the 50 most severe extended-winter events separately in four
   source datasets. Use these for conditional events and source sensitivity;
   they cannot supply a complete annual occurrence population.
3. [Synthetic WISC catalogue](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-synthetic-events?tab=overview)
   describes 22,980 footprints and three iterations, with September–May
   coverage. The older [service overview](https://climate.copernicus.eu/windstorm-information-service)
   describes 7,660 events. Counts must be reconciled by version/iteration;
   neither number alone establishes independent event/year weights.
4. [CLIMAAX workflow](https://handbook.climaax.eu/notebooks/workflows/STORMS/01_windstorm/Risk_assessment_STORMS.html)
   publishes six Feuerstein/Koks construction response estimates and a LUISA
   workbook. It explicitly requires regional adjustment. Its land-use
   maximum-damage proxies are not observed building replacement values.
5. [EUBUCCO live source repository](https://github.com/ai4up/eubucco)
   describes a newer 322M+ building coverage across 30 countries with
   ground-truth/merged/ML provenance. The [2023 paper](https://www.nature.com/articles/s41597-023-02040-2)
   describes v0.1, 202M buildings, EU27+CH and incomplete attributes. Do not
   combine version coverage figures; inferred height/use is not observed
   resistance, and a complete attribute column is not complete ground truth.
6. [Cusack 2023](https://nhess.copernicus.org/articles/23/2841/2023/)
   describes divergence of modelled ERA5 wind-loss trends from observed gusts
   and industry losses. This motivates time-period holdouts and station
   challenges; it does not justify applying a generic correction factor.
7. [European wind damage study](https://www.nature.com/articles/s41598-020-63580-w)
   and [2024 vulnerability sensitivity study](https://nhess.copernicus.org/articles/24/1555/2024/)
   support treating response and calibration uncertainty explicitly. A mean
   response curve alone cannot identify insured tails or spatial dependence.

## Actual newly acquired numerical sources

The original CLIMAAX repository commit is
`38613ba890d2b4506112aef4254766f6a4753d06`.
Downloads succeeded to temporary `/dev/shm/windstorm-europe-sources/`:

| Original file | Bytes | SHA-256 |
|---|---:|---|
| `01_windstorm/CURVES_feuerstein_koks.csv` | 3380 | `d960e67ab726815974feb08e5850054d7fac2873ea5bb3b02956e6262da7fd81` |
| `01_windstorm/LUISA_damage_info_curves.xlsx` | 20858 | `a4ddff2c35bbc3536330389334c0fcae378799a49c6b7f3c643276065bbb8276` |

Original URLs are the corresponding paths under
`https://raw.githubusercontent.com/CLIMAAX/STORMS/38613ba890d2b4506112aef4254766f6a4753d06/`.
README and both licence files were also downloaded; README declares
`Apache-2.0 OR CC-BY-4.0`. Preserve attribution and upstream scientific
references. We do not assert the table equals the missing original WISC
CURVES.csv. The workbook has been acquired but its cell-level valuation
semantics have not been validated or inserted into building values.

## What changed in the model

- Per-building response IDs replace the assumption of one response curve
  for an entire portfolio. Country and dependence group are explicit inputs.
- `paa_mdd_two_point` retains the existing reference sampler. New
  `construction_percent_deterministic` reads a named external percent column
  and uses a deterministic fraction-of-value response. PAA=1 here is an
  implementation encoding of that declared assumption, not an observed
  affected-building probability. We do not turn percent damage into a
  fragility probability.
- External response tables must match their configured SHA-256. The original
  hazard still passes its independent source digest and schema checks.
- Hazard fields/point lookup are cached per source event; individual building
  IDs and complete weather support are checked before policy aggregation.
- Distinct response classes aggregate to the same policy before deductibles.
  Countries participate in the same financial occurrence before treaty terms.
- Seed/sample/occurrence/dependence keys remain reproducible. Year is included
  in the sampling key to avoid identical damage draws for a repeated physical
  scenario in separate supplied years.
- The integrated version accepts only explicitly labelled uncalibrated
  scenario schedules. Annual EP is a diagnostic of that supplied schedule;
  the model does not silently promote historical selected extremes into rates.

## Configuration and reproduction

```sh
python research_runners/windstorm_europe_model_v1.py \
  --config /private/europe-model.json --output /private/europe-result.json
```

The config keys are `profile` (`windstorm-europe-research-v1`),
`annual_schedule_basis` (`explicit_user_scenario_not_calibrated`), integer
`seed`, `bounds` (west/south/east/north), `hazard_source` (local original CLIMK),
`responses`, `buildings`, `policies`, `treaty`, `year_ids` and `occurrences`.
Relative source paths resolve against the configuration directory.

Each response entry declares `path`, `sha256`, `kind` and, for a construction
percent table, exact `column`. Each building declares `building_id`,
`policy_id`, ISO alpha-2 `country`, `dependence_group`, `response_id`,
`longitude`, `latitude`, and positive `building_value_eur`. Building country
is supplied metadata, not inferred or geometrically validated by the runner.
Policies declare EUR `deductible_eur` and `limit_eur`. The treaty declares
EUR `attachment_eur` and `limit_eur` (single occurrence layer with unlimited
annual reinstatements). Occurrences declare `year_id`, `occurrence_id`,
nonnegative integer `sample_id`, and source `storm_index` (0..49).

## Executed evidence and limits

The integrated original-source run completed for three fictional EUR1m
locations at London (-0.12,51.5), Paris (2.35,48.86) and Cologne (6.96,50.94),
using the downloaded CLIMAAX weakest-outbuilding/strong-brick classes, original Kyrill,
EUR1000 policy deductibles, and an assumed EUR100000 layer above EUR10000.
The supplied schedule contains one occurrence in year 1 and zero occurrences
in years 2 and 3. This is an integration check, not an annual frequency claim.
The local result/config remain outside Git. Ten focused offline tests passed,
including class-specific policy loss, explicit zero years, sampler mean,
seed/order behavior, missing classes and physical-to-financial conservation.

The calibrated full model remains dependent on complete event/year data,
source-domain masks, observed building resistance/value data, empirical
severity/dependence validation and portfolio-specific financial terms. Native
Oasis equivalence for the newly integrated multi-class path is still to be
established. Existing one-cell and earlier native experiments do not prove
that new path. The WISC workbook and new curve table supply useful
alternatives to investigate rather than automatic country calibration.

An earlier weak/strong-brick-only probe produced zero insured loss at these
three gusts and deductible assumptions. The mixed-resistance example is a
separate sensitivity run, not a fitted change to reproduce a target loss.
The mixed-resistance replay returned EUR206591.34873161552 gross occurrence
loss, EUR100000 ceded and EUR106591.34873161552 net. The brick-only replay
returned zero insured loss under its curve/deductible assumptions. Neither
amount is an observed loss or a basis for fitting German/European parameters.
