<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NRW geocoded 10k hypothetical R+V-like portfolio → NextGen C3S wind-grid input, strict nonadmission

**Date 2026-11-05, research only.** The goal is to reuse the existing NextGen `research/c3s_wind_footprint_stage_v0.py`, NOT write another catastrophe modelling engine or misrepresent the available 2022 NRW HU building sites as observed R+V insurer assets. Oasis OED ≠ windstorm source hazard ≠ calibrated vulnerability ≠ annual frequency / gross/net model.

## Original exposure evidence and handoff scope

Input is [PR #1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373)'s independently verified 10,000 location/account/evidence research ZIP from [successful complete official HU ZIP run #42097472463](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463). The physical source original full 901,092,946-byte archive SHA-256 must equal `10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da`; individual input CSV hashes from that exact output manifest are verified, original HU 2022 full-member CRC gate must be true, full sample count 10,000 and all 53 NRW Kreise. The original building's physical location is authentic public provider data, **not actual R+V insured address, 2025 exposure or a verified wind-vulnerability taxonomy**. Synthetic BuildingTIV is held exactly as provided for shape contract validation and must not be called a measured replacement cost or sum insured.

The runnable standard-library module `research_runners/rva_nrw_hu22_to_nextgen_c3s_spatial_v0.py` exports `nextgen_c3s_spatial_handoff.json` and `source_boundary_receipt.json`. Each named fake policy/site is preserved as `asset_id`. NextGen-shaped `crosswalk_assignments` contain exactly:

- `asset_id`, `cedant_id` (explicitly `FICTITIOUS_RVA_LIKE_NRW_NOT_OBSERVED`), `country_iso2` (`DE`), `taxonomy` (`UNMAPPED_HU22_GFK_31001_XXXX`), `lon_e6`, `lat_e6`, `col`, `row`, `cell_id`.
- NextGen-shaped `insured_asset_values` have only `asset_id` and `replacement_cost_eur`. The field name comes from the existing downstream interface, not from actual insurer records.
- `grid` has exact fields `grid_id`, `west_lon_e6`, `south_lat_e6`, `width_e6`, `height_e6`, `num_lon`, `num_lat`, `crs`, with one-to-one half-open 0.25° cell mapping, exact source seven-decimal locations rounded to microdegrees, rejection of boundary ambiguity and out-of-crop records.

**No real storm grid is available at this point.** The bundled `research/fixtures/rva_nrw_c3s_synthetic_grid_demo_v0.toml` declares a **completely invented grid** at 5.5°E–10.5°E, 50.0°N–53.25°N with 20 × 13 fictitious 0.25° cells. The importer **refuses** all grid requests without `INVENTED_RECTANGULAR_GRID_NOT_AUTHENTICATED_C3S`, and its generated receipt cannot claim C3S provenance, storm gusts, annual EP or German-catastrophe model admission. The synthetic grid does **not** reflect the original cell centers or spatial extent of any actual C3S event. Real NetCDF grid geometry must be supplied via a distinct original-source-attested stage, with all 10k assigned to complete coherent source grid mosaics; a 64×64 cropped example may not span every country or location for some higher-resolution inputs.

**No vulnerability curves are provided.** The original ALKIS residential/commercial building-function code cannot establish wall material, roof form, construction year, fragility or intensity bin. This intentionally makes a direct NextGen `stage_wind_footprint` invocation fail for missing source-authenticated grid cells and absent matching vulnerability taxonomy. Filling the missing curve with a default material or a fictional universal loss ratio would silently promote invented damage. Stop there.

## Source-identified model and hazard leads

- Existing OpenCatastrophe-data source register already contains Copernicus C3S **WISC synthetic European windstorm footprints** (22,980 event representations, multiple ensembles and three alternative downscaling/recalibration sets), and separately the C3S **EWS historical ERA5 windstorm reanalysis**. They are not the same event population or automatically an IID annual simulation. Source registration is **metadata-only**. See `docs/research/oasis-model-data-second-pass-20261105.md` and `landscape/sources-oasis-model-input-leads-20261105.json`.
- Existing NextGen source staging is in `research/c3s_wind_footprint_stage_v0.py` (strict normalized 3-second gust, C3S 0.25° or downscaled 0.016°, explicit original NetCDF event identity and complete 64×64 maximum cell crop) and `research/c3s_wind_netcdf_extract_v0.py` (bounded local NetCDF file consumer, original source user staged, no CDS authentication). It has further common-event damage/trial and original insurer/retro bridges, but actual German storm source data and calibrated damage curves are still missing.
- Oasis PiWind and Paris windstorm are toy/foreign geographical model demonstrators, **not** an admitted German residential wind CAT model. The official Oasis model provider catalogue mentions European windstorm including Germany, but model/vendor licensing, source downloads and financial model interoperability require per-provider verification. No European vendor model has been installed or run on these actual NRW exposures.

## Reproduction

After downloading the ephemeral source-derived 10k OED archive and extracting this PR:

```sh
python -m unittest discover -s tests -p 'test_rva_nrw_hu22_to_nextgen_c3s_spatial_v0.py' -v
python research_runners/rva_nrw_hu22_to_nextgen_c3s_spatial_v0.py \
  rva-nrw-2022-10k-source-geocoded-oed-fictitious-insurance.zip \
  research/fixtures/rva_nrw_c3s_synthetic_grid_demo_v0.toml \
  /tmp/rva-nrw-nextgen-unadmitted-spatial-handoff.zip
```

The mandatory source manifest and full original ZIP sha256 are checked; the output is **only a shape/geometry transfer contract**. It does not run Oasis or NextGen in this repository, nor invent GUL, insured loss, reinsurance or 99.5% capital. The output ZIP includes its own SHA-256 evidence for the NextGen-shaped JSON.

## Next evidence required before any physical/GUL or annual EP

1. Obtain **one real, licence-reviewed C3S EWS NetCDF** from the original provider and capture original SHA-256, event algorithm, 10m 3-second gust m/s units, source spatial center and missing grid mask. Independently validate 2–3 source grid-point values. For WISC 22,980 different synthetic events, separately establish ensemble/model/version/time-window weights; do not combine them with EWS historic events as independent annual claims.
2. Replace the entire fake grid with exact source cells after independent NetCDF location/CRS/coverage audit and compute real site-to-source-cell assignments in NextGen's existing spatial module. Refuse out-of-domain/ambiguous source-cell matches.
3. Choose source-licensed Germany-relevant wind damage vulnerability functions **consistent with 3-second gust units and mapped wall/roof/occupancy taxonomy**; test sensitivity to missing building attributes instead of inferring them from GFK alone.
4. Run one real event in the native Oasis/NextGen hazard→GUL path with exact physical event, world/period and loss-sample receipts. Only after frequency, event clustering, insured coverage and fictional QS/XL terms are declared and independently tested can credible **synthetic** Gross/Net OEP/AEP follow.

**Decision:** geographic crosswalk readiness is an engineering PASS after tests, physical hazard/vulnerability/annual model admission remains NO-GO; real insured company-specific CAT modelling remains NO-GO.
