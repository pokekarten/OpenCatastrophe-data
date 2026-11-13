<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# FEMA USA Structures: correct current 2026 national ArcGIS item/view binding

**2026-11-13 original metadata observation; research only.** No building
geometry, individual structure row, address, parcel, insurer value, API query
or provider asset bytes were downloaded or retained. All three exact public
metadata source HTTP response bodies below were transiently decoded and
SHA-256 hashed with an implementation tested against the empty-string and
`abc` reference vectors. No HTTP status header is claimed from this
metadata capture.

## Identity correction and exact original REST receipts

The older canonical `access/fema.usa-structures.json` incorrectly used a
discoverable but **regionally scoped, different ArcGIS public service item**
as though it identified the national FEMA USA Structures source. We
verified the **actual Esri public item linked from FEMA's USA Structures
Hub** and its matching FeatureServer view.

| Original public endpoint | Observed original bytes | SHA-256 | Reviewed identity |
| --- | ---: | --- | --- |
| [Current public Esri item](https://www.arcgis.com/sharing/rest/content/items/0ec8512ad21e4bb987d7e848d14e7e24?f=json) | **9,601** | `90b735393979db65b83896bea85beee13b368cccc31a747e0a826c3807d4822d` | `0ec8512ad21e4bb987d7e848d14e7e24`; owner `Esri_US_Federal_Data`; public; published `CC BY 4.0` label |
| [Current national-feature view metadata](https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/USA_Structures_View/FeatureServer?f=pjson) | **4,164** | `d755bc79c1e3c3b52eb8abc60130b87cbd94840ec899b14e227ebd5130049ba7` | `serviceItemId=0ec8512...`, full extent `latestWkid=3857`, layer `0: USA_Structures_A` |
| [Previous incorrectly associated regional service](https://services.arcgis.com/VhMjCzR3cIjEkh7L/arcgis/rest/services/USA_Structures/FeatureServer?f=pjson) | **4,815** | `950a0bcf61dd665ac71a168ec473e1d588554e94d4ddea9aa05bf33bfb660100` | **Different** `serviceItemId=a51353d9b1d14b2ea3dc2f2eefb220d3`, localized extent `latestWkid=3452` |

The public national service has a Web Mercator `fullExtent` spanning
approximately x=-19,668,243 to +19,386,343 m; its
`initialExtent` may show a small Pacific locality and is NOT the intended
geographic-coverage test. The regional old service instead exposes a
localized `fullExtent` around x=3,658,908 to 3,787,030 (feet)
and must not be used to conclude national USA Structures coverage.

[Official FEMA Hub USA Structures view](https://gis-fema.hub.arcgis.com/datasets/fedmaps::usa-structures/about)
reports 2026 data currency, states that this view is updated periodically,
and describes its modeled building polygons for structures larger than
450 sq ft. [Federal Data.gov FEMA-0209 record](https://catalog.data.gov/dataset/usa-structures)
has a separate 2025 modification timestamp and points to the federal
government-works notice. These are different discovery/vintage layers:
the federal catalog, the FEMA Hub, and the independently confirmed
Esri public FeatureServer view must not be treated as identical asset releases.

## Exact rights and usage boundary

The public Esri item metadata itself declares `CC BY 4.0` in the item's
`licenseInfo`. That verifies a **published view item licence label**;
it does NOT resolve all upstream attributes or location-linked third-party
rights and does NOT independently establish service-level commercial
automation, rate limits, entitlement to unrestricted API extraction,
raw building-feature redistribution or permitted use for policyholder
underwriting decisions. These remain unknown in the canonical contract.

This research observation validates **metadata and service-item identity only**.
It does not validate a complete 146-million-building record count, actual
full dataset bytes, releases by state, boundary accuracy, construction
attributes, insured value or suitable CAT exposure/model inputs. It does not
grant source/model admission. In the current canonical contract, status stays
`documented_only`, executable probe `none`, commercial automation
`unknown`, model-input approval **false**.

## Reproducible independent offline check

`scripts/preflight_fema_usa_structures_2026_item_v0.py` consumes the
two saved **original** public metadata JSON bodies, never calls a provider,
and checks that the public Esri item ID, CC BY licence label,
FeatureServer metadata `serviceItemId`, layer identity, geometry type
and national-coordinate-system extent all agree:

```sh
python -m scripts.preflight_fema_usa_structures_2026_item_v0 \
  --item-json /trusted/private/2026_item_original.json \
  --service-json /trusted/private/2026_view_original.json
python -m unittest tests.test_preflight_fema_usa_structures_2026_item_v0 -v
```

No source JSON bodies belong in this public repository. The checker
emits hashes and bounded metadata only, with explicit no-feature/no-admission
flags. The synthetic regression suite rejects the wrong regional Esri
item, local projected extent, license/owner drift, unsafe JSON, different
layer/geometry and oversize inputs.

**Next independent gate:** determine precise Esri/FEMA usage rights for
commercial *automated* metadata requests and any bounded GIS attribute
access; freeze a fixed source release/vintage and state/territory coverage
before original low-byte feature sampling, private research storage,
and separately reviewed modelling. Do not follow arbitrary service links.
