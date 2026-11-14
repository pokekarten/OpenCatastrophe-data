<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Executable Germany wind scenario loss chain

The model now connects original CLIMK ERA5 hazard, native cell geometry,
explicit building point/value inputs and an external PAA/MDD table to
conditional expected ground-up building damage. Each output records input
hashes and source/event metadata; per-cell totals permit spatial auditing.
It is an executable scenario prototype requiring German vulnerability
calibration and real exposure values before an empirical loss claim.

## Reproduce

Portfolio CSV columns are exactly
`building_id,longitude,latitude,building_value_eur`. Values must be explicit,
positive EUR replacement-value assumptions. Curve CSV columns are exactly
`intensity_m_s,paa,mdd`; probabilities and damage fractions must be finite,
monotone and within [0,1]. Curves are supplied externally with their source
licences preserved. Interpolate PAA and MDD separately before multiplication.

```sh
python research_runners/germany_wind_scenario_loss_v0.py \
  --source /data/ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc \
  --portfolio /private/buildings.csv \
  --curve /data/schwierz-reference-curves/source_reference.csv \
  --curve-label 'Schwierz European reference; uncalibrated for Germany' \
  --all-storms --output /private/wind-scenarios.json
```

Omit `--all-storms` and use `--storm-index 0` for Kyrill. No annual weights
are inferred from the selected top-50 source events. Missing weather,
outside-grid locations and curve extrapolation block the affected scenario.
No deductible, policy limit, reinsurance or conditional damage variance is
inferred from a mean damage response.

## Actual executed example

Original SHA-verified Kyrill with fictional EUR1m buildings at longitude /
latitude (6.96,50.94), (10,53.55), (11.58,48.14), and the already acquired
Schwierz/CLIMADA reference table produced EUR205.3011438657001 expected
physical building damage on EUR3m assumed building value. This amount is
an implementation example, not German observed loss. The external curve
CSV SHA256 is `439c69de3a2680791076cd844caee5a0a6a03445bf637dbc096486742d4c506c`.
Original CLIMADA source and GPL COPYING are retained beside the local curve;
external curve arrays are not committed to this Apache-licensed repository.

## Data already acquired and remaining work

The current local data inventory under `/tmp/pr-ci/germany-wind-data` includes
all four original CLIMK footprint files, XWS Kyrill raw/decontaminated files,
DWD original station archives, NRW HU2022 building geometry, EIOPA exposure
and loss workbooks, and external Schwierz PAA/MDD references with source and
licence. These files are temporary local research storage. A durable archive
must retain source bytes, hashes, licence, retrieval receipt and version;
the raw data are not stored in Git. The original downloads and inspections
are described in this repository's corresponding source reports.

The next completion requirements are concrete:

- Generate and verify building locations from the acquired geometry, retaining
  occupancy/mixed-use classes; do not silently treat all candidates as homes.
- Obtain replacement values, valuation year and building resistance classes.
  Coordinates, footprint area and occupancy alone do not supply these values.
- Validate the external European reference against compatible German observed
  wind damage; the missing WISC CURVES.csv cannot be reconstructed from code.
- Acquire event/year weights and complete historical coverage for annual risk.
  The C3S authenticated download requires a configured account and accepted
  dataset terms; available anonymous selected footprints do not supply rates.
- Compare event footprints with DWD observations using event-era station
  metadata and matched time support, extending the completed Ciara diagnostics.
- Export the spatially audited portfolio and response distributions into
  native Oasis inputs and check physical loss against this independent oracle.

A full Germany stochastic insured CAT model is not complete until these data
and model requirements are resolved. The executable conditional scenario
chain lets them be developed and challenged without substituting zero losses
or invented annual probabilities for missing information.

The implemented `--all-storms` command was executed locally against all 50
original ERA5 storm fields with this three-point fictional portfolio and
external reference curve: **50 completed, 0 blocked**. This establishes the
scenario pipeline on that example portfolio. It does not establish complete
weather support at other buildings. The exporter reads each event field once
before cell extraction to avoid repeated NetCDF decompression per cell.

## Europe architecture, Germany first validation

A common European event domain is appropriate because a single windstorm
can damage several countries. Preserve the physical source event identity
and native area-peril IDs across national portfolios; do not simulate country
losses independently and then call their sum one European storm. Exposure
values, valuation years, building classes, response calibration and policy
terms still need country-specific evidence. A generic European response curve
is a reference assumption rather than evidence of transferability.

The map, point crosswalk and scenario CLI now accept
`--bounds WEST SOUTH EAST NORTH`; default remains the Germany bounding box.
A local original-source Kyrill replay over `--bounds -5 45 16 56` exported
3825 cells and successfully mapped fictional probes in London, Paris and
Cologne to native IDs 22147, 25115 and 22713. Their source gusts were
34.37997265538519, 22.87145170942648 and 33.411881663861934 m/s respectively.
This proves common-event spatial lookup, not cross-country loss calibration.
The selected source footprint and its missing-value support remain binding;
a requested bounding box does not expand the provider's actual data domain.

Existing Impact Forecasting EUWS scenarios are useful model comparisons:
the source inventory describes Ciaran/Domingos deterministic scenarios and
multiple footprint interpolation alternatives. Empty occurrence data do not
supply an annual stochastic catalogue. CLIMK and the European response
reference are already acquired building blocks for our own implementation.
