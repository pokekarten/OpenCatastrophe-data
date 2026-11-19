-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Source-scoped, metadata-only separate INSPIRE product rights.
-- No original provider data, coordinates, crop/farmer fields or model admissions.
-- Distinct from earlier raw brpgewas OGC Collection product rights.

INSERT INTO research.source_usage_rights_v0
(source_id,product_scope,use_case,rights_result,evidence_url,evidence_observed_on,
 rationale,scientific_model_admission,original_asset_admitted)
VALUES
('nl.rvo.brp-gewaspercelen.2025', 'RVO/PDOK INSPIRE-harmonised Gewaspercelen: EXACT current Collection metadata GET only (no raw BRP features, 2025 immutable archive or parcel rights)', 'internal_research', 'allowed', 'https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1?f=html&lang=en', DATE '2026-11-13',
 'The official public INSPIRE service explicitly documents anonymous, no-charge Collection metadata access. Authorizes inspection of exact public collection ID, CRS, bbox and source semantics only; no individual parcel geometry or 2025 archive admission.', false, false),
('nl.rvo.brp-gewaspercelen.2025', 'RVO/PDOK INSPIRE-harmonised Gewaspercelen: EXACT current Collection metadata GET only (no raw BRP features, 2025 immutable archive or parcel rights)', 'automated_api_access', 'allowed', 'https://www.pdok.nl/how-to-faq', DATE '2026-11-13',
 'Exactly ONE non-recurring, manually reviewed source-locked first-party GitHub main push GET to Collection metadata (20 sec, 65536 byte budget, no redirect/retry). PDOK service PDC and fair-use do not authorize parcel/bulk/recursive crawling or expanded commercial API traffic.', false, false),
('nl.rvo.brp-gewaspercelen.2025', 'RVO/PDOK INSPIRE-harmonised Gewaspercelen: EXACT current Collection metadata GET only (no raw BRP features, 2025 immutable archive or parcel rights)', 'internal_neon_metadata', 'allowed', 'https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1?f=html&lang=en', DATE '2026-11-13',
 'Private Neon insurance research may retain source URL, original first-party metadata response SHA-256 and byte count, UTC, exact trusted main run/job/commit and license-scope flags only. Source response body and parcel fields are expressly forbidden.', false, false),
('nl.rvo.brp-gewaspercelen.2025', 'RVO/PDOK INSPIRE-harmonised Gewaspercelen: EXACT current Collection metadata GET only (no raw BRP features, 2025 immutable archive or parcel rights)', 'internal_neon_source_sample', 'allowed', 'https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1?f=html&lang=en', DATE '2026-11-13',
 'Only a sanitized public_metadata sample of collection identity, CRS/extent Boolean checks, hashes and trusted original GET timing is permitted. No individual feature, geometry, crop, farmer, area or insured value may be stored.', false, false),
('nl.rvo.brp-gewaspercelen.2025', 'RVO/PDOK INSPIRE-harmonised Gewaspercelen: EXACT current Collection metadata GET only (no raw BRP features, 2025 immutable archive or parcel rights)', 'commercial_cat_modelling', 'unknown', 'https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1?f=html&lang=en', DATE '2026-11-13',
 'Open data (publiek) does not independently establish a product-version-2025 raw national parcel redistribution licence, crop/farmer identifier privacy posture, or independent source scientific correctness; no commercial CAT model input or insurer portfolio use approved.', false, false),
('nl.rvo.brp-gewaspercelen.2025', 'RVO/PDOK INSPIRE-harmonised Gewaspercelen: EXACT current Collection metadata GET only (no raw BRP features, 2025 immutable archive or parcel rights)', 'external_raw_redistribution', 'unknown', 'https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1?f=html&lang=en', DATE '2026-11-13',
 'The public interface and no-cost authentication statement are NOT rights or authorization to publish precise original parcel polygons, features, crop attributes or a fixed 2025 source archive in Git. Requires exact original release rights and repository admission.', false, false),
('nl.rvo.brp-gewaspercelen.2025', 'RVO/PDOK INSPIRE-harmonised Gewaspercelen: EXACT current Collection metadata GET only (no raw BRP features, 2025 immutable archive or parcel rights)', 'published_derived_results', 'conditional', 'https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1?f=html&lang=en', DATE '2026-11-13',
 'A provenance-only description that identifies the official public INSPIRE collection is acceptable; any derived geospatial crop or insurance TIV publication requires original 2025 source-rights, farmer-location/privacy and science review before release.', false, false)
ON CONFLICT (source_id,product_scope,use_case) DO NOTHING;
