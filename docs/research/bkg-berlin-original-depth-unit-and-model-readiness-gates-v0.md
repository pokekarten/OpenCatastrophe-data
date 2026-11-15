<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# BKG Berlin original source: scientific unit and insurance CAT admission gates

**Research quality status: GEOMETRIC SCREENING ONLY.** The current
Berlin BKG building–raster overlay **must not** produce numeric water
depths, an insured exposure score, losses, AEP/OEP or return-period
loss estimates. This applies even to valid *positive* TIFF integers.

## Checked official source documents (version-aware)

- [BKG HWK_SRG documentation, 25 September 2026](https://sgx.geodatenzentrum.de/web_public/gdz/dokumentation/deu/hwk_srg.pdf):
  overall product reference year **2024**, 1-m horizontal raster grid,
  10-by-10-km TIFF tiles in ETRS89 / UTM32 and two *simulated*
  scenarios (KOSTRA extraordinary 100-year **rainfall** scenario and
  extreme 100-mm-per-hour scenario, with regional exceptions). This
  document does **not** specify a reviewed conversion multiplier,
  physical unit for the *stored signed Int16 values* in this exact
  original BKG TIFF tile, or an entrance water-ingress model.
- [BKG FAQ, 25 September 2026](https://sgx.geodatenzentrum.de/web_public/gdz/dokumentation/deu/hwk_srg_faq.pdf):
  explains the rainfall assumptions, model limitations and why
  detailed municipal maps should be preferred for property-specific
  assessment when available. The FAQ says Germany-wide completion
  was **planned for end-2027** in that revision; don't silently carry
  over an older web-summary forecast to a newer vintage.
- [BKG official WMS & download product page](https://gdz.bkg.bund.de/index.php/default/wms-hinweiskarte-starkregengefahren-wms-starkregen.html):
  DL-DE/BY-2.0 with specific public attribution and third-party
  sources; optional `.msk` files are described for **velocity**
  tiles where displayed depth is at least 10 cm. That does not
  establish either the numeric scale or NoData semantics for the
  separate *depth* TIFF. A color legend or WMS style cannot by itself
  calibrate the direct GeoTIFF's integer values.
- [BKG methodological overview](https://www.bkg.bund.de/DE/Themen/Umwelt-und-Klimawandel/Starkregen/starkregen_cont.html):
  not a metre-exact location engineering map. Sewer networks and
  infiltration are omitted from the nationwide model. Local
  calibration, building entrances and terrain may diverge.

These source links point to publisher-controlled live material and can
change. This review distinguishes their *stated publication date* from
the [immutable original BKG tile SHA](bkg-berlin-kostra-original-window-receipt-20261101.toml).

## Original 2026-11-01 research evidence

An independently checked, one-tile 47,280,200-byte BKG original TIFF
`7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f`
and a separate Berlin ALKIS WFS response
`c4342109c0c13b31996d7cb9a5a16db56af3e536dc4910938a9fc72bab049bba`
yielded original building-polygon × source-raster sample aggregates on
[main Actions run 41350285830](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41350285830).
Only five current first-listed pilot WFS polygons were checked.
[Original area receipt](berlin-bld4-bkg-original-exterior-ring-receipt-20261101.toml)
has disjoint 0–1 m / 1–3 m / 3–5 m exterior ring measurements.

The first-five building footprint interiors have **97.48% NoData**
by clipped projected area; exterior valid-numeric coverage is
**41.31%, 50.81%, 56.50%** by ring. The positive raw-code fraction
is a *spatial area fraction*, **not** the probability of flooding
and **not** a water depth. 2026 ALKIS footprints are not proven
contemporaneous with the BKG 2024 modelling inputs.

## Fail-closed model-readiness gate

`research_runners/bkg_berlin_source_readiness_gate_v0.py`
accepts only the pinned original receipt schema, exact source digests,
workflow run/commit, source CRS, source-size and all 0–5 m band
totals (including explicit NoData). It produces only an
**aggregate spatial-coverage diagnostic**, never a building record.

It explicitly disallows:

- raw signed Int16 integers (including the observed range 0–108)
  being converted to centimetres/metres without independent exact
  product calibration evidence;
- NoData being reclassified as numeric zero, dry land or no flood;
- positive raster source-area fractions being interpreted as an
  insured flood probability or any annual occurrence rate;
- interpolated building door/threshold/underground risk based only
  on general BKG model geometry; and
- insurer TIV, gross/ceded/net losses or CAT-XL capacity calculations
  using this research pilot as an admitted hazard.

The test suite rejects source swaps, mutable ALKIS response hashes,
fabricated area totals, changed NoData or positive/zero fractions,
invented unit approval and any future unauthorized CAT admission.

Reproduce offline without downloading provider bytes:

```bash
python -m unittest tests.test_bkg_berlin_source_readiness_gate_v0 -v
python -m research_runners.bkg_berlin_source_readiness_gate_v0
```

## Concrete next scientific steps

1. **Raw Int16 calibration (hard blocker):** obtain an exact
   publisher-defined numeric scale/offset and physical unit
   specification tied to the *downloaded direct original TIFF*,
   its scenario, source revision and sample values. Record the
   signed provider document/version and test using unmasked,
   nonzero source pixels and NoData sentinels. Neither a map legend
   nor a presumed cm conversion substitutes for this evidence.
2. **Geospatial validation:** compare published local municipal
   Starkregen products and source-vintage ALKIS footprints where
   licensed. Reconcile differing hydrology scenarios before
   computing a combined exposure proxy.
3. **Building entry risk:** add measured entrance and basement
   thresholds, uncertainty intervals, surveyed asset use,
   and defensible vulnerability curves. A proximity ring is
   not a validated path for water into a property.
4. **Insurance model gate:** source rights, independently
   validated physical depth, separate exposure sums insured,
   peril-specific event probabilities, model QA and financial
   contract treatment must all be signed off before NextGen
   or Oasis loss simulation ingests the data.

**Not a blocker to exploratory spatial source coverage research.
A hard blocker to physical flood depth, insurer portfolio loss, and
CAT model input.** No DB writes, insurance policy links or external
original source bytes are made by this PR.
