<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GTSM-ERA5-E v2 original statistical NetCDF research receipt (v0)

Source: https://zenodo.org/records/14671593; DOI 10.5281/zenodo.14671593; published 2025-02-25, v2.
Exact asset: `ds_GTSM-ERA5-E_1950-2024_stats.nc`, original HTTP content length **9,652,424 bytes**, publisher-listed **MD5 0f2b7071c6ec3585768be6cf427e6eab**.
Publisher metadata was independently verified by GitHub Actions exact-head run [41507598794](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41507598794), 2026-11-02 19:12:57 UTC: full 9,652,424 bytes, publisher-listed MD5 matched, NetCDF4/HDF5 signature confirmed. Independently observed source **SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767`** is now an additional fixed reject-on-drift source gate. SHA-256 was independently computed, not published by the provider. No source bytes committed or persisted to Neon.

## Executable research step

For a separately lawfully acquired original file, use the offline check:

    python scripts/gtsm_era5_e_original_receipt_v0.py --original /path/to/ds_GTSM-ERA5-E_1950-2024_stats.nc
    python -m unittest tests.test_gtsm_era5_e_original_receipt_v0 -v

To verify exactly one public provider file and optionally audit only native coordinate pairs in aggregated form on an internet-enabled runner, run:

    python scripts/gtsm_era5_e_original_receipt_v0.py --fetch --inspect-header --audit-coordinates

The fixed PR workflow `.github/workflows/gtsm-era5-e-original-receipt.yml` runs the offline tests followed by this exact one-file HTTPS download (only same-repository PRs). The fetch mode has no caller-selectable URL; refuses non-Zenodo redirects, unexpected size, HTTP failures and MD5 mismatch; only a metadata receipt reaches CI logs. Provider bytes are held only in an ephemeral temporary file during verification and deleted immediately. No source file or raw array is uploaded as an artifact.


The verifier performs local read-only streaming over the full regular non-symlink source file, checks exact published length and MD5, validates a recognizable HDF5/NetCDF signature, then **rejects any drift from the SHA-256 observed in successful original-source run 41507598794**. With `--inspect-header` it inventories dimensions, variable names, types, shape, units and short descriptive attributes without reading variable values; source-native science/vertical-datum validity is not inferred. Offline mode never fetches; online mode uses only an ephemeral temporary file and deletes it before returning. Neither mode retains provider bytes in the repository, derives losses, or publishes raw values. The production-facing CLI has no hash/size override; synthetic unit tests exercise the internal receipt function with independently invented fixtures.

## Scientific and licence barriers

- This particular Zenodo asset is descriptive statistics of modelled *still water levels*, not flood-inundation footprints, actual coastal building damage, tide-gauge measurements, insured values or stochastic CAT event losses.
- The accompanying 2026 study (https://essd.copernicus.org/articles/18/5759/2026/) identifies the statistics as detrended hourly total-water-level extreme values with 5%–95% confidence ranges and independent original time series in CDS DOI 10.24381/cds.a6d42d60. The full time series has separate identity, access and scope.
- Publication describes tidal/surge modelling and reference to 1986–2005 local mean sea level for the total-water-level series. The statistics are detrended. Do not attach these statistics to a local DEM, vertical datum or building altitude without an independent reference/geometry audit.
- The data's exact redistribution/commercial rights must be confirmed against current Zenodo rights metadata and any upstream CDS conditions. Public download is not an admission.
- A validated MD5, file signature and new SHA-256 **do not prove** NetCDF dimension names, value units, vertical datum, scientific fitness or source independence. These are separate next tests and no insurer/CAT input approval is implied.

## Original native NetCDF structural evidence (2026-11-02 21:01:44 UTC)

Exact-head GitHub Actions GTSM run [41524452571](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41524452571) completed successfully after independent fixed SHA-256, size and provider-MD5 verification; the header was read with pinned `netCDF4` without sampling a single variable value. The original contains precisely **38,957** station entries, **8** return-period slots and **7** quantile slots. Those **38,957** entries are an original file dimension, not an independently verified count of all 44,734 GTSM simulation locations mentioned in the paper. Do not equate them.

Confirmed original variables and storage: `lon`/`lat` int32 with coordinate units `degrees_east`/`degrees_north`; `stations` uint16; `return_period` int64 with units `years`; `wl_quantiles` float32 on quantile×station with metres; `wl_extreme_bestfit`, `wl_extreme_5perc`, `wl_extreme_95perc` float64 on station×return_period with metres; and `eva_param_scale`, `eva_param_shape`, `eva_param_loc` float64 by station. The quantile and return period *values* have not been read and cannot yet be certified as specific numerical slots from NetCDF, even if the provider describes them.

**Important:** int32 longitude/latitude require exact native `scale_factor`, `add_offset`, missing-value metadata and spatial bounding checks before use in site joins. The next profile inventories coordinate packing *attributes only*. Coordinate unpacking, projection/datum compatibility and uncertainty calibration remain blocked. The field-level native axes/types/units gate is a source-vintage drift detector, not scientific admission. No storm events, spatial footprints or observations should be fabricated from these return-period vectors.

The paper describes a hydrodynamic-model coastal output point set, whereas these statistical results are an independently selected 38,957-row NetCDF station axis. Reconcile missing/excluded locations and dependence on prior GTSM/WRI Aqueduct coastal products before treating them as independent validations. Study: https://essd.copernicus.org/articles/18/5759/2026/ .

## Pinned native coordinate packing (2026-11-02 21:04 UTC)

The successful exact-head original-source run [41524827932](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41524827932) confirmed source MD5 and independent pinned SHA-256 again, plus **18** successful offline regression tests. The NetCDF native `lon` and `lat` variables are `int32`; both have the **metadata-only** packing attributes `scale_factor = 0.001`, no `add_offset`, and `_FillValue = -999`. These exact attributes are now fail-closed invariants in the next revision. The raw coordinate and return-period arrays remain unread in this research pass.

A downstream coordinate transform must mask the native fill code before applying the scale factor and independently check geographic ranges, indexing, axis units, coordinate duplicates, and any source/epoch mismatch; **no site-to-building join is authorized by this metadata receipt**. Also assess time-varying datum, coastal-model output-point semantics and 38,957-vs-44,734 coverage before defining coastal exposure.

## Execution evidence

The complete real-source receipt of 2026-11-02 is verified from exact-head runner logs (run #41507598794, job #125490753179); 12 synthetic boundary tests and Python 3.11–3.14 matrix passed. The following revision pins the independently observed SHA-256, reproduces the original native metadata from the GitHub run above, and adds a version-specific dimension/axis/unit/type gate. The next exact-head CI and header-inventory capture remain required before accepting the stricter gate. The earlier receipt did not inspect the NetCDF variables. No model admission, permission for commercial reuse, raw file retention or event generation is implied.

## Bounded native coordinate QA

After the pinned-source SHA-256 and native structure/coordinate packing checks, the fixed source workflow now also reads *only* the native longitude/latitude int32 arrays and reports **aggregate counts**. Mask raw `-999` before applying native 0.001-degree scale; check ±180°/±90° geographic limits in raw integer units, one- or two-coordinate missingness, repeated raw coordinate pairs and positions at (0,0). The only copied values are the two ephemeral in-memory original vectors of 38,957 integers each; source coordinates, location samples, individual IDs, hazard cells and loss outputs are never logged or persisted.

`scripts/gtsm_era5_e_coordinate_audit_v0.py` contains a pure synthetic-testable counter with fixed 38,957-row source budget. It is **not** an all-coastal classifier: publisher data include both ocean and coastal model locations. Individual returned coordinate pairs are not geocoded or joined to buildings. Existing uncertainty about source simulation 44,734 locations, local datum, interpolation validity and permitted reuse remains unresolved.

The next exact-head CI run must confirm the geographic QA counts from the real original; a generated counter or standalone synthetic test is not evidence of real-source quality until this run succeeds.

## Observed original geographic QA receipt (2 November 2026)

The exact-source, same-repository GitHub workflow [41528000802](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41528000802), job `125561318447`, finished **successfully**. Its 32 synthetic offline tests passed and it revalidated the original source's published 9,652,424 bytes, published MD5 `0f2b7071c6ec3585768be6cf427e6eab` and independent pinned SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767`.

