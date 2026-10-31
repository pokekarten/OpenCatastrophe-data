<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CLIMK–WINDS v2 ERA5 footprint preflight (research only)

Publisher: https://zenodo.org/records/15305753, CLIMK–WINDS version 2, 2025-04-29, CC BY 4.0 according to provider metadata.

First bounded source: `ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc`. Publisher size 6,792,278 bytes, MD5 `887ae3218793c599862f115876c145f9`. Real provider-byte test passed on 2026-10-31, GitHub Actions run 41227457898. SHA-256: `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`. Confirmed native dimensions: `storm_number=50`, `latitude=181`, `longitude=269`. Mandatory variables include `Storm_Dates`, `Storm_Names`, `LI3D_CoreEurope`, `LI_gridpoint`, `relative_maxwindgusts` (dimensionless climatological ratio), and `absolute_maxwindgusts` (`m s**-1`). The LI3D indices are **dimensionless risk indices**, not gross or insured EUR losses. These are now explicit code gates.\n\nThe other three provider-native NetCDF models are larger and intentionally **not** read as if they share identical storm identities.

Run online after installing `requirements-glofas-acquisition.txt`:

    python scripts/inspect_climk_winds_era5_v0.py --fetch

Strict byte-size and publisher-MD5 checks precede in-memory NetCDF inspection. The script reports dimensions, variable names, shapes, units and source SHA-256; no raw grid arrays, event values, insured losses or source files are written. The exact SHA-256 is now pinned and `--require-sha256` must be used on subsequent live tests. CI includes synthetic tests and an exact-source download.

Research caveats: 50 extreme storms are selected per model, not all 50 *shared* events. ERA5 may be upstream of C3S products, hence it is not automatically an independent benchmark. Preserve native grid and gust variables, event date, origin, ID, temporal aggregation and baseline definitions. Before using NetCDF in a Cat loss engine, map occurrences across four source models and demonstrate separate scientific validation and reuse rights.

The provider record already contains the science paper DOI https://doi.org/10.5194/essd-17-4431-2025.
