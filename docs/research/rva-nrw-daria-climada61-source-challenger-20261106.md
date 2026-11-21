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
 
## Observed exact-source CI execution: 6 November 2026

The original XWS Daria 1990 source run
[GitHub Actions #42230854661](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42230854661)
completed **SUCCESS** at git head `0c0a57965086dadd98b7e75c56fe6853188c97ff`.
The workflow verified the exact three original CLIMADA **v6.1.0**
GPL-source Git-blob identities (3/3), completed 7/7 independent
synthetic CLIMADA-method regression tests, downloaded the unchanged
original four XWS Daria CSV sources, regenerated the actual
10,000-location original-hazard overlay, and computed six
source-replayed PAA × MDD scenarios.

**Exact model-run results: EUR integer cents** (fictional replacement
values, direct building-value sensitivity, **not actual insurer loss**):

| Published European impact-method replay | Daria lower95 gust | Daria mean gust | Daria upper95 gust |
| --- | ---: | ---: | ---: |
| Schwierz 2010 in CLIMADA 6.1 | 12,224 cents (EUR 122.24) | 10,999,796 cents (EUR 109,997.96) | 1,721,892,751 cents (EUR 17,218,927.51) |
| Welker 2021 in CLIMADA 6.1 | 21,893 cents (EUR 218.93) | 19,531,425 cents (EUR 195,314.25) | 3,059,869,204 cents (EUR 30,598,692.04) |

Every case uses identical original physical Daria event identity,
10,000 public NRW 2022 building candidates, 53 Kreise and EUR
4,826,029,500 **invented** building TIV. The three original
recalibrated wind fields are same-event uncertainty views rather than
independent years or loss confidence quantiles.

The mean-gust CLIMADA-method theoretical direct values differ greatly
from the prior wholly invented values (EUR 11,837,763 for the invented
resilient function and EUR 118,377,621.07 for the invented fragile
function). They are deliberately **not** reconciled by choosing
arbitrary scale factors. The external European methods are published,
but are not empirically fitted/verified against source-matched German
construction, roof type, insurer coverage, 3-second-gust measurement
conventions or R&V claims. The lower95 source field produces some
small CLIMADA output even though the separate *fixed 25 m/s cubic
severity index* is zero: published PAA/MDD at low gust is not
identical to the strictly thresholded SSI definition.

Time-limited [CLIMADA comparison artifact #13507852666](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42230854661/artifacts/13507852666)
contains all 10k × six site-level values, county summaries,
source-identity hashes and explicit false promotion flags. Original
CLIMADA GPL source code and raw XWS CSV data remain external to
GitHub repository and artifact. The source-based replay is
**not native installed CLIMADA execution**; an actual native
CLIMADA-to-standalone numerical parity test remains a follow-up
acceptance check before claiming reproducibility across engines.

**Remaining hard NO-GO:** true R&V exposure, approved German
vulnerability and independent loss calibration, coverage/limits and
outward reinsurance model, complete annual event catalogue including
zero years and clustering, consequently no gross/net OEP/AEP.

## Exact published original-method execution parity (6 November 2026)

[GitHub Actions original-code execution #42244616104](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42244616104)
completed **SUCCESS** with original XWS source and original CLIMADA
v6.1.0 source identities. Its separate
[method-level numerical parity receipt #13515854358](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42244616104/artifacts/13515854358)
documents exactly **60,000 per-building values checked**: two
source-authenticated published impact methods × three source
recalibrated wind views of the **same** Daria 1990 event × 10,000
2022 public NRW building candidates.

The separate research runner
`research_runners/rva_nrw_daria_climada61_original_method_parity_v0.py`
executes the **unchanged AST method bodies** from the three
original-byte-verified, GPL-v3 CLIMADA 6.1.0 source files:
`ImpfStormEurope.from_schwierz`,
`ImpfStormEurope.from_welker`,
`change_impf` and `ImpactFunc.calc_mdr`. It replaces only
CLIMADA's external **nonnumeric class lifecycle** with a strictly
checked minimal class state and uses pinned NumPy 1.26.4 /
SciPy 1.14.1 in an ephemeral CI environment.

**It is NOT a fully installed, native CLIMADA distribution** and
does not claim its broader exposure/hazard workflow, event-year
simulation or insurance financial engine work. No external GPL
source bytes are committed or included in result artifacts.

| Original published method and source wind case | Original float64 method aggregate | Independent Decimal aggregate | Asset cent differences |
| --- | ---: | ---: | ---: |
| Schwierz / lower95 | EUR 122.24 | EUR 122.24 | **0/10,000** |
| Schwierz / mean | EUR 109,997.96 | EUR 109,997.96 | **0/10,000** |
| Schwierz / upper95 | EUR 17,218,927.51 | EUR 17,218,927.51 | **0/10,000** |
| Welker / lower95 | EUR 218.93 | EUR 218.93 | **0/10,000** |
| Welker / mean | EUR 195,314.25 | EUR 195,314.25 | **0/10,000** |
| Welker / upper95 | EUR 30,598,692.04 | EUR 30,598,692.04 | **0/10,000** |

The original float64 PAA/MDD/MDR components deviate from the
Decimal source replay by at most approximately **5.02×10^-16**
in absolute value (binary floating-point representation).
All sampled *per-site* integer-cent impacts match **exactly**.
After this observation, the committed parity runner was strengthened
to **zero tolerated differences in integer cents per site**, rather
than allowing up to one cent as a floating-point round-off
accommodation; this policy must remain enforced in subsequent CI.
That tightening has its **own new-head CI gate** and must not be
represented as passed until that run completes.

**Bounded claim:** Scientific formulas and method implementation
agree at the original source-based Daria site inputs; this does
not validate actual R&V insurance, German buildings' roof/physical
vulnerability, compatibility of 3-second gust conventions with
the original literature calibration, zero-event-year frequency,
insured GUL/IL, reinsurance RI or gross/net annual EP.
A full conda/mamba native CLIMADA 6.1.0 package run, if required,
must be separately installed and validated against the original
package documentation/conda dependencies.

**Future source-replay reproducibility blocker:** The linked
original 2022 geocoded 10k research source artifact from
[earlier run #42097472463](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463)
is a temporary GitHub Actions artifact, not immutable long-term
source storage. The workflow must replace this dependency with
an enduring rights-aware source-intake/rebuild plan before those
artifacts expire. Immutable checksum/rights receipts alone cannot
recreate their source bytes.
