<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original CLIMK Kyrill → synthetic native Oasis GUL

**Research-only conditional scenario.** This procedure runs one verified
original CLIMK source cell through native OasisLMF GUL for a fictional
24-location portfolio. It is not an annual catastrophe model result,
calibrated vulnerability, insurer portfolio estimate or policy loss.

## Source and spatial bridge

- Provider source: [CLIMK–WINDS v2 ERA5](https://zenodo.org/records/15305753),
  original file `ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc`.
- Required original bytes: 6,792,278; SHA-256
  `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`.
- Event: source index 0, name `KYRILL`, source date label `20070118`.
  The date label is preserved verbatim; it is not interpreted as event
  frequency or a complete UTC timestamp.
- Native cell: row 78, column 112; direct `absolute_maxwindgusts` value
  35.21054044063598 m/s; Oasis area peril 21095.
- The two synthetic point markers from the [area-peril crosswalk](climk-kyrill-24-assets-original-oasis-area-peril-v0.md)
  are both sampled against the original bytes and must resolve to that
  exact cell and gust. The runner also derives the cell polygon from its
  neighboring native coordinate centers and checks that both points lie
  within it.

## Native run construction

`research_runners/climk_kyrill_native_gul_synthetic_v0.py` builds two fresh
model directories and runs `oasislmf model run --check-oed` twice using
OasisLMF 2.5.8. It pins the original provider bytes and the public
OasisPiWind repository scaffold commit
`94820c59f169b222d4c1a72256ff0a8f86a9e5bf`. Only the scaffold's model
settings and lookup configuration are copied. Its hazard, exposure,
vulnerability and loss data are not used; these are replaced by the
CLIMK source cell and synthetic inputs.

The portfolio has 24 fictional EUR10m buildings (EUR240m BuildingTIV),
all assigned to the one source cell. The model produces 48 OED keys
(two coverage types per location), zero key errors and coverage TIV equal
to EUR240m. A single deterministic sample uses an explicitly authored,
uncalibrated wind damage curve. Intensity is rounded to integer mm/s to
match the existing VLT convention. The curve's modeled damage ratio for
this event is approximately 20.10230303%; its analytical portfolio GUL
is EUR48,245,527.27. The native result is allowed EUR10 numerical
tolerance to account for engine binning/rounding.

## Current local receipt

On the pinned public source and OasisLMF 2.5.8 environment, two freshly
created native model runs each returned EUR48,245,536.00. Their output
CSV SHA-256 was identical:

`1bf7b2011d6e1a8bd2bd2970936e4fb6b81ed44b0b5f73144ee0490900dce9b4`

The native result differs from the authored curve's analytical amount by
EUR8.73 and passes the EUR10 tolerance. This supports a reproducible
**single-event synthetic GUL execution**. It does not validate the curve
or establish that it represents actual European buildings. The GitHub
Actions workflow reruns this proof from the pinned inputs; its receipt
and logs are temporary artifacts, not committed weather or exposure
data.

## Supersedes prototype estimate

The earlier [PR #1361 comment](https://github.com/pokekarten/OpenCatastrophe-data/pull/1361#issuecomment-6877427345)
reported EUR48,244,996 from a direct-precision prototype. This repeatable
runner applies the VLT's integer-mm/s half-up input rounding and produces
EUR48,245,536. The earlier number is superseded; the difference comes
from input quantization before evaluating the piecewise curve, not from
a change to the CLIMK source gust or portfolio TIV.

## Scope limits

- One historical event and one physical source cell only; CLIMK's 50
  selected extreme events do not define a complete stochastic year set.
- No annual frequency, AAL, AEP or OEP is inferred or admitted.
- Vulnerability is authored for a reproducibility exercise, not empirically
  calibrated or validated against claims/building observations.
- Exposure is fictional. No real insurer locations, coverage conditions,
  deductibles, limits, policy terms, insured loss, IL or RI are modeled.
- This run does not close the scientific validation or production readiness
  of the FFBK, RIM or OpenCatastrophe models.