The workflow then read only original *unscaled native int32 longitude and latitude arrays* with the already verified NetCDF4 `scale_factor=0.001`, absent offset and raw fill value `-999`. It published only the following aggregate QA receipt, with no individual point coordinates or original-byte artifacts:

| Original-coordinate check | Observed count |
| --- | ---: |
| Native location rows checked | 38,957 |
| Coordinate pairs within geographic bounds | 38,957 |
| Distinct within-range coordinate pairs | 38,957 |
| Both coordinates missing | 0 |
| Exactly one coordinate missing | 0 |
| Outside longitude ±180°, latitude ±90° | 0 |
| Repeated in-range coordinate pairs | 0 |
| Records at exactly (0°, 0°) | 0 |

This establishes **syntactically sound unique geographic coordinate pairs for this exact file version**, not truth of site locations, coastline proximity, actual 44,734-model-station completeness, physical vertical datum, observed sea level, uncertainty-calibrated local flood hazard or insurance-risk suitability. The raw source has been removed from the ephemeral workflow environment; no individual coordinates were added to Git or Neon.

Review the original-file `quantile` axis separately: the paper describes nine percentile levels but this NetCDF presents only seven `quantile` entries. The raw probability/period axis labels were not read during this coordinate audit. No substitution or extrapolation is allowed until reconciled.


