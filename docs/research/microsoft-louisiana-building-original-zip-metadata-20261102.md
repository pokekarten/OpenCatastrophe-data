<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Microsoft Louisiana building footprints: original archive research receipt

**Status:** bounded original-host metadata access under public PR; no source-row
or geolocation/insurance admission. This document must not be interpreted as
permission to consume or redistribute original building polygons.

## Why this is relevant to world-wide CAT exposure

The verified [Census 2026 all-64 Louisiana parish geometry source](https://github.com/pokekarten/OpenCatastrophe-data/pull/1100)
supplies official geographic containment polygons, *not buildings*. The
independent **Microsoft USBuildingFootprints** research candidate can supply
building roofprints, but the vintage of source imagery can be much older
than the 2026 administrative boundaries. Neither supplies real insurance
TIV, legal policies, replacement cost, elevation, deductible, or a
scientifically validated vulnerability curve.

Microsoft original primary source:
- [Microsoft USBuildingFootprints README](https://github.com/microsoft/USBuildingFootprints):
  advertises **2,173,567** machine-generated Louisiana footprints, **600.69
  MiB uncompressed**, ODbL license. This number is **publisher-reported**,
  **not independently counted from original GeoJSON** here.
- [Original Microsoft Azure static archive](https://minedbuildings.z5.web.core.windows.net/legacy/usbuildings-v2/Louisiana.geojson.zip):
  `Louisiana.geojson.zip`. This is an *older legacy USBuildings-v2
  release*, not an assertion of 2026 physical building completeness.
  Microsoft warns that imagery vintage varies, with newer extraction
  (2019–2020) in selected areas and older imagery in the remaining area.

This is distinct from the independently researched
[Overture building release 2026-10-21.0](https://docs.overturemaps.org/guides/buildings/).
The latter conflates Microsoft footprints, OSM and other providers; it
is **not** independent building ground truth just because two catalogue
products happen to overlap. Both Overture Buildings and Microsoft
USBuildingFootprints use ODbL, subject to separate licence/attribution
evaluation for the specific downstream exposure database and outputs.

## New bounded original-source metadata receipt

`research_runners/microsoft_louisiana_original_zip_receipt_v0.py` uses
**one hardcoded original HTTPS source**, without credentials or redirect
following. It performs one bounded HTTP HEAD, one tail Range (max
66,000 bytes) and one exact central-directory Range (max 4,096 bytes).
All responses must agree on object size, Content-Range, Content-Length
and original ETag, and the ZIP32 end/central-directory headers and
original single GeoJSON member identity are checked.

**Never acquire the full multi-hundred-MB Louisiana ZIP in this job.**
No polygons, source building IDs, addresses, coordinates or per-site
private insurance data are requested or persisted. No mutation of Neon,
production source registry or model admission. Run:

```sh
python -m unittest tests.test_microsoft_louisiana_original_zip_receipt_v0 -v
python -m research_runners.microsoft_louisiana_original_zip_receipt_v0 --live
```

[Public dedicated workflow](https://github.com/pokekarten/OpenCatastrophe-data/actions/workflows/microsoft-louisiana-building-original-zip-metadata.yml)
has separate synthetic falsifier and explicit read-only official-host steps.
A passing original metadata receipt only verifies HTTP/ZIP metadata and
observed compressed/uncompressed size. ETag is **not** accepted as original
full-archive SHA-256. If the host rejects strict Range semantics, the
probe fails closed rather than silently downloading a full ZIP.

## Next gates before a real Louisiana building-to-parish dataset

1. **Exact bytes and reuse**: independently version/pin the full original
   archive or a publisher-provided immutable fingerprint, verify ODbL
   attribution/share-alike duties and derivative database classification.
   A HEAD response is not a license or original content checksum.
2. **Age and footprint correctness**: record source imagery ages where
   known, topology validity, missing/duplicate/overlapping footprints,
   height/floor/count semantics, and per-footprint geometry version.
3. **Official parish join**: reconcile building source CRS to original
   Census NAD83 coordinates and use point-in-polygon or area fraction
   with an explicit boundary/cross-border policy. Count unmatched and
   ambiguous buildings. A 2026 parish code does not validate historic
   building vintage.
4. **Insurance model input**: only separately observed real asset value,
   occupancy, construction, TIV, insurance coverage, hazard intensity and
   peril-specific vulnerability can qualify for a scientifically and
   legally reviewed CAT model. The [synthetic OpenCat
   rollup](https://github.com/pokekarten/OpenCatastrophe/pull/16) is not
   automatically an insured loss engine.

## Executed official Microsoft archive proof — 2 November 2026

[Exact public GitHub run 41495629417](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41495629417) ran the reviewed fixed-source tool against Microsoft's original Azure endpoint. **9/9 offline falsifier tests passed** and the original HEAD + tail/central-byte ranges succeeded:

- **Original ZIP byte length:** `83,974,949` bytes; original HTTP ETag `"0x8DCFF4D6A6BD59D"` (source server metadata, **not** cryptographic SHA-256).
- **One original member:** `Louisiana.geojson`, ZIP central directory **87 bytes**, compressed payload **83,974,765** bytes, uncompressed member **629,872,164** bytes.
- The first public live run failed because the HEAD `Content-Length` was wrongly checked against the **zero HEAD response-body bytes**. That source-gate bug was corrected in source and the exact second workflow then passed. The correction did not change source rights or infer original GeoJSON features.
- **Not established:** the README's advertised **2,173,567** actual buildings, completeness/validity, imagery year, geolocations or insurer exposure; **no original content records or full archive SHA-256** were read.

## Bounded first-original-building prefix (separate source row screen)

The additive `research_runners/microsoft_louisiana_original_building_sample_v0.py` performs this strictly restricted research step on the same source: it checks the previous exact HTTP metadata receipt, requests **only** compressed ZIP bytes 0–65,535, validates local member header and ZIP identity, inflates at most **1 MiB** of original text, and screens at most **20 fully decoded initial source GeoJSON features** with pinned Shapely for polygon validity and coarse Louisiana geographic bounds. The original *first* records are neither random nor a representative statewide sample. No IDs, source coordinates, footprint polygons, private insurance input or source payload are logged or persisted, and any unsupported provider format fails closed. The full source content/SHA-256, historical imagery vintage, rights and parish crosswalk remain separate gates.

**Executed exact original-source result:** [public GitHub Actions run 41496043928](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41496043928) succeeded with **18/18** synthetic tests covering the archive headers, remote Range integrity, source format, malformed coordinates and no-model-admission. Its separately executed official `--live` prefix step read **65,536 source compressed bytes**, yielding **478,429 first-prefix decoded UTF-8 bytes**, and inspected **20 fully decoded source-original Polygon footprints**. All 20 were topologically valid and inside a **coarse Louisiana sanity envelope**; none was a MultiPolygon or an insured or independently measured property location. The first 20 original records are an **ordered, nonrandom subset** and cannot estimate 2.17M source-wide validity/completeness, census-parish residence, or insurer portfolios. The verified source metadata remained `83,974,949` ZIP bytes and ETag `"0x8DCFF4D6A6BD59D"` (not a whole-object SHA-256).

**Critical next dependency:** the verified original Census 2026 Louisiana parish polygons are still in [separate draft PR #1100](https://github.com/pokekarten/OpenCatastrophe-data/pull/1100). Do not silently assume this building-data research branch has that geometry loaded or join source files without an explicit source hash, vintage, coordinate CRS, boundary ambiguity/coverage and rights gate. The next complete field-level pilot should spatially join real candidate building polygons (not artificial representative points) against independently verified `STATEFP=22` parish geometries and report unmatched/ambiguous counts before any real underwriting use.
