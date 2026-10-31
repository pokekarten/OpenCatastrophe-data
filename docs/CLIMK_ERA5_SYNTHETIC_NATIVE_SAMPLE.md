<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CLIMK-WINDS v2 ERA5 synthetic native-grid hazard sampling

Research-only: sample the **actual, SHA-256-pinned** CLIMK–WINDS v2 ERA5 NetCDF source at exactly declared synthetic lon/lat points for one of the 50 per-source storm indices. It is not a catastrophe financial model, an annual event simulation, a complete exposure dataset, or an insurance loss projection.

Source: https://zenodo.org/records/15305753. The independently verified source SHA-256 is 92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102 and the native source grid is longitude=269 by latitude=181 with storm_number=50. The original provider data remain outside the repository.

Physical variables: absolute_maxwindgusts, units m s**-1; relative_maxwindgusts is a dimensionless ratio to the 98th-percentile climatological maximum wind gust. The source also publishes dimensionless LI3D loss-index values; these **are not insurance losses**. A storm index from this ERA5 file is not an event identity shared automatically with COSMO-REA6 or the CCLM models.

## Reproduce

Use the explicit synthetic-site JSON schema already employed by the EFFIS point audit, with schema_version oc-effis-synthetic-sites-v0, crs OGC:CRS84, synthetic_only=true, site_id, latitude and longitude. This schema is reused solely as a controlled synthetic marker representation, not as a claim that the data originate from EFFIS or correspond to real buildings.

Install the pinned netCDF4 dependency:

    python -m pip install -r requirements-glofas-acquisition.txt

Then execute:

    python scripts/climk_era5_synthetic_native_sample_v0.py --fetch --sites /tmp/synthetic-sites.json --storm-index 0

The source exact bytes are independently SHA-256 pinned, original scientific NetCDF axes are validated, and the nearest center is selected **only if the coordinate lies within that grid's half-cell cover**. Out-of-domain, masked/NaN or nonphysical wind gusts fail closed; missing is never silently zero. Two samples are recorded by CI as raw observed physical gust values, with explicit source event index, chosen native cell and units, never TIV, vulnerability or insured loss.

## NextGen integration gates

The NextGen C3S stager assumes a different wind measure (72-hour maximum of 3-second gusts), plus explicit vulnerability and site-to-cell mapping. It is scientifically incorrect to substitute this CLIMK footprint for that C3S source. Future work must establish storm identity/date matching, sampling/temporal semantics, source rights and attribution, exposure/vulnerability mappings, and independent validation before a NextGen loss stage.

The source sampler now also exports the exact provider `Storm_Names` and `Storm_Dates` labels at the same zero-based source-specific storm index. These are **annotations**, not a cross-model event match; the date label is intentionally never parsed as an exact UTC timestamp without its source time convention.