## Native probability and return-period axis semantics

The official 2026 GTSM paper enumerates nine percentile levels (1, 5, 10, 25, 50, 75, 90, 95, 99), but the pinned Zenodo v2 statistical NetCDF has only seven `quantile` coordinate entries. The next original-file reader now retrieves only these seven native scalar labels and the eight scalar `return_period` year labels. It runs after the published MD5, independently pinned SHA-256 and exact native header validation. It compares observed period years against the paper (1, 2, 5, 10, 25, 50, 75, 100) without reading `wl_quantiles`, storm events or individual water-level values.

The quantile encoding is only tentatively interpreted as fraction or percent based on observed scalar ranges, and the paper-level discrepancy is retained as a *research unresolved* field until a scientific review confirms exact semantics. The script never interpolates or invents missing quantiles. Run the fixed-source GitHub workflow again before treating the new axis label evidence as verified.

## Actual original quantile and return-year coordinate labels (2026-11-02)

The successful exact-head GitHub runner [41528816768](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41528816768), job `125563439416`, repeated the publisher MD5 and independently pinned SHA-256 verification and passed **42** synthetic offline tests. Without reading `wl_quantiles`, any water-level extreme or any individual station locations, it read the pinned original's two native scalar coordinate axes:

- Native `quantile` values: `[0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]` (fraction-scale *candidate* metadata encoding, i.e. candidate 5, 10, 25, 50, 75, 90 and 95th percentiles).
- Native `return_period` values, units years: `[1, 2, 5, 10, 25, 50, 75, 100]` (exactly matching the publication).
- Official paper describes nine percentile levels: `[1, 5, 10, 25, 50, 75, 90, 95, 99]`. This source asset includes seven, omitting **1st and 99th**. Do **not** interpolate, fabricate or claim them in native asset exports. The reason for the paper/file mismatch needs a provider- or scientific-review explanation.

The original source also again reported **38,957** valid, in-geographic-range unique longitude/latitude coordinate pairs, no missing or duplicate pairs, and no (0,0) locations. The audit does not establish coastline proximity, local inundation depths, vertical datum compatibility, probability calibration, annual stochastic event independence, reuse permission or insurer-level losses. All admission flags remain false; no provider grids, site coordinates or source bytes were written to Git or Neon.


