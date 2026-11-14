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
