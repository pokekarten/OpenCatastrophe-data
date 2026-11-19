<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# PLATEAU single-file CityGML CRS / building-height structural preflight (2026-11-01)

## Scientific basis and scope

Official MLIT PLATEAU guidance gives a CityGML 2.0 `core:CityModel` sample with a root `gml:Envelope`, `srsName="http://www.opengis.net/def/crs/EPSG/0/6697"` and `srsDimension="3"`, with geographic coordinates in **latitude, longitude, height** order. This compound reference combines JGD2011 horizontal coordinates and a Tokyo Bay mean sea level vertical reference. EPSG:6668 is geographic 2D only and should **not** be silently substituted when a height-dependent CAT transformation is contemplated.

The building `bldg:measuredHeight` is an optional `gml:LengthType` attribute in metres (`uom="m"`). The documentation warns that its value depends on the measurement method and filtering and need not represent the exact highest roof point. A reported building height is therefore not a verified insured height or vulnerability input.

Primary provider references:
- [MLIT: CityGML CityModel/envelope and feature structure](https://www.mlit.go.jp/plateau/learning/tpc03-2/)
- [MLIT: geographic reference systems and the 6697/6668 difference](https://www.mlit.go.jp/plateau/learning/tpc03-4/)
- [MLIT: bldg:_AbstractBuilding measuredHeight cardinality and metres](https://www.mlit.go.jp/plateaudocument01-01/Contents/%E5%AE%9A%E7%BE%A9%E6%96%87%E6%9B%B8/bldg--_AbstractBuilding.html)
- [MLIT: height measurement and DSM noise caveats](https://www.mlit.go.jp/plateaudocument02/tocC/tocC_03/tocC_03_02/tocC_03_02_03/)

## How to run on a separately lawfully supplied single GML file

```bash
python research_runners/plateau_citygml_sample_structure_v0.py \
  --input /secure/local/independently-provided-small-building-tile.gml
```

This tool reads a **single already-existing regular file**, at most **4 MiB**, via the existing symlink/FIFO-safe local file reader. It does **not** fetch or unzip data, use an API, validate rights or open any remote references. It rejects DTD/ENTITY declarations, non-CityGML 2.0 root, malformed XML, more than 50,000 XML elements or 64 levels of nesting, a missing/multiple root envelope, missing/contradictory EPSG:6697 or 3D declarations, non-finite or inverted envelope corners, duplicate/malformed `gml:id` values, missing building IDs, and invalid explicit `bldg:measuredHeight` values/units. No measured height is required: missingness is counted rather than imputed. BuildingParts are counted **separately**; they are not double-counted as whole buildings. LOD0–LOD3 *property presence* is counted but **not** interpreted as actual valid geometry.

A successful receipt provides only file SHA-256, file byte count, total XML-element, building, BuildingPart, height-presence and LOD-property counts, plus explicit **false** status for topology, independent vertical-datum verification, measured-height method, GML XML-schema conformance, source provenance, licence/privacy clearance and CAT model admissibility. It returns **no building IDs, coordinates, raw heights, filenames, source ZIPs, parcels, personal data or insured values**.

### Deliberate scientific limits

The root envelope's numeric order can be checked, but the municipality and year **cannot be inferred or authenticated from an envelope**, or from a GML name alone. The parser does **not** verify spatial accuracy, mesh-extent completeness, actual `posList` polygons, topology, ground level, floor area, LoD geometry validity, per-building coordinate reference, exposure, seismic vulnerability or insurers. The optional height presence does not imply measured source method or suitability. Additional XML Schema, source ZIP CRC and exact-record rights validation remain separate stages.

This is a sample-sized, bounded structural smoke test, not a safe full-archive parser or a replacement for scientific CityGML tooling. All tests are **synthetic**. No provider original was downloaded or put in Git, and no new source is admitted.

## Next causal evidence gate

After exact municipal provider rights/API-service review: acquire one immutable licensed CityGML ZIP outside Git, retain UTC receipt + original byte SHA-256, verify ZIP CRC and member byte identity through a separate bounded extraction process, run this structural preflight on one authorised GML sample, then validate actual coordinates and topology and test an independent geometry holdout before joining hazards or approving any model input.

## LOD0 inline polygon ring screening (research-only extension)

The offline parser additionally counts *screened* inline `gml:Polygon/gml:exterior/gml:LinearRing/gml:posList` rings separately for `bldg:lod0FootPrint` (ground footprint) and `bldg:lod0RoofEdge` (roof-edge outline). The two are **not interchangeable** for exposure footprint area. This screening requires EPSG:6697 3D latitude/longitude/height triples, a closed ring, at least three unique horizontal vertices, finite vertices within the declared root envelope, nonzero local horizontal signed area and no non-adjacent crossing in a conservative planar screening. Ring length and total inline polygon count are bounded; there is no polygon area output, reprojection, geometry repair or insured building join. **Screening is not GIS topology validation** and does not resolve source coverage.

Legitimate alternative encodings, polygon holes, XLink-referenced shapes or an empty declared LOD0 geometry are reported as *unresolved*, never silently promoted to a valid polygon. Only the explicitly recognized inline ring subset is screened. The extra counts are structural diagnostics, not admitted building geographies. Primary MLIT explanation of footprint versus roof edge and `gml:MultiSurface/gml:Polygon/gml:posList`: https://www.mlit.go.jp/plateau/learning/tpc03-3/ .

**Official 3D dimension variant:** MLIT's formal reference https://www.mlit.go.jp/plateaudocument02/tocB/tocB_04/tocB_04_1/ explicitly demonstrates `srsDimension="3"` on each `gml:lowerCorner` and `gml:upperCorner` while the envelope has the EPSG:6697 `srsName`. The preflight now accepts this, or a dimension-3 declaration on the envelope. A sole explicit corner dimension is insufficient. Neither variant independently proves a height measurement method or the associated municipality.
