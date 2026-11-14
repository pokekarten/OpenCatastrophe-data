<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NASA OPERA DSWx-S1 v1: strict classified-water/mask semantics preflight

Research-only, **not admitted to commercial CAT model input**. This companion
check advances [source intake #1130](https://github.com/pokekarten/OpenCatastrophe-data/issues/1130),
which already has a canonical source candidate and documented-only CMR
contract on main. No duplicate candidate IDs or access contracts are created.

## Original authority and version pin

- NASA JPL OPERA **DSWx-S1A/B Product Specification**, JPL D-108761,
  **version 1.0.0, Rev A, 2024-08-16**, Table 4-1 (PDF pp. 9–10):
  https://d2pn8kiwq2w21t.cloudfront.net/documents/OPERA_DSWx-S1_Product_Spec_v1.0.0_D-108761_RevA_2024-08-16_.pdf
- [JPL OPERA product page](https://www.jpl.nasa.gov/go/opera/products/dswx-product-suite/).
- [NASA OPERA documentation](https://nasa-opera.github.io/docs/products/)
  identifies OPERA_L3_DSWX-S1_V1 release on 2024-08-16.
- The **older 2023 specification version 0.2.1** uses materially different
  water/mask/fill codes. Never apply that code table to declared v1.0 scenes.
- Product is 30 m, MGRS-tiled and distributes separate WTR/BWTR/CONF/DIAG
  layers; declared product metadata alone is not independent source identity.

## Explicit v1.0 WTR/BWTR class contract

| WTR uint8 | Meaning | Corresponding BWTR | Research accounting |
|---|---|---|---|
| 0 | Valid *not water* observation, not proof of dry or flood-free ground | 0 | Valid non-water |
| 1 | Open water | 1 | Water |
| 3 | Inundated vegetation | 1 | Water observation, not depth |
| 250 | HAND mask | 250 | Unsupported / excluded |
| 251 | Layover/shadow mask | 251 | Unsupported / excluded |
| 255 | No-data fill | 255 | Unsupported / excluded |

Note that the v1.0 product specification also mentions alternative **CONF**
confidence codes and DIAG outputs. These are *different layers*, not values to
relabel as WTR/BWTR. Both 250 and 251 masks **must not** be interpreted as
dry pixels. Even WTR 0 can reflect land-cover mask processing; it is a class,
not hydraulic evidence about an event.

## Executable non-admission tool

`research_runners/nasa_opera_dswx_s1_v1_class_preflight.py` accepts only
**small, caller-supplied synthetic** flat integer WTR and BWTR arrays (maximum
4,096 pixels, side <= 128), exact product name/version and explicit
dimensions. It rejects older class values (including v0.2.1's 120 fill),
unknown classes, shape contradictions, float/bool-as-int and inconsistent
WTR/BWTR pairs. It emits **aggregate counts only**, never raw pixels,
coordinates, granule IDs, URLs or satellite imagery.

Run:

```bash
python -m unittest tests.test_nasa_opera_dswx_s1_v1_class_preflight -v
python scripts/check_all.py
```

No external downloads or credentials are used in the tool, and this code is
**not a GeoTIFF reader or a model-ready provider ingestion utility**. The
existing access contract remains `documented_only` and forbids a CMR probe
without an independently authorized fixed-scope T1 review.

## Scientific and rights gates still closed

A real original-granule follow-up would require exact NASA CMR collection and
granule identity, original file SHA, UTC sensing time, processing provenance,
full band/GeoTIFF CRS and pixel masks, independently licensed baseline water
evidence, fixed event/AOI matching, provider-rights/terms, and uncertainty
assessment. Only then could it challenge CEMS/DFO flood extent, not
automatically establish flood causation, depth, return period, a building
footprint, insured exposure, insurer losses or an ELT/YLT. Use of the
individual OPERA/Sentinel-derived asset in a commercial model remains
unreviewed. Never promote a synthetic test result to real-data acceptance.

Admission flags remain **false**: source original bytes, science, rights,
model input, historical loss, and insured portfolio are not validated.
