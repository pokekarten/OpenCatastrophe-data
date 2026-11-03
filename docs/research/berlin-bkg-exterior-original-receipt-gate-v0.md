<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin BLD4 – original building exterior ring research receipt gate

**Status: research-only. No metered flood depth, model input, insured loss,
asset replacement value or insurer portfolio.**

## Why this additional gate is needed

The pinned first real building-footprint/raster proof
[original run 41349226673](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41349226673)
found 5 original ALKIS-derived building polygons inside the fixed pilot,
covering 683.311267 m² after reprojecting to the BKG raster CRS. Of that,
666.124849 m² (about 97.5%) was **NoData** and only 2.752013 m²
intersected **positive original raw integer codes**. This does not
establish building inundation or an insured loss.

The already reviewed
`research_runners/berlin_bld4_bkg_exterior_ring_raw_support_v0.py`
defines unioned, disjoint, source-cell fractional exterior bands around
the five original building footprints: 0–1 m, 1–3 m and 3–5 m,
all clipped to the *exact* original 200 × 200 m pilot geometry.
It computes areas for original positive codes, valid zero codes,
NoData/mask and out-of-window separately. The outer bands do **not**
represent building-level depths or building entrance elevations.

## This PR adds an independent fail-closed receipt guard

- `research_runners/validate_berlin_bkg_exterior_original_receipt_v0.py`
  independently checks the executed workflow's aggregate report:
  fixed full original BKG TIFF SHA-256 and byte count, WFS response
  digest identity, exact 47,089-cell pilot / five building sample,
  footprint and three ring area conservation, distinct NoData and
  valid zero categories, numeric support fractions and **zero**
  model/insurer admission.
- Six-plus adversarial synthetic tests cover wrong source SHA, mutated
  mask/area totals, ring reorder, numeric overflow/nonfinite data,
  false physical-depth approval, duplicate JSON keys and the bounded
  input-size guard.
- On a reviewed workflow change merged to `main`, the dedicated source
  workflow performs **one bounded original Berlin ALKIS WFS request**,
  **one original BKG direct TIFF download** and the existing two pinned
  auxiliary boundary sources. Everything is temporary and deleted.
  Only checked **aggregate ring areas**, no feature identifiers,
  coordinates, individual pixels, original geometry or insurer data,
  are emitted. No production DB writes.

The source TIFF is BKG KOSTRA 2024/2025 design-storm scenario,
**not** the Berlin GDI 2022-named different hazard ZIPs or a recorded
insurance loss. The BKG full original TIFF SHA-256 is
`7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f`
(47,280,200 B, EPSG:25832, 1 m horizontal cells,
Int16 NoData = -9999). This full hash is a locally calculated source
identity receipt, **not** a provider-signed checksum.

### Distinct Berlin detailed model (not interchangeable)

The official Berlin Senate's
[02.24.2 detailed Starkregengefahrenkarte](https://www.berlin.de/umweltatlas/wasser/starkregen/fortlaufend-aktualisiert/kartenbeschreibung/)
uses locally covered, coupled **1D sewer + 2D surface** scenarios,
whereas the
[BKG HWK_SRG](https://www.bkg.bund.de/DE/Themen/Umwelt-und-Klimawandel/Starkregen/starkregen_cont.html)
is a nationwide **surface-oriented indicative** model. Even their
KOSTRA durations / storm assumptions differ; coverage of the fixed
BLD4 pilot by Berlin 02.24.2 has not been confirmed.
The public [Berlin 02.24.2 WFS catalogue](https://daten.berlin.de/datensaetze/starkregengefahrenkarte-wfs-1aa4f1ef)
is metadata / spatial coverage research, **not** automatic source
permission or a ground-truth comparison.

The BKG [official FAQ](https://sgx.geodatenzentrum.de/web_public/gdz/dokumentation/deu/hwk_srg_faq.pdf)
states that urban sewer coupling is omitted to maintain nationwide
comparability. The BKG [product overview](https://www.bkg.bund.de/DE/Themen/Umwelt-und-Klimawandel/Starkregen/starkregen_cont.html)
explicitly cautions against a metre-exact site safety evaluation.
Neither PDF or overview independently specifies the physical scale of
our original signed Int16 TIFF code. **A horizontal 1-m raster cell
is not a 1-m flood-depth unit.**

## Scientific gate still open

Original exterior-band data are **pending a reviewed main run**. A
passing synthetic PR workflow only proves the receipt checker, not
observed perimeter support. A main run can fail if the mutable Berlin
WFS or original BKG TIFF changes; do not bypass hash or provenance
checks to obtain a green status.

Before loss modelling, independently verify authoritative depth
scaling and original NoData semantics, actual compatible building
vintages, source-specific CAT rights, entry elevations and vulnerability
functions. The five WFS buildings remain **a pilot sample**, not
a representative insured-building population.
