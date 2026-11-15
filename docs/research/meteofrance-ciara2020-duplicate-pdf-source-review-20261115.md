<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Ciara 2020: official Seine-Maritime duplicate station-PDF original-byte comparison

As of 15 November 2026, the earlier source audit documented eight verified unique station PDFs among nine 72-hour-quality-complete Ciara stations in north France. One Seine-Maritime station had multiple exact official PDF source-catalogue records. No record was selected or admitted.

This experiment reopens the source question without revealing station identifiers: the exact SHA-256-pinned 2020-2024 departmental original is parsed and the quality-complete Ciara station cohort is reconstructed internally. Every official primary Météo-France PDF resource record referring to the single ambiguous station is validated for exact department, title, source UUID, HTTPS provider path, and original declared byte length. At most six candidate PDFs are acquired in temporary CI memory, their complete byte length and PDF signature/tail verified, and their original SHA-256 values compared. Only candidate counts, byte-equality results, and a private-station-ID-bound digest are published; original provider PDFs, URLs, IDs, and hourly measured data remain out of Git.

Authoritative sources: https://www.data.gouv.fr/datasets/fiches-dinformations-sur-les-stations and the April 2026 station-ID harmonization notice at https://confluence-meteofrance.atlassian.net/wiki/spaces/OpenDataMeteoFrance/pages/1603796993 .

Byte-equal PDFs prove duplicate resource bytes, not the identity of a February 2020 sensor or historic location. Byte-different PDFs expose a real provider-version conflict. Either result keeps the instrument-history, site relocation, wind-hour aggregation, ERA5/grid-point model-skill, rights admission, and annual AAL/OEP/AEP gates closed until separately verified. The network workflow is a one-off branch probe and will become manual-only after source evidence and full CI checks.
