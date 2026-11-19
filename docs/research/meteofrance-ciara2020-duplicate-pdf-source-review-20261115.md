<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Ciara 2020: official Seine-Maritime duplicate station-PDF original-byte comparison

As of 15 November 2026, the earlier source audit documented eight verified unique station PDFs among nine 72-hour-quality-complete Ciara stations in north France. One Seine-Maritime station had multiple exact official PDF source-catalogue records. No record was selected or admitted.

This experiment reopens the source question without revealing station identifiers: the exact SHA-256-pinned 2020-2024 departmental original is parsed and the quality-complete Ciara station cohort is reconstructed internally. Every official primary Météo-France PDF resource record referring to the single ambiguous station is validated for exact department, title, source UUID, HTTPS provider path, and original declared byte length. At most six candidate PDFs are acquired in temporary CI memory, their complete byte length and PDF signature/tail verified, and their original SHA-256 values compared. Only candidate counts, byte-equality results, and a private-station-ID-bound digest are published; original provider PDFs, URLs, IDs, and hourly measured data remain out of Git.

Authoritative sources: https://www.data.gouv.fr/datasets/fiches-dinformations-sur-les-stations and the April 2026 station-ID harmonization notice at https://confluence-meteofrance.atlassian.net/wiki/spaces/OpenDataMeteoFrance/pages/1603796993 .

Byte-equal PDFs prove duplicate resource bytes, not the identity of a February 2020 sensor or historic location. Byte-different PDFs expose a real provider-version conflict. Either result keeps the instrument-history, site relocation, wind-hour aggregation, ERA5/grid-point model-skill, rights admission, and annual AAL/OEP/AEP gates closed until separately verified. The initial source-byte proof completed successfully; the live network workflow has been changed to manual-only after the observed result. Full repository CI is required for the final commit.


## Actual official source-byte result, 15 November 2026

The [successful one-off original data workflow 43747605431](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43747605431) re-checked exact original Seine-Maritime hourly-gust gzip SHA-256
`406dbf752f042254bfade674f606c2035eeb2560d06314324c9bd4694936780d` and the authoritative Météo-France PDF-resource catalogue SHA-256
`d0b465ae592e1d1a586f87aed4f29292bc063c3ca3d73d489f42af1d3b913a6b`.

| Source property | Executed original-byte result |
|---|---:|
| Ambiguous 72-hour-quality-complete Ciara station identities | 1 |
| Exact official PDF resource metadata records | 2 |
| Distinct resource UUIDs / original URLs | 2 / 2 |
| Successfully verified original PDF bytes across both files | 1,390,940 |
| Distinct original PDF SHA-256 values | **2** |
| Are the original PDF bytes identical? | **NO** |
| Station/site/wind instrument history validated for February 2020? | **NO** |
| Production hazard/source admission | **BLOCKED** |

A station-ID-bound digest of the two exact resource-UUID and original-byte-SHA receipts, without leaking the station identity or individual PDF URLs, is
`08fa1dc144c415d9485a3f2f358e0fb9b9eb952bb1db8221c2b0afe5120612d9`.

**Interpretation:** this is genuine **document-version divergence**, not a duplicated catalogue listing pointing to identical PDF bytes. The two PDFs must be reviewed for their actual site placement dates, anemometer/sensor history, measurement class and any station renumbering before one can represent the February 2020 measurement. The source PDF-byte proof **does not select or admit either version**. It also does not prove that the two documents have scientifically meaningful textual differences: distinct PDF bytes can reflect metadata, images or regenerated layout. That further distinction needs content-level inspection.

No source PDF bytes, actual station identifiers, station-specific locations or original wind time series were written to Git.
