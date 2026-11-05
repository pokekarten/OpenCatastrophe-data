<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WISC NetCDF-4 → Oasis hazard tile v0

**2026-11-05. An executable, explicitly limited synthetic-data adapter.
This is NOT a native WISC model run or a licensed/admitted full 22,980-event
storm library.**

## Original scientific source and important new service warning

- [C3S Synthetic European Windstorm Event Set](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-synthetic-events?tab=overview), source DOI `10.24381/cds.ce973f02`, product 1.0, CC-BY as advertised by CDS.
- [Official Copernicus Product User Guide](https://confluence.ecmwf.int/spaces/CKB/pages/255094970/Synthetic+Windstorm+Events+for+Europe+from+1986+to+2011+Product+User+Guide), last modified **2026-07-02**: the WISC synthetic-event dataset is **no longer supported and will be removed from CDS at a later date**. The download page currently asks the user to log in and accept licence terms before requesting the source bytes. No anonymous complete original NetCDF-4 asset was available to this turn.
- Published 22,980 footprints = three recalibration/downscaling sets with **7,660 storm variants in each set**, plus five independently initialized historical-forcing climate ensemble members (1–5). This is not 22,980 independent annual probabilities. A storm can be represented in multiple alternative recalibration methods. It is also not an observed 1986–2011 weather-event record.
- **Missing simulated periods are documented** by the original Met Office guide: Oct 1988–Nov 1998 (ensemble member 4), Dec 1988–Mar 1990 (member 3), Oct–Nov 2002 (member 4), Dec 2008–Feb 2010 (member 5). Historic calendar labels in filenames are simulated forcing time, not actual dated losses. Never treat these missing months as zero-storm years or assume five fully observed equal-exposure model windows.
- Source wind variable has 10 m height, 3-second maximum gust averaged over a 72-hour physical storm window, in **m/s**. The published grid is approximately 4.4 km after interpolation from 25 km. Grid-cell gust is **not** point gust at the insured building. The upstream filename is documented as `fp_ga3ups_<YYYYMMDDHHMM>_<track4>_<three-digit-code>_v1.nc` (possibly `C3S_EvenSet_` prefix). The trailing three-digit code is deliberately **opaque in this adapter**, until checked against real filenames and file metadata. Do not decode it into a verified ensemble/set mapping from appearance alone.

## Exact deliverable and limitations

[`research_runners/wisc_netcdf_oasis_tile_v0.py`](../../research_runners/wisc_netcdf_oasis_tile_v0.py) reads **one local original
NetCDF-4 HDF5 file** after validating its full SHA-256 and official
filename structure. It requires the user to explicitly name the wind,
latitude, longitude variables; it never chooses the first plausible data
variable or silently changes km/h to m/s. Source data must have a
single **2D latitude × longitude** gust field, with strictly monotone
1D geographic coordinates (ascending or descending). More complex
native WISC variable/dimension structures fail, pending a verified
first-byte provider example and a new explicit profile.

The converter reads **only a bounded tile** of up to 10,000 cells and
emits exactly:

- `events.csv`: single local synthetic event ID. Not a probability.
- `footprint.csv`: `event_id,areaperil_id,intensity_bin_index,prob`;
  an unambiguous deterministic gust bin per original cell and
  probability **1.0** within that cell. This is hazard conditional on
  the declared event, not occurrence frequency.
- `intensity_bin_dict.csv`: contiguous wind-speed bins with explicitly
  declared edges and numeric interval reference.
- `areaperil_dict.csv`: exact source grid row/column and cell **centre**
  latitude/longitude for a stable global-grid-based integer area-peril
  ID. This is not a polygon or insured-site geocoder.
- `research_receipt.json`: full original-byte SHA-256; output-file
  hashes/size; selected simulated-event filename, synthetic set,
  ensemble-member (the latter are user declarations, not verified
  original-code crosswalk); source grid/tile extents; counts of
  unobserved/no-data weather cells; and hard NO flags.

Missing `_FillValue`/NaN cells are **unknown hazard**, never zero gust;
negative, nonfinite infinite or out-of-bin gust values block. The
lowest bin begins at 0 m/s. A value on an internal bin boundary is
placed in the upper bin, while the final upper endpoint is inclusive;
values exceeding the last bin edge are refused, not clipped.
Output location must not exist; no overwrite and no source asset
bytes enter Git.

### No annual EP inference

This scope does **not** generate `occurrence.csv`,
`returnperiods.csv`, `periods.csv`, `vulnerability.csv`,
`damage_bin_dict.csv`, lookup and financial terms or annual loss
curves. These outputs and a validated exposure/treaty mapping are
required before any native calculation. `annual_oep_aep_authorized`
and `native_oasis_run_verified` stay **false**, even when source
input and four CSV output checks pass. Conversion of **one** gust tile
does not prove completeness of an event-set, correlated storm identity,
year/ensemble rate measure, damage functions, insurance and
reinsurance results or calibration of return periods.

## Reproduce on a local licensed original file

First, download an exact NetCDF-4 original via the official provider
account under accepted CC-BY terms. Store outside this repository,
record the provider request/version, original byte size, SHA-256 and
source acquisition time. An example below uses only a placeholder path
and SHA string; no original provider bytes were obtained in this study.

```sh
python -m pip install "xarray==2025.1.2" "netCDF4==1.7.3"
sha256sum /external/c3s/fp_ga3ups_199311201800_1708_002_v1.nc
python research_runners/wisc_netcdf_oasis_tile_v0.py \
  --netcdf /external/c3s/fp_ga3ups_199311201800_1708_002_v1.nc \
  --original-sha256 "<64-hex-original-receipt>" \
  --variable "<exact-original-gust-variable>" \
  --latitude-variable "<original-1d-latitude-variable>" \
  --longitude-variable "<original-1d-longitude-variable>" \
  --event-id 1 \
  --synthetic-set 1.2 --ensemble-member 2 \
  --row-start 0 --col-start 0 --height 2 --width 3 \
  --bin-edges "0,10,20,30,40,50,60,80,120,200" \
  --out /external/output/wisc-oasis-demo
```

**Important:** `--synthetic-set 1.2` and `--ensemble-member 2` are
illustrative **claims to check**, not observed metadata for that
filename. The variable names are unknown until an original NetCDF-4
file has been inspected. A nonmatching filename, unsupported spatial
dimensions or unknown gust units must block; do not edit the guard to
accept guessed source formats. The output directory parent must
already exist, and the target must be absent.

## Synthetic-only executable evidence

[`tests/test_wisc_netcdf_oasis_tile_v0.py`](../../tests/test_wisc_netcdf_oasis_tile_v0.py)
tests malformed identifiers, duplicate/nonmonotone geocoordinates,
no-data cells, bad units, bad dates and bin boundaries, strict
original SHA-256 and output hash determinism.

The separate
[`wisc-oasis-netcdf4-synthetic.yml`](../../.github/workflows/wisc-oasis-netcdf4-synthetic.yml)
installs a pinned NetCDF-4 reader and, **on a temporary Linux runner**,
creates a fully **invented** two-by-three-cell NetCDF-4 HDF5 file
with one missing cell. It must produce the exact four Oasis-style
CSV types and a deterministic receipt; no provider asset is fetched.
Local repository base CI exercises pure-stdlib core tests, while the
extra workflow exercises actual NetCDF-4 byte decoding. Neither
test is allowed to assert a full or even half-real WISC event model.

## Future ingestion gates

1. **Original source retrieval, priority/high urgency** given
   announced dataset deprecation: CDS authenticated contract,
   provider terms, original file, original download SHA-256, sample
   NetCDF variables and dimensions, exact method/ensemble/track
   filename crosswalk and source temporal availability.
2. **Grid profile:** freeze and confirm WGS84 grid topology,
   coordinate bounds, cell polygons (not just centroids),
   original wind units and metadata. Only then validate area-peril
   OED lookup for synthetic building coordinates.
3. **Complete events/occurrences:** one explicitly selected
   recalibration methodology, five complete ensemble-member
   *observed* simulated-year windows, missing simulation intervals,
   physical-storm ID, geographic overlaps, multistorm clustering,
   zero-event years and period weights. Never turn missing source
   coverage into zero-loss years.
4. **Financial pathway:** source-licensed vulnerability functions
   paired to 3-sec gust bins; independent weather validation;
   synthetic location/account/policy OED, native GUL/IL/RI tests,
   full original annual loss series, gross/insured/net curves,
   scientific checks versus historical observations. The unrelated
   [native public toy PiWind runtime proof](https://github.com/pokekarten/OpenCatastrophe-data/pull/1383)
   cannot substitute for this model.

This work deliberately avoids the separate
[C3S historical frequency research PR #1308](https://github.com/pokekarten/OpenCatastrophe-data/pull/1308),
the [synthetic carrier-OED PR #1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373),
and the existing regional wind-footprint overlay scripts.
