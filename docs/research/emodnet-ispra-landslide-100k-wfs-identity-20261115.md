<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EMODnet / ISPRA 100k submarine landslide polygons: WFS identity contradiction (2026-11-15)

**Source:** \`emodnet.geology.geological-events\` (broad non-admitted landscape candidate).
**One exact product under review:** Submarine Landslides Polygons (100k).
**Upstream metadata UUID:** \`ecb22f233db3b5c3dfbe94939df786605a2cac3c\`.
**Data provision:** EMODnet Geology / Italian Geological Survey (ISPRA); original contributors may differ.
**Scope:** independent T0 research and offline synthetic gate only; *no WFS request or vector feature acquired in this change*.

## Authoritative evidence checked (T0)

1. [EGDI basic metadata](https://metadata.europe-geology.eu/record/basic/ecb22f233db3b5c3dfbe94939df786605a2cac3c): advertises the exact WFS resource name \`ispra:landslide_pol_100k_2023\`; its page shows source revision 2023-07-28 and geographic bounds roughly -31.50..69.00 longitude, 27.50..82.00 latitude. The document identifies this as a 1:100,000 submarine landslide *polygon occurrence* layer, not a hazard return-period map.
2. [EGDI full metadata](https://metadata.europe-geology.eu/record/full/ecb22f233db3b5c3dfbe94939df786605a2cac3c): advertises **a different WFS name** \`ispra:landslide_pol_100k\`, revision 2025-09-04, broader geographic bounds -104.010..68.678 longitude and 3.373..82.080 latitude. Its metadata timestamp and source revision are distinct, and the revised polygon layer cannot silently be assumed to have the same geometry or coverage as the basic-page 2023 product.
3. [EMODnet web-service documentation](https://emodnet.ec.europa.eu/en/emodnet-web-service-documentation): authoritative service family for **Events and Probabilities** is the ISPRA WFS 2.0.0 endpoint \`https://drive.emodnet-geology.eu/geoserver/ispra/wfs\`; its WMS endpoint is visualization, not data acquisition.
4. [EMODnet Terms of Use](https://emodnet.ec.europa.eu/en/terms-use-emodnet-online-services-data-and-data-products): EMODnet aggregates heterogeneous partner datasets; users must check the individual metadata and original data owners' rights. EMODnet-produced products are generally EU CC BY 4.0 unless otherwise indicated; it does *not* turn the entire combined WFS catalogue into a single source-rights decision.
5. **Product-specific metadata:** both EGDI pages state **CC BY 4.0**, no public-access restriction, ISPRA as metadata contact and dataset scale 1:100,000. The source is compiled from mapped partner datasets/literature. Listed polygons cover **greater than 10 hectares**. The absence of mapped polygons is **not evidence of absence** of submarine landslides.

## Explicit contradiction and current verdict

\`basic\` and \`full\` are **two representations of the same UUID**, but disclose **different WFS layer names, revisions and bounding boxes**. An XML capabilities result must establish which name the live service actually exposes. A passing webpage read or the presence of either upstream link is **not** a provider-origin feature receipt. This is a blocking *version/asset identity* discrepancy and not an arbitrary choice between similar aliases.

For this *individual* layer, the official metadata contains a CC BY 4.0 source-rights statement. Do **not** promote the broad \`access/emodnet.geology.geological-events.json\` contract to \`dataset_rights_status=verified\`; it contains several other event families and possibly different originator restrictions. Likewise, the no-restriction public-access statement does not alone establish unlimited commercial **automated** polling, original asset redistribution review scope or scientific CAT admission.

## Reproducible next gate

The standalone offline script \`scripts/audit_emodnet_ispra_landslide_capabilities_v0.py\` accepts only a **caller-supplied, maximum 256 KiB original-byte candidate** from an independently reviewed, bounded WFS 2.0.0 GetCapabilities request. It compares the two exact upstream names, rejects both-present/none-present cases and malformed or unsafe XML, requires one coherent 100k polygon title and EPSG:4326 default CRS, and emits only aggregate metadata with a **local input hash**. The script does **not** fetch the WFS, verify a response as original, read GetFeature vectors, interpret geomorphology or authorize use.

Manual next step (only after explicit WFS request rate/terms review): one frozen provider-origin \`GetCapabilities\` request, response HTTP status and final URL, UTC, content-type, original SHA-256 and byte count; then check exact service feature-type name, GetFeature output encoding, schema, CRS and separate individual data-originator acknowledgement before planning a *small* AOI/feature-count-bounded feature probe. Never use an unbounded GetFeature query or use these polygons as annual event occurrence frequency or tsunami loss calibration without an independent model and validation programme.

## Gates

| Gate | Verdict |
| --- | --- |
| T0 publisher/EGDI metadata and CC BY statement | checked for **one exact polygon layer**, contradictory service names |
| WFS capabilities T1 original provider HTTP + bytes | **not tested** |
| T2 credentials | none documented for this WFS; not a live access test |
| T3 bounded feature original sample + checksum | **not tested** |
| T4 science/model admission | **blocked** pending version, feature/attributes, scale, completeness and damage-model validation |
| NeonDB source-asset write | **none**; no unverified source bytes persisted |

Offline tests are independently synthetic; they are not evidence that the provider currently serves either exact WFS layer name.