## Original extreme-return-level QA (research 2026-11-03)

The next research workflow reads the three source-native water-level statistic matrices `wl_extreme_bestfit`, `wl_extreme_5perc` and `wl_extreme_95perc` (38,957 station rows × 8 return-period columns). The read is **strictly gated** behind an exact original 9,652,424-byte download, published MD5, independently pinned SHA-256, release-specific NetCDF dimensions, units, packing and the eight original return-period year labels. An isolated, size-bounded checker `scripts/gtsm_era5_e_return_level_qa_v0.py` counts missing/nonfinite values, uncertainty band inversions, best estimates outside the 5–95% bands and descending adjacent best-fit return levels. Source-declared fill/missing sentinels are excluded from numeric comparison. A 1e-9 metre comparison tolerance avoids obvious floating point rounding false positives.

The workflow emits **only aggregate counts**: no point values, station IDs, raw coordinates, measured sea levels, inundation depths or provider source assets. Its synthetic tests are located at `tests/test_gtsm_era5_e_return_level_qa_v0.py`. Detected flags warrant scientific investigation; a difference in fitted extreme-value parameters and statistical uncertainty conventions is not automatically a data defect. These checks do not establish local vertical datum, rate independence, tide-gauge skill, coastal flood connectivity, proper loss-model coupling, allowed commercial reuse or model admission. Real-source numbers must be obtained from the exact-head GitHub execution; no counts are preasserted.

Primary sources: https://zenodo.org/records/14671593 and https://essd.copernicus.org/articles/18/5759/2026/.

## Verified aggregate original return-level findings (2026-11-03)

The same-repository exact original-source GitHub Actions run [41640280655](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41640280655), job `125931771294`, passed **58 deterministic offline source-boundary/synthetic tests** and the **real, exact pinned Zenodo original NetCDF QA**. It repeated the 9,652,424-byte source-byte receipt and original SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767`. Original three native water-level statistic matrices were inspected in memory only. The workflow printed *aggregate counts*, never individual station water levels.

| Observed original statistic QA | Count |
| --- | ---: |
| Original station positions | 38,957 |
| Return-period slots | 8 |
| Candidate (best-fit, 5%, 95%) triples | 311,656 |
| Numerically finite triples | **311,655** |
| Triples with at least one missing/nonfinite cell | **1** |
| Inverted 5%–95% intervals | **0** |
| Best-fit above upper 95% bound (cell comparisons) | **22** |
| Best-fit below lower 5% bound (cell comparisons) | **4** |
| Stations with any best-fit/band disagreement | **6** |
| Adjacent best-fit return-period descents (> 1e-9 m) | **0** |
| Stations with a missing/nonfinite triple | **1** |
| Stations with no tested flags | **38,950** |

**Interpretation:** the 22 above-band and 4 below-band *cells* are not 26 independent stations; the original source shows six distinct station rows with a band/point-estimate inconsistency. There is one *additional* station row with a missing/nonfinite triple. These observations should trigger examination of source-native `wl_extreme_5perc`, `wl_extreme_95perc`, the fitting/uncertainty convention and possible numeric encoding; they are **not** sufficient to conclude physical error, bias or unfitness at any given location. The source's extreme-value and coastal model assumptions, vertical datum and dependence on ERA5 require separate scientific checks.

The original published 1st and 99th percentiles are not present in this specific seven-level `quantile` array (verified labels are 5, 10, 25, 50, 75, 90, 95 %); the above 5%-95% confidence bound checks concern the *separate return-level arrays*. Do not confuse these two kinds of percentile quantity, fabricate missing levels or use return-level vectors as stochastic YLT/ELT inputs.

**Admission boundary:** this is reproducible original-source numeric QA only. No commercial licensing or redistribution of source bytes is approved, no geometry join or coastal inundation computed, no insurer or portfolio rows created, no Cat XL/NextGen loss outputs inferred.

