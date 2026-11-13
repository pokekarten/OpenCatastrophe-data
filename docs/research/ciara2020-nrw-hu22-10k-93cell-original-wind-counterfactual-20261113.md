<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ciara 2020 original gust × HU22 public NRW 2022 10k: 93-cell counterfactual

**13 November 2026: Original-source-derived public building candidates plus fictional insurance, not real insured losses.**

## Source original authenticity and reproduction

The original-source-derived 10k NRW research artifact was actually inspected in the research workspace. Its exact full ZIP SHA-256 is **5b0055ce71314f7d7baf4f67008cd4abba3df28a4bce0690bbe9521a3cc35757**; the upstream original 2022 HU full-source ZIP SHA is **10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da**. All three original-derived account/location/physical-evidence CSVs have verified byte SHA pins in the accepted source gate from PR #1494. The 10k source archive reports 53 NRW counties and **EUR 4,826,029,500 fictional building TIV**, NOT observed R+V exposure.

This PR adds a **1,889-byte 93-cell aggregate CSV**, SHA-256 **fe012f9e0a42b67ad7b73b49bb7ca24edd1be7c785db2321b3997ebc466315e7**. Its original site-count-only 93-cell signature is **de10099a9b79febb1a254bc765dc477a47589cb1f49ba75415bfe6b9723c2ebd**. Each row has only the 0.25-degree raster quarter-index, number of 2022 public building candidates and aggregate fictional TIV. **No site IDs, insurer policies, original site coordinates or full polygons are committed.**

The original bounded 10k OED ZIP is still a GitHub Actions artifact from [run 42097472463](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463), artifact 13447603258, with observed expiration **19 November 2026 19:52 UTC**. The aggregated CSV is persistently versioned in Git; nevertheless, **the upstream original archived 10k ZIP must be independently preserved or re-created from the original original-source reproducible runner before that ephemeral artifact expires** to make future full source regeneration possible.

## Independent actual historical 2020 weather

[PR #1556](https://github.com/pokekarten/OpenCatastrophe-data/pull/1556) produced original public Google Research ARCO ERA5 **10m gust 10fg**, 96 consecutive 2020-02-08 00Z to 2020-02-11 23Z hours over the **10 × 16 original 0.25-degree NRW rectangle**, **15,360 actually read historical reanalysis wind values**.

The accepted 96h float32 LE decoded 160-node original-source SHA-256 is **5fb7c41963a94f88ee3651b51bfa84cc2f4bf379e1ee6f4eb4a4fb597d37f932**, with independent 2020-02-09 12Z 51N/7E original source Gust SHA **12d34d73cece12a90220ddbbb5b092e388a6b1e0d9b0c9dcf5004a01a7c3119c**. These digests are of decoded values, not original compressed GCS chunk bytes or original ECMWF GRIBs.

## Join output and science boundaries

Every 2022 public location is rounded to its nearest ERA5 0.25-degree grid centre with Decimal, refusing exact tie midpoints; all 93 cell candidate counts and fictional TIV are conserved and checked against the original full 10k ZIP. The live joined result reports **2020 peak hourly wind-gust exposure on public 2022 physical candidates**, weighted by building-candidate counts or the fictional TIV. Counts/TIV of public candidates at gust >=25/30/35/40 m/s are **wind exposure**, NOT wind *damage* or insured loss. No individual 10k site records are published.

The 2020 weather is meteorological **ERA5 reanalysis**, not a DWD station gust; the buildings were sourced from public **2022 physical building polygons**, and their 2025-like fictional policies are NOT real R+V insured site records, nor evidence those buildings/coverage existed in 2020.

Offline source aggregate check:

    python research_runners/ciara2020_nrw_hu22_10k_google_arco_wind_counterfactual_v0.py --dry-run

Independent rebuild and comparison of all 93 count/TIV rows from exact original-derived 10k ZIP, which rechecks whole ZIP SHA, 3 CSV SHA, source authenticity, 53 counties and residential-use candidates:

    python research_runners/ciara2020_nrw_hu22_10k_google_arco_wind_counterfactual_v0.py --verify-source-zip /path/to/nrw_hu22_original_derived_10k.zip

Live authentic 96-hour Google ERA5 source and counterfactual overlay:

    python -m pip install -r requirements-google-arco-2020-original-smoke.txt
    python research_runners/ciara2020_nrw_hu22_10k_google_arco_wind_counterfactual_v0.py --live-google

A temporary branch-scoped GitHub CI job checks the full original Google 96h SHA plus the 93 source-cell aggregate SHA and runs 9 adversarial offline source/wind tests. Do not merge until both source job and all normal Python 3.11–3.14, Required, REUSE and dependency checks succeed.

## Actual first original 2020 wind × 2022 public 10k source-grid result

The first independent original live wind join **succeeded** in
[GitHub run 43489088388](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43489088388),
source job **132105176207**. All 10,000 public 2022 building
candidates and EUR 4,826,029,500 **fictional** original-derived TIV
were conserved across the original 93 occupied grid cells.

The candidate-weighted **2020 peak hourly gust** was
**31.673449949645995 m/s**, and the fictional-TIV-weighted peak
was **31.67299538469392 m/s**. The 93 occupied 0.25-degree
source-cell maxima range **30.28105926513672 to
34.43796157836914 m/s**. At 25/30m/s thresholds, **10,000**
2022 public candidates and EUR 4.826bn **fictional** TIV were
in cells where historical 2020 reanalysis gust peaks exceeded
those thresholds; at 35/40m/s none were. Although only
157 of the original 160 Google ERA5 grid cells had peaks >=30m/s,
all 93 *building-candidate occupied* grid cells met 30m/s.
**This is a weather counterfactual, not a damage estimate.**

The immutable actual first-live outcome is frozen at
research/observations/ciara2020_nrw_hu22_10k_public_2022_2020_gust_counterfactual_receipt_v0.toml.
The live runner now rejects future wind overlays differing from
that logged result in source SHA, population, weighted peaks or
threshold statistics. No caller can pass a source SHA string
plus substituted peak values without triggering a no-go.

**Rights:** retain original NRW HU public building source/attribution conditions; public Google ARCO reanalysis data is governed by **Copernicus Licence** with acknowledgement to **Copernicus Climate Change Service (C3S) and Google Research**. The Google research code licence is not a reinsurance data licence.

**Permanent scientific NO-GO:** real R+V 2020 insured buildings or claims, independently matched actual loss and insured exposure denominator, roof/material vulnerabilities, German damage function, actual GUL/IL/RI, OEP/AEP, annual event frequencies and SCR; separate historical 1990 Daria wind and 2020 Ciara wind are not interchangeable. The German wind-loss calibration source-rights gate remains active.
