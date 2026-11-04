-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- READ ONLY: run against Neon insurance-risk-core/insurance MAIN
-- branch br-late-recipe-ba1cr8hc. NEVER assume this shares SQL tables
-- with a validation branch. Secondary directory is discovery only.
WITH directory AS (
  SELECT count(*) AS candidate_rows,
         count(DISTINCT country_slug) AS country_slugs,
         count(DISTINCT (lower(display_name), country_slug)) AS distinct_name_country,
         count(*) FILTER (WHERE raw_provider_sha256 ~ '^[0-9a-f]{64}$') AS original_sha_rows,
         count(*) FILTER (WHERE model_input_approved) AS approved_rows
    FROM research.insurer_directory_candidate_v0
), verified AS (
  SELECT count(*) FILTER (WHERE identity_status='verified') AS verified_rows,
         count(*) FILTER (WHERE identity_status='verified' AND domicile_country='US') AS verified_us_rows
    FROM entity.organization
)
SELECT 'main_worldwide_directory'::text AS evidence_scope,
       current_database() AS database_name,
       (current_database()='insurance') AS expected_database,
       directory.candidate_rows,
       directory.country_slugs,
       directory.distinct_name_country,
       directory.original_sha_rows,
       directory.approved_rows,
       verified.verified_rows AS verified_legal_entities,
       verified.verified_us_rows AS verified_us_legal_entities,
       false::boolean AS automatic_us_carrier_coverage_inferred,
       false::boolean AS model_input_approved,
       CASE
         WHEN current_database()<>'insurance' THEN 'BLOCKED_WRONG_DATABASE'
         WHEN directory.candidate_rows=0 THEN 'BLOCKED_EMPTY_DIRECTORY'
         WHEN directory.original_sha_rows<>directory.candidate_rows
           THEN 'BLOCKED_ORIGINAL_PROVIDER_SHA_COVERAGE'
         WHEN directory.approved_rows<>directory.candidate_rows
           THEN 'BLOCKED_REGULATOR_IDENTITY_AND_SOURCE_ADMISSION'
         WHEN verified.verified_us_rows=0
           THEN 'BLOCKED_NO_VERIFIED_US_LEGAL_ENTITIES'
         ELSE 'BLOCKED_INDEPENDENT_COMPANY_GEO_EXPOSURE_VALIDATION'
       END AS first_gate
  FROM directory CROSS JOIN verified;