<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# First genuine, licence-labelled European wind footprints for the NRW 10k physical portfolio

**2026-11-05 / Stage 1: primary-source discovery + exact original CSV source preflight; no 10k source-wind overlay or CAT loss result yet.**

The current public physical NRW portfolio has 10,000 sample source-geometry positions spread across all 53 2022 Kreise, with solely **hypothetical** R+V-like insurance policies and valuation (source Draft PR #1373). Its 20 × 13 synthetic 0.25° grid is **NOT an actual meteorological source grid**.

An independently researched **alternative to CDS-authenticated C3S EWS** is the original [Extreme Wind Storms Catalogue (XWS)](https://www.europeanwindstorms.org/). XWS states that its original footprint data are available in CSV and NetCDF under **CC BY 4.0** for research *and commercial use* with the attribution: **(c) Copyright Met Office, University of Reading and University of Exeter. Licensed under Creative Commons CC BY 4.0 International.** The original [XWS source data description](https://www.europeanwindstorms.org/database/dataDesc/) explicitly identifies a *rotated-pole* ~0.22° grid and a separate WGS84 long/lat-by-grid-ID CSV. The storm footprint data measure **the maximum 3-second gust over a 72-hour storm window in m/s**, which is a hazard intensity only, not a damage or insured loss.

## Strict original provider URLs (XWS Daria, 25 January 1990)

Official [storm detail and data download links](https://www.europeanwindstorms.org/cgi-bin/storms/storms.cgi?storm1=Daria) provide the following **four separate original files**:

1. Grid ID to public lon/lat: https://www.europeanwindstorms.org/database/dataDesc/grid_locations.csv
2. Daria lower 95% recalibrated storm footprint: https://www.europeanwindstorms.org/repository/Daria/Daria_biasL95.csv
3. Daria recalibrated **mean** storm footprint: https://www.europeanwindstorms.org/repository/Daria/Daria_biasMean.csv
4. Daria upper 95% recalibrated storm footprint: https://www.europeanwindstorms.org/repository/Daria/Daria_biasU95.csv

The independent XWS page also offers the original raw/uncontaminated windstorm footprint in CSV/NetCDF; do **not** interpret recalibrated mean/lower/upper 95% fields as three independent storms or stochastic yearly model draws. Keep all these variants under the **same original Daria physical event identity**.

The first original source-admission implementation is `research_runners/xws_daria_1990_original_csv_preflight_v0.py`: it acquires up to 24 MB of original bytes per file by **explicit --live** only and rejects changed final URLs, HTTP status, truncated/over-budget files, invalid original grid IDs or WGS84 lat/lon, inconsistent row populations, wind-unit domain errors, incomplete sources, and pointwise lower/mean/upper inversions. It stores **only original file SHA-256, byte counts, source variant summary and CC BY 4.0 attribution**. Full original CSV bytes never enter the repository or GitHub artifacts.

The [independent small live original-source CI](../../.github/workflows/rva-nrw-xws-daria-source.yml) runs fake-source negative fixtures first, then reads the original four XWS CSVs and uploads only that metadata receipt. It is not an authorized download of Copernicus C3S and does not require a CDS account.

## Scientific model gating and next spatial work

- A successful source-only XWS CSV preflight establishes a **publicly accessible, original and hashed historical European wind hazard field**, not its geographic attachment to 2022 NRW physical footprints. A subsequent separate source-space crosswalk must convert the supplied original public WGS84 **grid point coordinates** to a bounded nearest-cell/interpolation rule with explicit distance and missing-data diagnostics. The ~0.22° rotated source grid **must never** be read as the existing fake 0.25° C3S grid or passed to the ERA5 staging module without a bespoke typed source adapter.
- The exact 10k asset public physical locations and their fictional TIV can be used to calculate **event-conditional exposure to wind gusts**, but **HU building function/GFK does NOT reveal wall/roof construction, calibrated fragility or insurance coverage**. The output must be *site gust in m/s only*, not GUL/IL/RI or an OEP/AEP. A hypothetical damage response would need a separate explicitly fictional parameterized test branch; a scientifically admitted Germany wind vulnerability needs independent licence and validation.
- XWS has a deliberately **extreme-storm-selected** catalogue (historically 50 storms), not a complete unbiased calendar of all European storms or a stochastic yearly loss table. Its physically selected event sample is **not** annual frequency or a 10k-world catastrophe distribution. Storm clustering, out-of-sample baseline, all zero storm-years, 72-hour overlap, and annual model set calibration must be established independently.
- XWS and C3S storm IDs / source eras / downscaling methods are unrelated without an original physical event crosswalk. A year or familiar storm name alone cannot justify reusing a vendor event ID or vulnerability calibration.
- If the primary-source preflight succeeds, implement a **source-specific WGS84 XWS lat/lon nearest-grid overlay** on the existing 10k public HU locations. Preserve nearest-point distances, exact XWS grid row IDs, full XWS input digests, and same physical event ID across the three uncertainty variants. Audit the 53-Kreis population and EUR 4,826,029,500 fictional total building value, but **never** present gust-weighted buildings as actual R+V insured risks.
- Before a native Oasis/NextGen Germany CAT model can run: independently source the **original wind vulnerability**, coverage/values/terms, event frequency/occurrence, and financial model crosswalk. Only then run pathwise wind damage, insured financial module, reinsurance and valid annual EP curves.

**No source-specific loss calculations, licence transfer, registered insurer-site data or production admission have occurred here.**

## Original-source Daria spatial application (first 10k hazard overlay code)

A second source-specific implementation now exists:
`research_runners/rva_nrw_xws_daria_10k_original_gust_overlay_v0.py` and
`tests/test_rva_nrw_xws_daria_10k_original_gust_overlay_v0.py`.
It streams four actual original XWS CSVs in ephemeral CI storage and obtains the
already-validated, source-geocoded 10k fictional NRW OED from the prior successful
[original NRW source run #42097472463](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463).

The spatial method **uses the original WGS84 grid-point lon/lat from XWS**, not
the invented 0.25° C3S-style grid. It searches nearby half-degree geographical
buckets, chooses the minimum exact spherical great-circle distance to the original
source point (tie-break by original integer grid ID), and **rejects** any point
with no original grid point within 45 km. The original source's ~0.22° rotated
grid is only a provenance descriptor; the algorithm does not assume its native
rotated-pole coordinates are already ordinary WGS84.

Outputs after a passing live original CI will be:
- 10,000 *fictional* NRW policy/sample asset IDs with matched **original Daria
  1990 3-second wind gusts (lower 95%, mean and upper 95% in m/s)** and exact
  original XWS grid ID and nearest-point distance;
- a 53-Kreis summary of fictional building value exposed to the **same**
  original Daria event, including source mean gust >=25 m/s;
- original four full-file XWS SHA-256s, prior full original HU22 archive SHA,
  XWS CC-BY-4.0 attribution and explicit false model/insurer/yearly-event claims.

No original XWS grid/footprint files are committed or uploaded to GitHub
artifacts. The public source-derived 10k *site-gust* table is shared under
its original CC BY 4.0 attribution. A single original **1990** historical storm
on **2022** public building locations with entirely fictional **2025** insurer
values is a retrospective *counterfactual* hazard exposure; it cannot be
interpreted as historical insured claims, today's underwriting exposure,
a calibrated conditional damage model, a sample of independent years or
a premium / solvency-risk estimate.

**CI admission:** The exact live original-source and 10k join workflows must
show a completed SUCCESS before any site-gust artifacts or numerical results
are called verified. A failed source row schema, drifted original URL,
missing county, unusually distant grid mapping, source uncertainty inversion
or source artifact mismatch must remain NO-GO.
