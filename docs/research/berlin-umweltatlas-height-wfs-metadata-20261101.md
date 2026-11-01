<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin Umweltatlas 2022: source-specific building-height metadata lane

**Non-admission source discovery / WFS capabilities only.** This does not request building
polygons, roof heights, address attributes, model input, or insurer records.

## Official product identity

- Publisher catalogue:
  https://daten.berlin.de/datensaetze/gebaudehohen-umweltatlas-wfs-d918088d
- Official download service, metadata operation **only**:
  https://gdi.berlin.de/services/wfs/ua_gebaeudehoehen?request=GetCapabilities&service=WFS
- Product: Berlin Umweltatlas **Gebäudehöhen 2022**; portal publication 2022-04-06,
  dataset update 2023-08-23; underlying Berlin LoD2/ALKIS original
  footprint vintage reported as 2022-04-07. These are distinct dates,
  not the current monthly ALKIS WFS data vintage.
- Listed data rights in the publisher catalogue: **dl-de-zero-2.0**.
  The repository candidate stays `rights_review_status=not_reviewed`,
  `scientific_review_status=not_reviewed`, `admission_status=not_admitted`.
  Scaled access and use of any specific attributes require a new review.

Official field definitions include `role_txt` (building versus building part),
`hoehe` (first/roof height in metres), `dachart` (roof form), `geschosse`
(storeys), and `grundrissaktualitaet` (source footprint vintage),
as well as source-method codes for ground/roof estimation. This is not the
same namespace as the current `alkis_gebaeude:gebaeude` WFS. The original
height methodology uses LoD2 with digital surface/terrain data; where a height
cannot be determined, **3m may be used as a placeholder**. Never interpret
such a default as a measured 3m roof height; no field coverage or value
quality is proven by a metadata GetCapabilities request.

## Bounded initial operation

`research_runners/berlin_umweltatlas_gebaeudehoehen_wfs_metadata_v0.py`:

- One exact HTTPS GetCapabilities request, fixed official URL; no arbitrary
  bbox, GetFeature, query, authentication, redirected host, proxy or pagination.
- Max **2 MiB**, 35-second timeout, XML mime check and parser against
  DTD/entity expansion, unsupported WFS versions and wrong source layers.
- Only public layer names and declared source CRS, source response byte count,
  SHA-256 and UTC receipt in the JSON output.
- New, separate canonical discovery identity:
  `de.berlin.umweltatlas-gebaeudehoehen-2022.wfs`.
- Explicit proof limits: historical source is related to ALKIS/LoD2,
  neither independent physical ground truth nor model-admitted exposure.

Review tests without network:

```bash
python -m unittest tests.test_berlin_umweltatlas_gebaeudehoehen_wfs_metadata_v0 -v
```

## First independently observed original provider metadata receipt — 2026-11-01

The dedicated [GitHub Actions source run 41322717682](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41322717682)
**succeeded** on merged main commit
`7710132e1466a89dab5b9b87234414d9802de2bb`, after seven
synthetic endpoint/XXE/redirect/schema tests passed.

- UTC receipt: `2026-11-01T15:44:17.559617+00:00`.
- Exactly one original source GetCapabilities (no GetFeature).
- Official WFS version **2.0.0**, **one** advertised feature type:
  `ua_gebaeudehoehen:gebaeudehoehen`.
- Advertised source CRSs: EPSG **25832**, **25833**, **3857**, **4258**,
  **4326**. Layer names/CRSs are official *service metadata*, not source
  polygon identity or height field proof.
- Official source XML **96,123 bytes**, response SHA-256
  `29911c913544dd1e04ef75fb370ff6d5729de9fa50d26f62634830b1effcd642`.
- Executing source metadata script SHA-256
  `ccaf32170cc1b335eaca6eeb0f8e1253720e83d160cefb859a15a27fea10a070`.
- No individual building footprint, Firsthöhe, roof form, floor count,
  provider personal attributes, source XML bytes, insurer values, or model
  permissions were acquired, persisted or approved.

This verifies **metadata endpoint reachability and one layer name only**.
It does **not** establish `hoehe`, `dachart`, `geschosse` or
`role_txt` live-field availability/non-null coverage, data completeness,
measured versus algorithmically imputed (including 3 m) heights, or
independent building crosswalk. These require a separately reviewed
source-specific DescribeFeatureType preflight and bounded original sample.

## Later attribute science gates (not authorized by this PR)

1. Independently pin exact WFS layer, version, date, EPSG and first-height
   measurement versus estimated/imputed metadata.
2. Fix a tiny, bounded ROI and source release. Distinguish real buildings
   and parts and veto split/merge false identity.
3. Evaluate polygon alignment with monthly ALKIS and quantify temporal
   drift; **never** use feature positions, addresses or names as keys.
4. Exclude missing or imputed heights from measured-height validation
   unless original method codes prove the interpretation.
5. Rights/legal and scientific review, independent validation holdout,
   uncertainty and separate model-admission decision before any CAT use.

Other official reference pages:
- https://www.berlin.de/umweltatlas/nutzung/gebaeudehoehen/fortlaufend-aktualisiert/datengrundlage/
- https://www.berlin.de/umweltatlas/nutzung/gebaeudehoehen/fortlaufend-aktualisiert/methode/
- https://fbinter.stadt-berlin.de/fb_daten/beschreibung/umweltatlas/datenformatbeschreibung/Datenformatbeschreibung_06_10_1gebhoehen.html
