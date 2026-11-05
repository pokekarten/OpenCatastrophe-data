<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Executed Loing-Aval original WFS GML geometry check: 2023 hazard class, not a 2016 observed flood extent

**Observed 2026-11-05. Source-specific read-only proof.** We fetched **one real feature** from the official DDT45 Geo-IDE WFS, parsed provider GML geometry with a bounded in-memory spatial test, and checked **two first-party 2016 flood-mark positions**. We have **not** acquired a separate official 2016 ZIP/ZICH event product, verified a reference flood-hazard holdout, or inferred asset water depths.

## Reproducible first-party publication and service endpoint

- Official DDT45 national catalogue dataset: [*Zone d'aléa du PPRi de la Vallée du Loing Aval*](https://www.data.gouv.fr/datasets/zone-dalea-du-ppri-de-la-vallee-du-loing-aval-departement-du-loiret); published dataset id **\`67377bf18609c51859c40b3b\`**, dataset-level licence **\`lov2\` (Licence Ouverte 2.0)**.
- Official Geo-IDE linked WFS service route: [published GetCapabilities metadata](https://ogc.geo-ide.developpement-durable.gouv.fr/wxs?map=/opt/data/stack/mapfiles/1.4/org_38032/a204d342-e3b5-45bc-8103-d248ddb7bd78.internet.map&SERVICE=WFS&REQUEST=GetCapabilities).
- **Executed original WFS request**: [WFS 2.0.0 GetFeature, one item only](https://ogc.geo-ide.developpement-durable.gouv.fr/wxs?map=/opt/data/stack/mapfiles/1.4/org_38032/a204d342-e3b5-45bc-8103-d248ddb7bd78.internet.map&SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=ms:N_ZONE_ALEA_PPRN_20220018_S_045&COUNT=1).

A public read-only intermediary returned **HTTP 200**, response content type **\`text/xml; subtype="gml/3.2.1"\`**, WFS element \`numberReturned="1"\`, and \`timeStamp="2026-11-05T08:42:06"\` (server timestamp, not a historic event date). The returned XML text length was **5,158,955 characters**. This was **one** feature with many polygon parts, **not** 5.16 million geospatial assets, a full WFS layer or an authenticated full publisher archive. The live source was inspected in memory; a byte-for-byte original download from the user's own execution environment and its SHA-256 **remain separate acquisition gates**, not attained by the browser intermediary. A direct container HTTPS request was blocked by DNS, independent of the provider's working WFS response.

## Exact provider feature semantics, inspected from returned GML (not a guessed GIS schema)

| Returned attribute / geometry | Direct observation |
| --- | --- |
| Feature typename | \`ms:N_ZONE_ALEA_PPRN_20220018_S_045\` |
| \`ID_ZONE\` | \`PPR_Loing-Av_F\` |
| \`NIVALEA\`, \`NIVALEA_ST\` | \`F\`, \`04\` (source codes, not interpreted as a measured water depth) |
| \`DESCRIPT\` | \`Crue a debordement lent de cours d eau\` |
| \`DATECARTE\` | \`2023-janvier\` |
| \`SRCE_ANNEE\`, \`SRCE_GEOM\`, \`PRECISION\` | **empty** in this feature – no source event-vintage or per-feature accuracy certificate |
| \`TITRECARTE\` | \`Cartographie de l alea de reference\` |
| Spatial CRS | \`urn:ogc:def:crs:EPSG::2154\` (RGF93 Lambert-93, projected x/y metres) |
| Returned GML geometries in this **single WFS feature** | **335 \`gml:Polygon\` surfaces**, with **335 exteriors** and **455 interior rings** |
| Provider WFS caution | XML contains **\`WARNING: No featureid defined ... Output will not validate.\`** – this response is XML-parsable but **OGC WFS schema conformance is not certified** |
| \`numberMatched\` | \`unknown\`; \`numberReturned\` is only \`1\`, so **no inference about full source feature count** |

The original geometries were not committed (multimegabyte unreviewed GML), and no original provider SHA-256 has been pinned. It would be scientifically invalid to label this one regulatory hazard feature an independent 2016 reconstruction, a measured flood-depth raster, or a total flood exposure map just because PPRI study work relied in part on the 2016 catastrophe.

## Two 2016 flood-mark sites: original horizontal WGS84 and Lambert-93 coordinates

1. [Montargis *Commissariat de police*](https://www.reperesdecrues.developpement-durable.gouv.fr/site/commissariat-de-police-0): official site \`CER_LO_16_S_174\`, Lambert-93 \`679817.12, 6766779.20\`, physical 2016 flood trace 85.557 m **NGF IGN 1969** measured afterwards by Cerema. For the **one returned 2023 PPRI class-F feature only**, the actual in-memory point-in-ring/inside-hole test produced **0 polygon overlaps**.
2. [Montargis *Sous-préfecture*](https://www.reperesdecrues.developpement-durable.gouv.fr/site/sous-prefecture): official site \`CER_LO_16_S_175\`, Lambert-93 \`680192.03, 6766742.32\`, source type **oral testimony** rather than independently surveyed physical flood trace; related flood level 86.482 m NGF IGN 1969. For the **same one class-F feature**, the in-memory geometry test produced **1 polygon overlap**, outside all 455 interior-hole exclusions.

These are **2016 point locations joined against a later 2023 hazard category**, not an accuracy comparison of recorded 2016 water-surface elevations. The police site lying **outside the single returned first class-F feature** does **not** prove it lay outside other PPRI classes, the wider flood-risk area or actual May/June 2016 flooding. The Sous-préfecture site lying **inside** one class-F polygon does not verify independent 2016 water-depth or insured building loss. The two marks also have **different evidence provenance** and different spatial coordinates, so their numerical NGF69 levels must not be treated as two synchronized measurements of one horizontal plane.

The inspected GML includes multi-surface polygon exteriors/holes and a large envelope. We checked point membership without converting the source Lambert-93 x/y into unverified WGS84 precision, using independently published **Lambert-93 site coordinates** from the national flood-mark records. A later CRS transformation is not needed for this *local* inclusion test.

## Executable next step merged behind exact CI checks

The [new offline original-GML scope tester](../../research_runners/loing2016_ppri2023_one_gml_spatial_audit_v0.py) reads a **bounded local WFS XML/GML file (max 8 MiB)** and:

- Requires the exact provider WFS 2.0 FeatureCollection, \`numberReturned=1\`, layer name, January-2023 PPRI code, original \`SRCE_ANNEE\` blank, and projected \`EPSG::2154\` CRS; refuses a silently changed source or invented 2016 year.
- Parses every \`gml:Polygon\` part and all \`gml:interior\` rings, validates closed 2D positions and finite bounded Lambert-93 coordinates, and returns per-site point-in-polygon matches with exact-boundary ambiguity explicitly marked.
- Computes a SHA-256 of **the local input bytes only**. A computed hash is **not independent proof of source origin**; a trusted acquisition receipt must also verify provider URL, HTTP headers, original byte identity, access authorization and dataset-specific rights.
- Rejects DTD/entities, malformed XML, unknown raster/feature types or extra model approval fields by contract.
- **Always refuses** historical 2016 original ZIP/ZICH provenance, source/calibration independence, 2016 building depth and gross/net insured-loss admission.

[15 synthetic offline tests](../../tests/test_loing2016_ppri2023_one_gml_spatial_audit_v0.py) exercise source scope, multi-surface coverage, hole exclusion, exact edge ambiguity, wrong CRS/vintage, malicious DTD, malformed and nonfinite GML and fake data rights; tests do **not** claim to repackage the actual large original GML response.

A separately authorized execution lane can save the real \`COUNT=1\` GET response as a local GML and then run:

\`\`\`sh
python research_runners/loing2016_ppri2023_one_gml_spatial_audit_v0.py --gml-file /local/verified-single-ppri-feature.gml
python -m unittest discover -s tests -p 'test_loing2016_ppri2023_one_gml_spatial_audit_v0.py' -v
python scripts/check_all.py
\`\`\`

## Remaining actual 2016 event source gate

The target remains **the independently original 2016 Loing flood ZIP/ZICH or 2021 DDT event-specific AZI GIS raster/vector**, with actual acquisition date, original data rights, input-mark lineage (including 2017's 68 selected and DDT 2021 corrections) and independently surveyed high-water marks held out from the model. Only then can a 2016 building-vintage exposure overlay and physically justified flood-depth-vulnerability loss calculation follow. The 2023 PPRI GML test is a **real spatial parsing/provenance demonstration**, not the missing 2016 observation.
