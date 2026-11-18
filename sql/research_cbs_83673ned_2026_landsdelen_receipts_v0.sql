-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Private research-only, read-only reconciliation for two exact original
-- intermediary-returned CBS 83673NED five-row region/tenure observations.
-- This does NOT call CBS, migrate Neon, save source response bytes, grant
-- additional API rights or approve any CAT insured replacement-cost model.
--
-- Every underlying value is selected from current PRIVATE Neon research
-- summaries by fixed official source URL + full bounded JSON response SHA256.
-- A future CBS revision or a changed original source hash fails the pinned
-- provenance gate until independently reviewed. The SHA over sample_json is
-- the private canonical JSONB receipt digest, NOT original provider body SHA.
WITH pinned AS (
    SELECT s.*,
        CASE
            WHEN s.source_url =
              'https://opendata.cbs.nl/ODataApi/OData/83673NED/TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028867%27&$top=5'
              AND s.provider_response_sha256 =
              '2b224f3f6546f7c5f5905a6b226a3471c986eaf2d7cd16b7001f720ff26e9fe0'
              AND s.sample_json->>'tenure' = 'rental'
              AND s.sample_json->>'original_response_bytes' = '1457'
            THEN 'rental'
            WHEN s.source_url =
              'https://opendata.cbs.nl/ODataApi/OData/83673NED/TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028868%27&$top=5'
              AND s.provider_response_sha256 =
              '67a2647fc84a812569caf0d128d1b7f7cd8a3d8e2f427fc2ebe28ab68ed39ed3'
              AND s.sample_json->>'tenure' = 'owner'
              AND s.sample_json->>'original_response_bytes' = '1459'
            THEN 'owner'
        END AS checked_tenure,
        ROW_NUMBER() OVER (PARTITION BY s.source_url ORDER BY s.sample_id DESC) AS version_rank
    FROM research.source_sample_v0 s
    WHERE s.source_id = 'nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned'
      AND s.sample_kind = 'observed_values'
      AND s.research_only IS TRUE
      AND s.model_input_approved IS FALSE
      AND s.source_byte_persistence_authorized IS FALSE
      AND s.sample_sha256 = encode(sha256(convert_to(s.sample_json::text, 'UTF8')), 'hex')
      AND s.sample_json->>'official_publisher_revision' = '2026-08-20T02:00:00'
      AND s.sample_json->>'rolling_12_month_period' = '2026VJ06'
      AND s.sample_json->>'publication_status' = 'Voorlopig'
      AND s.sample_json->'source_native_field_crosswalk'->>'GemiddeldeBouwkostenPerM_2' = 'EUR per m³ (cubic metre), NOT per square metre'
      AND s.sample_json->'source_native_field_crosswalk'->>'GemiddeldeBouwkostenPerM_3' = 'EUR per m² (square metre), NOT per cubic metre'
      AND s.sample_json->>'raw_original_response_body_persisted' = 'false'
      AND s.sample_json->>'direct_trusted_repository_runner_executed' = 'false'
),
trusted_original_github AS (
    SELECT s.sample_id, s.source_url, s.provider_response_sha256,
           s.sample_json->>'original_response_bytes' AS original_response_bytes,
           ROW_NUMBER() OVER (PARTITION BY s.source_url ORDER BY s.sample_id DESC) AS proof_rank
    FROM research.source_sample_v0 s
    WHERE s.source_id = 'nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned'
      AND s.sample_kind = 'public_metadata'
      AND s.research_only IS TRUE
      AND s.model_input_approved IS FALSE
      AND s.source_byte_persistence_authorized IS FALSE
      AND s.sample_sha256 = encode(sha256(convert_to(s.sample_json::text, 'UTF8')), 'hex')
      AND s.sample_json->>'profile' =
          'oc-cbs-83673ned-2026-regional-two-github-trusted-original-direct-v0'
      AND s.sample_json->>'github_run_id' = '43580334849'
      AND s.sample_json->>'github_job_id' = '132403533534'
      AND s.sample_json->>'github_job_conclusion' = 'success'
      AND s.sample_json->>'original_period_status' = 'Voorlopig'
      AND s.sample_json->>'source_revision' = '2026-08-20T02:00:00'
      AND s.sample_json->>'original_response_sha256' = s.provider_response_sha256
      AND s.sample_json->>'direct_github_runner_executed' = 'true'
      AND s.sample_json->>'strict_repository_runner_executed' = 'true'
      AND s.sample_json->>'raw_original_response_bytes_saved' = 'false'
      AND s.sample_json->>'model_input_approved' = 'false'
      AND s.sample_json->>'original_aggregate_region_rows' = '5'
),
receipts AS (
    SELECT p.* FROM pinned p
    JOIN trusted_original_github d ON d.source_url = p.source_url
       AND d.provider_response_sha256 = p.provider_response_sha256
       AND d.original_response_bytes = p.sample_json->>'original_response_bytes'
       AND d.proof_rank = 1
    WHERE p.checked_tenure IS NOT NULL
      AND p.version_rank = 1
      AND jsonb_array_length(p.sample_json->'actual_public_aggregate_rows') = 5
),
unpacked AS (
    SELECT
      s.sample_id,
      s.checked_tenure AS tenure,
      s.provider_response_sha256 AS bounded_response_sha256,
      s.sample_json->>'official_publisher_revision' AS provider_revision,
      v.entry->>'native_RegionS_code' AS region_code,
      v.entry->>'region_name' AS region_name,
      v.entry->>'native_Eigendom_code' AS original_tenure_code,
      v.entry->>'native_period' AS original_rolling_period,
      (v.entry->>'native_row_ID')::integer AS native_row_id,
      (v.entry->>'average_permitted_eur_per_m3')::integer AS eur_per_m3,
      (v.entry->>'average_permitted_eur_per_m2')::integer AS eur_per_m2,
      (v.entry->>'average_permitted_eur_per_dwelling_thousands')::integer AS thousands_eur_per_dwelling,
      (v.entry->>'mean_permitted_dwelling_volume_m3')::integer AS mean_m3,
      (v.entry->>'mean_permitted_dwelling_floor_area_m2')::integer AS mean_m2
    FROM receipts s
    CROSS JOIN LATERAL jsonb_array_elements(
        s.sample_json->'actual_public_aggregate_rows'
    ) AS v(entry)
),
quality AS (
    SELECT
        COUNT(*) = 10
        AND COUNT(DISTINCT sample_id) = 2
        AND COUNT(DISTINCT (region_code, tenure)) = 10
        AND COUNT(DISTINCT region_code) = 5
        AND COUNT(*) FILTER (WHERE tenure = 'rental') = 5
        AND COUNT(*) FILTER (WHERE tenure = 'owner') = 5
        AND COALESCE(BOOL_AND(
          region_code ~ '^(NL01|LD0[1-4])  $'
          AND original_rolling_period = '2026VJ06'
          AND original_tenure_code =
              CASE WHEN tenure = 'rental' THEN 'A028867' ELSE 'A028868' END
          AND eur_per_m3 > 0 AND eur_per_m2 > 0
          AND thousands_eur_per_dwelling > 0 AND mean_m3 > 0 AND mean_m2 > 0
          AND ABS(eur_per_m3 * mean_m3 -
                  thousands_eur_per_dwelling * 1000) <= 2000
          AND ABS(eur_per_m2 * mean_m2 -
                  thousands_eur_per_dwelling * 1000) <= 2000
        ), FALSE) AS passes_completeness_and_units
    FROM unpacked
)
SELECT
  u.sample_id, u.tenure,
  u.region_code, u.region_name,
  u.original_rolling_period,
  u.eur_per_m3, u.eur_per_m2, u.thousands_eur_per_dwelling,
  u.mean_m3, u.mean_m2,
  u.native_row_id, u.bounded_response_sha256,
  '2026VJ06 preliminary; new-dwelling permit 12-month rolling mean; excluded VAT'
    AS source_context,
  'research_only_trusted_original_GitHub_HTTP_and_SHA_valid; NOT model approved'::text AS research_gate
FROM unpacked u
CROSS JOIN quality q
WHERE q.passes_completeness_and_units IS TRUE
UNION ALL
SELECT
  NULL::bigint, NULL::text,
  NULL::text, NULL::text,
  NULL::text,
  NULL::integer, NULL::integer, NULL::integer,
  NULL::integer, NULL::integer,
  NULL::integer, NULL::text,
  '2026VJ06 one or both direct original GitHub receipts absent, SHA-invalid or source values malformed'::text,
  'BLOCKED_missing_or_malformed_research_evidence_or_direct_original_proof'::text
FROM quality q
WHERE q.passes_completeness_and_units IS NOT TRUE
ORDER BY region_code NULLS LAST, tenure;
