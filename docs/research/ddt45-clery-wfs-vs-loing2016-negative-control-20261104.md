<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# DDT45 2026-11-04: original Cléry WFS availability is NOT 2016 Montargis flood truth

**Primary-source public metadata review only. No vector feature, ZIP original file, original HTTP response byte hash, historical flood extent layer, or insurer exposure admitted.**

## Actually executed original publisher lookup

The [French governmental DDT45 dataset record](https://www.data.gouv.fr/datasets/zones-inondables-en-dehors-des-zones-reglementaires-des-ppri-2), exact national catalogue ID `67377bc98609c51859c40b28`, lists:

| Original-source field | Provider-verifiable finding |
| --- | --- |
| Official publisher | Direction Départementale des Territoires du Loiret (DDT45) |
| Published source description | `Zones enveloppes de toutes les crues connues, soit par modélisation, soit par constat sur le terrain.` = envelopes of **all known floods**, from models or ground observation |
| Dataset licence | `lov2`, French Licence Ouverte 2.0 (dataset-level licence, not a claim that individual records represent 2016 physical evidence) |
| Exact public Geo-IDE Atom archive identifier | `756ece59-3ac3-448e-a644-5c2c31daa161` |
| Original public Atom ZIP route | [Geo-IDE `GetResource`](https://atom.geo-ide.developpement-durable.gouv.fr/atomArchive/GetResource?id=756ece59-3ac3-448e-a644-5c2c31daa161&dataType=dataset) |
| Original public WFS `GetCapabilities` | [Geo-IDE public WFS](https://ogc.geo-ide.developpement-durable.gouv.fr/wxs?map=/opt/data/stack/mapfiles/1.4/org_38032/756ece59-3ac3-448e-a644-5c2c31daa161.internet.map&SERVICE=WFS&REQUEST=GetCapabilities) |
| Actual public WFS response | A single bounded intermediary metadata query returned **HTTP 200**, WFS versions including `2.0.0`, and a feature identified in the metadata as **`N_INOND_HORSPPRI_CLERY`** (`ZINF_S_045` title suffix). It did not return original feature bytes |
| Advertised `WGS84BoundingBox` | West `2.76257501317139`; south `48.0382890910261`; east `3.13472665244762`; north `48.1469782244935` |
| Advertised geographic reference availability | `EPSG:2154` among supported server CRS; not a proof of any downloaded feature's CRS/geometry validity |

The original public Atom archive download **did not succeed** through the accessible container route. No ZIP file exists on disk from that attempted operation; no SHA-256, ZIP file list, geometry topology or source event-date attribute is available. The error may reflect an intermediary/access path, **not** provider unavailability. A `GetCapabilities` service reply, although useful live evidence, cannot be treated as geospatial source-byte authentication.

## The negative geographic proof against the original 2016 research marker

The original [French government's official Montargis `Commissariat de police` high-water-mark site](https://www.reperesdecrues.developpement-durable.gouv.fr/site/commissariat-de-police-0), `CER_LO_16_S_174`, lists **WGS84 longitude `2.72937190`, latitude `48.00108820`**, with 2016 event trace and separately measured **85.557 m NGF IGN 1969** water surface. This exact *site* identity is not the same thing as a full Montargis municipal boundary.

Both original flood-mark coordinates are numerically **outside** the official Cléry WFS published rectangle:

- WFS western limit `2.76257501317139` E is **east of** the mark longitude `2.72937190` E;
- WFS southern limit `48.0382890910261` N is **north of** the mark latitude `48.00108820` N.

A source feature cannot cover a point **outside its advertised feature-envelope rectangle**, unless the service itself is incorrect or has changed: either case must trigger independent re-review. This is a **reliable negative control** for this *specific marker*, not a proof that **no** Cléry flood geometry touches any part of the wider Loing drainage basin. The published `N_INOND_HORSPPRI_CLERY` layer is **not the correct source for a first Montargis water-depth validation slice**.

Independently, the DDT45 source describes a **multi-event flood envelope**, mixing reconstructed and observed sources of potentially different vintages. Thus even for a location actually inside this WFS region, it is NOT a single dated 2016 observed flood perimeter, 2016 water-surface height, 2016 asset flood depth, held-out gauge observation, or insured claim.

[The tiny pure offline exclusion checker](../../research_runners/loing2016_clery_wfs_spatial_exclusion_v0.py) freezes and compares **only these first-party reviewed metadata fields** and deliberately reports `published_wfs_bbox_contains_montargis_2016_mark=false`, `layer_is_2016_event_specific=false` and all data/rights/insured-loss/model approvals as false. Ten synthetic/source-metadata regression tests [here](../../tests/test_loing2016_clery_wfs_spatial_exclusion_v0.py) guard against guessed/expanded bboxes, fabricated 2016-vintage flags, coordinate/precision coercion and other false approvals. These are **metadata-scoping tests, not hydro-model skill tests**.

```sh
python -m unittest discover -s tests -p 'test_loing2016_clery_wfs_spatial_exclusion_v0.py' -v
python scripts/check_all.py
```

## Exclude other misleading source interpretations

The separate [DRIEAT historical PHEC downloadable ZIP](https://www.drieat.ile-de-france.developpement-durable.gouv.fr/atlas-des-zones-inondees-par-les-plus-hautes-eaux-a244.html) is a compilation of highest-known historical floods. The direct provider download link found in its page resolves to `/IMG/zip/phec-2006.zip`, not an authenticated 2016 Loing flood asset. Its own documentation gives historical examples including the **1910 Seine**, **1926 Oise** and **1955 Marne**. The 1.9 MiB advertised source ZIP was not retrievable through the available external file-download path. The mere presence of `Loing` as a watercourse name cannot turn this historical compilation into a Montargis June 2016 validation product.

No original 2016 Cléry or Montargis geodata were acquired. For the actual 2016 event trial, focus instead on **the final DDT45 Loing Aval 2021 AZI original event-specific GIS**, the **2017 original DRIEE selected 68 high-water mark identity list** and **2016 Copernicus EMSN028/EMSR165 exact AOI acquisition and provider asset rights**, already documented in the repository. A clean CartoZI/VIGInond result is model/data transformation evidence, not independent survey ground truth. Do not use any unrelated PPRI regulatory, multi-event, or PHEC composite geometry as a 2016 observation just because the service is downloadable or holds a broad flood-related name.

**Verdict:** Licence and WFS technical metadata verified; **direct geographic match to Montargis 2016 gauge mark DISPROVED**. Actual event original-source rights, geodata, water depths and independent validation still blocked.
