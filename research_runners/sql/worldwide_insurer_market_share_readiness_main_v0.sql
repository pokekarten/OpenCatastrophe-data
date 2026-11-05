-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Worldwide insurer market-share readiness, MAIN-ONLY read-only receipt.
-- Intended database: insurance-risk-core / insurance.
-- Intended branch: br-late-recipe-ba1cr8hc (main).
-- This does NOT infer licensed insurer population, company market shares,
-- group ownership, actual insured risk locations or CAT model eligibility.
-- Do not run on validation-schema-20261031: its tables are different.
WITH directory AS (
  SELECT count(*) AS candidate_rows,
         count(DISTINCT country_slug) AS country_slugs,
         count(DISTINCT (lower(display_name), country_slug)) AS distinct_name_market_pairs,
         count(*) FILTER (WHERE model_input_approved IS TRUE) AS admitted_directory_rows,
         count(*) FILTER (WHERE raw_provider_sha256 ~ '^[0-9a-f]{64}$') AS original_sha_rows
    FROM research.insurer_directory_candidate_v0
),
organization AS (
  SELECT count(*) FILTER (WHERE identity_status = 'verified') AS verified_legal_entities,
         count(*) FILTER (
           WHERE identity_status = 'verified' AND domicile_country = 'US'
         ) AS verified_us_entities
    FROM entity.organization
),
candidates AS (
  SELECT count(*) AS entity_candidate_rows,
         count(*) FILTER (WHERE verified_organization_id IS NULL) AS unresolved_candidate_rows
    FROM entity.organization_candidate
),
identifiers AS (
  SELECT count(*) FILTER (
           WHERE is_verified IS TRUE AND identifier_scheme = 'GLEIF_LEI'
         ) AS verified_lei_rows,
         count(*) FILTER (
           WHERE is_verified IS TRUE AND identifier_scheme ILIKE '%NAIC%'
         ) AS verified_naic_identifier_rows
    FROM entity.organization_identifier
),
other AS (
  SELECT (SELECT count(*) FROM entity.organization_relationship)
           AS verified_group_relationship_rows,
         (SELECT count(*) FROM entity.published_metric)
           AS published_company_metric_rows,
         (SELECT count(*) FROM entity.licence_observation)
           AS licence_observation_rows
)
SELECT current_database() AS database_name,
       directory.*,
       organization.*,
       candidates.*,
       identifiers.*,
       other.*,
       false AS worldwide_complete_census_verified,
       false AS company_market_shares_computable_from_core,
       CASE
         WHEN current_database() <> 'insurance'
           THEN 'BLOCKED_WRONG_DATABASE'
         WHEN other.published_company_metric_rows = 0
           THEN 'BLOCKED_NO_COMPANY_PREMIUM_METRICS'
         WHEN identifiers.verified_naic_identifier_rows = 0
           THEN 'BLOCKED_NO_VERIFIED_NAIC_COMPANY_KEYS'
         ELSE 'BLOCKED_MISSING_MATCHED_OFFICIAL_MARKET_DENOMINATORS'
       END AS first_market_share_gate
  FROM directory
 CROSS JOIN organization
 CROSS JOIN candidates
 CROSS JOIN identifiers
 CROSS JOIN other;
