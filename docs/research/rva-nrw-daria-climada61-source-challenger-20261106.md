<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CLIMADA 6.1.0 as an external, source-pinned European wind impact challenger

**Research-only, 6 November 2026. Not an actual R+V model.** We compare
published European winterstorm impact-function **methods** with the first
original Daria 1990 → 10,000 public 2022 NRW building candidate spatial
overlay. This is the next scientific check on the previous **entirely
invented** wind damage response experiments and fixed-threshold cubic
wind severity index. It is an **independent source-derived replay**, NOT
native CLIMADA execution, empirical German calibration, source-year
claims, insurer GUL/IL/RI or annual OEP/AEP.

## Pinned upstream code, rights and scientific definitions

Original public [CLIMADA Python](https://github.com/CLIMADA-project/climada_python),
immutable **release v6.1.0** (2025-09-30); CLIMADA code is **GPL v3**,
not Apache-2.0. The benchmark script NEVER commits or vendors its GPL
source, imports implementation into the Apache project, modifies CLIMADA,
or republishes full provider code. An isolated GitHub runner retrieves
just three unmodified upstream files temporarily from the original
release and verifies their **Git blob SHA-1** before extracting the
underlying numerical function inputs (without executing untrusted
source code).

| Upstream release v6.1.0 original file | Git blob SHA-1 |
| --- | --- |
| `climada/entity/impact_funcs/storm_europe.py` | `76973c3df21bc5dbb89f21a962846a01c0c9fce9` |
| `climada/engine/calibration_opt.py` | `5f174b5f77cc55d690a7d962d735221928838029` |
| `climada/entity/impact_funcs/base.py` | `c51540d5738a6a6f1fa38fe8440f65ace8d9ccc4` |

Scientific citations:
- [Schwierz et al., 2010, European windstorms impact-function
  model](https://doi.org/10.1007/s10584-009-9712-1)
- [Welker et al., 2021, European winterstorm impacts and
  calibration](https://doi.org/10.5194/nhess-21-279-2021)
- [CLIMADA 6.1.0 source: `ImpfStormEurope`](https://github.com/CLIMADA-project/climada_python/blob/v6.1.0/climada/entity/impact_funcs/storm_europe.py)
- [CLIMADA original impact interpolation
  `ImpactFunc.calc_mdr`](https://github.com/CLIMADA-project/climada_python/blob/v6.1.0/climada/entity/impact_funcs/base.py)

The published method has two separate components of expected direct
damage at site gust `v`:

- `PAA(v)`: proportion of assets affected.
- `MDD(v)`: mean damage degree conditional on affected assets.
- `MDR(v)=interpolate(PAA,v) * interpolate(MDD,v)`: CLIMADA
  interpolates **both** separately, then multiplies; interpolating the
  product of their original knots instead is **not numerically identical**.

For Welker, source-pinned `calibration_opt.change_impf` scales **both**
PAA and MDD, clips to [0,1], and first resamples to
`(N+1)*10+1` equally spaced source-gust intensities, where N is the
original Schwierz knot count. The bridge independently replays that
defined interpolation using Python's decimal arithmetic. Results may
differ by floating-point rounding from *native* NumPy/CLIMADA, so
full-model bitwise parity is **not claimed**; a later cross-engine
parity benchmark must execute the actual tagged CLIMADA package.

The 2021 method is a **published Europe-wide impact-function
calibration**, not independently validated for R+V German buildings,
roof categories, building-specific vulnerability, original insurer
terms, historical Daria losses, or today's underwriting distribution.
The source 3-second gust footprint may not be directly comparable to
the specific wind-intensity conventions used for the literature
calibration without independent measurement/height/duration assessment.

## Input and calculation scope

The script
`research_runners/rva_nrw_daria_climada61_source_challenger_v0.py`
uses the **existing** SHA-verified source-derived XWS Daria 1990
site-gust ZIP: **10,000 public 2022 NRW physical building candidates,
53 Kreise and EUR 4,826,029,500 completely fictitious 2025-like TIV**.
The actual *source hazard bytes and geometry* are independently linked
to [the original 2026-11-05 XWS source-run](rva-nrw-xws-daria-original-wind-source-20261105.md).

The model never relabels a public building as actually insured.
It computes six deterministic **event-conditional theoretical direct
building-value** calculations (2 published method variants × 3
alternate wind estimates for **one** physical 1990 Daria event), as
`ROUND_TO_CENTS(fictional_TIV × interpolate(PAA,v) × interpolate(MDD,v))`.
The per-building integer EUR-cent values reconcile to 53 Kreis rows
and an all-portfolio total; the output labels the numbers as a
**comparative hypothetical loss sensitivity**, not real GUL, IL,
RI, gross/net EP, an insurer TIV inventory or pricing.

- Own, offline **fictional** unit tests:
  `tests/test_rva_nrw_daria_climada61_source_challenger_v0.py`,
  hand-calculated with invented miniature PAA/MDD curves. They
  challenge source byte tampering, false company/frequency status,
  interpolation order, scaled vs original methods, duplicate sites,
  deterministic ZIP bytes, and nonredistribution of original GPL code.
- No annual event catalogues, no licensed vendor hazard model,
  source-independent outcome observations, model calibration or
  stochastic secondary-uncertainty distribution. The three wind
  estimates are **not** three event years or quantiles of portfolio
  monetary loss.
- No GPL curve arrays or provider program text is stored in Git.
  The external original-code bytes are fetched and verified at runtime,
  remain ephemeral on GitHub CI and are removed prior to artifact upload.

## Interpretation and forward model gates

Compare published European method **sensitivity** to the existing
[entirely invented two-curve Daria experiment](rva-nrw-xws-daria-invented-event-direct-value-20261106.md)
and [wind-intensity-only excess cube index](rva-nrw-xws-daria-asset-sampled-excess-cubed-severity-20261106.md).
A difference is not an error unless independently established
material/roof claims validation proves a candidate approach wrong.

The first meaningful *scientific calibration* gate is to obtain
independent, properly licensed German or wider European
**building-type-specific storm loss and wind** observations, including
source hazard reference period/height/duration and policy coverage
boundaries. Only then calibrate/hold out vulnerability. For annual
OEP/AEP, require complete annual physical-event occurrence/cluster
model, explicit zeros, insured contract mapping, financial module
and outward reinsurance/retro chronology with NextGen.

**Status remains NOT MODEL ADMITTED for actual carrier risk.**
